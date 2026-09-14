"""
Document Ingestion & Embedding Pipeline (Steps 3 & 4 of PRD)
- Splits raw BIS documents by natural structure (headings, numbered clauses, sections).
- Preserves section and clause labels for verifiable citations.
- Generates embeddings and persists chunks into local ChromaDB.
"""
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

try:
    from app.config import settings
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import settings


def extract_document_title(content: str, filename: str) -> str:
    """Extracts the top-level document title from markdown `# Title` or returns cleaned filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return Path(filename).stem.replace("_", " ")


def chunk_markdown_document(content: str, filename: str) -> List[Dict[str, Any]]:
    """
    Rule-based structural splitter for markdown BIS documents:
    - Splits by ## Sections and ### Clauses.
    - Preserves document name, section title, and clause identifier.
    - Attaches rich metadata to each chunk for citations.
    """
    doc_title = extract_document_title(content, filename)
    file_stem = Path(filename).stem

    chunks: List[Dict[str, Any]] = []
    lines = content.splitlines()

    current_section = "General Overview"
    current_clause: Optional[str] = None
    current_lines: List[str] = []

    def flush_chunk():
        nonlocal current_lines, current_section, current_clause
        text_block = "\n".join(current_lines).strip()
        if not text_block:
            current_lines = []
            return

        sec_slug = re.sub(r"[^a-zA-Z0-9]+", "_", current_section)[:30]
        clause_slug = re.sub(r"[^a-zA-Z0-9]+", "_", current_clause or "general")[:30]
        chunk_id = f"{file_stem}__{sec_slug}__{clause_slug}__{len(chunks) + 1}"

        header_parts = [f"Document: {doc_title}", f"Section: {current_section}"]
        if current_clause:
            header_parts.append(f"Clause: {current_clause}")
        contextual_text = f"[{' | '.join(header_parts)}]\n\n{text_block}"

        chunks.append({
            "id": chunk_id,
            "document_name": doc_title,
            "section": current_section,
            "clause": current_clause or "",
            "source_file": Path(filename).name,
            "text": contextual_text,
            "raw_content": text_block,
        })
        current_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            continue

        if stripped.startswith("## "):
            flush_chunk()
            current_section = stripped[3:].strip()
            current_clause = None
            continue

        if stripped.startswith("### "):
            flush_chunk()
            current_clause = stripped[4:].strip()
            continue

        if stripped in ["---", "***", "___"]:
            continue

        current_lines.append(line)

    flush_chunk()
    return chunks


def chunk_pdf_document(file_path: str) -> List[Dict[str, Any]]:
    """Extracts text from PDF documents using pypdf and chunks by pages / sections."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required to process PDF files. Run 'pip install pypdf'.")

    reader = PdfReader(file_path)
    filename = os.path.basename(file_path)
    file_stem = Path(file_path).stem
    doc_title = file_stem.replace("_", " ")

    chunks: List[Dict[str, Any]] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            continue

        chunk_id = f"{file_stem}__page_{page_num}"
        section_label = f"Page {page_num}"
        contextual_text = f"[Document: {doc_title} | Section: {section_label}]\n\n{text}"

        chunks.append({
            "id": chunk_id,
            "document_name": doc_title,
            "section": section_label,
            "clause": f"Page {page_num}",
            "source_file": filename,
            "text": contextual_text,
            "raw_content": text,
        })

    return chunks


def chunk_document(file_path: str) -> List[Dict[str, Any]]:
    """Reads a single document (.md, .txt, or .pdf) and returns labeled structural chunks."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return chunk_pdf_document(file_path)

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    return chunk_markdown_document(content, file_path)


def chunk_all_documents(directory: Optional[str] = None) -> List[Dict[str, Any]]:
    """Reads all documents in raw_documents directory and returns all labeled chunks."""
    dir_path = directory or settings.raw_documents_directory
    all_chunks: List[Dict[str, Any]] = []

    if not os.path.exists(dir_path):
        print(f"Warning: Raw documents directory not found at: {dir_path}")
        return all_chunks

    files = sorted(os.listdir(dir_path))
    for filename in files:
        if filename.startswith(".") or filename.endswith(".gitkeep") or filename.endswith(".json"):
            continue

        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path) and Path(filename).suffix.lower() in [".md", ".txt", ".pdf"]:
            doc_chunks = chunk_document(file_path)
            print(f"  Processed '{filename}': generated {len(doc_chunks)} chunks.")
            all_chunks.extend(doc_chunks)

    return all_chunks


def get_embedding_function():
    """
    Returns embedding function:
    - If GEMINI_API_KEY is configured, uses Google Gemini embeddings.
    - Otherwise defaults to Chroma's local ONNX all-MiniLM-L6-v2 embedding function (zero cost/no key).
    """
    api_key = getattr(settings, "gemini_api_key", "").strip()
    if api_key:
        try:
            return embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                api_key=api_key,
                model_name=getattr(settings, "embedding_model", "models/embedding-001")
            )
        except Exception as e:
            print(f"Notice: Could not initialize Gemini embedding function ({e}). Using local Chroma embeddings.")

    return embedding_functions.DefaultEmbeddingFunction()


def ingest_all_documents():
    """
    Offline indexing pipeline (Step 4 of PRD):
    1. Reads & structurally chunks all documents in raw_documents/.
    2. Initializes local Chroma vector database at chroma_persist_directory.
    3. Embeds and stores all chunks with source/section metadata.
    """
    print("=" * 60)
    print("BIS Setu — Document Ingestion & Embedding Pipeline (Step 4)")
    print("=" * 60)

    # 1. Generate structural chunks
    chunks = chunk_all_documents()
    print(f"\nTotal chunks to index: {len(chunks)}")
    if not chunks:
        print("No chunks to index. Exiting.")
        return

    # 2. Setup ChromaDB client & collection
    persist_dir = settings.chroma_persist_directory
    os.makedirs(persist_dir, exist_ok=True)
    print(f"Using local ChromaDB persist directory: {persist_dir}")

    client = chromadb.PersistentClient(path=persist_dir)
    emb_fn = get_embedding_function()

    # Reset collection for clean indexing
    col_name = settings.chroma_collection_name
    try:
        client.delete_collection(name=col_name)
        print(f"Cleared existing collection '{col_name}'.")
    except Exception:
        pass

    collection = client.create_collection(
        name=col_name,
        embedding_function=emb_fn,
        metadata={"description": "BIS official documents and guidelines"}
    )

    # 3. Add chunks to Chroma in batches
    batch_size = 50
    total_added = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        ids = [c["id"] for c in batch]
        documents = [c["text"] for c in batch]
        metadatas = [
            {
                "document_name": c["document_name"],
                "section": c["section"],
                "clause": c["clause"],
                "source_file": c["source_file"],
            }
            for c in batch
        ]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        total_added += len(batch)
        print(f"  Indexed {total_added}/{len(chunks)} chunks into ChromaDB...")

    count = collection.count()
    print(f"\nSuccessfully populated ChromaDB collection '{col_name}' with {count} chunks.")
    print("=" * 60)
    return collection


if __name__ == "__main__":
    ingest_all_documents()

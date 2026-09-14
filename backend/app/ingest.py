"""
Document Ingestion & Chunking Pipeline (Steps 3 & 4 of PRD)
- Splits raw BIS documents by natural structure (headings, numbered clauses, sections).
- Preserves section and clause labels for verifiable citations.
- Generates embeddings and persists chunks into local ChromaDB.
"""
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from app.config import settings
except ImportError:
    # Allow running standalone
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

        # Build clean unique ID
        sec_slug = re.sub(r"[^a-zA-Z0-9]+", "_", current_section)[:30]
        clause_slug = re.sub(r"[^a-zA-Z0-9]+", "_", current_clause or "general")[:30]
        chunk_id = f"{file_stem}__{sec_slug}__{clause_slug}__{len(chunks) + 1}"

        # Context header helps embeddings capture document & section context
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
        # Check for top-level title
        if stripped.startswith("# ") and not stripped.startswith("## "):
            continue

        # Check for Section header (##)
        if stripped.startswith("## "):
            flush_chunk()
            current_section = stripped[3:].strip()
            current_clause = None
            continue

        # Check for Clause / Sub-heading (###)
        if stripped.startswith("### "):
            flush_chunk()
            current_clause = stripped[4:].strip()
            continue

        # Skip horizontal dividers
        if stripped in ["---", "***", "___"]:
            continue

        current_lines.append(line)

    flush_chunk()
    return chunks


def chunk_pdf_document(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text from PDF documents using pypdf and chunks by pages / sections.
    """
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
    """
    Reads a single document (.md, .txt, or .pdf) and returns labeled structural chunks.
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return chunk_pdf_document(file_path)

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    return chunk_markdown_document(content, file_path)


def chunk_all_documents(directory: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Reads all documents in the raw_documents directory and returns all labeled chunks.
    """
    dir_path = directory or settings.raw_documents_directory
    all_chunks: List[Dict[str, Any]] = []

    if not os.path.exists(dir_path):
        print(f"Warning: Raw documents directory not found at: {dir_path}")
        return all_chunks

    files = sorted(os.listdir(dir_path))
    for filename in files:
        if filename.startswith(".") or filename.endswith(".gitkeep"):
            continue

        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path) and Path(filename).suffix.lower() in [".md", ".txt", ".pdf"]:
            doc_chunks = chunk_document(file_path)
            print(f"  Processed '{filename}': generated {len(doc_chunks)} chunks.")
            all_chunks.extend(doc_chunks)

    return all_chunks


if __name__ == "__main__":
    print("=" * 60)
    print("BIS Setu — Document Chunking Test (Step 3)")
    print("=" * 60)
    chunks = chunk_all_documents()
    print(f"\nTotal chunks generated across all documents: {len(chunks)}\n")

    if chunks:
        sample = chunks[0]
        print("Sample Chunk Preview:")
        print(f"  ID:            {sample['id']}")
        print(f"  Document:      {sample['document_name']}")
        print(f"  Section:       {sample['section']}")
        print(f"  Clause:        {sample['clause']}")
        print(f"  Source File:   {sample['source_file']}")
        print(f"  Excerpt:       {sample['raw_content'][:180]}...")
        print("=" * 60)

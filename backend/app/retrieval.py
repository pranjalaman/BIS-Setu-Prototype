"""
Vector Retrieval Pipeline (Step 5 of PRD)
- Embeds user query using the same embedding model as indexing.
- Queries persistent ChromaDB collection for top-k relevant chunks.
- Formats retrieved chunks with rich source metadata for citation generation.
"""
from typing import List, Dict, Any, Optional
import os
import chromadb

try:
    from app.config import settings
    from app.ingest import get_embedding_function
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import settings
    from app.ingest import get_embedding_function

_client = None
_collection = None


def get_chroma_collection():
    """Returns singleton cached ChromaDB collection."""
    global _client, _collection
    if _collection is None:
        persist_dir = settings.chroma_persist_directory
        _client = chromadb.PersistentClient(path=persist_dir)
        emb_fn = get_embedding_function()
        _collection = _client.get_collection(
            name=settings.chroma_collection_name,
            embedding_function=emb_fn
        )
    return _collection


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 4,
    score_threshold: Optional[float] = 1.6
) -> List[Dict[str, Any]]:
    """
    Retrieves top_k relevant chunks from ChromaDB for the given query.
    Filter out chunks with cosine distance above score_threshold if desired.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        return []

    try:
        collection = get_chroma_collection()
    except Exception as e:
        print(f"Error connecting to ChromaDB collection: {e}")
        return []

    results = collection.query(
        query_texts=[cleaned_query],
        n_results=top_k
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if "distances" in results else [None] * len(documents)
    ids = results.get("ids", [[]])[0]

    retrieved: List[Dict[str, Any]] = []
    for chunk_id, doc_text, meta, dist in zip(ids, documents, metadatas, distances):
        # If distance exceeds threshold, it may be irrelevant
        if score_threshold is not None and dist is not None and dist > score_threshold:
            continue

        retrieved.append({
            "id": chunk_id,
            "text": doc_text,
            "document_name": meta.get("document_name", "BIS Document"),
            "section": meta.get("section", ""),
            "clause": meta.get("clause", ""),
            "source_file": meta.get("source_file", ""),
            "distance": dist
        })

    return retrieved

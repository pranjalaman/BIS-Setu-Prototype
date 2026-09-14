"""
Document Ingestion Pipeline (Step 3 & 4 of PRD)
- Splits raw BIS documents by natural structure (headings, numbered clauses, sections).
- Generates embeddings.
- Persists chunks in local Chroma DB.
"""
import os
import chromadb
from app.config import settings

def chunk_document(file_path: str):
    """
    Reads a document and splits by section/clause identifiers.
    Returns list of dicts: {'text': ..., 'source': ..., 'section': ...}
    """
    # To be implemented in Step 3
    pass

def ingest_all_documents():
    """
    Scans raw_documents folder, chunks each document, embeds, and stores in Chroma collection.
    """
    # To be implemented in Step 4
    pass

if __name__ == "__main__":
    print("Starting document ingestion pipeline...")
    ingest_all_documents()

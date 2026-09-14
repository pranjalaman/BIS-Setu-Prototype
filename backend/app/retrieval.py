"""
Vector Retrieval Pipeline (Step 5 of PRD)
- Embeds user query using the same embedding model.
- Queries Chroma collection for top-k relevant chunks.
"""
from typing import List, Dict, Any
import chromadb
from app.config import settings

def get_chroma_client():
    return chromadb.PersistentClient(path=settings.chroma_persist_directory)

def retrieve_relevant_chunks(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Retrieves top_k relevant chunks from Chroma DB for the given user query.
    """
    # To be implemented in Step 5
    return []

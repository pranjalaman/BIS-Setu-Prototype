"""
Step 4 Test Checkpoint (Mandatory per PRD)
- Embeds a hardcoded test question.
- Queries local ChromaDB collection.
- Prints the top 3 matching chunks and their citations.
"""
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chromadb
from app.config import settings
from app.ingest import get_embedding_function

def test_query(question: str, top_k: int = 3):
    print("=" * 70)
    print(f"TEST QUESTION: {question}")
    print("=" * 70)

    client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
    emb_fn = get_embedding_function()

    try:
        collection = client.get_collection(
            name=settings.chroma_collection_name,
            embedding_function=emb_fn
        )
    except Exception as e:
        print(f"Error accessing collection '{settings.chroma_collection_name}': {e}")
        return

    results = collection.query(
        query_texts=[question],
        n_results=top_k
    )

    print(f"\nTop {top_k} Retrieved Chunks:\n")
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if "distances" in results else [None] * len(documents)

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), start=1):
        print(f"--- MATCH #{i} ---")
        print(f"Distance/Score: {dist}")
        print(f"Document:       {meta.get('document_name')}")
        print(f"Section:        {meta.get('section')}")
        print(f"Clause:         {meta.get('clause')}")
        print(f"Source File:    {meta.get('source_file')}")
        print("Excerpt:")
        lines = [l for l in doc.splitlines() if l.strip() and not l.startswith("[Document:")]
        excerpt = " ".join(lines)[:250]
        print(f"  \"{excerpt}...\"\n")

if __name__ == "__main__":
    # Test queries across core domains
    sample_questions = [
        "What are the three mandatory marks on gold jewellery and what is HUID?",
        "What is the penalty for unauthorized use of ISI mark under the BIS Act 2016?",
        "Are laptops and mobile phones covered under the Compulsory Registration Scheme?"
    ]

    for q in sample_questions:
        test_query(q, top_k=3)
        print("\n")

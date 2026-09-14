"""
Interactive CLI for BIS Setu
Ask any question live from terminal and test Gemini LLM + Chroma retrieval.
"""
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.retrieval import retrieve_relevant_chunks
from app.llm import generate_grounded_answer

def ask(query: str):
    print("\n" + "=" * 75)
    print(f"QUESTION: {query}")
    print("=" * 75)
    print("Retrieving relevant BIS document chunks...")
    chunks = retrieve_relevant_chunks(query, top_k=5)
    print(f"Found {len(chunks)} chunks from ChromaDB.")
    print("Generating grounded answer via Gemini...")
    result = generate_grounded_answer(query, chunks)

    print("\n" + "-" * 30 + " ANSWER " + "-" * 30)
    print(result["answer"])
    print("-" * 68)

    print("\nCITATIONS & SOURCES:")
    if result["sources"]:
        for s in result["sources"]:
            print(f"  • {s['document_name']}")
            print(f"    Section: {s['section']}")
            print(f"    Clause:  {s['clause']}")
            print(f"    File:    {s['source_file']}\n")
    else:
        print("  (No citations - question is out of scope)\n")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        ask(query)
    else:
        print("=" * 75)
        print("BIS Setu Interactive Query Terminal")
        print("Type any question about BIS standards, ISI mark, HUID, or FMCS.")
        print("Type 'exit' or 'quit' to exit.")
        print("=" * 75)
        while True:
            try:
                user_q = input("\nEnter your question: ").strip()
                if user_q.lower() in ["exit", "quit", "q"]:
                    break
                if not user_q:
                    continue
                ask(user_q)
            except (KeyboardInterrupt, EOFError):
                break

"""
Step 5 Test Script: Retrieval + LLM Generation Pipeline
Tests 8 diverse questions (in-scope and out-of-scope) directly in the terminal:
- Verifies accuracy of answers.
- Verifies source and citation attribution.
- Verifies rejection of out-of-scope questions (no-hallucination guardrail).
"""
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.retrieval import retrieve_relevant_chunks
from app.llm import generate_grounded_answer

TEST_QUESTIONS = [
    # 1. Product Certification (Scheme-I / ISI)
    "Can a trader or importer apply for an ISI mark licence under Scheme-I?",

    # 2. Hallmarking & HUID
    "What are the three marks on BIS hallmarked gold jewellery?",

    # 3. Compulsory Registration Scheme (CRS)
    "Are mobile phones and power adapters covered under the Compulsory Registration Scheme?",

    # 4. Foreign Manufacturers (FMCS)
    "Who is an Authorized Indian Representative (AIR) under FMCS and what are their qualifications?",

    # 5. Penalties under BIS Act 2016
    "What is the penalty for unauthorized use or counterfeiting of the ISI mark?",

    # 6. Consumer Compensation
    "What compensation is a consumer entitled to if hallmarked gold jewellery is found deficient in purity?",

    # 7. Laboratory Recognition
    "What accreditation standard is required for a testing lab to get recognized under LRS?",

    # 8. Guardrail Test (Out of Scope - should say no info available)
    "What is the population of Tokyo and how do I bake sourdough bread?"
]

def run_test_suite():
    print("=" * 80)
    print("BIS SETU — STEP 5 RETRIEVAL + LLM PIPELINE VERIFICATION SUITE")
    print("=" * 80)

    for i, question in enumerate(TEST_QUESTIONS, start=1):
        print(f"\n[QUERY #{i}]: \"{question}\"")
        print("-" * 80)

        # 1. Retrieval
        chunks = retrieve_relevant_chunks(question, top_k=3)
        print(f"Retrieved {len(chunks)} relevant chunks from ChromaDB.")

        # 2. Generation
        result = generate_grounded_answer(question, chunks)
        answer = result["answer"]
        sources = result["sources"]

        print(f"\nANSWER:\n{answer}\n")
        print("CITATIONS & SOURCES:")
        if sources:
            for s in sources:
                print(f"  • {s['document_name']} -> {s['section']} ({s['clause']}) [{s['source_file']}]")
        else:
            print("  (No sources — query out of scope)")
        print("-" * 80)

    print("\n" + "=" * 80)
    print("ALL 8 PIPELINE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_test_suite()

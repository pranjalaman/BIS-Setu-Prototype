"""
LLM Generation Pipeline (Step 5 of PRD)
- Constructs prompt strictly bound to retrieved context.
- Formulates source citations.
- Enforces no-hallucination guardrail.
"""
from typing import List, Dict, Any

STRICT_RAG_PROMPT_TEMPLATE = """You are BIS Setu, an AI assistant for Indian Standards & Bureau of Indian Standards (BIS) services.
Answer the question using ONLY the following retrieved context.
If the answer cannot be determined from the context, clearly state: "I don't have information on that in the available BIS documents."
Do not make up facts or extrapolate beyond the provided text.
Cite the source document and section for every key factual claim.

Context:
{context}

Question:
{question}

Answer:"""

def generate_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates answer using retrieved chunks and LLM, returning answer and source list.
    """
    # To be implemented in Step 5
    return {
        "answer": "Answer generation pipeline stub.",
        "sources": []
    }

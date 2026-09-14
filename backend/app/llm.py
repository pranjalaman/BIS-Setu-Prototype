"""
LLM Generation Pipeline (Step 5 of PRD)
- Strictly bounds answer generation to retrieved BIS document chunks.
- Enforces no-hallucination guardrail: if not in context, explicitly states lack of information.
- Formulates verifiable citations referencing document name, section, and clause.
"""
from typing import List, Dict, Any, Optional
import os
import re

try:
    from app.config import settings
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import settings

STRICT_RAG_PROMPT_TEMPLATE = """You are BIS Setu, an authoritative AI Assistant for Indian Standards & Bureau of Indian Standards (BIS) services.

STRICT INSTRUCTIONS:
1. Answer the question using ONLY the provided retrieved context below.
2. If the answer cannot be determined directly from the context, respond EXACTLY with:
   "I do not have information on that in the available Bureau of Indian Standards (BIS) documents."
3. Do NOT assume, extrapolate, or bring in external knowledge.
4. Keep the answer plain, clear, and direct.
5. At the end of your answer, list the exact source citations used.

RETRIEVED CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:"""


def format_context_for_prompt(chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved chunks into clean numbered blocks with clear source headers."""
    formatted_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        doc = chunk.get("document_name", "BIS Document")
        section = chunk.get("section", "")
        clause = chunk.get("clause", "")
        raw_text = chunk.get("text", "")

        header = f"[Source #{idx}: {doc}"
        if section:
            header += f" | {section}"
        if clause:
            header += f" | {clause}"
        header += "]"

        formatted_blocks.append(f"{header}\n{raw_text}")

    return "\n\n---\n\n".join(formatted_blocks)


def extract_sources_from_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicates and formats sources list from retrieved chunks."""
    seen = set()
    sources = []
    for c in chunks:
        doc = c.get("document_name")
        sec = c.get("section")
        cl = c.get("clause")
        key = (doc, sec, cl)
        if key not in seen:
            seen.add(key)
            sources.append({
                "document_name": doc,
                "section": sec,
                "clause": cl,
                "source_file": c.get("source_file", "")
            })
    return sources


def synthesize_offline_grounded_answer(query: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Fallback synthesis when no external LLM API key is configured.
    Extracts strictly matching statements from the retrieved chunks without hallucinating.
    """
    if not chunks:
        return "I do not have information on that in the available Bureau of Indian Standards (BIS) documents."

    # Check relevance threshold: if top match distance is too high (weak semantic match), reject
    top_chunk = chunks[0]
    dist = top_chunk.get("distance")
    if dist is not None and dist > 0.95:
        return "I do not have information on that in the available Bureau of Indian Standards (BIS) documents."

    # Extract factual points from the most relevant chunks
    points = []
    for c in chunks[:3]:
        text = c.get("text", "")
        # Remove context header bracket
        body = re.sub(r"^\[.*?\]\s*", "", text, flags=re.DOTALL).strip()
        lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#")]
        if lines:
            points.append(f"• **{c.get('section', '')} ({c.get('clause', '')})**:\n  " + " ".join(lines))

    header = "Based on official BIS documentation:\n\n"
    footer = "\n\n*(Note: Add your GEMINI_API_KEY to backend/.env to enable generative natural-language formatting)*"
    return header + "\n\n".join(points) + footer


def generate_grounded_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Core RAG generation function:
    1. Returns 'no information' if no chunks retrieved or relevance is too low.
    2. Calls Gemini LLM with strict context prompt if API key is present.
    3. Falls back to deterministic grounded synthesis if offline/no key.
    4. Returns structured answer and verified source list.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        return {
            "answer": "Please ask a specific question about BIS standards, certification, or services.",
            "sources": []
        }

    # Guardrail: If no chunks retrieved or best distance is very poor
    if not retrieved_chunks:
        return {
            "answer": "I do not have information on that in the available Bureau of Indian Standards (BIS) documents.",
            "sources": []
        }

    top_chunk = retrieved_chunks[0]
    dist = top_chunk.get("distance")
    if dist is not None and dist > 0.95:
        return {
            "answer": "I do not have information on that in the available Bureau of Indian Standards (BIS) documents.",
            "sources": []
        }

    sources = extract_sources_from_chunks(retrieved_chunks)
    api_key = getattr(settings, "gemini_api_key", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_name = getattr(settings, "llm_model", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)

            context_str = format_context_for_prompt(retrieved_chunks)
            prompt = STRICT_RAG_PROMPT_TEMPLATE.format(
                context=context_str,
                question=cleaned_query
            )

            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.0}
            )

            answer_text = response.text.strip() if response and response.text else ""
            if not answer_text:
                answer_text = "I do not have information on that in the available Bureau of Indian Standards (BIS) documents."

            return {
                "answer": answer_text,
                "sources": sources
            }
        except Exception as e:
            print(f"Gemini API call failed ({e}). Falling back to grounded synthesis.")

    # Offline / local synthesis fallback
    answer_text = synthesize_offline_grounded_answer(cleaned_query, retrieved_chunks)
    return {
        "answer": answer_text,
        "sources": sources
    }

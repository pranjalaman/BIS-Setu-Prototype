"""
LLM Generation Pipeline (Step 5 of PRD)
- Strictly bounds answer generation to retrieved BIS document chunks.
- Enforces no-hallucination guardrail: if not in context, explicitly states lack of information.
- Formulates verifiable citations referencing document name, section, and clause.
"""
from typing import List, Dict, Any, Optional
import os
import re
import warnings

# Suppress deprecation notice in terminal
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from app.config import settings
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import settings

STRICT_RAG_PROMPT_TEMPLATE = """You are BIS Setu, a helpful and friendly AI assistant for Indian Standards and Bureau of Indian Standards (BIS) services.

Your primary mission is to explain standards, certifications, and BIS schemes in simple, clear, layman-friendly English so that everyday citizens, consumers, students, and small business owners can easily understand them without getting overwhelmed by technical or legal jargon.

COMMUNICATION & STYLE GUIDELINES:
1. EXPLAIN IN SIMPLE LAYMAN'S TERMS:
   - Use straightforward, everyday conversational English. Avoid dry, bureaucratic, or excessively technical language.
   - Start with a clear 1-2 sentence overview in plain words ("In simple terms, ...").
   - Demystify technical terms whenever they appear. For example, explain what terms like "conformity assessment", "surveillance audit", "QCO", or "management systems" mean in plain everyday concepts (e.g., "surveillance audit — an annual on-site quality check to ensure standards are being followed").
   - Structure your response cleanly using bullet points, short paragraphs, or step-by-step points.

2. ACCURACY & STRICT GROUNDING:
   - Base your answer strictly on the facts present in the RETRIEVED CONTEXT below.
   - Recognize informal queries or slight variations (e.g. if the user asks "what is ISO 900", connect it to the relevant standard like IS/ISO 9001 from the context).
   - If a specific detail (like an exact fee, fine amount, or specialized technical clause) is not in the context, state simply and politely that this specific detail is not available in the current BIS documents.

3. HANDLING UNANSWERABLE OR MISSING INFORMATION:
   - NEVER give a vague or blunt one-liner like "I do not have information on that."
   - Explicitly identify and state WHICH information or topic the user is asking about.
   - Transparently explain that your current system lacks data for this specific topic because your knowledge base currently covers a curated set of official BIS documents (such as ISI Mark, Compulsory Registration Scheme, Hallmarking, Foreign Manufacturers Scheme, Management Systems Certification, and Ecomark), and the specific records or standard for this inquiry have not been ingested into your local database yet.
   - If the question is completely non-BIS related (e.g. general sports, cooking, coding), politely explain that BIS Setu is exclusively designed for Indian Standards and BIS services.
   - Always guide the user to check the official BIS portal (bis.gov.in) or ManakOnline (manakonline.in), or suggest searching by Indian Standard (IS) number.

RETRIEVED CONTEXT:
{context}

USER QUESTION:
{question}

HELPFUL LAYMAN ANSWER:"""


def build_missing_data_response(query: str) -> str:
    """
    Constructs a clear, transparent, and helpful response when information on a specific
    topic is missing from the indexed BIS dataset, explaining what is missing and why.
    """
    cleaned = query.strip().rstrip("?")
    return (
        f"I currently do not have enough specific information in my database regarding **\"{cleaned}\"**.\n\n"
        "My knowledge base is presently equipped with a curated set of official Bureau of Indian Standards (BIS) documents "
        "(covering schemes such as ISI Mark Certification, Compulsory Registration Scheme (CRS), Hallmarking, Foreign Manufacturers Scheme (FMCS), "
        "Management Systems Certification (IS/ISO 9001, 14001, 45001), Ecomark, and NITS Training).\n\n"
        "Because the specific standard, clause, or detailed records for your inquiry have not yet been ingested into my current dataset, "
        "I am unable to answer this accurately without risking misinformation.\n\n"
        "**Recommended Next Steps:**\n"
        "- Search the official Bureau of Indian Standards portal at [www.bis.gov.in](https://www.bis.gov.in) or [manakonline.in](https://www.manakonline.in).\n"
        "- If you know the relevant Indian Standard number (e.g., IS code) or product category, try asking with that specific standard name."
    )


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
        return build_missing_data_response(query)

    top_chunk = chunks[0]
    dist = top_chunk.get("distance")
    if dist is not None and dist > 1.65:
        return build_missing_data_response(query)

    points = []
    for c in chunks[:3]:
        text = c.get("text", "")
        body = re.sub(r"^\[.*?\]\s*", "", text, flags=re.DOTALL).strip()
        lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#")]
        if lines:
            points.append(f"• **{c.get('section', '')} ({c.get('clause', '')})**:\n  " + " ".join(lines))

    header = "Here is what the official BIS documentation explains in simple terms:\n\n"
    return header + "\n\n".join(points)


def generate_grounded_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Core RAG generation function:
    1. Returns structured missing data response if no chunks retrieved or relevance is too low.
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
            "answer": build_missing_data_response(cleaned_query),
            "sources": []
        }

    top_chunk = retrieved_chunks[0]
    dist = top_chunk.get("distance")
    if dist is not None and dist > 1.65:
        return {
            "answer": build_missing_data_response(cleaned_query),
            "sources": []
        }

    sources = extract_sources_from_chunks(retrieved_chunks)
    api_key = getattr(settings, "gemini_api_key", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model_name = getattr(settings, "llm_model", "gemini-2.5-flash")
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
                answer_text = build_missing_data_response(cleaned_query)

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

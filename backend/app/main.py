from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional

from app.config import settings
from app.retrieval import retrieve_relevant_chunks
from app.llm import generate_grounded_answer

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="BIS Setu - AI Assistant for Indian Standards & BIS Services",
)

# Serve raw documents for citations
app.mount("/documents", StaticFiles(directory=settings.raw_documents_directory), name="documents")

# Enable CORS for local React/Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User query about BIS standards/services")

class SourceCitation(BaseModel):
    document_name: str
    section: Optional[str] = None
    clause: Optional[str] = None
    source_file: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str
    sources: List[SourceCitation] = []

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.app_name,
        "version": settings.app_version,
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    """
    Core RAG Endpoint (Step 6 of PRD):
    1. Validates incoming question.
    2. Retrieves top relevant chunks from local ChromaDB.
    3. Prompts LLM with strict context-bounding and citation extraction.
    4. Returns grounded answer and verified citations.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )

    try:
        # Retrieve top 10 matching clauses
        chunks = retrieve_relevant_chunks(question, top_k=10)

        # Generate strictly grounded answer
        result = generate_grounded_answer(question, chunks)

        formatted_sources = [
            SourceCitation(
                document_name=s.get("document_name", "BIS Document"),
                section=s.get("section"),
                clause=s.get("clause"),
                source_file=s.get("source_file")
            )
            for s in result.get("sources", [])
        ]

        return AnswerResponse(
            answer=result["answer"],
            sources=formatted_sources
        )

    except Exception as e:
        print(f"Error processing /ask request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the answer: {str(e)}"
        )

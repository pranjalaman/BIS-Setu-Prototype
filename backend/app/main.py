from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="BIS Setu - AI Assistant for Indian Standards & BIS Services",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User's query about BIS standards/services")

class SourceCitation(BaseModel):
    document_name: str
    section: Optional[str] = None
    clause: Optional[str] = None
    excerpt: Optional[str] = None

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
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Placeholder for retrieval and LLM pipeline integration
    # Full implementation will be connected in Steps 3-5
    return AnswerResponse(
        answer="Walking skeleton endpoint ready. Retrieval pipeline pending document ingestion.",
        sources=[]
    )

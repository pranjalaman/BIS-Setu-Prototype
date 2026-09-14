# BIS Setu — AI Assistant for Indian Standards & BIS Services
### SIH 2026 | PS 26107 | Team ByteKode

BIS Setu is an AI-powered conversational assistant for Indian Standards, certification requirements (ISI, CRS, Hallmarking), and BIS services. It provides plain-language, source-backed answers with verifiable citations directly referencing official Bureau of Indian Standards documentation.

---

## 🏛️ Project Architecture

```
[React Frontend (Vite)]
       │  (POST /ask)
       ▼
[FastAPI Backend]
       │
       ├─► [Retrieval Pipeline: Query Embedding → ChromaDB Vector Search]
       │
       └─► [LLM Generation: Strict Context-Bound Prompting + Citations]
```

### Pipelines
1. **Offline Ingestion Pipeline**: Reads raw BIS documents from `backend/data/raw_documents/`, chunks by natural clauses/sections, generates embeddings, and persists to local ChromaDB.
2. **Query Pipeline**: User query is received via `POST /ask`, embedded with the same model, top-k chunks retrieved from ChromaDB, and passed to LLM for strictly grounded answer generation with exact citations.

---

## 📁 Repository Structure

```
BIS-Setu-Prototype/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI entrypoint (/ask endpoint)
│   │   ├── ingest.py         # Chunking + embedding ingestion script
│   │   ├── retrieval.py      # Vector search logic
│   │   ├── llm.py            # LLM prompt template & generation logic
│   │   └── config.py         # Pydantic environment configuration
│   ├── data/
│   │   ├── raw_documents/    # Curated real BIS documents (PDFs/Text)
│   │   └── chroma/           # Local Chroma vector database storage (git-ignored)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Clean chat interface with source citations
│   │   ├── App.css
│   │   ├── index.css         # Design tokens and base styles
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Gemini API Key (or supported LLM provider API key)

### 1. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY
```

### 2. Ingest BIS Documents (Offline step)
Place 5–10 curated BIS PDF or text documents into `backend/data/raw_documents/`, then run:

```bash
python -m app.ingest
```

### 3. Run FastAPI Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```
API Documentation will be accessible at: `http://localhost:8000/docs`

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend will be accessible at: `http://localhost:5173`

---

## 🔒 Guardrails & Principles
- **No Hallucinations**: Responses are strictly bound to retrieved BIS document chunks.
- **Verifiable Citations**: Every claim is cited with the source document and section name.
- **Zero Cloud DB Dependency**: Vector storage uses local ChromaDB for fast, cost-free, zero-config local prototyping.
- **Incremental Commits**: Commits follow structured feature progression according to the PRD.

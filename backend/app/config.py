import os
from pathlib import Path

# BASE_DIR is always the directory containing the 'app' directory, i.e., <repo_root>/backend
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_FILE)
except ImportError:
    pass

def _resolve_to_backend(val: str) -> str:
    if not val:
        return str(BASE_DIR)
    p = Path(val)
    if p.is_absolute():
        return str(p)
    clean = val.replace("\\", "/").lstrip("./")
    if clean.startswith("backend/"):
        clean = clean[8:]
    return str((BASE_DIR / clean).resolve())

try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator

    class Settings(BaseSettings):
        app_name: str = "BIS Setu API"
        app_version: str = "0.1.0"
        gemini_api_key: str = ""
        embedding_model: str = "models/embedding-001"
        llm_model: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        chroma_persist_directory: str = str(BASE_DIR / "data" / "chroma")
        chroma_collection_name: str = "bis_documents"
        raw_documents_directory: str = str(BASE_DIR / "data" / "raw_documents")

        @field_validator("chroma_persist_directory", "raw_documents_directory", mode="before")
        @classmethod
        def resolve_paths(cls, v: str) -> str:
            return _resolve_to_backend(v)

        class Config:
            env_file = str(ENV_FILE)
            env_file_encoding = "utf-8"
            extra = "ignore"

    settings = Settings()

except ImportError:
    from dataclasses import dataclass

    @dataclass
    class FallbackSettings:
        app_name: str = os.getenv("APP_NAME", "BIS Setu API")
        app_version: str = "0.1.0"
        gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        embedding_model: str = os.getenv("EMBEDDING_MODEL", "models/embedding-001")
        llm_model: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        chroma_persist_directory: str = _resolve_to_backend(os.getenv("CHROMA_PERSIST_DIRECTORY", "data/chroma"))
        chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "bis_documents")
        raw_documents_directory: str = _resolve_to_backend(os.getenv("RAW_DOCUMENTS_DIRECTORY", "data/raw_documents"))

    settings = FallbackSettings()

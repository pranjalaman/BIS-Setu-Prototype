import os

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        app_name: str = "BIS Setu API"
        app_version: str = "0.1.0"
        gemini_api_key: str = ""
        embedding_model: str = "models/embedding-001"
        llm_model: str = "gemini-1.5-flash"
        chroma_persist_directory: str = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma"
        )
        chroma_collection_name: str = "bis_documents"
        raw_documents_directory: str = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_documents"
        )

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            extra = "ignore"

    settings = Settings()

except ImportError:
    # Graceful fallback to dataclass / standard library when pydantic_settings is not yet installed
    from dataclasses import dataclass

    @dataclass
    class FallbackSettings:
        app_name: str = os.getenv("APP_NAME", "BIS Setu API")
        app_version: str = "0.1.0"
        gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        embedding_model: str = os.getenv("EMBEDDING_MODEL", "models/embedding-001")
        llm_model: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        chroma_persist_directory: str = os.getenv(
            "CHROMA_PERSIST_DIRECTORY",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma")
        )
        chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "bis_documents")
        raw_documents_directory: str = os.getenv(
            "RAW_DOCUMENTS_DIRECTORY",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_documents")
        )

    settings = FallbackSettings()

"""
Lecture et validation de la configuration de l'application via Pydantic Settings.

Toutes les variables sont lues depuis le fichier .env (voir .env.example)
et exposees sous forme d'un objet `settings` fortement type, importable
partout dans l'application.
"""

from functools import lru_cache
from typing import List, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration globale de l'application, lue depuis les variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = "AssIA"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-me-super-secret-key"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ------------------------------------------------------------------
    # Base de donnees
    # ------------------------------------------------------------------
    database_url: str = "sqlite:///./data/app.db"

    # ------------------------------------------------------------------
    # LLM (Ollama Local)
    # ------------------------------------------------------------------
    llm_provider: Literal["ollama"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b"

    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048
    llm_max_retries: int = 3

    # ------------------------------------------------------------------
    # Embeddings (Ollama Local)
    # ------------------------------------------------------------------
    embedding_provider: Literal["ollama"] = "ollama"
    ollama_embedding_model: str = "nomic-embed-text"
    embedding_dimensions: int = 768

    # ------------------------------------------------------------------
    # Vector store
    # ------------------------------------------------------------------
    vector_store_provider: Literal["chroma"] = "chroma"
    chroma_persist_dir: str = "./data/chroma_db"
    chroma_collection_name: str = "documents"

    # ------------------------------------------------------------------
    # Keycloak / Auth
    # ------------------------------------------------------------------
    keycloak_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "assistant-reunions"
    keycloak_client_id: str = "assistant-reunions-app"
    keycloak_client_secret: str = ""
    keycloak_admin_user: str = "admin"
    keycloak_admin_password: str = "admin"

    jwt_algorithm: str = "RS256"
    access_token_expire_minutes: int = 60

    # ------------------------------------------------------------------
    # Upload / documents
    # ------------------------------------------------------------------
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 25
    allowed_extensions: str = ".pdf,.docx,.txt,.md"

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # ------------------------------------------------------------------
    # Proprietes derivees
    # ------------------------------------------------------------------
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",") if ext.strip()]

    @field_validator("app_env")
    @classmethod
    def _validate_env(cls, value: str) -> str:
        return value.lower()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
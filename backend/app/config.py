import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database — defaults to local SQLite for zero-setup demo.
    # Swap DATABASE_URL to a Postgres/MySQL DSN in production, e.g.
    # postgresql+psycopg2://user:pass@localhost:5432/complaints
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./complaints.db")

    # Groq (mandatory per assignment spec)
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_extraction_model: str = os.getenv("GROQ_EXTRACTION_MODEL", "gemma2-9b-it")
    groq_reasoning_model: str = os.getenv("GROQ_REASONING_MODEL", "llama-3.3-70b-versatile")

    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()

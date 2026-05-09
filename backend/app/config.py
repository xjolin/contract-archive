import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    mineru_api_url: str = os.getenv("MINERU_API_URL", "")
    ollama_url: str = os.getenv("OLLAMA_URL", "")
    llm_model: str = os.getenv("LLM_MODEL", "qwen3:8b-q8_0")
    storage_dir: str = os.getenv("STORAGE_DIR", "/storage")


settings = Settings()

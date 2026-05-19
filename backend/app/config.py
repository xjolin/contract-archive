import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    mineru_api_url: str = os.getenv("MINERU_API_URL", "")
    ollama_url: str = os.getenv("OLLAMA_URL", "")
    llm_model: str = os.getenv("LLM_MODEL", "qwen3:8b-q8_0")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    llm_top_p: float = float(os.getenv("LLM_TOP_P", "1"))
    llm_top_k: int = int(os.getenv("LLM_TOP_K", "0"))
    llm_seed: int | None = (
        int(os.getenv("LLM_SEED")) if os.getenv("LLM_SEED") else None
    )
    llm_num_ctx: int = int(os.getenv("LLM_NUM_CTX", "16384"))
    storage_dir: str = os.getenv("STORAGE_DIR", "/storage")


settings = Settings()

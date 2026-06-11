import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    mineru_api_url: str = os.getenv("MINERU_API_URL", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "qwen3.6-flash")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    llm_top_p: float = float(os.getenv("LLM_TOP_P", "1"))
    storage_dir: str = os.getenv("STORAGE_DIR", "/storage")


settings = Settings()

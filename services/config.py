from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-flash-latest"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    GITHUB_TOKEN: Optional[str] = None
    JOB_API_KEY: Optional[str] = None
    ADZUNA_APP_ID: Optional[str] = None

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://crewai:crewai_pass@localhost:5432/crewai_db"

    # Redis
    REDIS_URL: str = "redis://:redis_pass@localhost:6379/0"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()

from functools import lru_cache
from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "PROVEXA Backend"
    app_env: str = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "PROVEXA Backend"),
        app_env=os.getenv("APP_ENV", "development"),
        app_debug=_parse_bool(os.getenv("APP_DEBUG"), False),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        cors_origins=_parse_csv(os.getenv("CORS_ORIGINS"), ["http://localhost:3000"]),
    )

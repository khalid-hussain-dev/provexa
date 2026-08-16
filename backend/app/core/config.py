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
    database_url: str = "sqlite:///./provexa_dev.db"
    redis_url: str | None = None
    redis_connect_timeout_seconds: int = 1
    transient_state_prefix: str = "provexa"
    jwt_secret_key: str = "dev-only-change-me"
    jwt_access_token_minutes: int = 30
    pending_2fa_token_minutes: int = 5
    password_reset_token_minutes: int = 30
    adzuna_app_id: str | None = None
    job_api_key: str | None = None
    adzuna_country: str = "us"

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


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "PROVEXA Backend"),
        app_env=os.getenv("APP_ENV", "development"),
        app_debug=_parse_bool(os.getenv("APP_DEBUG"), False),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        cors_origins=_parse_csv(os.getenv("CORS_ORIGINS"), ["http://localhost:3000"]),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./provexa_dev.db"),
        redis_url=os.getenv("REDIS_URL"),
        redis_connect_timeout_seconds=_parse_int(os.getenv("REDIS_CONNECT_TIMEOUT_SECONDS"), 1),
        transient_state_prefix=os.getenv("TRANSIENT_STATE_PREFIX", "provexa"),
        jwt_secret_key=os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY", "dev-only-change-me"),
        jwt_access_token_minutes=_parse_int(os.getenv("JWT_ACCESS_TOKEN_MINUTES"), 30),
        pending_2fa_token_minutes=_parse_int(os.getenv("PENDING_2FA_TOKEN_MINUTES"), 5),
        password_reset_token_minutes=_parse_int(os.getenv("PASSWORD_RESET_TOKEN_MINUTES"), 30),
        adzuna_app_id=os.getenv("ADZUNA_APP_ID"),
        job_api_key=os.getenv("JOB_API_KEY"),
        adzuna_country=os.getenv("ADZUNA_COUNTRY", "us").strip().lower() or "us",
    )

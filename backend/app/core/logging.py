import json
import logging
from typing import Any

SENSITIVE_KEYS = {"password", "passwd", "secret", "token", "authorization", "api_key", "apikey", "access_token", "refresh_token"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in getattr(record, "extra_fields", {}).items():
            payload[key] = redact(value) if key.lower() not in SENSITIVE_KEYS else "[REDACTED]"
        return json.dumps(payload, default=str)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

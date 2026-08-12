from fastapi import APIRouter
from sqlalchemy import text

from app.core.cache import get_cache_health
from app.database.session import SessionLocal, init_database

router = APIRouter(tags=["support"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readiness")
async def readiness() -> dict[str, str | dict[str, str]]:
    init_database()
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    cache_health = get_cache_health()
    return {
        "status": "ready",
        "dependencies": {
            "database": "ready",
            "redis": "ready" if cache_health.ready else "degraded",
        },
        "cache_mode": cache_health.mode,
    }

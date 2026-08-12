from fastapi import APIRouter
from sqlalchemy import text

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
    return {"status": "ready", "dependencies": {"database": "ready"}}

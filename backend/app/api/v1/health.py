from fastapi import APIRouter

router = APIRouter(tags=["support"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readiness")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}

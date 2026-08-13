from fastapi import APIRouter

from .release_readiness import evaluate_release_readiness


router = APIRouter(prefix="/api/v1/readiness", tags=["integration-readiness"])


@router.get("/release")
async def release_readiness() -> dict:
    return evaluate_release_readiness()

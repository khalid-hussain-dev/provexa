from fastapi import APIRouter

from .provider_status import provider_status


router = APIRouter(prefix="/api/v1/readiness", tags=["integration-readiness"])


@router.get("/providers")
async def providers_readiness() -> dict:
    return provider_status()

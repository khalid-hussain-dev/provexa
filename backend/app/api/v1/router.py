from fastapi import APIRouter

from app.api.v1.analysis import router as analysis_router
from app.api.v1.auth import router as auth_router
from app.api.v1.courses import router as courses_router
from app.api.v1.candidate import router as candidate_router
from app.api.v1.health import router as health_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.subscription import router as subscription_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(candidate_router)
api_router.include_router(analysis_router)
api_router.include_router(jobs_router)
api_router.include_router(interviews_router)
api_router.include_router(courses_router)
api_router.include_router(resumes_router)
api_router.include_router(subscription_router)

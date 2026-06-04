from fastapi import APIRouter

from app.api.routes.applications import router as applications_router
from app.api.routes.mvp import router as mvp_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.job_import import router as job_import_router
from app.api.routes.resume_versions import router as resume_versions_router


api_router = APIRouter()
api_router.include_router(mvp_router)
api_router.include_router(applications_router)
api_router.include_router(jobs_router)
api_router.include_router(job_import_router)
api_router.include_router(resume_versions_router)

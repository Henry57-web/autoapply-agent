from fastapi import APIRouter, HTTPException

from app.schemas.job_import import JobImportRequest, JobImportResult
from app.services.job_import import JobImportError, JobImportService


router = APIRouter(prefix="/job-import", tags=["job-import"])


@router.post("/url", response_model=JobImportResult)
async def import_job_url(payload: JobImportRequest) -> JobImportResult:
    try:
        return await JobImportService().import_url(str(payload.url))
    except JobImportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

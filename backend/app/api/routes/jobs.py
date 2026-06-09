from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.application_presenter import build_application_detail, build_job_metadata
from app.schemas.jobs import (
    DashboardStats,
    JobBatchImportRequest,
    JobBatchImportResult,
    JobCreate,
    JobDetail,
    JobSortField,
    JobStatus,
    JobStatusEventDetail,
    JobStatusUpdate,
    JobSummary,
    JobUpdate,
    SortDirection,
)
from app.models import ResumeVersion
from app.services.job_import import JobImportService
from app.services.job_service import (
    get_dashboard_stats,
    create_saved_job,
    delete_job,
    get_job,
    get_job_application_artifacts,
    job_needs_review,
    list_jobs,
    update_job_status,
    update_job,
)
from app.services.resume_version_presenter import build_resume_version_summary


router = APIRouter(tags=["jobs"])


@router.post("/jobs", response_model=JobDetail, status_code=status.HTTP_201_CREATED)
async def post_job(payload: JobCreate, db: AsyncSession = Depends(get_db_session)) -> JobDetail:
    return await _job_detail(db, await create_saved_job(db, payload))


@router.get("/jobs", response_model=list[JobSummary])
async def get_jobs(
    search: str | None = None,
    job_status: JobStatus | None = Query(default=None, alias="status"),
    min_score: float | None = Query(default=None, ge=0, le=100),
    max_score: float | None = Query(default=None, ge=0, le=100),
    sort_by: JobSortField = "created_at",
    direction: SortDirection = "desc",
    db: AsyncSession = Depends(get_db_session),
) -> list[JobSummary]:
    jobs = await list_jobs(
        db,
        search=search,
        job_status=job_status,
        min_score=min_score,
        max_score=max_score,
        sort_by=sort_by,
        direction=direction,
    )
    linked_job_ids = set(
        await db.scalars(select(ResumeVersion.job_id).where(ResumeVersion.job_id.in_([job.id for job in jobs])))
    )
    return [_job_summary(job, has_resume_version=job.id in linked_job_ids) for job in jobs]


@router.post("/jobs/batch-import", response_model=JobBatchImportResult)
async def batch_import_jobs(payload: JobBatchImportRequest) -> JobBatchImportResult:
    return await JobImportService().import_urls([str(url) for url in payload.urls])


@router.get("/jobs/{job_id}", response_model=JobDetail)
async def get_job_detail(job_id: str, db: AsyncSession = Depends(get_db_session)) -> JobDetail:
    job = await get_job(db, job_id)
    return await _job_detail(db, job)


@router.patch("/jobs/{job_id}/status", response_model=JobDetail)
async def patch_job_status(
    job_id: str,
    payload: JobStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> JobDetail:
    job = await update_job_status(db, await get_job(db, job_id), payload.status)
    return await _job_detail(db, job)


@router.patch("/jobs/{job_id}", response_model=JobDetail)
async def patch_job(
    job_id: str,
    payload: JobUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> JobDetail:
    job = await update_job(db, await get_job(db, job_id), payload)
    return await _job_detail(db, job)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_job(job_id: str, db: AsyncSession = Depends(get_db_session)) -> Response:
    await delete_job(db, await get_job(db, job_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db_session)) -> DashboardStats:
    return await get_dashboard_stats(db)


def _job_summary(job, *, has_resume_version: bool = False) -> JobSummary:
    return JobSummary(
        id=job.id,
        application_id=job.application_id,
        company=job.company,
        title=job.title,
        location=job.location,
        job_type=job.job_type,
        source=job.source,
        url=job.url,
        salary=job.salary,
        deadline=job.deadline,
        match_score=job.match_score,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        has_resume_version=has_resume_version,
        needs_review=job_needs_review(job),
    )


async def _job_detail(db: AsyncSession, job) -> JobDetail:
    application, resume, resume_version = await get_job_application_artifacts(db, job)
    application_detail = (
        build_application_detail(application, resume, resume_version)
        if application and resume and resume_version
        else None
    )
    return JobDetail(
        **_job_summary(job, has_resume_version=resume_version is not None).model_dump(),
        description=job.description,
        ats_keywords=job.ats_keywords or [],
        missing_skills=job.missing_skills or [],
        strengths=job.strengths or [],
        weaknesses=job.weaknesses or [],
        notes=job.notes,
        applied_at=job.applied_at,
        oa_received_at=job.oa_received_at,
        interview_at=job.interview_at,
        offer_at=job.offer_at,
        generated_at=application.created_at if application else job.created_at,
        analysis=application_detail.analysis if application_detail else None,
        tailored_resume=application_detail.tailored_resume if application_detail else None,
        cover_letter=application_detail.cover_letter if application_detail else None,
        resume_diff=application_detail.resume_diff if application_detail else None,
        metadata=build_job_metadata(application) if application else None,
        status_events=[
            JobStatusEventDetail(
                id=event.id,
                from_status=event.from_status,
                to_status=event.to_status,
                source=event.source,
                created_at=event.created_at,
            )
            for event in job.status_events
        ],
        resume_version=build_resume_version_summary(resume_version) if resume_version else None,
    )

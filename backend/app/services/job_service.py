from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Application, ApplicationMetadata, Job, JobStatusEvent, Resume, ResumeVersion
from app.schemas.jobs import DashboardStats, JobCreate, JobSortField, JobStatus, JobUpdate, SortDirection


MILESTONE_FIELDS = {
    "APPLIED": "applied_at",
    "OA_RECEIVED": "oa_received_at",
    "INTERVIEW": "interview_at",
    "OFFER": "offer_at",
}


async def create_saved_job(db: AsyncSession, payload: JobCreate) -> Job:
    job = Job(**payload.model_dump(), status="SAVED")
    db.add(job)
    await db.flush()
    db.add(JobStatusEvent(job_id=job.id, to_status=job.status, source="manual"))
    await db.commit()
    return await get_job(db, job.id)


def job_needs_review(job: Job) -> bool:
    metadata = job.ingestion_metadata or {}
    return bool(metadata.get("requires_review") or not job.description.strip())


async def create_job_for_application(
    db: AsyncSession,
    application: Application,
    *,
    job_metadata: dict[str, str | None],
    event_source: str = "tailoring_workflow",
) -> Job:
    analysis = application.analysis or {}
    job = Job(
        application_id=application.id,
        company=job_metadata.get("company") or application.company_name,
        title=job_metadata.get("title") or application.job_title,
        location=job_metadata.get("location"),
        job_type=job_metadata.get("job_type"),
        source=job_metadata.get("source"),
        url=job_metadata.get("job_url"),
        salary=job_metadata.get("salary"),
        deadline=_parse_date(job_metadata.get("deadline")),
        description=application.job_description,
        match_score=float(analysis.get("match_score", 0)),
        status="READY_TO_APPLY",
        ats_keywords=analysis.get("ats_keywords", []),
        missing_skills=analysis.get("missing_keywords", []),
        strengths=_derive_strengths(analysis),
        weaknesses=analysis.get("missing_keywords", []),
        notes=job_metadata.get("notes"),
    )
    db.add(job)
    await db.flush()
    db.add(JobStatusEvent(job_id=job.id, to_status=job.status, source=event_source))
    return job


async def list_jobs(
    db: AsyncSession,
    *,
    search: str | None = None,
    job_status: JobStatus | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    sort_by: JobSortField = "created_at",
    direction: SortDirection = "desc",
) -> list[Job]:
    query = select(Job)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Job.company.ilike(pattern), Job.title.ilike(pattern)))
    if job_status:
        query = query.where(Job.status == job_status)
    if min_score is not None:
        query = query.where(Job.match_score >= min_score)
    if max_score is not None:
        query = query.where(Job.match_score <= max_score)
    order_column = {"match_score": Job.match_score, "created_at": Job.created_at, "deadline": Job.deadline}[sort_by]
    query = query.order_by((asc if direction == "asc" else desc)(order_column), desc(Job.created_at))
    return list(await db.scalars(query))


async def get_job(db: AsyncSession, job_id: str) -> Job:
    query = (
        select(Job)
        .options(selectinload(Job.status_events))
        .where(Job.id == job_id)
        .execution_options(populate_existing=True)
    )
    job = await db.scalar(query)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


async def update_job_status(db: AsyncSession, job: Job, next_status: JobStatus) -> Job:
    previous_status = job.status
    if previous_status != next_status:
        job.status = next_status
        milestone_field = MILESTONE_FIELDS.get(next_status)
        if milestone_field and not getattr(job, milestone_field):
            setattr(job, milestone_field, datetime.now(timezone.utc))
        db.add(JobStatusEvent(job_id=job.id, from_status=previous_status, to_status=next_status))
        await db.commit()
    return await get_job(db, job.id)


async def update_job(db: AsyncSession, job: Job, payload: JobUpdate) -> Job:
    values = payload.model_dump(exclude_unset=True)
    required_fields = {"description", "match_score", "ats_keywords", "missing_skills", "strengths", "weaknesses"}
    if any(field in values and values[field] is None for field in required_fields):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Job description, score, and skill lists cannot be null.",
        )

    for field, value in values.items():
        setattr(job, field, value)

    if job.application_id:
        application = await db.scalar(
            select(Application)
            .options(selectinload(Application.metadata_record))
            .where(Application.id == job.application_id)
        )
        if application:
            await _sync_application_from_job_update(db, application, values)

    await db.commit()
    return await get_job(db, job.id)


async def delete_job(db: AsyncSession, job: Job) -> None:
    await db.delete(job)
    await db.commit()


async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    counts = dict((await db.execute(select(Job.status, func.count()).group_by(Job.status))).all())
    score_stats = await db.execute(select(func.avg(Job.match_score), func.max(Job.match_score)))
    average_score, highest_score = score_stats.one()
    return DashboardStats(
        total_jobs=sum(counts.values()),
        ready_to_apply=counts.get("READY_TO_APPLY", 0),
        applied=counts.get("APPLIED", 0),
        oa=counts.get("OA_RECEIVED", 0) + counts.get("OA_COMPLETED", 0),
        interviews=counts.get("INTERVIEW", 0),
        offers=counts.get("OFFER", 0),
        rejected=counts.get("REJECTED", 0),
        average_match_score=round(float(average_score or 0), 2),
        highest_match_score=round(float(highest_score or 0), 2),
    )


async def get_job_application_artifacts(
    db: AsyncSession,
    job: Job,
) -> tuple[Application | None, Resume | None, ResumeVersion | None]:
    if not job.application_id:
        return None, None, None
    application = await db.scalar(
        select(Application)
        .options(selectinload(Application.status), selectinload(Application.metadata_record))
        .where(Application.id == job.application_id)
    )
    if not application:
        return None, None, None
    resume = await db.get(Resume, application.resume_id)
    resume_version = await db.get(ResumeVersion, application.resume_version_id)
    return application, resume, resume_version


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _derive_strengths(analysis: dict) -> list[str]:
    breakdown = analysis.get("match_score_breakdown", {})
    categories = breakdown.get("categories", [])
    matched = [keyword for category in categories for keyword in category.get("matched_keywords", [])]
    return list(dict.fromkeys(matched))


async def _sync_application_from_job_update(db: AsyncSession, application: Application, values: dict) -> None:
    if "company" in values:
        application.company_name = values["company"]
    if "title" in values:
        application.job_title = values["title"]
    if "description" in values:
        application.job_description = values["description"]

    analysis_updates = {
        "match_score": "match_score",
        "ats_keywords": "ats_keywords",
        "missing_skills": "missing_keywords",
    }
    if any(field in values for field in analysis_updates):
        analysis = dict(application.analysis or {})
        for field, analysis_field in analysis_updates.items():
            if field in values:
                analysis[analysis_field] = values[field]
        application.analysis = analysis

    metadata_updates = {
        "url": "job_url",
        "source": "source",
        "location": "location",
        "salary": "salary",
        "deadline": "deadline",
        "notes": "notes",
    }
    if any(field in values for field in metadata_updates):
        metadata = application.metadata_record
        if not metadata:
            metadata = ApplicationMetadata(application_id=application.id)
            db.add(metadata)
        for field, metadata_field in metadata_updates.items():
            if field in values:
                value = values[field]
                setattr(metadata, metadata_field, value.isoformat() if isinstance(value, date) else value)

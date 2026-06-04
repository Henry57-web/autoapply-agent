from io import BytesIO
import re

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Application, Job, Resume, ResumeVersion
from app.schemas.resume_versions import ResumeVersionCreate
from app.services.pdf_export import build_resume_pdf
from app.services.resume_diff import build_resume_diff_summary


async def create_base_resume_version(db: AsyncSession, resume: Resume) -> ResumeVersion:
    existing = await db.scalar(
        select(ResumeVersion).where(ResumeVersion.resume_id == resume.id, ResumeVersion.is_base.is_(True))
    )
    if existing:
        return existing
    return await create_resume_version(
        db,
        ResumeVersionCreate(
            source_resume_id=resume.id,
            name=f"{resume.file_name} - Base Resume",
            is_base=True,
            content_text=resume.raw_text,
            created_from="BASE_UPLOAD",
        ),
    )


async def create_tailored_resume_version(
    db: AsyncSession,
    *,
    resume: Resume,
    company: str | None,
    job_title: str | None,
    content_text: str,
    content_json: dict,
    ats_keywords: list[str],
    match_score: float,
) -> ResumeVersion:
    return await create_resume_version(
        db,
        ResumeVersionCreate(
            source_resume_id=resume.id,
            name=f"Tailored Resume - {job_title or 'Target Role'}",
            role_type=job_title,
            company=company,
            job_title=job_title,
            content_text=content_text,
            content_json=content_json,
            ats_keywords=ats_keywords,
            match_score=match_score,
            created_from="TAILORING_RESULT",
        ),
    )


async def create_resume_version(db: AsyncSession, payload: ResumeVersionCreate) -> ResumeVersion:
    resume = await db.get(Resume, payload.source_resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source resume not found.")
    version_number = await _next_version_number(db, resume.id)
    diff_summary = (
        {}
        if payload.is_base
        else build_resume_diff_summary(resume.raw_text, payload.content_text, payload.ats_keywords)
    )
    version = ResumeVersion(
        resume_id=resume.id,
        job_id=payload.job_id,
        title=payload.name,
        name=payload.name,
        role_type=payload.role_type,
        version_number=version_number,
        is_base=payload.is_base,
        company=payload.company,
        job_title=payload.job_title,
        content=payload.content_text,
        content_json=payload.content_json,
        diff_summary=diff_summary,
        created_from=payload.created_from,
        ats_keywords=payload.ats_keywords,
        match_score=payload.match_score,
    )
    db.add(version)
    await db.flush()
    return version


async def list_resume_versions(
    db: AsyncSession,
    *,
    search: str | None = None,
    role_type: str | None = None,
    company: str | None = None,
    direction: str = "desc",
) -> list[ResumeVersion]:
    query = select(ResumeVersion)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                ResumeVersion.name.ilike(pattern),
                ResumeVersion.company.ilike(pattern),
                ResumeVersion.job_title.ilike(pattern),
            )
        )
    if role_type:
        query = query.where(ResumeVersion.role_type == role_type)
    if company:
        query = query.where(ResumeVersion.company.ilike(f"%{company.strip()}%"))
    order = ResumeVersion.created_at.asc() if direction == "asc" else ResumeVersion.created_at.desc()
    return list(await db.scalars(query.order_by(order)))


async def get_resume_version(db: AsyncSession, version_id: str) -> ResumeVersion:
    version = await db.get(ResumeVersion, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found.")
    return version


async def get_job_resume_version(db: AsyncSession, job_id: str) -> ResumeVersion:
    version = await db.scalar(
        select(ResumeVersion)
        .where(ResumeVersion.job_id == job_id)
        .order_by(ResumeVersion.created_at.desc())
    )
    if not version:
        job = await db.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
        if job.application_id:
            version = await db.scalar(
                select(ResumeVersion)
                .join(Application, Application.resume_version_id == ResumeVersion.id)
                .where(Application.id == job.application_id)
            )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked resume version not found.")
    return version


async def delete_resume_version(db: AsyncSession, version: ResumeVersion) -> None:
    if version.is_base:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Base resume versions cannot be deleted.")
    await db.execute(
        update(Application).where(Application.resume_version_id == version.id).values(resume_version_id=None)
    )
    await db.delete(version)
    await db.commit()


def build_resume_version_download(version: ResumeVersion, file_format: str) -> tuple[BytesIO, str, str]:
    filename = f"{_safe_filename(version.name)}_v{version.version_number}.{file_format}"
    if file_format == "pdf":
        return build_resume_pdf(version.content), filename, "application/pdf"
    content = version.content
    if file_format == "md":
        content = f"# {version.name}\n\n{content}\n"
        media_type = "text/markdown; charset=utf-8"
    else:
        media_type = "text/plain; charset=utf-8"
    return BytesIO(content.encode("utf-8")), filename, media_type


async def _next_version_number(db: AsyncSession, resume_id: str) -> int:
    current = await db.scalar(
        select(func.max(ResumeVersion.version_number)).where(ResumeVersion.resume_id == resume_id)
    )
    return int(current or 0) + 1


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_") or "Tailored_Resume"

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Application, Job, Resume, ResumeVersion
from app.schemas.resume_versions import ResumeVersionCreate
from app.services.job_service import create_job_for_application
from app.services.resume_diff import build_resume_diff_summary
from app.services.resume_version_service import create_base_resume_version, create_resume_version


@dataclass
class BackfillSummary:
    applications_scanned: int = 0
    jobs_created: int = 0
    resumes_scanned: int = 0
    resume_versions_created: int = 0
    tailored_results_scanned: int = 0
    tailored_versions_updated: int = 0
    skipped_existing: int = 0
    failed: int = 0

    def render(self) -> str:
        return "\n".join(
            [
                "Backfill completed.",
                f"Applications scanned: {self.applications_scanned}",
                f"Jobs created: {self.jobs_created}",
                f"Resumes scanned: {self.resumes_scanned}",
                f"Resume versions created: {self.resume_versions_created}",
                f"Tailored results scanned: {self.tailored_results_scanned}",
                f"Tailored versions updated: {self.tailored_versions_updated}",
                f"Skipped existing: {self.skipped_existing}",
                f"Failed: {self.failed}",
            ]
        )


async def run_legacy_backfill(db: AsyncSession) -> BackfillSummary:
    summary = BackfillSummary()
    applications = list(
        await db.scalars(select(Application).options(selectinload(Application.metadata_record)))
    )
    summary.applications_scanned = len(applications)
    jobs_by_application = {
        job.application_id: job
        for job in await db.scalars(select(Job).where(Job.application_id.is_not(None)))
    }

    for application in applications:
        job = jobs_by_application.get(application.id)
        if not job:
            metadata = application.metadata_record
            job = await create_job_for_application(
                db,
                application,
                job_metadata={
                    "job_url": metadata.job_url if metadata else None,
                    "source": metadata.source if metadata else None,
                    "location": metadata.location if metadata else None,
                    "salary": metadata.salary if metadata else None,
                    "deadline": metadata.deadline if metadata else None,
                    "notes": metadata.notes if metadata else None,
                },
                event_source="legacy_backfill",
            )
            jobs_by_application[application.id] = job
            summary.jobs_created += 1
        else:
            summary.skipped_existing += 1

    resumes = list(await db.scalars(select(Resume)))
    summary.resumes_scanned = len(resumes)
    for resume in resumes:
        existing = await db.scalar(
            select(ResumeVersion.id).where(
                ResumeVersion.resume_id == resume.id,
                ResumeVersion.is_base.is_(True),
            )
        )
        if existing:
            summary.skipped_existing += 1
            continue
        await create_base_resume_version(db, resume)
        summary.resume_versions_created += 1

    for application in applications:
        tailored_resume = (application.analysis or {}).get("tailored_resume") or {}
        content = tailored_resume.get("ats_optimized_resume")
        if not content:
            continue
        summary.tailored_results_scanned += 1
        job = jobs_by_application.get(application.id)
        version = (
            await db.get(ResumeVersion, application.resume_version_id)
            if application.resume_version_id
            else None
        )
        if not version:
            version = await create_resume_version(
                db,
                ResumeVersionCreate(
                    source_resume_id=application.resume_id,
                    job_id=job.id if job else None,
                    name=f"Tailored Resume - {application.job_title or 'Target Role'}",
                    role_type=application.job_title,
                    company=application.company_name,
                    job_title=application.job_title,
                    content_text=content,
                    content_json=tailored_resume,
                    ats_keywords=(application.analysis or {}).get("ats_keywords", []),
                    match_score=float((application.analysis or {}).get("match_score", 0)),
                    created_from="TAILORING_RESULT",
                ),
            )
            application.resume_version_id = version.id
            summary.resume_versions_created += 1
            continue

        changed = False
        if job and not version.job_id:
            version.job_id = job.id
            changed = True
        if not version.company and application.company_name:
            version.company = application.company_name
            changed = True
        if not version.job_title and application.job_title:
            version.job_title = application.job_title
            changed = True
        if not version.role_type and application.job_title:
            version.role_type = application.job_title
            changed = True
        if (version.diff_summary or {}).get("schema_version") != 2:
            resume = await db.get(Resume, version.resume_id)
            if resume:
                version.diff_summary = build_resume_diff_summary(
                    resume.raw_text,
                    version.content,
                    version.ats_keywords,
                )
                changed = True
        if changed:
            summary.tailored_versions_updated += 1
        else:
            summary.skipped_existing += 1

    await db.commit()
    return summary

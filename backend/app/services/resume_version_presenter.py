from app.models import ResumeVersion
from app.schemas.resume_versions import ResumeVersionDetail, ResumeVersionSummary


def build_resume_version_summary(version: ResumeVersion) -> ResumeVersionSummary:
    return ResumeVersionSummary(
        id=version.id,
        source_resume_id=version.resume_id,
        job_id=version.job_id,
        name=version.name,
        role_type=version.role_type,
        version_number=version.version_number,
        is_base=version.is_base,
        company=version.company,
        job_title=version.job_title,
        created_from=version.created_from,
        match_score=version.match_score,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def build_resume_version_detail(version: ResumeVersion) -> ResumeVersionDetail:
    return ResumeVersionDetail(
        **build_resume_version_summary(version).model_dump(),
        content_text=version.content,
        content_json=version.content_json or {},
        diff_summary=version.diff_summary or {},
        ats_keywords=version.ats_keywords or [],
    )

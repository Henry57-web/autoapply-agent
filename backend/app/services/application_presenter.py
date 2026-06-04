from app.models import Application, Resume, ResumeVersion
from app.schemas.applications import ApplicationDetail, ApplicationSummary, JobMetadata
from app.schemas.mvp import TailoredResume
from app.services.resume_diff import build_resume_diff


def build_application_summary(application: Application) -> ApplicationSummary:
    analysis = application.analysis or {}
    return ApplicationSummary(
        id=application.id,
        job_title=application.job_title,
        company_name=application.company_name,
        match_score=float(analysis.get("match_score", 0)),
        status=application.status.status if application.status else "Draft",
        created_at=application.created_at,
        metadata=build_job_metadata(application),
    )


def build_application_detail(application: Application, resume: Resume, resume_version: ResumeVersion) -> ApplicationDetail:
    summary = build_application_summary(application)
    analysis = normalize_analysis(application.analysis or {})
    tailored_resume = analysis.get("tailored_resume") or {
        "headline": resume_version.title,
        "summary": analysis.get("match_summary", ""),
        "rewritten_bullets": [],
        "ats_optimized_resume": resume_version.content,
    }
    return ApplicationDetail(
        **summary.model_dump(),
        application_id=application.id,
        candidate_profile_id=application.candidate_profile_id,
        resume_id=application.resume_id,
        resume_version_id=application.resume_version_id,
        job_description=application.job_description,
        analysis=analysis,
        tailored_resume=TailoredResume.model_validate(tailored_resume),
        cover_letter=application.cover_letter or "",
        resume_diff=build_resume_diff(resume.raw_text, resume_version.content),
    )


def build_job_metadata(application: Application) -> JobMetadata:
    metadata_record = application.metadata_record
    values = {
        "company": application.company_name,
        "title": application.job_title,
        "job_url": metadata_record.job_url if metadata_record else None,
        "source": metadata_record.source if metadata_record else None,
        "job_type": None,
        "location": metadata_record.location if metadata_record else None,
        "salary": metadata_record.salary if metadata_record else None,
        "deadline": metadata_record.deadline if metadata_record else None,
        "notes": metadata_record.notes if metadata_record else None,
        "missing_skill_categories": dict(metadata_record.missing_skill_categories or {}) if metadata_record else {},
    }
    for keyword in (application.analysis or {}).get("missing_keywords", []):
        values["missing_skill_categories"].setdefault(keyword, "not_on_resume")
    return JobMetadata.model_validate(values)


def normalize_analysis(analysis: dict) -> dict:
    normalized = dict(analysis)
    normalized.setdefault("required_skills", [])
    normalized.setdefault("preferred_skills", [])
    normalized.setdefault("responsibilities", [])
    normalized.setdefault("ats_keywords", [])
    normalized.setdefault("missing_keywords", [])
    normalized.setdefault("match_score", 0)
    normalized.setdefault("match_summary", "")
    normalized.setdefault(
        "match_score_breakdown",
        {
            "total_score": normalized["match_score"],
            "categories": [],
            "explanation": "This saved application predates detailed score breakdowns. Generate a new version to see category-level scoring.",
        },
    )
    return normalized

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Application, ApplicationMetadata, ApplicationStatus, CandidateProfile, Resume
from app.schemas.mvp import ApplicationResult, JobAnalysis, TailoredResume
from app.services.llm import LLMServiceUnavailable, create_llm_provider
from app.services.match_scorer import (
    MatchScoreBreakdown as ComputedMatchScoreBreakdown,
    build_match_score_breakdown,
    extract_fallback_keywords,
)
from app.services.prompt_registry import load_prompt
from app.services.job_service import create_job_for_application
from app.services.resume_version_service import create_base_resume_version, create_tailored_resume_version


class TailoringService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.ai = create_llm_provider(self.settings)

    async def run_mvp_workflow(
        self,
        db: AsyncSession,
        candidate_file_name: str,
        candidate_profile_text: str,
        resume_file_name: str,
        resume_text: str,
        job_description: str,
        candidate_profile_id: str | None = None,
        resume_id: str | None = None,
        job_metadata: dict[str, str | None] | None = None,
    ) -> ApplicationResult:
        candidate_profile = await db.get(CandidateProfile, candidate_profile_id) if candidate_profile_id else None
        if not candidate_profile:
            candidate_profile = CandidateProfile(file_name=candidate_file_name, raw_text=candidate_profile_text)
            db.add(candidate_profile)
        resume = await db.get(Resume, resume_id) if resume_id else None
        if not resume:
            resume = Resume(file_name=resume_file_name, raw_text=resume_text)
            db.add(resume)
        await db.flush()
        await create_base_resume_version(db, resume)

        analysis = await self.analyze_job(candidate_profile_text, resume_text, job_description)
        analysis.company_name = (job_metadata or {}).get("company") or analysis.company_name
        analysis.job_title = (job_metadata or {}).get("title") or analysis.job_title
        tailored_resume = await self.generate_tailored_resume(
            candidate_profile_text,
            resume_text,
            job_description,
            analysis,
        )
        cover_letter = await self.generate_cover_letter(
            candidate_profile_text,
            tailored_resume.ats_optimized_resume,
            job_description,
            analysis,
        )

        resume_version = await create_tailored_resume_version(
            db,
            resume=resume,
            company=analysis.company_name,
            job_title=analysis.job_title,
            content_text=tailored_resume.ats_optimized_resume,
            content_json=tailored_resume.model_dump(),
            ats_keywords=analysis.ats_keywords,
            match_score=analysis.match_score,
        )

        persisted_analysis = analysis.model_dump()
        persisted_analysis["tailored_resume"] = tailored_resume.model_dump()
        application = Application(
            candidate_profile_id=candidate_profile.id,
            resume_id=resume.id,
            resume_version_id=resume_version.id,
            job_description=job_description,
            job_title=analysis.job_title,
            company_name=analysis.company_name,
            analysis=persisted_analysis,
            cover_letter=cover_letter,
        )
        db.add(application)
        await db.flush()
        db.add(ApplicationStatus(application_id=application.id, status="Draft"))
        application_metadata = {
            key: value for key, value in (job_metadata or {}).items() if key not in {"company", "title", "job_type"}
        }
        db.add(ApplicationMetadata(application_id=application.id, **application_metadata))
        job = await create_job_for_application(db, application, job_metadata=job_metadata or {})
        resume_version.job_id = job.id
        await db.commit()

        return ApplicationResult(
            application_id=application.id,
            job_id=job.id,
            candidate_profile_id=candidate_profile.id,
            resume_id=resume.id,
            resume_version_id=resume_version.id,
            analysis=analysis,
            tailored_resume=tailored_resume,
            cover_letter=cover_letter,
        )

    async def analyze_job(self, candidate_profile: str, resume: str, job_description: str) -> JobAnalysis:
        prompt = load_prompt("analyze_job")
        payload = {
            "candidate_profile": candidate_profile,
            "resume": resume,
            "job_description": job_description,
        }

        try:
            data = await self.ai.generate_json(prompt, payload)
        except LLMServiceUnavailable:
            keywords = extract_fallback_keywords(job_description)
            score_breakdown = build_match_score_breakdown(resume, keywords[:15], [], keywords)
            return JobAnalysis(
                required_skills=keywords[:15],
                preferred_skills=[],
                responsibilities=[],
                ats_keywords=keywords,
                missing_keywords=_ats_missing_keywords(score_breakdown),
                match_score=score_breakdown.total_score,
                match_score_breakdown=_serialize_score_breakdown(score_breakdown),
                match_summary="Local keyword analysis only. Configure LLM_API_KEY for full AI analysis.",
            )

        required_skills = data.get("required_skills", [])
        preferred_skills = data.get("preferred_skills", [])
        ats_keywords = data.get("ats_keywords", [])
        score_breakdown = build_match_score_breakdown(
            resume,
            required_skills,
            preferred_skills,
            ats_keywords,
        )
        data["match_score"] = score_breakdown.total_score
        data["match_score_breakdown"] = _serialize_score_breakdown(score_breakdown)
        data["missing_keywords"] = _ats_missing_keywords(score_breakdown)
        return JobAnalysis.model_validate(data)

    async def generate_tailored_resume(
        self,
        candidate_profile: str,
        resume: str,
        job_description: str,
        analysis: JobAnalysis,
    ) -> TailoredResume:
        prompt = load_prompt("tailor_resume")
        payload = {
            "candidate_profile": candidate_profile,
            "resume": resume,
            "job_description": job_description,
            "analysis": analysis.model_dump(),
        }

        try:
            data = await self.ai.generate_json(prompt, payload)
            return TailoredResume.model_validate(data)
        except LLMServiceUnavailable:
            return TailoredResume(
                headline=analysis.job_title or "Target Role",
                summary=analysis.match_summary,
                rewritten_bullets=_fallback_bullets(resume),
                ats_optimized_resume=resume,
            )

    async def generate_cover_letter(
        self,
        candidate_profile: str,
        tailored_resume: str,
        job_description: str,
        analysis: JobAnalysis,
    ) -> str:
        prompt = load_prompt("cover_letter")
        payload = {
            "candidate_profile": candidate_profile,
            "tailored_resume": tailored_resume,
            "job_description": job_description,
            "analysis": analysis.model_dump(),
        }

        try:
            data = await self.ai.generate_json(prompt, payload)
            return str(data.get("cover_letter", "")).strip()
        except LLMServiceUnavailable:
            return (
                "Configure LLM_API_KEY to generate a tailored cover letter. "
                f"Current match summary: {analysis.match_summary}"
            )


def _fallback_bullets(resume: str, limit: int = 6) -> list[str]:
    bullets = [
        line.strip(" -•\t")
        for line in resume.splitlines()
        if line.strip().startswith(("-", "•")) and len(line.strip()) > 12
    ]
    return bullets[:limit]


def _serialize_score_breakdown(score_breakdown: ComputedMatchScoreBreakdown) -> dict:
    return {
        "total_score": score_breakdown.total_score,
        "categories": [
            {
                "key": category.key,
                "label": category.label,
                "weight": category.weight,
                "score": category.score,
                "contribution": category.contribution,
                "matched_count": category.matched_count,
                "total_count": category.total_count,
                "matched_keywords": category.matched_keywords,
                "missing_keywords": category.missing_keywords,
            }
            for category in score_breakdown.categories
        ],
        "explanation": score_breakdown.explanation,
    }


def _ats_missing_keywords(score_breakdown: ComputedMatchScoreBreakdown) -> list[str]:
    ats_category = next(
        (category for category in score_breakdown.categories if category.key == "ats_keywords"),
        None,
    )
    return ats_category.missing_keywords if ats_category else []

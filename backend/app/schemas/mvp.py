from pydantic import BaseModel, Field


class ScoreCategory(BaseModel):
    key: str
    label: str
    weight: float
    score: float
    contribution: float
    matched_count: int
    total_count: int
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)


class MatchScoreBreakdown(BaseModel):
    total_score: float
    categories: list[ScoreCategory] = Field(default_factory=list)
    explanation: str


class JobAnalysis(BaseModel):
    job_title: str | None = None
    company_name: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    ats_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    match_score: float = Field(ge=0, le=100)
    match_score_breakdown: MatchScoreBreakdown
    match_summary: str


class TailoredResume(BaseModel):
    headline: str
    summary: str
    rewritten_bullets: list[str]
    ats_optimized_resume: str


class ApplicationResult(BaseModel):
    application_id: str
    job_id: str
    candidate_profile_id: str
    resume_id: str
    resume_version_id: str
    analysis: JobAnalysis
    tailored_resume: TailoredResume
    cover_letter: str

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.mvp import JobAnalysis, TailoredResume


ApplicationStatusValue = Literal["Draft", "Ready to Apply", "Applied", "Interview", "Rejected", "Offer"]
MissingSkillCategory = Literal["not_on_resume", "can_add", "learning", "not_relevant"]


class CandidateProfileSummary(BaseModel):
    id: str
    file_name: str
    created_at: datetime


class CandidateProfileDetail(CandidateProfileSummary):
    raw_text: str


class ResumeSummary(BaseModel):
    id: str
    file_name: str
    created_at: datetime


class ResumeDetail(ResumeSummary):
    raw_text: str


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatusValue


class JobMetadata(BaseModel):
    company: str | None = None
    title: str | None = None
    job_url: str | None = None
    source: str | None = None
    job_type: str | None = None
    location: str | None = None
    salary: str | None = None
    deadline: str | None = None
    notes: str | None = None
    missing_skill_categories: dict[str, MissingSkillCategory] = Field(default_factory=dict)


class ApplicationMetadataUpdate(BaseModel):
    job_url: str | None = None
    source: str | None = None
    location: str | None = None
    salary: str | None = None
    deadline: str | None = None
    notes: str | None = None
    missing_skill_categories: dict[str, MissingSkillCategory] | None = None


class ResumeDiffLine(BaseModel):
    kind: Literal["unchanged", "added", "removed"]
    text: str


class ResumeDiff(BaseModel):
    added_lines: int
    removed_lines: int
    unchanged_lines: int
    lines: list[ResumeDiffLine]


class ApplicationSummary(BaseModel):
    id: str
    job_title: str | None
    company_name: str | None
    match_score: float
    status: ApplicationStatusValue
    created_at: datetime
    metadata: JobMetadata


class ApplicationDetail(ApplicationSummary):
    application_id: str
    candidate_profile_id: str
    resume_id: str
    resume_version_id: str
    job_description: str
    analysis: JobAnalysis
    tailored_resume: TailoredResume
    cover_letter: str
    resume_diff: ResumeDiff

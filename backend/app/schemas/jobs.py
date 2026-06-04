from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.applications import JobMetadata, ResumeDiff
from app.schemas.mvp import JobAnalysis, TailoredResume
from app.schemas.resume_versions import ResumeVersionSummary


JobStatus = Literal[
    "SAVED",
    "READY_TO_APPLY",
    "APPLIED",
    "OA_RECEIVED",
    "OA_COMPLETED",
    "INTERVIEW",
    "REJECTED",
    "OFFER",
    "WITHDRAWN",
    "GHOSTED",
]
JobSortField = Literal["match_score", "created_at", "deadline"]
SortDirection = Literal["asc", "desc"]


class JobStatusEventDetail(BaseModel):
    id: str
    from_status: str | None
    to_status: JobStatus
    source: str
    created_at: datetime


class JobCreate(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    job_type: str | None = None
    source: str | None = None
    url: str | None = None
    salary: str | None = None
    deadline: date | None = None
    description: str
    notes: str | None = None


class JobUpdate(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    job_type: str | None = None
    source: str | None = None
    url: str | None = None
    salary: str | None = None
    deadline: date | None = None
    description: str | None = Field(default=None, min_length=1)
    notes: str | None = None
    match_score: float | None = Field(default=None, ge=0, le=100)
    ats_keywords: list[str] | None = None
    missing_skills: list[str] | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    applied_at: datetime | None = None
    oa_received_at: datetime | None = None
    interview_at: datetime | None = None
    offer_at: datetime | None = None


class JobSummary(BaseModel):
    id: str
    application_id: str | None
    company: str | None
    title: str | None
    location: str | None
    job_type: str | None
    source: str | None
    url: str | None
    salary: str | None
    deadline: date | None
    match_score: float
    status: JobStatus
    created_at: datetime
    updated_at: datetime


class JobDetail(JobSummary):
    description: str
    ats_keywords: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    notes: str | None
    applied_at: datetime | None
    oa_received_at: datetime | None
    interview_at: datetime | None
    offer_at: datetime | None
    generated_at: datetime
    analysis: JobAnalysis | None
    tailored_resume: TailoredResume | None
    cover_letter: str | None
    resume_diff: ResumeDiff | None
    metadata: JobMetadata | None
    status_events: list[JobStatusEventDetail] = Field(default_factory=list)
    resume_version: ResumeVersionSummary | None = None


class JobStatusUpdate(BaseModel):
    status: JobStatus


class DashboardStats(BaseModel):
    total_jobs: int
    ready_to_apply: int
    applied: int
    oa: int
    interviews: int
    offers: int
    rejected: int
    average_match_score: float
    highest_match_score: float

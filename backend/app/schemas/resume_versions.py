from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ResumeVersionSource = Literal["BASE_UPLOAD", "TAILORING_RESULT", "MANUAL_EDIT", "IMPORT"]
ResumeDownloadFormat = Literal["txt", "md", "pdf"]


class ResumeVersionCreate(BaseModel):
    source_resume_id: str
    job_id: str | None = None
    name: str
    role_type: str | None = None
    is_base: bool = False
    company: str | None = None
    job_title: str | None = None
    content_text: str = Field(min_length=1)
    content_json: dict = Field(default_factory=dict)
    ats_keywords: list[str] = Field(default_factory=list)
    match_score: float = Field(default=0, ge=0, le=100)
    created_from: ResumeVersionSource = "MANUAL_EDIT"


class ResumeVersionSummary(BaseModel):
    id: str
    source_resume_id: str
    job_id: str | None
    name: str
    role_type: str | None
    version_number: int
    is_base: bool
    company: str | None
    job_title: str | None
    created_from: ResumeVersionSource
    match_score: float
    created_at: datetime
    updated_at: datetime


class ResumeVersionDetail(ResumeVersionSummary):
    content_text: str
    content_json: dict = Field(default_factory=dict)
    diff_summary: dict = Field(default_factory=dict)
    ats_keywords: list[str] = Field(default_factory=list)


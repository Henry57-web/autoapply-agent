from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.jobs import JobSummary


EmailType = Literal[
    "APPLICATION_CONFIRMATION",
    "OA_INVITATION",
    "OA_REMINDER",
    "INTERVIEW_INVITATION",
    "INTERVIEW_REMINDER",
    "REJECTION",
    "OFFER",
    "RECRUITER_OUTREACH",
    "OTHER",
]


class GmailConnectionStatus(BaseModel):
    connected: bool
    email_address: str | None = None
    scopes: list[str] = Field(default_factory=list)
    last_sync_at: datetime | None = None
    requires_configuration: bool = False


class GmailOAuthStart(BaseModel):
    authorization_url: str
    scope: str
    state: str


class GmailSyncRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=90)


class GmailSyncResult(BaseModel):
    scanned: int
    imported: int
    updated: int
    matched: int
    unmatched: int
    status_updates: int
    failed: int
    errors: list[str] = Field(default_factory=list)


class EmailSummary(BaseModel):
    id: str
    gmail_message_id: str
    thread_id: str | None
    job_id: str | None
    subject: str | None
    sender: str | None
    received_at: datetime
    email_type: EmailType
    raw_snippet: str
    is_processed: bool
    created_at: datetime
    linked_job: JobSummary | None = None


class EmailUpdate(BaseModel):
    email_type: EmailType | None = None
    job_id: str | None = None
    clear_job: bool = False


class EmailIngest(BaseModel):
    gmail_message_id: str
    thread_id: str | None = None
    subject: str | None = None
    sender: str | None = None
    received_at: datetime
    raw_snippet: str = ""
    body_text: str = ""

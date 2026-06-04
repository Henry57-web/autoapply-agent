from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    file_name: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    file_name: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    versions: Mapped[list["ResumeVersion"]] = relationship(back_populates="resume")


class ResumeVersion(Base):
    __tablename__ = "resume_versions"
    __table_args__ = (
        Index("uq_resume_versions_resume_id_version_number", "resume_id", "version_number", unique=True),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    resume_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("resumes.id"), index=True)
    job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role_type: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    is_base: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    content_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    diff_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_from: Mapped[str] = mapped_column(String(32), default="TAILORING_RESULT", index=True)
    ats_keywords: Mapped[list[str]] = mapped_column(JSONB, default=list)
    match_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    resume: Mapped[Resume] = relationship(back_populates="versions")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    candidate_profile_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("candidate_profiles.id"), index=True
    )
    resume_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("resumes.id"), index=True)
    resume_version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("resume_versions.id"), nullable=True
    )
    job_description: Mapped[str] = mapped_column(Text)
    job_title: Mapped[str] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=True)
    analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    cover_letter: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    status: Mapped["ApplicationStatus"] = relationship(back_populates="application", uselist=False)
    metadata_record: Mapped["ApplicationMetadata"] = relationship(
        back_populates="application",
        uselist=False,
    )


class ApplicationStatus(Base):
    __tablename__ = "application_statuses"

    application_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(32), default="Draft")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    application: Mapped[Application] = relationship(back_populates="status")


class ApplicationMetadata(Base):
    __tablename__ = "application_metadata"

    application_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), primary_key=True
    )
    job_url: Mapped[str] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    salary: Mapped[str] = mapped_column(String(255), nullable=True)
    deadline: Mapped[str] = mapped_column(String(32), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    missing_skill_categories: Mapped[dict] = mapped_column(JSONB, default=dict)

    application: Mapped[Application] = relationship(back_populates="metadata_record")

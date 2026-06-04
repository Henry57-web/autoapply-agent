from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
    company: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=True)
    salary: Mapped[str] = mapped_column(String(255), nullable=True)
    deadline: Mapped[date] = mapped_column(Date, nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    match_score: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(32), default="READY_TO_APPLY", index=True)
    ats_keywords: Mapped[list[str]] = mapped_column(JSONB, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSONB, default=list)
    strengths: Mapped[list[str]] = mapped_column(JSONB, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSONB, default=list)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    oa_received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    interview_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    offer_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    status_events: Mapped[list["JobStatusEvent"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="JobStatusEvent.created_at",
    )


class JobStatusEvent(Base):
    __tablename__ = "job_status_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    job_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
    )
    from_status: Mapped[str] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(64), default="manual")
    metadata_record: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    job: Mapped[Job] = relationship(back_populates="status_events")

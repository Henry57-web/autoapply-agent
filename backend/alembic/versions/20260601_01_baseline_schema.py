"""baseline schema

Revision ID: 20260601_01
Revises:
Create Date: 2026-06-01 03:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260601_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("candidate_profile_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("resume_version_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cover_letter", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_profile_id"], ["candidate_profiles.id"]),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_applications_candidate_profile_id", "applications", ["candidate_profile_id"])
    op.create_index("ix_applications_resume_id", "applications", ["resume_id"])
    op.create_table(
        "application_metadata",
        sa.Column("application_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_url", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("salary", sa.String(length=255), nullable=True),
        sa.Column("deadline", sa.String(length=32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("missing_skill_categories", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("application_id"),
    )
    op.create_table(
        "application_statuses",
        sa.Column("application_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("application_id"),
    )
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("job_type", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("salary", sa.String(length=255), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ats_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("weaknesses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("oa_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interview_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("offer_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_application_id", "jobs", ["application_id"], unique=True)
    op.create_index("ix_jobs_company", "jobs", ["company"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])
    op.create_index("ix_jobs_deadline", "jobs", ["deadline"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_title", "jobs", ["title"])
    op.create_table(
        "resume_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role_type", sa.String(length=64), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("is_base", sa.Boolean(), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("diff_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_from", sa.String(length=32), nullable=False),
        sa.Column("ats_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name="fk_resume_versions_job_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_versions_company", "resume_versions", ["company"])
    op.create_index("ix_resume_versions_created_from", "resume_versions", ["created_from"])
    op.create_index("ix_resume_versions_is_base", "resume_versions", ["is_base"])
    op.create_index("ix_resume_versions_job_id", "resume_versions", ["job_id"])
    op.create_index("ix_resume_versions_resume_id", "resume_versions", ["resume_id"])
    op.create_index("ix_resume_versions_role_type", "resume_versions", ["role_type"])
    op.create_index(
        "uq_resume_versions_resume_id_version_number",
        "resume_versions",
        ["resume_id", "version_number"],
        unique=True,
    )
    op.create_foreign_key(
        "fk_applications_resume_version_id",
        "applications",
        "resume_versions",
        ["resume_version_id"],
        ["id"],
    )
    op.create_table(
        "job_status_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_status_events_created_at", "job_status_events", ["created_at"])
    op.create_index("ix_job_status_events_job_id", "job_status_events", ["job_id"])
    op.create_index("ix_job_status_events_to_status", "job_status_events", ["to_status"])


def downgrade() -> None:
    op.drop_index("ix_job_status_events_to_status", table_name="job_status_events")
    op.drop_index("ix_job_status_events_job_id", table_name="job_status_events")
    op.drop_index("ix_job_status_events_created_at", table_name="job_status_events")
    op.drop_table("job_status_events")
    op.drop_constraint("fk_applications_resume_version_id", "applications", type_="foreignkey")
    op.drop_index("uq_resume_versions_resume_id_version_number", table_name="resume_versions")
    op.drop_index("ix_resume_versions_role_type", table_name="resume_versions")
    op.drop_index("ix_resume_versions_resume_id", table_name="resume_versions")
    op.drop_index("ix_resume_versions_job_id", table_name="resume_versions")
    op.drop_index("ix_resume_versions_is_base", table_name="resume_versions")
    op.drop_index("ix_resume_versions_created_from", table_name="resume_versions")
    op.drop_index("ix_resume_versions_company", table_name="resume_versions")
    op.drop_table("resume_versions")
    op.drop_index("ix_jobs_title", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_deadline", table_name="jobs")
    op.drop_index("ix_jobs_created_at", table_name="jobs")
    op.drop_index("ix_jobs_company", table_name="jobs")
    op.drop_index("ix_jobs_application_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("application_statuses")
    op.drop_table("application_metadata")
    op.drop_index("ix_applications_resume_id", table_name="applications")
    op.drop_index("ix_applications_candidate_profile_id", table_name="applications")
    op.drop_table("applications")
    op.drop_table("resumes")
    op.drop_table("candidate_profiles")

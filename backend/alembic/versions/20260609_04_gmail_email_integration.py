"""add gmail connections and emails

Revision ID: 20260609_04
Revises: 20260604_03
Create Date: 2026-06-09 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260609_04"
down_revision: Union[str, None] = "20260604_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gmail_connections",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DISCONNECTED"),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gmail_connections_created_at"), "gmail_connections", ["created_at"], unique=False)
    op.create_index(op.f("ix_gmail_connections_status"), "gmail_connections", ["status"], unique=False)

    op.create_table(
        "emails",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("gmail_message_id", sa.String(length=255), nullable=False),
        sa.Column("thread_id", sa.String(length=255), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("sender", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email_type", sa.String(length=64), nullable=False, server_default="OTHER"),
        sa.Column("raw_snippet", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gmail_message_id", name="uq_emails_gmail_message_id"),
    )
    op.create_index(op.f("ix_emails_created_at"), "emails", ["created_at"], unique=False)
    op.create_index(op.f("ix_emails_email_type"), "emails", ["email_type"], unique=False)
    op.create_index(op.f("ix_emails_gmail_message_id"), "emails", ["gmail_message_id"], unique=False)
    op.create_index(op.f("ix_emails_is_processed"), "emails", ["is_processed"], unique=False)
    op.create_index(op.f("ix_emails_job_id"), "emails", ["job_id"], unique=False)
    op.create_index(op.f("ix_emails_received_at"), "emails", ["received_at"], unique=False)
    op.create_index(op.f("ix_emails_thread_id"), "emails", ["thread_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_emails_thread_id"), table_name="emails")
    op.drop_index(op.f("ix_emails_received_at"), table_name="emails")
    op.drop_index(op.f("ix_emails_job_id"), table_name="emails")
    op.drop_index(op.f("ix_emails_is_processed"), table_name="emails")
    op.drop_index(op.f("ix_emails_gmail_message_id"), table_name="emails")
    op.drop_index(op.f("ix_emails_email_type"), table_name="emails")
    op.drop_index(op.f("ix_emails_created_at"), table_name="emails")
    op.drop_table("emails")
    op.drop_index(op.f("ix_gmail_connections_status"), table_name="gmail_connections")
    op.drop_index(op.f("ix_gmail_connections_created_at"), table_name="gmail_connections")
    op.drop_table("gmail_connections")

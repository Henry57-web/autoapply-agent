"""upgrade legacy resume version ledgers

Revision ID: 20260601_02
Revises: 20260601_01
Create Date: 2026-06-01
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260601_02"
down_revision: str | None = "20260601_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS job_id UUID")
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS name VARCHAR(255)")
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS role_type VARCHAR(64)")
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS version_number INTEGER DEFAULT 1")
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS is_base BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS company VARCHAR(255)")
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS content_json JSONB DEFAULT '{}'::jsonb")
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS diff_summary JSONB DEFAULT '{}'::jsonb")
    op.execute(
        "ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS created_from VARCHAR(32) DEFAULT 'TAILORING_RESULT'"
    )
    op.execute("ALTER TABLE resume_versions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now()")
    op.execute("UPDATE resume_versions SET name = title WHERE name IS NULL")
    op.execute("UPDATE resume_versions SET version_number = 1 WHERE version_number IS NULL")
    op.execute("UPDATE resume_versions SET is_base = FALSE WHERE is_base IS NULL")
    op.execute("UPDATE resume_versions SET content_json = '{}'::jsonb WHERE content_json IS NULL")
    op.execute("UPDATE resume_versions SET diff_summary = '{}'::jsonb WHERE diff_summary IS NULL")
    op.execute("UPDATE resume_versions SET created_from = 'TAILORING_RESULT' WHERE created_from IS NULL")
    op.execute("UPDATE resume_versions SET updated_at = created_at WHERE updated_at IS NULL")
    op.execute(
        """
        WITH duplicate_sources AS (
            SELECT resume_id
            FROM resume_versions
            GROUP BY resume_id
            HAVING COUNT(*) <> COUNT(DISTINCT version_number)
        ),
        ranked AS (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY resume_id ORDER BY created_at, id) AS next_version
            FROM resume_versions
            WHERE resume_id IN (SELECT resume_id FROM duplicate_sources)
        )
        UPDATE resume_versions AS version
        SET version_number = ranked.next_version
        FROM ranked
        WHERE version.id = ranked.id
        """
    )
    op.execute("ALTER TABLE resume_versions ALTER COLUMN name SET NOT NULL")
    op.execute("ALTER TABLE resume_versions ALTER COLUMN version_number SET NOT NULL")
    op.execute("ALTER TABLE resume_versions ALTER COLUMN is_base SET NOT NULL")
    op.execute("ALTER TABLE resume_versions ALTER COLUMN content_json SET NOT NULL")
    op.execute("ALTER TABLE resume_versions ALTER COLUMN diff_summary SET NOT NULL")
    op.execute("ALTER TABLE resume_versions ALTER COLUMN created_from SET NOT NULL")
    op.execute("ALTER TABLE resume_versions ALTER COLUMN updated_at SET NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_versions_job_id ON resume_versions (job_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_versions_role_type ON resume_versions (role_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_versions_is_base ON resume_versions (is_base)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_versions_company ON resume_versions (company)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_resume_versions_created_from ON resume_versions (created_from)")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_resume_versions_job_id'
            ) THEN
                ALTER TABLE resume_versions
                ADD CONSTRAINT fk_resume_versions_job_id
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL;
            END IF;
        END $$;
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_resume_versions_resume_id_version_number "
        "ON resume_versions (resume_id, version_number)"
    )


def downgrade() -> None:
    # Compatibility upgrades are intentionally non-destructive for legacy data.
    pass

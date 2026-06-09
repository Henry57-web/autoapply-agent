# Resume Version Control Findings

## Job Pipeline Workspace Findings - 2026-06-04

- Existing `POST /api/v1/jobs` persists manual Jobs as `SAVED`, but `company` and `title` are optional while `description` is required.
- Existing `PATCH /api/v1/jobs/{id}/status` already writes milestone timestamps and `job_status_events`; Kanban can reuse it unchanged.
- Existing single-URL Job Import service already centralizes source detection, safe fetches, parsing, LLM fallback, timeout handling, and user-readable failures.
- Existing `/jobs` is a single Table page with server-side search/status/score/sort filters.
- Job summaries do not expose whether a tailored Resume Version is linked.
- Imported confidence and warnings are not persisted, so a generic ingestion metadata ledger is needed for reliable Needs Review filtering.
- Native drag/drop works well for desktop Kanban; the Move To selector remains the accessible and mobile-safe primary fallback.
- Batch import must remain a preview operation. Saving each selected preview through `POST /jobs` preserves one validation and persistence path.
- URL syntax validation belongs inside each batch item, not on the top-level list, so one malformed URL cannot reject valid siblings.
- Empty descriptions are a useful general Needs Review signal for both manual and imported Jobs.

## Alembic Migration Findings

- FastAPI startup currently runs `Base.metadata.create_all()`, `ensure_resume_version_schema()`, Job backfill, and Resume Version backfill.
- `create_all()` does not upgrade existing tables and startup DDL is not auditable or downgradeable.
- `ensure_resume_version_schema()` contains schema changes and legacy normalization; structural DDL belongs in Alembic.
- Job and Resume Version backfills are idempotent data reconciliation and should become an explicit CLI command with summary counters.
- Existing Supabase contains production-like local personal data. Preserve it by stamping the baseline after schema validation; do not run destructive baseline DDL against it.
- Alembic must run with `async_engine_from_config()` because the configured database URL uses `postgresql+asyncpg`.
- The legacy ledger upgrade remains a second, additive Alembic revision so an existing database can be stamped at the baseline and upgraded without executing create-table statements.
- FastAPI startup now performs no DDL and no historical scans.

## Existing Data Flow

- `resumes` stores reusable uploaded source text.
- `resume_versions` already exists and stores tailored output snapshots with `resume_id`, `title`, `job_title`, `content`, `ats_keywords`, `match_score`, and `created_at`.
- `applications.resume_version_id` records the tailored version used by one application.
- `jobs.application_id` provides an indirect Job-to-Version relationship.
- `build_resume_diff()` provides a line-level diff at read time, but versions do not persist a diff summary.

## Gaps

- No base resume version row is created for uploaded resumes.
- No `job_id`, type, version number, source enum, company, role type, JSON content, persisted diff, or update timestamp on `resume_versions`.
- No resume version API or UI.
- Existing DOCX exports are application-oriented. New scope requires TXT, MD, and ATS-friendly PDF version downloads.

## Compatibility

- Existing Supabase tables are created with `Base.metadata.create_all()`, which does not add columns to existing tables.
- Add an idempotent startup compatibility migration for the new columns and backfill legacy rows.
- Compatibility migration also enforces non-null ledger fields, a Job foreign key, and unique `(resume_id, version_number)` numbering.
- Alembic remains the recommended follow-up before deployment.

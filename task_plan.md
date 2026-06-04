# Alembic And Integration Test Plan

## Goal

Replace startup schema mutation with Alembic migrations, add an explicit idempotent legacy backfill command, and strengthen core API integration tests without adding product features.

## Current Phase

Completed

## Phases

### Phase 1: Schema Analysis And Migration Design
- [x] Inventory current models and startup mutation logic.
- [x] Separate schema migration from idempotent data backfill.
- [x] Add Alembic runtime and baseline migration.
- [x] Add legacy compatibility revision and remove startup DDL.
- **Status:** completed

### Phase 2: Backfill Command
- [x] Build idempotent applications/jobs and resume-version backfill CLI.
- [x] Produce summary counters and safe repeat behavior.
- **Status:** completed

### Phase 3: Integration Tests
- [x] Add isolated PostgreSQL-backed API integration test harness.
- [x] Cover Generate, Jobs, Dashboard, Resume Versions, Job Import, and repeatable backfill.
- **Status:** completed

### Phase 4: Migration Verification
- [x] Verify upgrade head on empty database.
- [x] Verify downgrade -1 and re-upgrade.
- [x] Stamp configured legacy Supabase database and run backfill.
- **Status:** completed

### Phase 5: Frontend Smoke And Documentation
- [x] Run browser smoke test for existing pages.
- [x] Update README, PROJECT_STATUS.md, and progress.md.
- **Status:** completed

## Decisions

- Alembic owns schema creation and evolution.
- FastAPI startup performs no DDL and no legacy scans.
- Existing Supabase data is preserved with `alembic stamp 20260601_01`, then upgraded and backfilled.
- Empty databases use `alembic upgrade head`.
- Legacy backfill remains idempotent and explicit because data migration may need to be rerun independently from schema rollout.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| Docker socket permission denied inside sandbox | 1 | Re-run Docker verification with approved escalated access. |
| `alembic check` detected ORM drift for the resume-version ledger unique index | 1 | Declare the existing unique index in SQLAlchemy metadata and re-run the check. |
| Dashboard initially showed retryable load error after a Supabase connection timeout | 1 | Reloaded after direct API health validation; Dashboard recovered and retained persisted data. |
| Browser screenshot capture timed out | 2 | Completed smoke verification with DOM snapshots and console logs instead. |

# Resume Version Control Progress

## 2026-06-01

- Inspected current resume models, tailoring workflow, runtime diff, exports, navigation, and Job Detail.
- Confirmed `resume_versions` already exists but is a minimal tailored snapshot table.
- Chose an additive compatibility migration to preserve existing Supabase data.
- Added ResumeVersion ledger fields, the original idempotent compatibility path, and legacy backfill.
- Added immutable version service, direct Job association, base upload versions, diff summaries, delete protection, and TXT/MD/PDF exports.
- Added resume version APIs, `/resumes`, `/resumes/[id]`, navigation, and Job Detail linked-version entry.
- Installed ReportLab. First frontend build found a narrow TypeScript direction type; fixed with explicit filter typing.
- Rendered PDF preview and tightened heading styling to known resume sections.
- Browser QA found diff summary noise; upgraded persisted summaries to schema v2 and enabled startup recomputation.
- Verified `35/35` backend tests, Python compilation, frontend production build, Supabase schema upgrade, 7-row history backfill, sequential version normalization, Job linkage, protected Base deletion, non-base deletion, and TXT/MD/PDF downloads.
- Browser-smoked `/resumes`, `/resumes/{id}`, diff summary v2, and Job Detail linked-version entry.
- Hardened compatibility migration with non-null ledger fields, Job foreign key, and unique source-resume version numbers.

## Alembic And Integration Tests - 2026-06-01

- Inspected all 8 core tables and identified startup DDL plus startup backfill paths.
- Chose Alembic for schema ownership and an explicit repeatable CLI for legacy reconciliation.
- Added Alembic async runtime, full schema baseline, and additive resume-ledger compatibility revision.
- Removed FastAPI startup `create_all()` and startup backfills.
- Added explicit `python -m app.cli.backfill_legacy` reconciliation command with summary counters.
- Updated `./start.sh` to apply migrations before launching services.
- Verified Python compilation and the existing `35/35` backend tests.
- Started local Docker PostgreSQL and created isolated migration and API test databases.
- Verified empty-database Alembic upgrade, non-destructive compatibility downgrade `-1`, re-upgrade, and `alembic check`.
- Added the missing ORM declaration for the unique `(resume_id, version_number)` ledger index after `alembic check` exposed drift.
- Added PostgreSQL-backed integration coverage for Generate, Jobs CRUD, lifecycle milestones, Dashboard, Resume Versions, downloads, Job Import, and repeatable legacy reconciliation.
- Verified `42/42` backend tests with the PostgreSQL integration database enabled.
- Adopted the configured Supabase database by stamping `20260601_01`, upgrading to `20260601_02`, and running backfill twice.
- Supabase backfill was idempotent: first run updated one legacy tailored link; second run created and updated zero records.
- Updated README and PROJECT_STATUS with migration, backfill, Supavisor, and integration-test commands.
- Browser-smoked `/`, `/generate`, `/jobs`, `/jobs/{id}`, `/resumes`, and `/resumes/{id}` after one-command startup.
- Confirmed refresh persistence for the 5 Supabase Jobs and 7 Resume Versions and found no browser console errors.
- Observed one transient Supabase connection timeout on the first Dashboard request; the retryable error state rendered correctly and reload recovered.

## Job Pipeline Workspace - 2026-06-04

- Audited Jobs API, Jobs Table page, status update flow, Job URL Import service, and Dashboard aggregation.
- Chose native Kanban drag/drop plus Move To fallback, explicit batch preview/confirmation, and generic ingestion metadata.
- Added migration `20260604_03`, richer Job summaries, manual-create validation, and partial-success batch import previews.
- Added Table/Kanban views, status rollback, manual create, batch confirmation, and five quick filters.
- Verified empty PostgreSQL migration, downgrade/re-upgrade, Alembic check, `47/47` backend tests, compileall, and frontend production build.
- Upgraded the configured Supabase database to `20260604_03`.
- Browser-smoked Table/Kanban switching, ten status groups, Add Job, Batch Import, Quick Filters, persisted Supabase Jobs, and console errors.
- Restarted a stale pre-change backend process and reverified all 6 Supabase Jobs expose review and linked-resume summary flags.
- Acceptance testing exposed and fixed whole-batch rejection for malformed URLs, empty-JD review classification, whitespace-only required fields, and missing batch result totals.
- Verified Table/Kanban parity with 10 persisted Jobs, status movement through APPLIED/INTERVIEW/OFFER/REJECTED, 5 status events, Dashboard synchronization, Quick Filters, live Greenhouse/Lever parsing, `3 success / 2 failed` partial import, and restart persistence.

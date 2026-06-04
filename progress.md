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

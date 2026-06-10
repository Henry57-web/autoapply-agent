# PROJECT STATUS

## Project Overview

AutoApply Agent is a local-first AI Job Application Management Platform. It accepts a reusable candidate profile, a reusable base resume, and a job description, then extracts ATS keywords, computes an explainable match score, generates a tailored resume and concise cover letter, and automatically saves the role into a persistent job pipeline.

The current product is intended for personal local use. It is not yet prepared for public deployment or multi-user access.

## Current Architecture

```text
Next.js frontend
  -> FastAPI REST API
    -> PostgreSQL database
    -> Provider-independent LLM service
      -> Gemini, OpenAI, Groq, or DeepSeek
```

Backend boundaries:

- `backend/app/api/routes`: HTTP validation and REST endpoints.
- `backend/app/services`: parsing, scoring, resume diffing, DOCX generation, prompt loading, LLM adapters, and workflow orchestration.
- `backend/app/services/job_import`: source detection, SSRF-aware single-page fetching, platform parsers, and LLM fallback extraction.
- `backend/app/services/email_*` and `backend/app/services/gmail_client.py`: Gmail OAuth, encrypted refresh-token handling, metadata-only sync, email classification, Job matching, and automated status sync.
- `backend/app/services/resume_version_service.py`: immutable resume ledger, Job linkage, backfill, deletion rules, and downloads.
- `backend/app/prompts`: externalized prompt templates.
- `backend/app/models`: SQLAlchemy persistence models.
- `backend/app/schemas`: typed API request and response contracts.
- `backend/alembic`: async Alembic runtime and versioned PostgreSQL schema migrations.
- `backend/app/cli/backfill_legacy.py`: explicit repeatable historical-data reconciliation command.

Frontend boundaries:

- `frontend/app/page.tsx`: Dashboard.
- `frontend/app/generate/page.tsx`: AI tailoring workflow.
- `frontend/app/jobs/page.tsx`: Table/Kanban pipeline workspace, quick filters, manual create, and batch import entry.
- `frontend/components/jobs`: reusable Table, Kanban, status selector, manual create, and batch import components.
- `frontend/app/jobs/[id]/page.tsx`: job detail and lifecycle tracking.
- `frontend/app/resumes/page.tsx`: searchable resume version ledger.
- `frontend/app/resumes/[id]/page.tsx`: version detail, diff summary, linked Job, and downloads.
- `frontend/app/emails/page.tsx`: Gmail-derived application email inbox with search, filters, manual reclassification, and Job linking.
- `frontend/app/settings/page.tsx`: Gmail connection status, OAuth start, and manual sync controls.
- `frontend/components`: reusable UI sections for profiles, resumes, history, metadata, score results, exports, and diffs.
- `frontend/lib/api.ts`: typed backend client.
- `start.sh`, `status.sh`, and `stop.sh`: root-level local lifecycle helpers.
- `sync-github.sh`: secret-aware one-time or watch-mode GitHub synchronization.

Database model:

- `candidate_profiles`: reusable parsed candidate profiles.
- `resumes`: reusable parsed base resumes.
- `resume_versions`: immutable base and tailored snapshots with source resume, direct Job link, role type, version number, source type, structured diff, and export content.
- `applications`: job description, analysis, cover letter, and links to profile and resume entities.
- `application_statuses`: application workflow status.
- `application_metadata`: optional job URL, source, location, salary, deadline, notes, and missing-skill classifications.
- `jobs`: pipeline aggregate for a role, including status, score, lifecycle dates, generic ingestion metadata, and future integration anchors.
- `job_status_events`: auditable state transition history with a source field for manual or automated updates.
- `gmail_connections`: Gmail OAuth connection metadata, readonly scopes, encrypted refresh token, sync timestamps, and OAuth state.
- `emails`: Gmail message metadata, snippet, classification, processing flag, optional Job link, and match metadata.

## Tech Stack

- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide icons
- Backend: FastAPI, Python, SQLAlchemy async, Pydantic Settings, Uvicorn
- Database: PostgreSQL; local Docker Compose is available, and the current machine is configured to use Supabase PostgreSQL
- Database driver: `asyncpg` configured for Supabase/Supavisor compatibility
- AI: provider abstraction supporting Gemini, OpenAI, Groq, and DeepSeek
- Parsing: TXT, Markdown, PDF via `pypdf`, DOCX via `python-docx`
- Export: DOCX via `python-docx`; ATS-friendly PDF via `reportlab`; TXT and Markdown
- Job URL import: `httpx`, Beautiful Soup, platform-specific parsers, JSON-LD parsing, and optional LLM fallback
- Tests: Python `unittest`

## Completed Features

- Upload and parse candidate profiles from TXT, MD, PDF, and DOCX.
- Save and reuse candidate profiles.
- Upload and parse base resumes from TXT, MD, PDF, and DOCX.
- Save and reuse base resumes through the Resume Library.
- Analyze job descriptions with an interchangeable LLM provider.
- Extract required skills, preferred skills, ATS keywords, and responsibilities.
- Compute a deterministic weighted match score with category-level explanation.
- Generate tailored resume bullets and ATS-optimized resume content.
- Generate concise cover letters.
- Store application history and workflow status.
- Store job URLs, sources, locations, salaries, deadlines, and notes.
- Classify missing skills as `not_on_resume`, `can_add`, `learning`, or `not_relevant`.
- Compare original and tailored resumes with a structured line-level diff.
- Export tailored resumes and cover letters as DOCX files.
- Keep prompts outside business logic in `backend/app/prompts`.
- Keep LLM adapters isolated behind a provider interface.
- Add Supabase/Supavisor-compatible async PostgreSQL connection settings.
- Automatically create a persistent Job after AI tailoring.
- Manually save Jobs for future import workflows.
- Search Jobs by company or role.
- Filter Jobs by status and score range.
- Sort Jobs by score, creation time, or deadline.
- Track `SAVED`, `READY_TO_APPLY`, `APPLIED`, `OA_RECEIVED`, `OA_COMPLETED`, `INTERVIEW`, `REJECTED`, `OFFER`, `WITHDRAWN`, and `GHOSTED`.
- Edit saved Job fields from Job Detail, including metadata, JD, score, keyword lists, notes, and lifecycle timestamps.
- Automatically record applied, OA, interview, and offer milestone timestamps.
- Record auditable Job status events.
- Show Dashboard pipeline counts, average score, and highest score.
- Import a single public Job URL into the Generate form without automatically generating or saving a Job.
- Detect Greenhouse, Lever, Ashby, Workday, LinkedIn, Handshake, Simplify, generic company career pages, and unknown URLs.
- Parse Greenhouse, Lever, and Ashby with dedicated parsers; parse Workday and public career pages on a best-effort basis.
- Fall back to schema-validated LLM field extraction when deterministic parsing leaves important fields empty.
- Show import warnings and preserve user editing and confirmation before generation.
- Block private-network targets, unsafe redirects, oversized responses, login-restricted sources, and fetch timeouts.
- Backfill legacy `applications` into `jobs` idempotently during startup so historical analyses appear in Jobs.
- Start the configured local frontend and backend together with `./start.sh`.
- Create protected Base Resume versions when source resumes are uploaded.
- Create immutable Tailored Resume versions after each Generate workflow and link them directly to Jobs.
- Preserve the exact `resume_version_id` used by each Application.
- Search and filter Resume Versions at `/resumes`.
- Review version metadata, linked Job, persisted diff summary, and content at `/resumes/{id}`.
- Download Resume Versions as TXT, Markdown, or ATS-friendly text PDF.
- Delete non-base versions while protecting Base Resume versions.
- Backfill existing Resume data into the version ledger and normalize legacy version numbers idempotently.
- Manage schema creation and evolution with Alembic instead of FastAPI startup DDL.
- Reconcile legacy applications, Jobs, source resumes, and tailored resume links with an explicit idempotent CLI.
- Cover core persistence workflows with PostgreSQL-backed API integration tests.
- Safely synchronize source changes to the configured GitHub remote with one-time or watch-mode commands.
- Run GitHub Actions CI for backend migrations/tests/compileall and frontend production build using an isolated PostgreSQL service.
- Provide test environment templates for backend and frontend without real secrets.
- Provide a Gmail manual QA checklist covering OAuth setup, readonly scope verification, sync, classification, status sync, revocation, and local token cleanup.
- Switch Jobs between Table and Kanban views.
- Drag Jobs between status columns or use a reliable Move To selector with rollback on failure.
- Create manual Jobs with an optional JD and required company/title.
- Batch-import up to 10 public Job URLs into previews with partial success, retry, selection, and explicit save confirmation.
- Filter Jobs quickly by high match, ready status, review need, upcoming deadline, or missing Resume Version.
- Connect Gmail through Google OAuth using only `gmail.readonly`.
- Encrypt Gmail refresh tokens with `GMAIL_TOKEN_ENCRYPTION_KEY`.
- Manually sync recent Gmail messages without storing full bodies or attachments.
- Classify application confirmations, OA invitations/reminders, interview invitations/reminders, rejections, offers, recruiter outreach, and other mail.
- Match emails to existing Jobs by company, title, subject, sender, and snippet.
- Automatically update Job status from matched Gmail signals and write `job_status_events` with source `gmail_sync`.
- Review, search, filter, reclassify, link, unlink, and rematch emails at `/emails`.
- Display pending OA, upcoming interviews, recruiter messages, unmatched emails, rejections, and offers on Dashboard.

## Current Progress

The MVP is functional locally at `http://localhost:3000`.

Working flows:

- Reuse or upload a candidate profile.
- Reuse or upload a base resume.
- Save a newly uploaded profile or resume for later use.
- Paste a JD and optional job metadata.
- Paste a public Job URL to prefill editable metadata and JD, then review it before generation.
- Generate and persist analysis, tailored resume, cover letter, and status.
- Review application history.
- Edit job metadata and missing-skill classifications.
- View the tailored resume diff.
- Export DOCX files.
- Review Jobs from the Dashboard, Jobs table, and Job Detail screens.
- Manage Jobs from Table or Kanban view, add manual Jobs, and confirm batch-import previews.
- Review Resume Versions from `/resumes`, open historical snapshots, and download TXT, Markdown, or PDF exports.
- Connect Gmail from `/settings`, run manual sync, and manage imported email records at `/emails`.

New Job Management APIs:

```text
POST   /api/v1/jobs
POST   /api/v1/jobs/batch-import
GET    /api/v1/jobs
GET    /api/v1/jobs/{job_id}
PATCH  /api/v1/jobs/{job_id}
PATCH  /api/v1/jobs/{job_id}/status
DELETE /api/v1/jobs/{job_id}
GET    /api/v1/dashboard
POST   /api/v1/job-import/url
GET    /api/v1/gmail/status
GET    /api/v1/gmail/oauth/start
GET    /api/v1/gmail/oauth/callback
POST   /api/v1/gmail/sync
GET    /api/v1/emails
PATCH  /api/v1/emails/{email_id}
GET    /api/v1/resume-versions
GET    /api/v1/resume-versions/{version_id}
POST   /api/v1/resume-versions
DELETE /api/v1/resume-versions/{version_id}
GET    /api/v1/resume-versions/{version_id}/download?format=txt|md|pdf
GET    /api/v1/jobs/{job_id}/resume-version
```

`POST /api/v1/mvp/run` now also creates a `jobs` row automatically and returns `job_id`.

Local endpoints when the development servers are running:

- Frontend dev server: `http://localhost:3000`
- Backend API: `http://127.0.0.1:8000`
- Backend health check: `http://127.0.0.1:8000/health`

The development servers are intentionally stopped after verification. Start them when needed with the command below.

Simplest local startup:

```bash
./start.sh
```

Keep the terminal open while using the app. Press `Control+C` to stop both services.

Verification completed:

- Backend unit and integration tests: `47/47` passing.
- Python bytecode compilation: passing.
- Frontend production build: passing.
- API health, Dashboard, Job create/list/detail/status/delete, application list/detail, metadata PATCH, and resume list requests: passing.
- Browser smoke test for Jobs list, Job Detail, and Job URL Import error handling: passing.
- Legacy Job backfill idempotency across repeated backend startups: passing.
- Root-level `./start.sh`, `./status.sh`, and `Control+C` shutdown flow: passing.
- Resume Version legacy schema upgrade, backfill, version-number normalization, Job linkage, base deletion protection, manual-version deletion, and TXT/MD/PDF downloads: passing.
- Browser smoke test for `/resumes`, `/resumes/{id}`, persisted diff summary, and Job Detail linked-version entry: passing.
- PDF text extraction and rendered first-page visual review: passing.
- Browser smoke test after Alembic adoption for `/`, `/generate`, `/jobs`, `/jobs/{id}`, `/resumes`, and `/resumes/{id}`: passing with refresh persistence and no console errors.
- Browser smoke test for Jobs Table/Kanban switching, Add Job, Batch Import, Quick Filters, and persisted Supabase data: passing with no console errors.
- Configured Supabase is at Alembic revision `20260604_03 (head)` and all 6 existing Jobs expose linked Resume Version and review summary flags.
- Acceptance verification created and persisted 4 review records, confirmed 10 Table/Kanban Jobs, all 10 status columns, 5 status events for the manual acceptance Job, Dashboard synchronization, and restart persistence.
- Live batch import verified Greenhouse and Lever success with isolated invalid/private URL failures, including a `3 success / 2 failed` partial-success run.
- Alembic empty-database `upgrade head`, `downgrade -1`, re-upgrade, and `alembic check`: passing.
- Job Pipeline migration `20260604_03`, manual create, status movement/events, batch partial-success import, and review rules: passing in isolated PostgreSQL.
- Frontend production build with Table/Kanban workspace: passing.
- Gmail integration migration `20260609_04`, metadata-only email ingestion, OAuth state storage, email classification, Job matching, automated status updates, and Dashboard email metrics: passing in isolated PostgreSQL.
- Backend tests after Gmail integration: `55/55` passing with PostgreSQL integration database enabled.
- Python bytecode compilation after Gmail integration: passing.
- Frontend production build after Gmail pages: passing.
- CI workflow local simulation after Gmail QA hardening: Alembic upgrade, latest downgrade/re-upgrade, backend tests `60/60`, compileall, and frontend build: passing.
- Gmail safety review: `.env` ignored, tokens encrypted, full bodies/attachments not stored, tokens/API keys not logged, OAuth state validated, sync bounded to 1-90 days and 50 Gmail messages per run.
- Configured Supabase adoption: stamped baseline, upgraded to `20260601_02 (head)`, and ran repeatable backfill successfully.
- Supabase backfill first run: 5 applications scanned, 0 Jobs created, 2 resumes scanned, 0 versions created, 1 tailored version updated, 0 failures.
- Supabase backfill second run: 0 records created or updated, confirming idempotency.

## Files Modified This Session

- `.gitignore`
- `README.md`
- `PROJECT_STATUS.md`
- `.github/workflows/ci.yml`
- `docs/GMAIL_QA_CHECKLIST.md`
- `docker-compose.yml`
- `profiles/haoyang-lin-candidate-profile.md`
- `start.sh`
- `sync-github.sh`
- `status.sh`
- `stop.sh`
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/.env.test.example`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/20260601_01_baseline_schema.py`
- `backend/alembic/versions/20260601_02_resume_ledger_legacy_compat.py`
- `backend/alembic/versions/20260604_03_job_ingestion_metadata.py`
- `backend/alembic/versions/20260609_04_gmail_email_integration.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/models/application.py`
- `backend/app/models/job.py`
- `backend/app/models/email.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/mvp.py`
- `backend/app/schemas/applications.py`
- `backend/app/schemas/jobs.py`
- `backend/app/schemas/emails.py`
- `backend/app/schemas/job_import.py`
- `backend/app/schemas/resume_versions.py`
- `backend/app/schemas/jobs.py`
- `backend/app/api/routes/__init__.py`
- `backend/app/api/routes/mvp.py`
- `backend/app/api/routes/applications.py`
- `backend/app/api/routes/jobs.py`
- `backend/app/api/routes/job_import.py`
- `backend/app/api/routes/resume_versions.py`
- `backend/app/api/routes/emails.py`
- `backend/app/services/document_parser.py`
- `backend/app/services/docx_export.py`
- `backend/app/services/match_scorer.py`
- `backend/app/services/prompt_registry.py`
- `backend/app/services/resume_diff.py`
- `backend/app/services/tailoring_service.py`
- `backend/app/services/application_presenter.py`
- `backend/app/services/job_service.py`
- `backend/app/services/email_classifier.py`
- `backend/app/services/email_matcher.py`
- `backend/app/services/email_service.py`
- `backend/app/services/gmail_client.py`
- `backend/app/services/token_cipher.py`
- `backend/app/services/job_import/__init__.py`
- `backend/app/services/job_import/fetcher.py`
- `backend/app/services/job_import/parsers.py`
- `backend/app/services/job_import/service.py`
- `backend/app/services/job_import/source_detector.py`
- `backend/app/services/pdf_export.py`
- `backend/app/services/legacy_backfill.py`
- `backend/app/cli/__init__.py`
- `backend/app/cli/backfill_legacy.py`
- `backend/app/services/resume_version_presenter.py`
- `backend/app/services/resume_version_service.py`
- `backend/app/services/llm/provider.py`
- `backend/app/services/llm/factory.py`
- `backend/app/services/llm/gemini.py`
- `backend/app/services/llm/openai_compatible.py`
- `backend/app/prompts/analyze_job.md`
- `backend/app/prompts/tailor_resume.md`
- `backend/app/prompts/cover_letter.md`
- `backend/app/prompts/parse_job_page.md`
- `backend/tests/test_docx_export.py`
- `backend/tests/test_llm_factory.py`
- `backend/tests/test_match_scorer.py`
- `backend/tests/test_resume_diff.py`
- `backend/tests/test_job_service.py`
- `backend/tests/test_resume_versions.py`
- `backend/tests/test_job_import.py`
- `backend/tests/test_email_services.py`
- `backend/tests/integration/__init__.py`
- `backend/tests/integration/test_api_integration.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/.env.test.example`
- `frontend/app/layout.tsx`
- `frontend/app/globals.css`
- `frontend/app/page.tsx`
- `frontend/app/generate/page.tsx`
- `frontend/app/jobs/page.tsx`
- `frontend/app/jobs/[id]/page.tsx`
- `frontend/app/resumes/page.tsx`
- `frontend/app/resumes/[id]/page.tsx`
- `frontend/app/emails/page.tsx`
- `frontend/app/settings/page.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/job-pipeline.ts`
- `frontend/components/jobs/AddJobDialog.tsx`
- `frontend/components/jobs/BatchImportDialog.tsx`
- `frontend/components/jobs/JobKanban.tsx`
- `frontend/components/jobs/JobStatusSelect.tsx`
- `frontend/components/jobs/JobsTable.tsx`
- `frontend/components/FileField.tsx`
- `frontend/components/ProfileManager.tsx`
- `frontend/components/ResumeManager.tsx`
- `frontend/components/JobMetadataFields.tsx`
- `frontend/components/JobUrlImport.tsx`
- `frontend/components/JobEditPanel.tsx`
- `frontend/components/ApplicationMetadataPanel.tsx`
- `frontend/components/HistoryPanel.tsx`
- `frontend/components/ResumeDiffPanel.tsx`
- `frontend/components/KeywordList.tsx`
- `frontend/components/ResultPanel.tsx`
- `frontend/components/AppShell.tsx`

## Outstanding Issues

- Existing test data includes duplicate candidate profiles and duplicate base resumes with identical filenames.
- Resume Library stores parsed text and filename, not the original PDF or DOCX binary.
- SQLAlchemy metadata contains a deliberate circular relationship between `applications`, `jobs`, and `resume_versions`. The baseline migration handles foreign-key creation order explicitly, but `alembic check` emits a non-fatal table-sort warning.
- Supabase/Supavisor can occasionally time out on a fresh connection. Existing UI error states surface the failure and allow retry; consider adding bounded retry for read-only requests if this becomes frequent.
- Automatic GitHub watch mode runs only while its terminal remains open. A persistent background LaunchAgent is intentionally not installed by default.
- Diff summaries use text heuristics. They capture keyword, bullet, ordering, and technology changes but are not semantic AI explanations.
- Profile and resume libraries do not yet support rename, delete, or deduplication.
- Native HTML drag/drop is desktop-oriented; mobile and keyboard users should use the Move To selector.
- Batch URL import is intentionally sequential and capped at 10 URLs; it does not generate materials or save without confirmation.
- Workday, Simplify, and generic company career pages use best-effort parsing and may require manual corrections.
- LinkedIn and Handshake imports intentionally stop with a user-readable manual-paste instruction when login or anti-bot restrictions are expected.
- The Job URL importer fetches public server-rendered HTML only. It does not run a browser for JavaScript-heavy pages.
- Integration tests cover core APIs, but metadata PATCH, DOCX endpoints, and generic public career-page imports still rely on unit or smoke coverage.
- The browser automation security policy blocked an automated click into the History tab. History metadata behavior was verified through API checks and frontend build validation, but the History screen should receive a short manual UI smoke test.
- Gmail sync is manual and metadata-only; there is no realtime Gmail watch, incremental cursor, or Google Pub/Sub integration yet.
- Gmail OAuth requires local Google Cloud OAuth credentials and a Fernet encryption key. Public deployment may require Google app verification for the restricted Gmail readonly scope.
- Email classification and Job matching are deterministic heuristics. Unmatched and manually overridden emails are supported, but semantic LLM classification is not enabled yet.
- CI is configured but has not been observed on GitHub Actions in this local session. The local equivalent commands pass.
- There is no authentication or per-user data boundary. This is acceptable for local-only personal use, but it blocks public deployment.

## TODO (Priority Order)

1. Push this branch and confirm the GitHub Actions CI workflow passes on GitHub.
2. Add integration coverage for application metadata PATCH, DOCX downloads, and generic public career-page imports.
3. Add Gmail incremental sync cursor and optional Google Pub/Sub watch after manual sync proves stable.
4. Add optional manual tailored-resume editing that creates a new immutable version instead of overwriting snapshots.
5. Add rename, delete, and deduplication controls for saved candidate profiles and base resumes.
6. Design dedicated OA and Interview tracking modules keyed by `job_id` and linked `emails`.
7. Decide whether original uploaded files should be stored locally or in object storage.
8. Add authentication only if the product scope changes from local personal use to deployment.

## Next Recommended Task

Push the CI workflow and confirm it passes on GitHub Actions before beginning Gmail realtime sync or dedicated OA/Interview modules.

## Session Summary

- Built a production-shaped Next.js and FastAPI MVP for AI-assisted job application tailoring.
- Configured PostgreSQL persistence with Supabase/Supavisor-compatible async settings.
- Isolated LLM switching behind provider adapters and configured Gemini as the cost-effective default.
- Added explainable weighted ATS scoring and category-level score breakdowns.
- Added reusable candidate profile persistence and created a detailed local candidate profile document.
- Added application history, workflow statuses, DOCX exports, job metadata, missing-skill categories, and resume diffs.
- Added a reusable Resume Library with saved-resume selection during generation.
- Fixed stale SQLAlchemy relationship state after first-time metadata creation by refreshing existing entities.
- Fixed a frontend compatibility bug when cached history entries did not yet contain `metadata`.
- Verified backend tests, frontend builds, API endpoints, and browser rendering.
- Added the extensible `jobs` aggregate and `job_status_events` lifecycle history.
- Added Dashboard, Jobs list, and Job Detail pages with loading, empty, retryable error, and persistent status tracking states.
- Added manual Job creation and deletion APIs for future imports and integration ingestion.
- Added Job URL Import with safe single-page fetching, platform detection, dedicated parsers, generic parsing, and schema-validated LLM fallback.
- Added Generate-page URL import with loading, warnings, editable prefills, and an explicit user-confirmed Generate step.
- Fixed historical analyses missing from the Jobs page by idempotently backfilling legacy applications during startup.
- Fixed Job Detail async relationship loading and removed an invalid nested form that caused Import clicks to refresh the Generate page.
- Added a one-command local launcher that configures missing local files, installs missing dependencies, starts both services, and shuts them down together with `Control+C`.
- Added persistent Job editing from Job Detail and synchronized shared edits back into application history metadata.
- Upgraded `resume_versions` into an immutable Base/Tailored resume ledger with direct Job linkage and application snapshots.
- Added persisted diff summaries, Resume Versions pages, linked-version Job navigation, and TXT/Markdown/ATS-friendly PDF downloads.
- Added idempotent Resume Version schema compatibility migration and legacy backfill for the configured Supabase database.
- Replaced startup schema mutation with async Alembic migrations and adopted the configured Supabase database at revision `20260601_02`.
- Added an explicit repeatable legacy backfill CLI and verified it is idempotent against local tests and Supabase.
- Added PostgreSQL-backed integration tests for Generate, Jobs, Dashboard, Resume Versions, Job Import, and legacy reconciliation.
- Added the Table/Kanban Jobs workspace, persistent status movement, manual Job creation, batch URL preview/confirmation, and quick filters.
- Added Gmail readonly OAuth integration, encrypted token storage, manual metadata-only sync, email classification, Job matching, automatic status updates, Dashboard email metrics, `/settings`, and `/emails`.
- Added GitHub Actions CI, test env templates, Gmail manual QA checklist, expanded Gmail mock/integration tests, and documented the Gmail security review.

## How To Resume

1. Open the repository at `/Users/haoyanglin/Documents/Playground/autoapply-agent`.
2. Read this file and `README.md`.
3. Check `git status --short` and review the current Gmail integration changes.
4. Confirm that `backend/.env` exists locally. Do not print or commit it because it contains database and LLM credentials.
5. Confirm the backend with `curl http://127.0.0.1:8000/health`. Start it if needed.
6. Confirm the frontend at `http://localhost:3000`. Start it if needed.
7. Run `cd backend && .venv/bin/python -m alembic current` and confirm `20260609_04 (head)`.
8. Run backend tests and the frontend production build before further feature work.
9. Create a clean Git baseline commit after reviewing untracked files and excluding secrets.

## Important Commands

Install backend dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run backend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run backend tests:

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q app
```

Run migrations and legacy reconciliation:

```bash
cd backend
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic check
.venv/bin/python -m app.cli.backfill_legacy
```

Generate Gmail token encryption key:

```bash
cd backend
.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Required Gmail environment variables:

```text
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REDIRECT_URI
GMAIL_TOKEN_ENCRYPTION_KEY
```

Run PostgreSQL-backed integration tests:

```bash
cd backend
TEST_DATABASE_URL=postgresql+asyncpg://autoapply:autoapply@127.0.0.1:5432/autoapply_test \
  .venv/bin/python -m unittest discover -s tests -v
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run frontend:

```bash
cd frontend
npm run dev
```

Build frontend:

```bash
cd frontend
npm run build
```

Run local Docker PostgreSQL if Supabase is not used:

```bash
docker compose up -d postgres
```

Create a migration after model changes:

```bash
cd backend
.venv/bin/python -m alembic revision --autogenerate -m "describe schema change"
```

Deployment:

```text
Not configured. The current scope is local-only personal use.
```

## Notes

- Never commit `backend/.env`, `frontend/.env.local`, API keys, or database passwords.
- `backend/.env.example` and `frontend/.env.example` are safe templates.
- The current machine uses a Supabase PostgreSQL connection configured outside tracked files. Use the transaction pooler port appropriate for async SQLAlchemy and Supavisor.
- `backend/app/db/session.py` intentionally disables prepared statement caching and uses `NullPool` for Supabase/Supavisor compatibility.
- `backend/alembic/env.py` uses the same asyncpg pooler compatibility settings.
- Prompts are stored in Markdown files under `backend/app/prompts`; do not hardcode provider prompts inside services.
- Gmail sync requests only `https://www.googleapis.com/auth/gmail.readonly`; do not add send/modify scopes unless the product scope changes and the security model is redesigned.
- Gmail stores metadata, snippet, classification, and Job linkage only. Do not store full email bodies or attachments without a privacy review.
- Existing saved profile and resume rows may contain duplicates from earlier workflow tests.
- Base resumes and tailored versions are separate concepts: `resumes` are reusable source documents, while `resume_versions` belong to job-specific tailoring runs.
- Local Node tooling was installed under `.tools/node` on the current machine. On another machine, a normal Node.js installation and standard `npm` commands are sufficient.
- Current LLM credentials and database credentials are intentionally omitted from this document.
- Job URL import is deliberately single-page and user-confirmed. Do not expand it into crawling, login bypass, captcha bypass, or automatic application submission without a separate product and security review.

## Last Updated

2026-06-09 15:52:10 EDT

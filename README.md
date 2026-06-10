# AutoApply Agent

AutoApply Agent is a local-first AI Job Application Management Platform. It combines resume tailoring with a persistent job pipeline:

- upload a candidate profile
- upload a base resume
- paste a job description
- extract ATS keywords and required skills
- compute a deterministic keyword match score
- generate rewritten resume bullets
- generate an ATS-optimized resume
- generate a concise cover letter
- store application history and resume versions in PostgreSQL
- save and reuse candidate profiles
- save and reuse base resumes
- review application history and update application status
- export tailored resumes and cover letters as DOCX files
- save job links, sources, locations, salary ranges, deadlines, and notes
- compare tailored resumes against their original versions
- classify missing skills for follow-up actions
- automatically save analyzed jobs to a pipeline
- search, filter, and sort jobs
- track application statuses and milestone dates
- review dashboard pipeline statistics
- import a single public job URL and prefill editable job metadata before generation
- preserve immutable base and tailored resume versions linked to Jobs
- review resume version diffs and download ATS-friendly TXT, Markdown, or PDF files
- manage Jobs in Table or Kanban view with persistent status moves
- create Jobs manually and batch-import up to 10 public Job URLs for review
- connect Gmail with read-only OAuth, sync recent application emails, classify OA/interview/rejection/offer signals, and update Job status automatically

## Architecture

```text
autoapply-agent/
  backend/    FastAPI, SQLAlchemy, PostgreSQL, LLM provider adapters, prompt templates
  frontend/   Next.js, TypeScript, Tailwind
```

Backend boundaries:

- API routes handle HTTP validation.
- Services handle JD analysis, scoring, tailoring, and persistence.
- Alembic migrations own PostgreSQL schema creation and upgrades. FastAPI startup does not mutate schema.
- Job import services isolate source detection, safe HTML fetching, platform parsing, and LLM fallback extraction.
- Gmail services isolate OAuth, token encryption, metadata-only message fetching, email classification, Job matching, and status synchronization.
- Prompt templates live in `backend/app/prompts`.
- `jobs` is the pipeline aggregate for future OA, interview, Gmail, and auto-apply integrations.
- `applications` stores AI-generated application materials associated with a job.
- `job_status_events` keeps an auditable lifecycle history.
- `resume_versions` is an immutable ledger for base uploads, tailoring results, manual edits, and imports.
- `emails` stores Gmail metadata/snippets, classification, processing state, and optional Job links without storing full bodies or attachments.
- `gmail_connections` stores OAuth connection metadata and an encrypted refresh token for manual sync.

## Local Setup

### Quick Start

For the configured local machine, run:

```bash
./start.sh
```

Then open `http://localhost:3000`.

Keep that terminal window open while using the app. Press `Control+C` to stop both services.

Useful commands:

```bash
./status.sh
./stop.sh
```

The startup script creates missing local environments, installs missing dependencies, starts the backend and frontend, and prints log locations if startup fails.
It also runs `alembic upgrade head` before launching the backend.

### GitHub Sync

The project is connected to the configured `origin` GitHub repository. Local secrets, environments, runtime files, and personal candidate profiles are excluded by `.gitignore`.

Run a safe one-time sync:

```bash
./sync-github.sh "Describe the changes"
```

Keep automatic sync running every five minutes while a terminal remains open:

```bash
./sync-github.sh --watch 300
```

The sync script stages changes, blocks common API keys and database credentials, creates a commit, rebases onto the remote branch, and pushes. Press `Control+C` to stop watch mode.

### 1. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Run the Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Set `LLM_PROVIDER`, `LLM_API_KEY`, and `LLM_MODEL` in `backend/.env` for AI resume and cover letter generation. Without a key, the backend still runs local keyword analysis and stores results.

Supported LLM providers:

```text
openai
gemini
groq
deepseek
test (offline CI/test adapter only)
```

Example Gemini configuration:

```env
LLM_PROVIDER=gemini
LLM_API_KEY=
LLM_MODEL=gemini-2.5-flash-lite
```

OpenAI-compatible providers use the same adapter:

```env
# Groq
LLM_PROVIDER=groq
LLM_API_KEY=
LLM_MODEL=openai/gpt-oss-20b

# DeepSeek
LLM_PROVIDER=deepseek
LLM_API_KEY=
LLM_MODEL=deepseek-v4-flash

# OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=
LLM_MODEL=gpt-4.1-mini
```

Use `LLM_BASE_URL` only when overriding a provider endpoint or connecting to a self-hosted OpenAI-compatible service.

Optional Gmail sync configuration:

```env
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REDIRECT_URI=http://127.0.0.1:8000/api/v1/gmail/oauth/callback
GMAIL_TOKEN_ENCRYPTION_KEY=
```

Generate a local encryption key:

```bash
cd backend
.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Gmail uses only `https://www.googleapis.com/auth/gmail.readonly`. The app does not request send, modify, or delete permissions.

### 3. Run the Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

### Test Environment Files

Safe test templates are provided and contain only dummy credentials:

```text
backend/.env.test.example
frontend/.env.test.example
```

These templates are intended for CI or isolated local test databases. Do not copy real Supabase, Gmail, or LLM secrets into them.

## Database Migrations

Run schema upgrades before starting the backend:

```bash
cd backend
.venv/bin/python -m alembic upgrade head
```

Useful migration commands:

```bash
cd backend
.venv/bin/python -m alembic current
.venv/bin/python -m alembic check
.venv/bin/python -m alembic revision --autogenerate -m "describe schema change"
.venv/bin/python -m alembic downgrade -1
```

For an existing pre-Alembic database whose tables already match the MVP schema, stamp the baseline once before upgrading:

```bash
cd backend
.venv/bin/python -m alembic stamp 20260601_01
.venv/bin/python -m alembic upgrade head
```

Run the repeatable legacy reconciliation command after adopting Alembic:

```bash
cd backend
.venv/bin/python -m app.cli.backfill_legacy
```

The backfill preserves old rows and fills missing `applications -> jobs`, `resumes -> base resume_versions`, and tailored-result links. It is safe to run repeatedly and prints a summary.

Supabase/Supavisor notes:

- Keep the `postgresql+asyncpg://` URL in `backend/.env`.
- Prefer the transaction pooler URL for IPv4-only networks.
- The app and Alembic disable statement caching and use unique prepared statement names for pooler compatibility.

## Tests

Use these commands for local verification. The CI workflow runs the same backend and frontend checks with an isolated PostgreSQL service.

## CI

GitHub Actions runs `.github/workflows/ci.yml` on pushes and pull requests to `main`.

CI backend checks:

- starts a PostgreSQL 16 service
- installs backend dependencies
- runs `python -m alembic upgrade head`
- verifies latest migration downgrade and re-upgrade
- runs `python -m unittest discover -s tests -v`
- runs `python -m compileall -q app`

CI frontend checks:

- installs frontend dependencies with `npm ci`
- runs `npm run build`

CI uses dummy Gmail and LLM environment variables. Gmail tests are mocked/service-level and do not require a real OAuth client.

Run unit tests:

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v
```

Run PostgreSQL-backed integration tests against an isolated local database:

```bash
cd backend
TEST_DATABASE_URL=postgresql+asyncpg://autoapply:autoapply@127.0.0.1:5432/autoapply_test \
  .venv/bin/python -m unittest discover -s tests -v
```

## API

Primary MVP endpoint:

```text
POST /api/v1/mvp/run
```

Multipart form fields:

- `candidate_profile`: TXT, MD, PDF, or DOCX
- `resume`: TXT, MD, PDF, or DOCX
- `job_description`: full job description text
- `company`, `title`, `job_url`, `source`, `job_type`, `location`, `salary`, `deadline`, `notes`: optional job metadata

Job URL import:

```text
POST /api/v1/job-import/url
POST /api/v1/jobs/batch-import
```

JSON body:

```json
{
  "url": "https://boards.greenhouse.io/example/jobs/123"
}
```

The import response contains editable company, title, location, salary, deadline, description, per-field confidence values, warnings, and the original URL. Importing never triggers generation or saves a Job. Review the populated form and click Generate explicitly.

Batch import processes up to 10 URLs sequentially and returns a success or user-readable failure for each URL. It only creates previews. The Jobs page requires the user to select and confirm previews before saving them through `POST /api/v1/jobs`.

Supported URL sources:

- Greenhouse, Lever, and Ashby: dedicated parsers
- Workday: best-effort generic parsing
- Simplify and other public company career pages: generic parsing with LLM fallback when needed
- LinkedIn and Handshake: detected but intentionally not fetched when login or anti-bot restrictions are expected; paste the JD manually

The importer fetches only one public HTTP(S) page per request, uses a timeout and response-size cap, validates redirect targets, and does not bypass login walls, captchas, or anti-bot protections.

Supporting endpoints:

```text
POST  /api/v1/candidate-profiles
GET   /api/v1/candidate-profiles
POST  /api/v1/resumes
GET   /api/v1/resumes
GET   /api/v1/applications
GET   /api/v1/applications/{application_id}
PATCH /api/v1/applications/{application_id}/status
PATCH /api/v1/applications/{application_id}/metadata
GET   /api/v1/applications/{application_id}/export/resume
GET   /api/v1/applications/{application_id}/export/cover-letter
POST  /api/v1/jobs
POST  /api/v1/jobs/batch-import
GET   /api/v1/jobs
GET   /api/v1/jobs/{job_id}
PATCH /api/v1/jobs/{job_id}
PATCH /api/v1/jobs/{job_id}/status
DELETE /api/v1/jobs/{job_id}
GET   /api/v1/dashboard
POST  /api/v1/job-import/url
GET   /api/v1/resume-versions
GET   /api/v1/resume-versions/{version_id}
POST  /api/v1/resume-versions
DELETE /api/v1/resume-versions/{version_id}
GET   /api/v1/resume-versions/{version_id}/download?format=txt|md|pdf
GET   /api/v1/jobs/{job_id}/resume-version
GET   /api/v1/gmail/status
GET   /api/v1/gmail/oauth/start
GET   /api/v1/gmail/oauth/callback
POST  /api/v1/gmail/sync
GET   /api/v1/emails
PATCH /api/v1/emails/{email_id}
```

## Resume Version Control

- Uploading a base resume creates a protected `BASE_UPLOAD` version.
- Every tailoring run creates a new immutable `TAILORING_RESULT` version and links it to the generated Job.
- Applications keep the exact `resume_version_id` used for that run.
- `/resumes` lists base and tailored versions with search and filtering.
- `/resumes/{id}` shows content, linked Job, match score, diff summary, and downloads.
- Non-base versions can be deleted. Base versions are protected.
- PDF exports use a simple single-column text layout for ATS compatibility.

## Job Pipeline Workspace

- `/jobs` switches between a sortable Table and a status-grouped Kanban.
- Cards can be dragged between columns or moved with the accessible `Move To` selector.
- Failed status moves roll back and display an error.
- `Add Job` saves a manual role as `SAVED`; company and title are required while JD is optional.
- `Batch Import URLs` shows per-URL previews, warnings, partial failures, retry, selection, and explicit confirmation before saving.
- Quick filters identify High Match, Ready To Apply, Needs Review, Deadline Soon, and Jobs without a linked Resume Version.
- Imported confidence, warnings, and review state are stored in `jobs.ingestion_metadata`.

## Gmail Integration

- `/settings` connects Gmail through Google OAuth.
- Manual sync pulls recent Gmail metadata and snippets from the last 1-90 days, defaulting to 30 days.
- The system classifies `APPLICATION_CONFIRMATION`, `OA_INVITATION`, `OA_REMINDER`, `INTERVIEW_INVITATION`, `INTERVIEW_REMINDER`, `REJECTION`, `OFFER`, `RECRUITER_OUTREACH`, and `OTHER`.
- Matching uses company, title, sender, subject, and snippet text against existing Jobs.
- Matched application confirmations, OA invitations, interview invitations, rejections, and offers update the linked Job status and write `job_status_events` with source `gmail_sync`.
- `/emails` lets the user search, filter, reclassify, link, unlink, and rematch emails manually.
- Dashboard now includes Pending OA, Upcoming Interviews, New Recruiter Messages, Unmatched Emails, Recent Rejections, and Recent Offers.
- The app stores message metadata and a short snippet only. It does not store full email bodies, attachments, passwords, or send permissions.

Known Gmail limitations:

- Sync is manual; there is no realtime Gmail watch yet.
- OAuth requires a Google Cloud OAuth client. Public deployment may require Google app verification for the restricted Gmail scope.
- Classification and matching are deterministic heuristics for now. Low-confidence or unmatched emails remain user-reviewable.

Manual Gmail QA:

```text
docs/GMAIL_QA_CHECKLIST.md
```

OAuth troubleshooting:

- `Gmail OAuth is not configured`: confirm `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REDIRECT_URI`, and `GMAIL_TOKEN_ENCRYPTION_KEY` are set in `backend/.env`.
- `Invalid Gmail OAuth state`: restart the connection from `/settings`; this protects against stale or forged callbacks.
- Google redirect mismatch: ensure Google Cloud Console uses exactly `http://127.0.0.1:8000/api/v1/gmail/oauth/callback`.
- Missing refresh token: reconnect Gmail and approve offline access on the consent screen.
- Revoked access: remove the local connection row or reconnect from `/settings`.
- Empty `/emails`: confirm Gmail is connected, run `Sync Gmail`, and ensure the Gmail account has recent application-related messages.

## Next Steps

1. Add CI for migration, integration tests, and frontend build.
2. Add Gmail incremental sync cursors and optional Google Pub/Sub watch after manual sync proves stable.
3. Add optional manual resume version editing without overwriting immutable snapshots.
4. Add library rename, delete, and deduplication controls.
5. Design dedicated OA and Interview tracking modules around `job_id` and `emails`.

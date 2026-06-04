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
- Prompt templates live in `backend/app/prompts`.
- `jobs` is the pipeline aggregate for future OA, interview, Gmail, and auto-apply integrations.
- `applications` stores AI-generated application materials associated with a job.
- `job_status_events` keeps an auditable lifecycle history.
- `resume_versions` is an immutable ledger for base uploads, tailoring results, manual edits, and imports.

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

### 3. Run the Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

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
```

JSON body:

```json
{
  "url": "https://boards.greenhouse.io/example/jobs/123"
}
```

The import response contains editable company, title, location, salary, deadline, description, per-field confidence values, warnings, and the original URL. Importing never triggers generation or saves a Job. Review the populated form and click Generate explicitly.

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
```

## Resume Version Control

- Uploading a base resume creates a protected `BASE_UPLOAD` version.
- Every tailoring run creates a new immutable `TAILORING_RESULT` version and links it to the generated Job.
- Applications keep the exact `resume_version_id` used for that run.
- `/resumes` lists base and tailored versions with search and filtering.
- `/resumes/{id}` shows content, linked Job, match score, diff summary, and downloads.
- Non-base versions can be deleted. Base versions are protected.
- PDF exports use a simple single-column text layout for ATS compatibility.

## Next Steps

1. Capture a clean Git baseline and add CI for migration plus integration tests.
2. Add optional manual resume version editing without overwriting immutable snapshots.
3. Add library rename, delete, and deduplication controls.
4. Design Gmail, OA, interview, and ATS auto-apply integrations around `job_id`.

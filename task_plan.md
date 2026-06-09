# Job Pipeline Workspace Plan

## Goal

Upgrade Jobs into a persistent pipeline workspace with Table/Kanban views, stable status movement, manual Job creation, batch URL import previews, and quick filters.

## Current Phase

Phase 4

## Phases

### Phase 1: Domain And API Foundation
- [x] Audit current Jobs, status, import, and Dashboard flows.
- [x] Add ingestion metadata migration and model fields.
- [x] Add batch import API and richer Job summaries.
- **Status:** completed

### Phase 2: Jobs Workspace UI
- [x] Add Table/Kanban switch and status movement.
- [x] Add manual Job create dialog.
- [x] Add batch import preview/confirmation dialog.
- [x] Add quick filters and explicit loading/error/empty states.
- **Status:** completed

### Phase 3: Tests And Verification
- [x] Add API and grouping tests.
- [x] Run Alembic, backend tests, compileall, and frontend build.
- [x] Browser-smoke Table/Kanban, manual create, batch partial success, and persistence.
- **Status:** completed

### Phase 4: Documentation
- [x] Update README, PROJECT_STATUS.md, findings.md, and progress.md.
- **Status:** completed

## Decisions

- Reuse `PATCH /jobs/{id}/status`; native drag/drop is paired with a Move To select for reliability and accessibility.
- Batch import only previews parsed URLs. Users explicitly select and save previews through existing `POST /jobs`.
- Persist generic `ingestion_metadata` JSONB rather than platform-specific confidence columns.
- Quick filters are client-side over the loaded Job collection; server filtering remains available for search/sort/status/score.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| TypeScript could not infer complete status keys from `Object.fromEntries` | 1 | Replaced it with a typed status reduce. |
| Sandbox blocked local PostgreSQL socket | 1 | Re-ran migration and integration verification with approved local-network access. |
| Port 8000 still served the pre-change backend during first browser pass | 1 | Restarted the backend and reverified new summary flags plus linked Resume Versions. |

# uniflow-tasks-service

**Status: Archived / superseded.** Do not deploy or extend this service.

Tasks now live in `uniflow-academic-service` (package `com.uniflow.academic.task`).
Keeping tasks next to courses and enrollments removed a network hop and a separate
deployment, so this standalone Python service became redundant.

## What this repo contained

- A FastAPI REST API for tasks (hexagonal layout: `src/domain`, `src/application`, `src/infrastructure`).
- DynamoDB persistence (`scripts/create_table.py` creates the table).
- An EventBridge-based reminder scheduler (with a no-op implementation for local runs).
- A `Dockerfile` and `docker-compose.yml`.

## History

This `main` branch holds the Python/FastAPI rewrite. The original Go implementation
(MongoDB, `cmd/` and `internal/` layout) is preserved on the `go-old-version` branch.

## Where to go

Central repository: https://github.com/UniFlowProject/uniflow

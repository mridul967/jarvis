# Anywhere Door

An executable baseline for SIH 26137: compare classical PSO and
quantum-behaved PSO (QPSO) on Solomon-style vehicle-routing problems with time
windows (VRPTW).

## Architecture

This is a modular monolith with two deployable processes in one repository:

```text
Browser -> Next.js App Router UI -> FastAPI /api/v1
                                      |-> api/routes (HTTP only)
                                      |-> datasets -> artifacts + SQLite metadata
                                      |-> vrptw service + decoder
                                      |-> optimizers (PSO / QPSO)
                                      `-> runs repository -> SQLite
```

The optimizer uses a random-keys representation: each particle is a continuous
vector, sorting its values produces a customer permutation, and a deterministic
splitter constructs capacity- and time-window-feasible routes. This lets the
supplied continuous PSO/QPSO equations solve a discrete routing problem without
claiming a quantum hardware advantage.

## Run locally

```bash
uv sync
uv run uvicorn backend.main:app --reload
```

In a second terminal:

```bash
cd frontend
bun install
bun run dev
```

Open http://localhost:3000. API documentation is at
http://localhost:8000/docs.

## Verify

```bash
uv run pytest
cd frontend && bun run lint && bun run build
```

## Import benchmark datasets

Download and extract the Solomon and Gehring-Homberger archives as described in
[data/inbox/README.md](data/inbox/README.md). Then run:

```bash
uv run python -m backend.tools.import_datasets data/inbox/Solomon_Instances --family solomon
uv run python -m backend.tools.import_datasets data/inbox/Gehring_Homberger_Instances --family homberger
```

## Current scope

- Included: strict Solomon text/CSV/canonical JSON import, immutable dataset
  versions, embedded demo instance, PSO, QPSO, deterministic feasibility
  evaluation, run persistence, comparison UI.
- Deferred: ACO/QACO, dynamic traffic ingestion, Supabase mirroring,
  background workers, authentication, QAOA/RL, maps. Add these only after the
  baseline benchmark is reproducible.

## API

- `GET /health`
- `GET /api/v1/instances/sample`
- `POST /api/v1/datasets/validate`
- `POST /api/v1/datasets`
- `GET /api/v1/datasets`
- `GET /api/v1/datasets/{version_id}`
- `POST /api/v1/solve`
- `GET /api/v1/runs`

Example request:

```json
{"algorithm":"qpso","population_size":30,"iterations":80,"seed":42}
```

## Backend structure

```text
backend/
  main.py             application factory, middleware, lifecycle, health
  api/                versioned routers and Pydantic request/response schemas
  core/               environment settings and SQLite connection lifecycle
  datasets/           strict importers, immutable artifacts, version metadata
  optimizers/         algorithm mechanics without HTTP or persistence imports
  vrptw/              Solomon parsing, route decoding, evaluation, solve service
  runs/               experiment persistence repository
tests/                 pure-domain and HTTP contract tests
```

Backend checks:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

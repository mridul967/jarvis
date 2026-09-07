# Jarvis task runner — `just dev` starts the FastAPI backend and Next.js frontend concurrently.

set dotenv-load := true

# Show recipe list when run with no arguments
default:
    @just --list

# ─── setup & dependencies ───────────────────────────────────────────────────

# One-time / fresh setup for both Python backend and Next.js frontend
setup: setup-python setup-frontend

# Sync Python environment via uv
setup-python:
    uv sync

# Install frontend dependencies using bun
setup-frontend:
    cd frontend && bun install

# Upgrade locked dependencies across Python and frontend
update-deps:
    uv lock --upgrade
    uv sync
    cd frontend && bun update

# ─── database & artifacts ───────────────────────────────────────────────────

# Initialize SQLite database tables
db-init:
    uv run python -c "from backend.app.core.database import initialize_database; initialize_database(); print('SQLite database initialized.')"

# Reset SQLite database (removes local db and re-initializes tables)
db-reset:
    uv run python -c "from backend.core.config import settings; import os; os.remove(settings.database_path) if os.path.exists(settings.database_path) else None; print('Removed', settings.database_path)"
    @just db-init

# Clean temporary Python, build, and test caches
clean:
    rm -rf frontend/.next
    rm -rf .pytest_cache .ruff_cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @echo "Cleaned build and cache artifacts."

# ─── run ────────────────────────────────────────────────────────────────────

# Run backend (:8000) and frontend (:3000) concurrently — Ctrl-C stops both cleanly
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "▶ backend  → http://localhost:8000  (API docs at http://localhost:8000/docs)"
    echo "▶ frontend → http://localhost:3000  (Interactive simulation & UI)"
    trap 'kill 0' EXIT
    uv run uvicorn backend.main:app --reload --port 8000 &
    ( cd frontend && bun run dev ) &
    wait

# Backend only — FastAPI on http://localhost:8000
backend:
    uv run uvicorn backend.main:app --reload --port 8000

# Frontend only — Next.js with Bun on http://localhost:3000
frontend:
    cd frontend && bun run dev

# Aliases for backwards compatibility
backend-dev: backend
frontend-dev: frontend

# ─── research & benchmarks ──────────────────────────────────────────────────

# Run GAT-QPSO quantum routing benchmark on XML dataset
gat-qpso DATA="research/X-n1001-k43.xml":
    uv run python research/gat_qpso_grq.py "{{DATA}}"

# Run unified OSMnx + GAT graph edge pruning and QPSO solver
unified:
    uv run python research/unified.py

# Launch Jupyter Lab in the research directory
research:
    uv run jupyter lab research

# Alias for research notebook runner
jupyter: research

# ─── lint, test & verification ──────────────────────────────────────────────

# Lint backend with Ruff and frontend with ESLint
lint:
    uv run ruff check .
    cd frontend && bun run lint

# Auto-format Python with Ruff and frontend with Prettier
format:
    uv run ruff format .
    cd frontend && bun run format

# Typecheck frontend with TypeScript
typecheck:
    cd frontend && bun run typecheck

# Run backend pytest suite
test-backend:
    uv run pytest tests/

# Typecheck and build frontend production bundle
test-frontend:
    cd frontend && bun run typecheck
    cd frontend && bun run build

# Run all verification tests across backend and frontend
test: test-backend test-frontend

# Probe running backend API health check endpoint
smoke:
    @curl --fail --silent http://localhost:8000/health | grep -q '"status":"ok"' && echo "✔ Backend API is healthy (http://localhost:8000/health)" || (echo "✖ Backend health check failed" && exit 1)

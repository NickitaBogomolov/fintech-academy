.PHONY: install backend web test lint up

install:
	cd backend && uv venv -p 3.12 && uv pip install -e ".[analysis,dev]"
	cd backend/toolchain/solc && npm ci
	cd web && npm ci

backend:
	cd backend && .venv/bin/uvicorn dfa_studio.api:app --reload --port 8000

web:
	cd web && npm run dev

test:
	cd backend && .venv/bin/pytest -q
	cd web && npm run typecheck

lint:
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .

up:
	docker compose up --build

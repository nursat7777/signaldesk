PYTHON ?= python3
VENV_PYTHON := .venv/bin/python

.PHONY: setup migrate backend frontend-dev frontend build test test-backend test-frontend verify demo
setup:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install -r requirements.txt
	cd frontend && npm ci
migrate:
	$(VENV_PYTHON) -m alembic upgrade head
backend:
	$(VENV_PYTHON) -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8000
frontend-dev:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
demo:
	cd frontend && VITE_SERVICE_MODE=mock npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
frontend: build
build:
	cd frontend && npm run build
test-backend:
	$(VENV_PYTHON) -m pytest -q
test-frontend:
	cd frontend && npm test -- --maxWorkers=1
test: test-backend test-frontend
verify: test build

test-integration:
	$(VENV_PYTHON) -m pytest integration -q

e2e:
	npm run e2e

lint:
	$(VENV_PYTHON) -m ruff check --select E9,F63,F7,F82 backend scripts tests integration
	cd frontend && npx tsc -b

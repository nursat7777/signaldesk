.PHONY: backend test frontend migrate
backend:
	.venv/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8000
test:
	.venv/bin/python -m pytest -q
frontend:
	cd frontend && npm run build

migrate:
	.venv/bin/python -m alembic upgrade head

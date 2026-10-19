.PHONY: backend test frontend
backend:
	.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
test:
	.venv/bin/python -m pytest -q
frontend:
	cd frontend && npm run build

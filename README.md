# SignalDesk

An advertising analytics workspace for one agency: administrator, assigned marketers and client viewers; manually entered daily campaign results; date-filtered reports and channel comparisons; dark English/Russian interface. Each client uses KZT, USD or EUR. Inspired by Cometly's product category; this MVP does not perform event attribution or connect advertising platforms.

React/TypeScript/Vite frontend, FastAPI REST API, SQLAlchemy ORM, Alembic migrations and persistent SQLite. Money crosses the API as exact decimal strings and is stored as integer minor units. Backend enforces current role/assignment permissions, unique campaign/day and optimistic edit versions.

## Run locally

Verified local runtime: Python 3.12.14 and Node.js 24.19.0 with npm. CI is configured to target Node.js 22; that remote CI target has not been executed. Commands below use macOS/Linux and run from the repository root. `make` is optional: its targets contain the exact underlying commands. Install Python/Node before starting.

```bash
make setup
cp .env.example .env
```

Edit root `.env`: set `BOOTSTRAP_ADMIN_EMAIL` to the Google email of the first administrator, and supply `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Use a Google OAuth web application with authorized redirect URI `http://localhost:8000/api/auth/google/callback`. The redirect must match `GOOGLE_REDIRECT_URI` exactly. Keep `FRONTEND_URL` and `ALLOWED_ORIGINS` as `http://localhost:5173` for the default development setup. Enable the relevant Google consent-screen test user if the OAuth application is in testing mode.

The administrator is approved by configuration; other accounts are approved in the application. There is no public signup. Credentials are never committed. Without Google credentials the application displays a setup-required screen; it does not pretend to sign in.

```bash
make migrate
make backend
```

In a second terminal, from the same repository root:

```bash
make frontend-dev
```

Open `http://localhost:5173`. Vite forwards `/api` requests to `http://127.0.0.1:8000`; sign-in redirects through the configured localhost callback. Use the exact frontend URL so the trusted Origin matches. `GET http://localhost:8000/api/health` reports the active SQLite repository. The backend uses a factory and requires migrations before startup.

`DATABASE_URL` in root `.env` defaults to `sqlite:///signaldesk.sqlite3`; relative paths resolve from the repository root. Alembic and runtime use this same configuration. An exported environment variable overrides `.env`. The database and secrets are excluded from git. Preserve the file between restarts; apply future migrations with `make migrate`.

For a separate, temporary frontend demonstration without accounts or backend:

```bash
make demo
```

This explicitly selects development-only mockService with a visible demo indicator. It does not persist across refreshes or prove backend/Google authentication. Production builds always use the real API. `VITE_API_BASE` optionally changes the frontend API base; normal local development needs no frontend environment file.

## Verify

```bash
make verify
```

Runs Python contract/API/auth/repository/migration and actual process-restart tests, serial frontend interaction and real HTTP integration tests, then a TypeScript/Vite production build. Frontend HTTP tests automatically create temporary migrated SQLite databases, start isolated uvicorn processes and seed sessions from test-only helpers; the production application has no test login route. No Google credentials are needed for automated tests.

Latest executed `make verify`: **124 Python tests, 35 frontend tests and production build passed**. Preserved logs and independent QA details are under `_docs/evidence/`; setup/delivery changes have a separate follow-up QA record. `.github/workflows/ci.yml` runs the same command on GitHub after publication; no remote CI execution is claimed.

## What was verified and what remains

The five required stages were implemented and independently checked in order: mock frontend → maintained OpenAPI → in-memory backend → migrated SQLite → real HTTP frontend integration. Local git tags preserve checkpoints. Reports, permission failures, edit conflicts and actual backend restart persistence were exercised.

Google provider validation is covered by locally signed token and mocked-provider tests. A real Google consent/login handshake remains unverified because credentials were not supplied. UI interactions ran in jsdom with actual HTTP backend calls; browser visual/responsive/CORS behavior was not verified. No hosted deployment is claimed.

GitHub connection/publication remains blocked: no remote repository URL, pushed commits, published issues or external closures are claimed. `_docs/backlog.json` contains honest local issue staging and independent QA history, not proof of GitHub publication. Delivery is incomplete until authorized GitHub access is connected, the repository/issues are published and reviewed MVP/bug issues are closed externally. Deferred post-MVP issues remain open.

## Documentation

- `_docs/plan.md`: approved scope and post-MVP proposals.
- `chat-brainstorm.md` and its identical `_docs/` copy: actual conversation.
- `_docs/process.md`, `_docs/backlog.json`: issue lifecycle and recorded gates.
- `_docs/architecture.md`, `_docs/design-system.md`, `_docs/testing-guidelines.md`.
- `_docs/openapi.yml`: maintained REST contract; tested against runtime operations and responses.
- `_docs/team/`: PM, engineer, QA and design responsibilities.
- `_docs/evidence/`: executed checks, raw logs and limitations.

No production hosting or license commitment has been selected.

# SignalDesk

Advertising analytics workspace: React/TypeScript/Vite, FastAPI, SQLAlchemy and
Alembic. PostgreSQL production configuration; one application container serves
static frontend and backend. Existing three roles, Google approved-account
sign-in, exact monetary storage and optimistic daily edits are preserved.

See [_docs/deployment.md](_docs/deployment.md) for architecture, local development,
environment variables, safe SQLite import, PostgreSQL migrations, Docker/Compose,
all tests, CI/CD, Render, AWS CloudFormation, costs, rollback and troubleshooting.

## Run

Copy .env.example to .env, set POSTGRES_PASSWORD and Google OAuth/approved admin:

```sh
docker compose up --build -d --wait
docker compose ps
docker compose logs --tail=100
```

Open http://localhost:8000. Google callback:
http://localhost:8000/api/auth/google/callback. Without credentials a setup
screen is shown. Database volume survives normal down/restarts.

## Actual verification — 2026-11-03

- 126 Python regression tests passed.
- 35 frontend tests passed before changes; final rerun in evidence.
- 17 Chromium Playwright tests passed against static frontend and real API with
  disposable SQLite compatibility storage.
- CloudFormation cfn-lint and Python lint passed.
- Actual image/Compose and PostgreSQL remain unverified locally; mandatory CI
  gates run them before deployment.
- No hosted deployment, live application Google OAuth handshake or AWS automatic
  deployment is claimed. GitHub sign-in is separate from application sign-in.

Issues #20–#28 track delivery tasks, #29–#45 track Playwright features, and #46–#47
track reproduced mobile accessibility and SPA API routing bugs. Keep unverified
acceptance criteria open. Historical evidence remains in _docs/evidence/.

## Tests

```sh
make setup
make verify
npm ci
npx playwright install chromium
make e2e
# Export disposable TEST_DATABASE_URL for PostgreSQL:
make test-integration
```

Maintained REST contract: _docs/openapi.yml. Advertising integrations/attribution
remain deferred. No production test-login endpoint exists.

## Deployment and observability extension — 2026-11-16

Issues #49–#65 track isolated development/production, immutable manual promotion,
OpenTelemetry, private Prometheus/Grafana/Tempo/Loki, six alert rules and a bounded
read-only incident responder. See [_docs/observability.md](_docs/observability.md)
for setup, metrics, alert testing, credentials, CI, backup, rollback and exact
external deployment blockers. Production no longer deploys automatically from main.

This extension preserves the existing application and PostgreSQL schema.
Real LLM calls remain disabled until separate cost approval. No new live deployment
is claimed. Executed verification is recorded in
[_docs/evidence/observability-2026-11-16.md](_docs/evidence/observability-2026-11-16.md).

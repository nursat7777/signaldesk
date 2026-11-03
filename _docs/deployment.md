# SignalDesk operations — 2026-11-03

## Architecture and actual status

Browser → HTTPS proxy → one FastAPI application container serving static React →
PostgreSQL. Existing SQLAlchemy/Alembic schema, exact integer money, current role
permissions, Google approved accounts and optimistic edits are retained. SQLite
compatibility is preserved for safe import and legacy regression, not production
Compose. No production auth bypass or signup was added.

Executed locally: baseline 124 Python/35 frontend tests; final 126 Python tests;
17 Chromium Playwright scenarios against static frontend + real API with a
disposable SQLite database; cfn-lint and Python lint pass. PostgreSQL/Compose/image
execution remain unverified in this restricted environment. CI requires those
checks. No hosted deployment or real application Google OAuth login is claimed.

## Docker and environment

Python 3.12, Node 22, PostgreSQL 16, Docker Engine/Desktop with Compose v2.
Copy .env.example to .env, set POSTGRES_PASSWORD to a URL-safe random value
(e.g. Python secrets.token_hex(24)); configure approved administrator email,
GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET. Credentials never belong in git.
FRONTEND_URL and ALLOWED_ORIGINS default to http://localhost:8000; callback is
http://localhost:8000/api/auth/google/callback. SESSION_SECONDS defaults to 28800.
APP_BIND defaults to 127.0.0.1 and APP_PORT to 8000. For HTTPS set the canonical
HTTPS origin/callback; secure session cookies follow the HTTPS frontend URL.

```sh
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
docker compose logs --tail=100
docker compose exec app python -m alembic current
curl --fail http://localhost:8000/api/health
```

Open http://localhost:8000. Without OAuth credentials the setup screen is shown.
Startup applies migrations before serving. Health checks execute SELECT 1.
The image runs as UID 10001, excludes test fixtures/secrets, contains no Node
runtime, and uses a read-only filesystem in Compose. PostgreSQL has no published
production port; pgdata volume survives down/restarts. Never use down -v on
valuable data. FORWARDED_ALLOW_IPS must trust only the actual ingress proxy;
the AWS stack's app has no published port and accepts only its internal proxy.

## Host development and tests

`make setup` installs .venv and frontend dependencies. For split development set
FRONTEND_URL/ALLOWED_ORIGINS to http://localhost:5173 and export DATABASE_URL
explicitly. Run make migrate, make backend, and make frontend-dev in separate
terminals. DATABASE_URL accepts postgres://, postgresql:// or explicit
postgresql+psycopg://. Use URL-encoded credentials, never log this variable.
Legacy SQLite requires explicit sqlite:///path configuration when migrating.

```sh
make verify
npm ci
npx playwright install chromium
make e2e
```

Local E2E starts the real backend with built frontend and disposable
.e2e-test.sqlite3. It is not PostgreSQL acceptance. For full-stack acceptance use
a **separate test Compose project and fresh test-only volume**, with POSTGRES_DB
containing test; do not repurpose an initialized production volume:

```sh
docker compose -p signaldesk-test -f compose.yaml -f compose.test.yaml up --build -d --wait
export TEST_DATABASE_URL='postgresql+psycopg://signaldesk:TEST_PASSWORD@127.0.0.1:55432/signaldesk_test'
export E2E_TEST_DATABASE_URL="$TEST_DATABASE_URL"
export E2E_BASE_URL=http://localhost:8000
make test-integration
make e2e
.venv/bin/python -m scripts.restart_check prepare
docker compose -p signaldesk-test restart app
.venv/bin/python -m scripts.restart_check verify
```

Set POSTGRES_DB=signaldesk_test and TEST_PASSWORD in a test-only .env before the
commands. Integration uses isolated schemas in a disposable PostgreSQL database.
E2E fixtures create unique per-test clients/users/campaigns and real server
sessions through a CLI excluded from production. They do not prove Google's live
provider handshake. Artifacts: playwright-report/ and test-results/ (failure
screenshots/video/traces). Issues #29–#45 individually track all 17 features.
Actual backend restart verification is separate from browser reload testing.

## Safe SQLite import and rollback

Stop writers and create a consistent backup via SQLite backup, including WAL
contents; never copy only an actively written main file. Keep originals. Create
a fresh empty PostgreSQL database and apply migrations **before starting an app
with bootstrap enabled**, since bootstrap creates a row and import rejects any
nonempty target:

```sh
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST/NEW_DATABASE'
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m scripts.import_sqlite /absolute/path/backup.sqlite3
```

Importer opens SQLite read-only, locks target tables, copies foreign-key order in
one transaction and compares every column before commit. IDs, dates, integer
money and edit versions survive. Active sessions/pending OAuth states are not
copied; users sign in again. Errors roll back the entire target transaction.
Before new PostgreSQL writes, rollback can switch back to untouched SQLite.
After new writes, reconcile explicitly; never overwrite either database blindly.

## CI/CD and initial hosting

GitHub Actions runs lint/typecheck, existing frontend/backend/contract/persistence
regression, frontend build, cfn-lint, actual Docker Compose build/start, PostgreSQL
integration, Playwright and actual application restart. Failure blocks deployment;
reports/logs are uploaded. Pull requests never receive deployment credentials.

Render deployment is prepared in render.yaml as a Docker service + PostgreSQL
Blueprint. This is **not direct Docker Compose deployment**. Official Render
sources document Dockerfile/image builds and translating Compose into Blueprints:
https://render.com/docs/docker
https://render.com/docs/blueprint-spec
https://render.com/blog/migrate-django-from-heroku

Check current free database expiry/storage limits and account credits before
provisioning. A free expiring database is not an indefinite production guarantee.
No Render account/billing eligibility/service/OAuth credentials are configured.
Do not upgrade plans without approval. Real live URL: **not deployed**.

Native auto-deployment is off so it cannot bypass CI. Configure GitHub environment
production, variable DEPLOY_TARGET=render, LIVE_URL=https://actual-origin, and
secrets RENDER_API_KEY / RENDER_SERVICE_ID. The dependent job requests the exact
verified commit, awaits live status and checks HTTPS frontend/PostgreSQL health.
Protect main with verify and restrict production environment access. Missing
configuration means CD is unconfigured, not completed.

## AWS CloudFormation

infra/cloudformation.yaml defines t3.micro (standard CPU credits), a dedicated
VPC/subnet, only ports 80/443 inbound, Caddy HTTPS, private app/PostgreSQL, encrypted
separate retained data EBS, IMDSv2, SSM without SSH, scoped secret access, seven-day
app logs and 50/80/100% budget emails. No NAT gateway, RDS or load balancer. This is
a single-host coursework stack, not HA; backups and restore drills are required.

Inputs: approved AWS account/region/credits, domain pointed at PublicIp output,
pullable immutable image URI pinned by sha256, owner's budget email, and existing
Secrets Manager JSON containing POSTGRES_PASSWORD (URL-safe >=24 chars),
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, BOOTSTRAP_ADMIN_EMAIL. Only the secret ARN
is passed into IaC; actual credentials are fetched privately on the instance.

```sh
.venv/bin/cfn-lint infra/cloudformation.yaml
aws cloudformation validate-template --template-body file://infra/cloudformation.yaml
```

cfn-lint passed locally. AWS API validation/provisioning needs account access.
After explicit cost approval, create/review a CloudFormation change set before
execution. Point DNS at PublicIp so Caddy can issue certificates. Verify HTTPS,
storage=postgresql, role journeys and persistence before declaring deployment.
Snapshot before instance/schema updates. Roll back app to previous immutable
image via SSM; never automatically downgrade database migrations. AWS automatic
release remains unconfigured without account/OIDC role/registry. Render CD does
not deploy AWS. Live AWS URL: **not deployed**.

Cost sources checked 2026-11-03:
https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html
https://aws.amazon.com/vpc/pricing/
https://aws.amazon.com/secrets-manager/pricing/
https://aws.amazon.com/ec2/pricing/on-demand/

Credits/eligibility are account-specific. IPv4 list price $0.005/hour and Secrets
Manager $0.40/secret/month plus API calls precede applicable benefits. EC2, EBS,
logs, snapshots and egress also count. Alerts are not hard cost caps. No paid
account activation or resource creation occurred. Stack deletion intentionally
retains data EBS; retained volumes keep billing. Inspect/back up data and get
explicit approval before deleting retained infrastructure.

## Troubleshooting

- 503 health: inspect DB/migration logs, do not reset the volume.
- Setup screen: configure actual Google client/callback and approved admin.
- 403 mutation: verify canonical Origin/CSRF; never disable protections.
- 409 metric: reload current version instead of overwriting concurrent data.
- Missing browser: install pinned Playwright; unrun checks are not passes.
- Docker/user namespace unavailable: run on a supported runner; keep acceptance
  open until real Compose and PostgreSQL tests execute.

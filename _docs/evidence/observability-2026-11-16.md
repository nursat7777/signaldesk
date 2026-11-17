# Observability extension verification — 2026-11-16

Scope: Issues #49–#65. Verification performed by the implementation orchestrator;
this is self-verification, not independent QA certification. Source base was
main commit47e935698fa087428348f8a90473c63d23db9272, recovered from authenticated
GitHub ZIP without changing application data.

| Executed check | Observed result |
|---|---|
| `.venv/bin/pytest -q --tb=short` |153 passed,6 warnings,12.75s |
| frontend `npm test -- --maxWorkers=1` |35 passed,8 files |
| frontend `npm run build` |TypeScript and Vite production build passed |
| `npm run e2e` |17 Chromium tests passed,26.7s, real API/static frontend with disposable SQLite |
| Python Ruff E9,F63,F7,F82 |Passed before final documentation |
| Official Prometheus3.5.0 `promtool test rules observability/alert-tests.yaml` |SUCCESS; six firing and six recovery expectations |
| Official Collector0.165.0 `otelcol-contrib validate --config=observability/collector.yaml` |exit0 |

Python coverage includes real HTTP/protobuf OTLP export for all three signals,
W3C trace parent propagation, SQL child spans/error status without parameters,
correlated JSON and OTLP log privacy, five actual successful business operations,
validation failures and authorization denial. Other tests cover webhook token,
payload limits, untrusted annotation rejection, persistent deduplication, recovery
comments without closure, upstream503 retry, default-disabled LLM and durable
call budget, immutable digest receipt validation and environment configuration
isolation. Existing application/auth/contract/SQLite/persistence regression tests
remain enabled.

No Docker daemon or PostgreSQL server is installed in this local workspace.
The new full monitoring Compose runtime, actual PostgreSQL exporter, Grafana UI,
remote notification delivery and cloud deployment are not locally verified.
CI contains actual container/DB/Playwright/observability smoke checks; a committed
workflow is not evidence those new checks passed. No live Render/AWS URLs,
service credentials, approved model budget or credit eligibility is available.
No paid resources or billing changes were made. All new Issues remain open
until their full acceptance criteria and external gates are satisfied.

Historical prior CI success for the previous application Docker/PostgreSQL
extension does not certify the new monitoring overlay. Real Google OAuth
application sign-in remains distinct from test session fixtures and GitHub login.

## Executed GitHub Actions verification

[PR CI run43917634351](https://github.com/nursat7777/signaldesk/actions/runs/43917634351)
for source2b878476c477bd083810084af21a6a5e54fac9dc completed successfully.
It built and started the actual application image, ran PostgreSQL integration,
all17 Chromium journeys and real restart persistence, validated CloudFormation,
started every monitoring service and passed private OTLP/Prometheus/PostgreSQL/
Tempo/Loki/Grafana readiness checks. Actual Alertmanager firing and recovery
notifications reached the authenticated persistent responder. Development deployment
was correctly skipped because the source was a PR, not develop. This certifies
the tested source, not a hosted deployment. Later strengthening changes require
their own green run before merge.

Bug #66 reproduced Playwright1.56.1 rejecting the new ubuntu26.04 runner.
Pinning Ubuntu24.04 restored dependency installation and the full regression.

Live account observations: GitHub environments development and production were
created and restricted respectively to develop and main. Both have no secrets.
The environment settings UI did not expose a required-reviewer control. Render
Google sign-in succeeded; My Workspace has no services, uses Hobby, and shows
credit balance$0.00. AWS console returned Site Unavailable; no account credits
or billing eligibility could be verified. AWS Core was offered but its connection
is not confirmed. No paid resources were provisioned.

## Follow-up regression — 2026-11-17

Recovered source from authenticated branch ZIP at 8cd55fd. Orchestrator
self-verification after the #68 daily-form safety fix and report coverage:

- `make verify`: 153 Python tests passed (6 warnings, 13.05s), 37 frontend
  tests in 9 files passed, TypeScript/Vite production build passed.
- `npm run e2e`: all 17 Chromium journeys passed in 26.8s against the actual
  static frontend/FastAPI and disposable SQLite compatibility database.
- E14 additionally requests the real report endpoint, checks exact persisted
  spend/revenue/ROAS and daily grouping, rejects an inverted range (422),
  permits the assigned viewer and rejects cross-client report access (403).
- CI business metrics verification now runs before the deliberate application
  restart because SDK counters belong to the application process lifetime.
  The subsequent restart database/session persistence check remains mandatory.
- Remote PR run44014999631 exposed a one-second React Testing Library wait
  expiring while a real HTTP save was still in progress. The HTTP workflow
  now waits for the loaded edit control and allows up to five seconds for
  the dialog to close. All persistence/version assertions remain unchanged.
  Re-run frontend suite: 37 passed in 16.13s.

These local results do not certify PostgreSQL or the latest Compose overlay.
The latest GitHub Actions result must be inspected before merge. No hosted
service was created, no secret or billing configuration was changed, and
no unverified issue was closed.

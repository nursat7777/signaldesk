# Architecture

## Stack comparison and decision

| Stack | Strengths | Tradeoff |
|---|---|---|
| React/TypeScript + FastAPI + SQLAlchemy | Explicit REST boundary, Python validation/testing, repository replacement, portable ORM | Two runtimes |
| React + Node/Express + Prisma | Shared TypeScript language, straightforward tooling | Additional schema/validation coordination; SQLite provider differences |
| Django + React | Mature permissions/admin and ORM | More framework surface than this reporting MVP needs |

Choose React/TypeScript/Vite and FastAPI/SQLAlchemy/Alembic/SQLite for a clear teaching boundary and testable in-memory-to-SQLite progression. ORM portability means business logic avoids SQLite-specific SQL; switching DBMS still requires configuration and migrations, not a promise of zero work.

## Layers

Frontend pages/components call a typed service interface. Iteration 1 provides mockService. Iteration 5 replaces it with the REST adapter without duplicating calculations or permissions in UI. FastAPI routes validate requests and resolve sessions; application services enforce current role, assignment and business rules; repository interfaces hide memory or ORM persistence. Server aggregates base metrics and derives ratios consistently.

## Domain and invariants

Users have approved normalized email, Google subject when linked, role, enabled status, and optional client ID. Client viewers belong to one client. Client stores name, currency (KZT/USD/EUR) and archive state. Assignment links marketers and clients. Campaign belongs to client and one fixed channel (Google Ads, Meta Ads, TikTok Ads, Other). DailyMetric has unique campaign/date, spend, impressions, clicks, leads, sales, revenue, edit version and timestamps. Sessions have opaque server-side identifiers, expiry and user association.

Amounts use integer minor units in storage and fixed decimal strings at API boundaries; never floating point currency. Counts are nonnegative integers. Use Asia/Almaty calendar dates, reject future entries, require all six metrics and allow explicit zero. No unsupported sales/leads or clicks/impressions inequality. Missing day remains missing. Currency is immutable after financial data. Archive retains history. Updating an existing metric requires its version; conflicting changes return 409 instead of silent overwrite. Uniqueness is enforced by both business handling and a database constraint.

## Authorization and Google OAuth

Bootstrap administrator from environment allowlist. No public signup. Configure Google OAuth client ID, secret and redirect URI outside source control. Authorization Code flow uses one-time state, nonce, verified token signature/issuer/audience/expiry, and verified email; link only approved enabled users. Session cookie is HttpOnly, SameSite=Lax, Secure in HTTPS production. Rotate session at sign-in, expire/revoke sessions, validate origin/CSRF for mutations and constrain redirect targets. Recheck enabled state and assignments on every request. No production mock-auth endpoint. Test identities are supplied through isolated test dependencies, never browser-accessible production bypasses. Missing OAuth configuration must produce a truthful setup-needed state.

Administrator manages clients/users/assignments and all campaigns. Marketers can create/update campaigns and daily metrics only for assigned clients. Client viewers read their own reports. IDs in URLs never grant access. Unauthenticated calls return 401; authenticated forbidden operations return 403 (or consistent 404 for hidden resources). Audit-sensitive session and identity fields are never returned.

## Reporting

Inclusive date ranges default to the latest 30 Almaty calendar days. Group by client/channel/day. Compute CTR = clicks/impressions × 100, CPC = spend/clicks, CPL = spend/leads, ROAS = revenue/spend from summed base metrics. Zero denominator yields null/unavailable. Never sum money across different currencies. Empty data has explicit empty-state wording.

## Operational boundaries

SQLite file path is configurable and excluded from git. Alembic owns schema changes. Backend validates configuration on startup and health reports actual service availability. Local development uses constrained CORS origins; production serves under one origin or configured proxy. REST error bodies and operations become exact in iteration 2, after frontend service needs are demonstrated.

## Reference and runtime decisions

The orchestrator checked official FastAPI, SQLAlchemy, Prisma SQLite and Django documentation during stack selection. Hosted Sites runtime does not support this assignment's exact Python/SQLite workflow; use a local repository implementation and reproducible setup. No hosted deployment is claimed. Browser/visual QA and live OAuth constraints are recorded in testing-guidelines.md.

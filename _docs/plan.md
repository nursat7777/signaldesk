# Agency advertising analytics — specification for approval

Status: Approved by the user on 2026-10-19: “да давай сделать и не забудь зайти в мой гит”. Confirmed and proposed completion details below are accepted scope. Working name: SignalDesk. Implementation and GitHub actions require genuine evidence.

## Concept and problem
A full-stack web application for one advertising agency to maintain daily advertising performance for several clients, compare channels, and share interactive reports. Inspired by the user's reference to Cometly. This MVP reports manually entered totals; it does not track visitors or perform event-level attribution.

## Confirmed MVP decisions
- One agency, multiple clients.
- Three roles: administrator, marketer, client viewer.
- Administrator controls approved email addresses, roles, clients and marketer assignments.
- Marketers access only assigned clients. Multiple marketers may be assigned to one client.
- Client viewers access only their own reports; no metric editing.
- Google sign-in, restricted to administrator-approved email addresses.
- Each campaign belongs to one client and one channel: Google Ads, Meta Ads, TikTok Ads or Other.
- Daily manual entry: spend, impressions, clicks, leads, sales and revenue.
- Exactly one record per campaign per date; repeated entry opens the existing record for editing.
- Interactive date-filtered reports, charts, campaign metrics and channel comparisons.
- Per-client currency with no automatic conversion or summation across different currencies.
- Dark graphite interface with contrasting charts; English/Russian switching.

## Proposed completion details — included in the approval request
These are engineering proposals, not answers attributed to the user.
- Administrator can manage all client/campaign data; assigned marketers create and edit campaigns and daily records. Client accounts are associated with one client in this version.
- Campaigns have name and active/archived status. Archiving retains historical reporting data. Client records with history are archived rather than destructively deleted.
- Currency choices initially KZT, USD and EUR. Currency cannot change after financial records exist. All reporting dates use Asia/Almaty calendar dates.
- Monetary values are nonnegative fixed-precision amounts; counts are nonnegative integers. Future daily entries are rejected. Do not impose clicks <= impressions or sales <= leads without agreement: data definitions can differ.
- All six daily metrics are required, with explicit zero allowed. Missing records mean missing data, not confirmed zero activity.
- Concurrent edits must not silently overwrite newer data: reject a stale update and ask the user to reload.
- No public signup. Bootstrap the first administrator through configuration; configure Google OAuth credentials outside source control. Real Google login requires an OAuth application and redirect configuration. Test-only identities must never bypass authentication in production.
- Administrators can revoke accounts and assignments; every API request rechecks permissions.
- Reports default to the latest 30 calendar days, allow inclusive custom date ranges, and show empty/loading/error states. Shared currency totals are allowed only within a currency group.

## Metrics
- CTR = sum(clicks) / sum(impressions) × 100%.
- CPC = sum(spend) / sum(clicks).
- CPL = sum(spend) / sum(leads).
- ROAS = sum(revenue) / sum(spend), displayed as a multiple.
- A zero denominator produces an unavailable indicator, never Infinity or a misleading zero. Compute ratios from summed base metrics rather than averaging daily ratios.

## Data relationships
- User: approved email, Google identity, role, enabled state, optional client association.
- Client: name, currency, archived state.
- Assignment: many-to-many relationship between marketers and clients.
- Campaign: client, fixed channel, name, archived state.
- DailyMetric: campaign, date, six metrics, edit version, timestamps; unique campaign/date.
- Session: authenticated user and expiry, implementation to be selected during architecture.

## Principal journeys
1. Administrator signs in, creates a client, approves a marketer and client viewer, assigns marketer access.
2. Marketer signs in, selects an assigned client, creates a campaign and enters daily results.
3. Marketer revisits the same campaign/date and edits the existing record; duplicate records cannot be created.
4. Administrator or marketer selects dates, reviews trends and compares channels for an accessible client.
5. Client viewer signs in and sees only their own interactive reports.
6. An unauthorized account or a direct API request for another client's data is denied.
7. After a backend restart, authorized users see the same persisted data.

## MVP boundaries
Includes the above workflows, responsive dark UI, RU/EN text, permission enforcement, SQLite persistence, an ORM, REST API, OpenAPI and automated tests. Google OAuth is a real integration requirement, not a simulated completed feature.

## Post-MVP — deferred proposals
- Advertising platform API integrations and CSV import/export.
- Tracking pixels, event ingestion and multi-touch attribution.
- PDF reports, scheduled email reports and notifications.
- Multiple agencies, subscriptions and currency conversion.
- Budgets, forecasting and AI recommendations.
These are deferred suggestions; they were not individually selected by the user.

## Combined development workflow
Read sources:
1. https://aishippingblog.com/p/ai-native-development-specifications
2. https://aishippingblog.com/p/build-and-ship-a-full-stack-app-with

Use the first article's specification, GitHub backlog and PM/engineer/independent-QA lifecycle throughout the second article's incremental service replacement. The assignment explicitly overrides the second article's integration-before-database ordering: preserve the following five iterations, each with runnable evidence and its own verified changes:
1. Frontend with centralized mockService and functional principal journeys.
2. Derive and validate _docs/openapi.yml from the frontend service operations.
3. REST backend with in-memory repository; test business rules and authorization.
4. ORM, migrations and SQLite repository; verify persistence across process restart.
5. Replace mockService with real API client; test full user journeys.

Chosen implementation: React/TypeScript/Vite + FastAPI + SQLAlchemy/Alembic + SQLite; comparison and architecture are recorded in architecture.md.

## Documentation and GitHub
Required: AGENTS.md, CLAUDE.md, README.md; _docs/plan.md, process.md, architecture.md, design-system.md, testing-guidelines.md, task-template.md, openapi.yml, chat-brainstorm.md; _docs/team/{pm,software-engineer,qa-engineer,design-agent}.md. Keep root chat-brainstorm.md as requested and an identical _docs copy.

GitHub Issues become the canonical backlog, labeled mvp, post-mvp or user-test-bug. Each issue contains Goal, Description, Acceptance criteria, Out of scope and Constraints. PM grooms one issue, engineer implements and commits without closing it, independent QA runs checks and reports evidence; closure follows PASS only. Bug fixes follow the same lifecycle and regression testing. Actual external actions and test outcomes must be recorded without fabrication.

## Acceptance and verification
- Verify each role in the running UI and direct API calls, including unassigned clients.
- Unit-test metric calculations, zero denominators and date/number validation.
- API integration-test authentication, authorization, daily uniqueness and stale edits.
- Exercise migrations and persistence after an actual backend process restart.
- Frontend interaction-test forms, duplicate editing, filters, both languages and error states.
- E2E-test administrator setup, marketer daily entry and client report visibility.
- Validate maintained OpenAPI contract against implemented endpoints.
- Run full regression suite; record commands, results and limitations.
- Completion requires pushed documentation/code and all mvp and user-test-bug issues closed after QA approval. Deferred post-mvp issues remain open.

## Approval gate
Final specification approved with the exact user message “да давай сделать и не забудь зайти в мой гит”. This authorizes implementation and GitHub connection/setup within the approved scope.

# M13 independent full-stack regression — iteration5 gate

Date2026-10-19. Independent QA, not application author. Local staged M13; no external issue URL. M12 commit0721fb6 followed by M12 QA41019f2 and frozen test-only M13 changes.

Verdict: PASS for integrated local application/testing gate. All five implementation iterations verified locally; delivery/configuration/GitHub and live Google limitations remain separately tracked.

Final executed checks and preserved raw logs:
- frontend `npm test -- --maxWorkers=1`: exit0,8files/35passed, final-frontend-tests.txt.
- `.venv/bin/python -m pytest tests -q`: exit0,122passed,4known deprecation warnings, final-python-tests.txt.
- frontend `npm run build`: exit0,TypeScript+Vite6.4.4,1586modules, final-build.txt.

Independent qa.http-integration.test.tsx uses a fresh migrated SQLite file, real uvicorn subprocess, production REST adapter and rendered AuthGate/App. Administrator creates campaign through UI; marketer enters six daily fields through UI; viewer sees persisted exact monetary report and only own client, no write/admin actions, RU switch works. HTTP isolation rejects other-client403, duplicate/unversioned save409, immediately revoked marketer assignments403, anonymous real backend shows honest missing-Google setup. Request evidence includes actual metric PUT. No mock backend responses supplied.

Three engineer realHTTP cases additionally execute admin client/account/assignment forms, marketer create/edit one record with version2, viewerreport/filter and real logout revocation. Independent reviewer reran these in final35-test suite. Earlier observed admincase failure was an immediate test query during legitimate loading refresh; explicit awaited UI readiness and explicit client selection corrected harness, with no production code change or fabricated bug.

HTTP fixture test-only transport supplies seeded per-role session cookie and Origin via NodeHTTP and records only method/path/role. Session bootstrap runs isolated tests.support_seed CLI; production app does not import it or expose any login bypass. Test transport restriction permits only its own loopback server. This is realHTTP/jsdom integration, not actual browser E2E or Google consent. Backend final122includes independent process-restart/session/data/report persistence and contract validation.

Remaining limitations: browser visual/responsive/CORS behavior and live Google OAuth account consent were not executed; real Google credentials required. No hosted deployment or external GitHub repository/issue closure verified. Setup/docs changes and any subsequently reproduced configuration bug require their own check. Raw logs contain no test tokens/cookies.

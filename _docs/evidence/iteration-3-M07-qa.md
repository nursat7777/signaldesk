# M07 independent auth scaffold QA

Date:2026-10-19. Reviewer: separate QA agent. Implementation commit e41c3af. Local staged M07; no GitHub issue URL. Backend contains auth/memory scaffold only, not domain CRUD.

Verdict: PASS for M07 local acceptance and release to M08.

Executed `.venv/bin/python -m pytest tests -q`: exit0,41 passed,4 dependency/validator deprecation warnings. This includes17 contract examples,11 engineer auth tests and13 independent tests/test_qa_auth.py cases.

Independent HTTP checks: public health and actual memory marker; no-session401; unconfigured OAuth503/status false; opaque hashed session lookup and CSRF exposure; exact safe current-user response fields; immediate disabled-user403; unknown/expired session401 with expired cleanup; mutation rejected for missing/wrong origin or token; valid logout204 revokes session; browser-bound OAuth transaction rejects other browser without consuming valid transaction; successful injected-provider callback rotates old session, sets secure HttpOnly SameSite cookies under HTTPS, fixed redirect, links subject, consumes state and rejects replay.

Independent production GoogleProvider verification: generated local RSA-signed ID token and mocked only token/certificate HTTP boundaries. A valid signed token reaches expected identity. Wrong nonce/audience/issuer, expired token, unverified email and mismatched signing key are rejected. These cases exercise actual JWT decode/claim validation in production provider rather than replacing identity() itself. Separate callback behavior tests replace provider to isolate session/state policy.

No browser-accessible login bypass route exists; engineer test /api/test-login404 passed. Inspected backend auth/app/core against maintained OpenAPI auth semantics. M07 does not implement remaining routes; those are explicitly later issues.

Limitations: no actual Google network sign-in, live account consent, browser, deployment, SQLite or persistence checked. Test fixtures create sessions inside repository and mock provider HTTP responses only in test process; production has no fixture endpoint. Deprecation warnings recorded but no runtime failures. No GitHub closure claimed.

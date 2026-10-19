# Iteration 3 — M07 engineer handoff

Implemented only auth/session and memory foundation. M08 domain CRUD and M09 reporting remain unimplemented.

- `backend/core.py`: configuration, opaque-token hashing, lock-backed in-memory repository, approved bootstrap administrator without fabricated Google identity.
- `backend/auth.py`: real Google authorization-code provider; RS256 token signature, issuer, audience, expiry, nonce, verified-email checks; live role/enabled session resolution; mutation Origin/CSRF guard.
- `backend/app.py`: health, configuration status, current user/CSRF header, browser-bound one-time Google state, fixed redirect, session rotation and logout. No production test login route or auth environment bypass.
- `.env.example`, pinned installed `requirements.txt`, Makefile provide reproducible local commands.

Engineer execution: `.venv/bin/python -m pytest tests/test_auth.py tests/test_contract.py -q` → 28 passed, exit 0. Warnings concern installed Starlette/Authlib API deprecations and validator shortcut. Repeated after RS256 restriction with same result.

Tests use `create_app(Settings(...), MemoryRepository())`, internal repository session creation, and replacement `app.state.oauth_provider` inside tests only. No browser-accessible identity override exists. OAuth provider success in these tests is a mocked provider handoff, not a live Google handshake. Actual Google application credentials absent; live handshake unverified.

Ready for independent QA. Engineer has not closed issues, claimed QA approval, committed, published or pushed. GitHub remains unavailable. Freeze here pending M07 QA.

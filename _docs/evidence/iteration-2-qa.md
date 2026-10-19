# Iteration 2 independent OpenAPI QA

Date: 2026-10-19. Reviewer: separate QA agent. Local M06; no GitHub URL. Snapshot: maintained _docs/openapi.yml following iteration1 commit156c8de; no backend implemented at review.

Verdict: PASS for contract gate.

Executed `.venv/bin/python -m pytest tests/test_contract.py -q`: exit0, 17 passed (one validator API deprecation warning). Independent tests call openapi-spec-validator on the maintained YAML, check 19 unique operations over16 paths, all13 frontend Service methods, protected/public operation security and mutation Origin/CSRF requirements; validate valid/invalid money, metric counts, whitespace names, role/account shape, patch nonemptiness, duplicate assignments and empty report JSON examples against Draft202012 schemas. Independent direct validate_spec execution also passed (23 schemas).

Semantic inspection covered actual frontend Service signatures and _docs/frontend-service.md against endpoints; wire decimal strings vs numeric adapter boundary; all four fixed channels, KZT/USD/EUR; inclusive calendar dates; existing/missing metric version conflict behavior; archived writes/history and currency lock; merged user role/client association and cleared former assignments; current enabled user and assignment enforcement; single-client report sums with weighted ratios and null zero denominators. Referential existence, future dates, merged-role conditions and concurrency require application validation as explicitly described rather than JSON Schema alone.

OAuth contract requires browser-bound one-time state/nonce, verified Google identity and approved email, secure-cookie production flags, current sessions and CSRF/Origin on mutation; auth-status honestly reflects configuration. No production test identity endpoint exists in contract. Forbidden/notfound/state-conflict/validation/configuration response schemas are defined. Extra report endpoint extends all frontend operations coherently.

Limitations: schema and semantic review does not prove runtime endpoint parity, real OAuth, persistence or HTTP behavior. Those belong to subsequent gates. Examples exercise schema behavior, not a backend. No GitHub creation/closure or deployment claimed.

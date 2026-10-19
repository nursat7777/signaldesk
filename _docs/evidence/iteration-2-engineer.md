# Iteration 2 — OpenAPI engineer handoff

Date: 2026-10-19. Scope: M06 local staged contract task. Entry gate: iteration 1 independent QA PASS, commit `156c8de`, tag `iteration-1-mock-verified`, as reported by orchestrator. No backend application code authored here.

Created `_docs/openapi.yml` with OpenAPI 3.1, 16 paths, 19 operations and 23 reusable schemas. Operations cover frontend Service methods plus explicit OAuth, health and server-report endpoints. The adapter keeps current frontend method signatures: nested campaign creation injects clientId from method argument; daily save moves campaign/date into path; wire money strings convert to frontend numbers; assignments returns no body.

Wire fields use camelCase. Monetary values are exact two-decimal nonnegative strings. Counts are nonnegative integers. Ratios are number/null and calculated from summed bases. Schemas close additional properties; patches require at least one allowed property. Merged user role/client association rules, state-preserving rejection, assignment reset on role transition, archive behavior, currency locks, Almaty dates, daily uniqueness and version conflict semantics are documented.

Sessions use opaque `signaldesk_session` cookie; `/api/me` returns `X-CSRF-Token`. All authenticated mutation operations require CSRF header and Origin; backend must verify both and recheck current permissions. OAuth state/nonce and verified identity rules are explicit. Google credentials remain absent; real handshake is not verified.

Executed:

```text
.venv/bin/python -m openapi_spec_validator _docs/openapi.yml
_docs/openapi.yml: OK
Exit status: 0
```

This validates schema structure, not implementation or independent QA approval. Independent QA must verify semantic coverage and examples before stage 3. No GitHub issue publication or closure is claimed.

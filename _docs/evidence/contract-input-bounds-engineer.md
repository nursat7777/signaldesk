# Contract refinement — per-record safe input bounds

Date: 2026-10-19. During M08 implementation review, the orchestrator selected explicit safe per-record bounds before SQLite and numeric frontend integration. `MoneyInput` permits 0.00–999999999999.99 with exact two decimals; `CountInput` permits integers 0–2147483647. Only MetricWrite references these input schemas. Metric responses, aggregate Money and output counts retain their original unbounded nonnegative representation.

This refines engineering validation, not product scope. `_docs/plan.md` records the rationale. The earlier stage 2 QA gate does not automatically approve the changed contract; independent QA must rerun validator and boundary examples.

Actual engineer checks:

- `.venv/bin/python -m openapi_spec_validator _docs/openapi.yml`: OK, exit 0.
- Python `jsonschema.validate`: 10 boundary examples checked, exit 0. Money 0.00 and 999999999999.99 accepted; 1000000000000.00, -0.01 and 0.001 rejected. Counts 0 and 2147483647 accepted; 2147483648, -1 and 1.5 rejected.

These are schema checks, not backend or frontend behavior approval. Backend and independent QA were notified of the exact bounds.

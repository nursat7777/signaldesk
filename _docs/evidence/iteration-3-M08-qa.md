# M08 independent domain HTTP QA

Date2026-10-19. Independent reviewer. Local staged M08; no external issue URL. Implementation commit bdb554b (following M07 QA commit2229a1e), with explicit numeric-bound refinement; independent tests/evidence were added for review.

Verdict: PASS for in-memory domain CRUD/metric issue; release to M09 reports. Not yet iteration3 complete.

Executed `.venv/bin/python -m pytest tests -q`: exit0,75 passed,4 recorded dependency/validator deprecation warnings. Includes16 independently authored domain HTTP scenarios (tests/test_qa_domain.py),13 engineer domain cases, prior auth checks and22 independent contract/schema cases. Independent maintained OpenAPI validator reruns within suite.

Independent cases build data using actual administrator HTTP client/account/campaign/assignment operations and internal session fixture only. Verify normalized email, assigned client listing, forbidden unassigned direct IDs/admin operations/viewer writes, immediate assignment revocation and disabled account refusal. Metric creates exact decimal strings; duplicate/stale writes409; current version updates one row; inclusive single-date list retains history; financial currency change409; archive preserves rows and denies metric edits and campaign patches under archived parent. User merged association validation rejects invalid transition, clears old grants, preserves valid association after failed patch and prevents self-access edit.

Validation cases reject negative/fractional/boolean counts, numeric/non-two-decimal/negative money, explicit null version, malformed and future dates. New plan/contract refinement independently tested: input999999999999.99 money and2147483647 counts accepted exactly; one-unit-over bounds rejected422. JSON Schema tests separately validate input/output distinction: totals can exceed one-record limits. Contract real validator passes after MoneyInput/CountInput change.

Source inspection confirms scoped permission recheck in access(), lock held across unique/version check and update, defensive memory copies, no SQLite code added early. Tests cover principal runtime behavior through FastAPI TestClient, not generated-schema claims.

Limitations: in-memory repository only; no process persistence or actual browser/live Google sign-in. M09 reporting still absent and not certified. No GitHub issue publication/closure claimed. Frontend mock-bound parity belongs to integration and remains explicitly scheduled.

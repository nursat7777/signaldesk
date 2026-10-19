# M12 — real API adapter and authentication shell

2026-10-19. Implemented only after independent SQLite gate passed at tag iteration-4-sqlite-verified.

## Changes

- All thirteen frontend service operations map to the maintained REST paths/body schemas. Cookies included; CSRF captured from current-user response, attached only on mutations. Browser supplies Origin.
- Metric decimal strings encode/decode at boundary; required six fields and optional version only. Client/campaign path IDs encoded; inclusive range query values URL encoded.
- Real API is default. Only explicit DEV mock mode loads preview identities. No production mock singleton/fallback. Network/server errors remain errors.
- AuthGate verifies session, loads configuration state, offers Google route only when configured, exposes localized setup instructions and retry when backend unreachable. Backend logout returns to login.
- Numeric per-record limits align maintained contract; large supported decimals use safe two-place roundtrip check. Frontend aggregation adds integer minor units rather than repeated floating decimal addition.

## Executed verification

`npm test` with configured maxWorkers1: 6 files / **30 tests passed**, exit0 before final minor-unit sum refinement; full post-refinement suite recorded at handoff. Covers adapter money strings, path/body/query encoding, credentials+CSRF,204, network/server errors, all thirteen operations (independent QA), upper money/count bounds, auth401/configured/setup/error/logout, previous mock role+daily UI regressions.

During concurrent independent test file creation, initial full run encountered a QA test source syntax error (unexpected EOF); QA corrected their harness. No application bug or fabricated result attached to this transient test authoring issue.

`npm run build`: TypeScript + Vite exit0. Production branch inspected in source: mock conditional guarded by `import.meta.env.DEV`; production AuthGate always real. Browser visual inspection not available. No live Google handshake claimed. No actual HTTP+RTL full-stack workflow claimed here; M13 separately exercises running server and isolated seeded test sessions.

Independent QA owns final approval; no GitHub closure by engineer.

Final post-refinement run: `npm test` exit0, **30/30 tests across6files**; `npm run build` exit0,269.42kB JS/83.36kB gzip. Source frozen for independent QA.

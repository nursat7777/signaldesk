# M12 independent REST adapter/auth shell QA

Date2026-10-19. Independent reviewer. Implementation commit0721fb6. Local staged M12, no GitHub URL.

Verdict: PASS for integration adapter/auth shell issue, release M13 integrated runtime tests. Final full-stack gate still pending M13.

Executed frontend `npm test -- --maxWorkers=1`: exit0,6files/30tests passed. Executed `npm run build`: exit0,TypeScript+Vite6.4.4,1586modules; dist/index-bJUp5t2d.js. Four independent qa.api.test.tsx scenarios plus10 independent service tests and5 independent interaction cases execute alongside11 engineer cases.

Independent boundary test calls all13 Service operations, checks methods/path mapping and encoded IDs, include credentials on every request, CSRF header from /me applied on mutations, clientId removed from nested campaign request, money serialized exactly10.25/30.75 strings and decoded numbers,204 handling. Stable409 code and network failure propagate as ServiceError without mock fallback. Production AuthGate renders missing-OAuth setup with no demo/account chooser;401configured exposes actual Google route and no analytics. Engineer tests further cover current workspace/logout, language and error states.

Current numeric acceptance includes123456789012.35 and maximum999999999999.99; passes current roundtrip validation. No historical monetary-range bug reproduced. Reviewed initial mock parity updates, per-record count/money caps and integer minor-unit/BigInt base-money aggregation. Prior B01/B02 regressions remain passing.

Source inspection: main.tsx defaults to actual API AuthGate. Mock controller requires both development flag and explicit VITE_SERVICE_MODE=mock; App requires injected service, no singleton mock fallback in production. REST failure cannot silently expose demo data. Build compiles production branch successfully.

Limitations: adapter tests here mock HTTP transport responses; actual server integration is separately M13. No browser visual or real Google sign-in. Cookie Origin is browser-generated in normal operation; real local integration tests need controlled test transport headers/session fixtures. No GitHub issue closure claimed.

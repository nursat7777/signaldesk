# B02 independent financial display regression

2026-10-19, independent QA. Local staged bug only; no GitHub issue or closure. Historical iteration1 gate preceded this additional finding.

Initial targeted rendered RTL test failed: spend10.25 not visible because shared money formatter rounded to whole currency units. PM groomed B02; engineer changed shared formatter to two fractional digits.

Independent final `npm test -- --maxWorkers=1`: exit0, 3 files,17 tests passed. Financial regression checks EN report/table amount10.25 and CPL2.56 and Russian10,25 after locale switch. Runtime Intl represents KZT in Russian with `KZT` or currency symbol; matcher permits both. Prior expanded test initially used unsupported symbol-only expectation; corrected harness to match runtime ICU. Concurrent full run hit one existing engineer test's5s timeout; serial worker execution passed all cases without app changes.

`npm run build` executed after monetary formatter change: exit0, Vite6.4.4,1584 modules, index-B6unJqQ_.js. No further application edit before final serial suite.

Verdict: PASS for B02 fix and affected frontend regression. No visual/browser or live Google authentication claim.

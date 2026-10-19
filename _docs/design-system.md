# Design system

SignalDesk is a focused agency reporting workspace. Use dark graphite surfaces, restrained cyan/blue highlights, dense readable tables and clear chart hierarchy. Avoid decorative gradient cards, excessive shadows and irrelevant dashboard widgets.

## Reference direction

Professional product references: Grafana, https://grafana.com/products/cloud/ ; Linear, https://linear.app/features . The orchestrator read these official product pages during preparation. This does not imply screenshot-based visual inspection or permission to reuse assets. Draw on Grafana's analytical density and Linear's restrained navigation; do not copy branding or interface assets.

## Tokens and layout

Canvas #0b1017; surface #121b27; raised surface #182432; border #263649; text #e8eef5; secondary #9caec0; accent #38bdf8; success #4ade80; warning #fbbf24; error #fb7185. Use a system sans-serif stack, tabular numerals in financial tables, 14px base body, 12px metadata, 24–30px page titles. Spacing scale 4/8/12/16/24/32px; corners 8px. Verify actual rendered contrast.

Desktop: compact left navigation, workspace header with client/date controls, key metrics, trend, channel comparison and campaign table. Mobile: stacked content and scrollable table with clear column labels. No monetary global total across currencies. Client view hides all mutation controls; backend still enforces permissions.

## Interaction and accessibility

Visible labels and keyboard focus; no meaning through color alone. Currency shown beside amounts; ratios use ×/%. Explain unavailable ratios. Loading, empty, forbidden, setup-needed and recoverable error states are first-class. Daily form handles existing date by loading its record and version; stale edits retain entered data and prompt reload. Both RU/EN include navigation, forms, validations, empty states, metrics and errors. Long Russian strings must wrap without clipping. Persist language preference locally. Charts include text/table equivalents.

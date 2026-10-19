# Iteration 1 frontend service boundary

`frontend/src/service.ts` exports TypeScript interfaces and an asynchronous mock service. App accepts `{api: Service, demo: boolean}`; integration must inject a real implementation with `demo=false`. No HTTP client is implemented in iteration 1. `main.tsx` currently mounts mock-only development preview, prominently marked DEVELOPMENT PREVIEW · MOCK DATA. Mock identity selection is deliberately not Google sign-in or real authentication.

## Models and wire mapping

Frontend models use camelCase. User: id, email, name, role (`admin|marketer|client`), enabled, clientId nullable, clientIds assignment array. Client: id/name/currency (`KZT|USD|EUR`)/archived. Campaign: id/clientId/name/channel/archived; fixed channels Google Ads, Meta Ads, TikTok Ads, Other. Metric: id/campaignId/date/spend/impressions/clicks/leads/sales/revenue/version. Dates are YYYY-MM-DD using Asia/Almaty current date. Monetary frontend values are decimal numbers limited to two fractional digits. API contract should use fixed decimal **strings** and storage integer minor units; the future REST adapter will convert at its boundary. Counts are integer numbers. IDs are opaque strings. Error details are stable codes localized by frontend.

| Method | Inputs | Result |
|---|---|---|
| getMe | none | User |
| listClients | none | accessible Client[] (including archived) |
| createClient | name,currency | Client |
| updateClient | id, patch name/currency/archived | Client |
| listCampaigns | clientId | Campaign[] (including archived) |
| createCampaign | clientId,name,channel | Campaign |
| updateCampaign | id, patch name/archived | Campaign |
| listMetrics | clientId,from,to | Metric[], inclusive dates |
| saveMetric | campaignId,date,six metrics, optional version | Metric |
| listUsers | none | User[] (admin only) |
| createUser | name,email,role,clientId nullable | User |
| updateUser | id,patch enabled/role/clientId | User |
| setAssignments | userId,clientIds[] | void |

## Semantics

One metric per campaign/day. New saves omit version; existing saves must include current version. UI date/campaign selection fetches that day, loads existing fields and version, and explains edit behavior. Duplicate unversioned create returns conflict rather than overwriting. Stale edits retain entered values and show localized reload instruction. Archived client/campaign data remains visible, writes reject until restored. Financial currency cannot change after any results exist. Account/assignment authorization is rechecked for every mock operation, modeling backend expectations. Role changes require valid client association for viewers and clear irrelevant associations/assignments; revoke takes effect on next service call.

Mock errors: required, invalidEmail, duplicateEmail, invalidAssignment, selfDisable, forbidden, notFound, invalidDate, futureDate, invalidNumber, dateRange, currencyLocked, archived, conflict. REST adapter should map server stable codes. Unexpected failures use localized general error.

Charts and tables aggregate only selected client, never mixed currencies. CTR/CPC/CPL/ROAS derive from summed base metrics; zero denominator produces unavailable em dash. Language persists in localStorage; tests reset storage per case. Report defaults to 30 calendar days. Demo seed regenerates latest 30 days relative to runtime Almaty date, 3 clients/9 campaigns and 270 daily entries. Mock data is memory-only intentionally at this iteration.

## UI structure and limitations

App orchestrates state/forms/service calls. Sidebar, AgencySettings and Trend are separate components; `i18n.ts` centralizes EN/RU user-facing labels/errors. `style.css` defines responsive graphite/lime/cyan visual system and financial tabular figures. Date/campaign filters and daily forms have accessible labels, chart has accessible title and table equivalents. No unsupported growth percentage is claimed; icons are decorative only. Browser visual validation and live Google OAuth are unverified because environment capabilities/credentials are absent. No deployment is claimed.

## Iteration 5 / M12 production adapter

`createApiService(base='/api',fetcher=fetch)` now implements all thirteen operations and adds `authStatus`, `loginUrl`, `logout`. HTTP uses credentials include; GET `/me` captures exposed X-CSRF-Token; mutations send it. Browser sets Origin automatically (the adapter must not set this forbidden header). Fixed-decimal wire strings convert to numeric frontend display and validated numbers encode with `toFixed(2)`. Request bodies intentionally omit path IDs and unknown fields. Error codes map to localized ServiceError; network/proxy failures never fall back to mock data.

`main.tsx` mounts AuthGate and real service by default. Only `import.meta.env.DEV && VITE_SERVICE_MODE=mock` dynamically creates the clearly marked preview. App requires an injected service; no singleton mock is instantiated. Production ignores mock mode. Vite proxies `/api` to backend8000 preserving actual Origin. Optional `VITE_API_BASE` supports an explicit backend base URL. Google config status is truthful: unconfigured server shows instructions, configured server offers real Google route. Logout revokes session with CSRF and returns to auth gate. Live provider authentication remains untested without credentials.

Metric input count max2147483647; per-record spend/revenue max999999999999.99. Two-decimal input validation uses round-trip `Number(toFixed(2))` to avoid rejecting large supported decimals due binary multiplication. Money aggregation sums integer minor units using BigInt before converting report display. No mixed currency totals.

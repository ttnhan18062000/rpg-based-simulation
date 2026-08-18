---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE
tags: [dashboard, observability]
---

# Test Plan — TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE

## Commands and results
```
npx tsc -b
```
Clean, no output.

```
npx vitest run src/test/StatsView.test.tsx
```
`Test Files 1 passed (1)` / `Tests 21 passed (21)` — zero modifications to this test file.

```
npx vitest run
```
`Test Files 15 passed (15)` / `Tests 145 passed (145)`.

```
npm run build
```
`✓ 701 modules transformed` / `✓ built in 3.90s`.

## Live verification (against the actually-running server, not just local build output)
```
curl -s http://127.0.0.1:8420/ | grep -o 'assets/index-[A-Za-z0-9]*\.js'
```
Returned `assets/index-DR8RBVqb.js`, matching the freshly-built `dashboard-frontend/dist/assets/`
filename exactly — confirms the running server is serving today's build, not a stale one.

```
grep -c "top-agents-table\|Rows per page\|Avg agents per run" dashboard-frontend/dist/assets/index-DR8RBVqb.js
```
Non-zero — confirms the new UI strings are present in what's actually being served.

## Final status
All verification passed. No test file needed modification.

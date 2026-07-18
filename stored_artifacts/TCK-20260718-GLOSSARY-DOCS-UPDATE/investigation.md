---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-DOCS-UPDATE
artifact_type: investigation
tags: [dashboard, observability, documentation]
---

# Investigation: TCK-20260718-GLOSSARY-DOCS-UPDATE

## Current Behavior
Read `docs/observability/agent_ops_dashboard_contract.md` in full (284 lines). Its backend routes
table (line 29-35) lists 6 routes, none of them `/api/glossary`. Its response-models section
(line 41-80) has no `GlossaryEntry`/`GlossaryResponse` entry. Its ingest/cache section (line
82-160) documents every `DashboardCache` method except `get_glossary`. Its frontend SPA structure
section (line 162-237) documents `App.tsx`/`api.ts`/every view/every component except
`GlossaryTooltip.tsx` and `useGlossary`. Its `## Related` section cites `INFRA-275`/`INFRA-276`
only — not `INFRA-279` (the glossary API's parity entry, added by `TCK-20260718-GLOSSARY-API`).

Read `docs/guides/agent_ops_dashboard.md`'s heading structure: `## Using the four views` with
`### Recent Activity Gantt`/`### Replay Timeline`/`### Tickets view`/`### Stats` subsections, no
tooltip-specific content anywhere.

## Prior Work / Precedent
`TCK-20260718-STATS-DOCS-UPDATE` is the direct precedent for this exact ticket shape — a
docs-only closing ticket for a completed epic's implementation tickets, editing these same two
files plus a parity ledger check. Followed the same structure: read every section that could be
stale, edit only what's actually missing, run `make knowledge-index-update` since `docs/` changes.

## Anti-Drift Hazards
This ticket must not modify any code file — a documentation-only ticket touching `src/` or
`dashboard-frontend/src/` would be a scope violation.

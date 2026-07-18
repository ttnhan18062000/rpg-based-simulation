---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-DOCS-UPDATE
artifact_type: plan
tags: [dashboard, observability, documentation]
---

# Implementation Plan — TCK-20260718-GLOSSARY-DOCS-UPDATE

## Summary
Bring `agent_ops_dashboard_contract.md` and `agent_ops_dashboard.md` up to date with the three
already-shipped glossary tickets, add a parity ledger entry, refresh the knowledge index.

## Steps

### Step 1 — `agent_ops_dashboard_contract.md`:
- Routes table: add `GET /api/glossary` row (`GlossaryResponse`, no params,
  `DashboardCache.get_glossary`).
- Response-models section: add `GlossaryEntry`/`GlossaryResponse` paragraph, describing the
  layer-note merge-at-read-time design (never duplicated into a second file).
- Ingest/cache section: add `get_glossary()` paragraph — independent fresh read like
  `get_ticket_corpus_stats`, merges `glossary_registry.py` + `layer_registry.py`.
- Frontend SPA structure section: add `GlossaryTooltip.tsx`/`useGlossary` bullet describing the
  fetch-once singleton and two-layer graceful degradation; note its use across
  `TicketsView`/`ReplayTimelineView`/`StatsView`/`BarChart`/`GroupedBarChart`, and the deliberate
  `GanttBar`/`Legend` exclusion.
- `## Related`: add the new parity ledger entry ID from Step 3.

### Step 2 — `agent_ops_dashboard.md`: add a short subsection (under `## Using the four views` or
as its own top-level note) describing hover tooltips — what's covered, backend-sourced, and the
Gantt/Legend exclusion.

### Step 3 — `docs/parity_ledger/infrastructure.yaml`: add one new entry covering the
frontend-tooltip-wiring behavior (registry + API already have `INFRA-279`; this covers the
frontend consumption specifically), `status: verified`, citing the 82-test frontend suite and the
live headless-Chromium hover verification.

### Step 4 — `make knowledge-index-update` (docs changed).

## Scope Guards
- No code file edits — documentation and parity ledger only.
- Do not alter the existing `INFRA-279` entry's content — add a new entry for the frontend piece
  rather than overloading one entry with three tickets' worth of unrelated evidence.

## Dependency Map
Depends on `TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND` (DONE). Closes out
`TCK-20260718-GLOSSARY-TOOLTIPS-EPIC`.

## Acceptance Criteria Map
- AC "contract doc mentions glossary in all 4 sections" → Step 1.
- AC "guide has a tooltips subsection" → Step 2.
- AC "parity ledger entry exists" → Step 3.
- AC "knowledge index refreshed" → Step 4.

## Anti-Drift Notes
None beyond the scope guard above — this is a low-risk documentation-only ticket.

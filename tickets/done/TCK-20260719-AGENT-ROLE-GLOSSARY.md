---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-AGENT-ROLE-GLOSSARY
phase: done
date: 2026-07-19
tags: [dashboard, observability]
---

# TCK-20260719-AGENT-ROLE-GLOSSARY

## Title
Add agent-role glossary descriptions (extend GET /api/glossary with a third "agent" merge source)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
User asked for hover descriptions on agent-name rows in the Stats view's
"Top agents by call volume" table, and explicitly noted this is useful
generally ("not only for this feature"), not a narrow one-off UI hack.
Investigation found every `.claude/agents/*.md` role file already has a
ready-to-use one-sentence description in its own frontmatter, so this is
extraction/reuse — mirroring exactly how the Layer registry's `note` field
was merged into the glossary yesterday — not new content authorship.

## Scope
- New `_load_agent_role_descriptions()` helper in
  `src/api/agent_ops_dashboard/ingest.py`, reading every `.claude/agents/*.md`
  file's frontmatter via the established `extract_frontmatter` parser.
- Wired as a third merge source in `get_glossary()`, category `"agent"`,
  alongside the existing glossary-registry and layer-registry sources.
- Stats view's Top Agents table `Agent` column wrapped in the existing
  `GlossaryTooltip` component.
- New backend + frontend test coverage.
- `docs/observability/agent_ops_dashboard_contract.md`'s glossary section
  updated to describe the third merge source.

## Out of Scope
- Writing new descriptions — every one already existed in role-file
  frontmatter.
- Any change to what values `agent-monitoring/events.jsonl`'s `agent` field
  can hold, or to non-agent-file workflow/orchestrator labels
  (`finalizer`, `implement-ticket-orchestrator`, etc.) — these correctly
  degrade to no tooltip, same as every other unmatched glossary lookup.

## Acceptance Criteria
- [x] `GET /api/glossary` includes all 13 real `.claude/agents/*.md` role
      descriptions under `category="agent"` (live-verified: term count
      grew from 54 to 67).
- [x] Hovering a real agent-role name (e.g. `architecture-reviewer`) in the
      Stats view's Top Agents table shows its real frontmatter description
      (live-verified via headless Chromium).
- [x] A non-agent-file label (e.g. `finalizer`) shows no hint icon, no
      tooltip, and causes no console error (live-verified).
- [x] All pre-existing glossary/StatsView tests still pass.

## Related Tickets
- TCK-20260718-GLOSSARY-REGISTRY
- TCK-20260718-GLOSSARY-API
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
- TCK-20260718-GLOSSARY-DOCS-UPDATE
- TCK-20260718-LAYER-REGISTRY-CONVERSION (established the read-time-merge-of-an-existing-source pattern this ticket's Agent merge reuses)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_agent_glossary.md
- docs/observability/agent_ops_dashboard_contract.md
- docs/agent-monitoring/schema.md (agent-identifier naming convention)

## Related Stored Artifacts
- stored_artifacts/TCK-20260719-AGENT-ROLE-GLOSSARY/

## Related Code Areas
- src/api/agent_ops_dashboard/ingest.py
- dashboard-frontend/src/views/StatsView.tsx
- dashboard-frontend/src/api.ts
- tests/tools/test_agent_ops_dashboard_glossary.py
- dashboard-frontend/src/test/StatsView.test.tsx

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
**Execution-order deviation (self-flagged, per this project's traceability
rule)**: implementation began in a background execution context that
stalled/hit session limits three times in a row. The second stall left
`ingest.py` calling `_load_agent_role_descriptions()` before it was ever
defined — confirmed genuinely broken via a real pre-fix test run (6 of 7
`test_agent_ops_dashboard_glossary.py` tests failing with `NameError`).
Given the repeated interruptions, the coordinating session finished the
implementation directly rather than risk a fourth stall, then wrote this
ticket and its staging artifacts (`stored_artifacts/TCK-20260719-AGENT-ROLE-GLOSSARY/`)
retroactively. Every claim in this ticket was independently re-verified via
real test runs and live browser checks by the coordinating session itself
— not merely asserted from the interrupted background context's own report.

A second, unrelated pre-existing bug was found and fixed along the way:
`dashboard-frontend/src/api.ts`'s `useGlossary()` hook's module-level
`_glossaryPromise` cache was never reset between tests, so any test file
mounting a view calling `useGlossary()` more than once with different
mocked glossary content would silently reuse an earlier test's resolved
value. Added `_resetGlossaryCacheForTests()` (test-only export) and wired
it into `StatsView.test.tsx`'s `afterEach` — confirmed load-bearing by
temporarily disabling the reset call and re-running (the new hint-icon
tests genuinely failed without it).

Backend: `_load_agent_role_descriptions(repo_root)` reads
`.claude/agents/*.md` via the established `extract_frontmatter` parser,
tolerant of a missing directory (returns `{}}`) or a file with no
`description:` field (skipped) — never raises, per this dashboard's
established graceful-degradation discipline. Wired into `get_glossary()`
as a third merge loop with the same `if term in terms: continue`
first-registered-wins shadow guard the layer merge already uses.

Frontend: `StatsView.tsx`'s Top Agents table `Agent` column wrapped in the
existing `GlossaryTooltip` component (already imported/used for that same
table's column headers and the Slow Runs status cell) — the most
consistent fit for a plain table cell.

## Test Summary
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_glossary.py -q` — 10/10 passing (7 pre-existing + 3 new).
- `python3 -m pytest tests/tools/ -q -k "agent_ops_dashboard or glossary"` — 87/87 passing.
- `cd dashboard-frontend && npm run test -- --run` — 90/90 passing.
- `cd dashboard-frontend && npx tsc -b --noEmit` — clean.
- `cd dashboard-frontend && npm run build` — clean production build.
- Live verification: killed a stale `dashboard-serve` process, rebuilt fresh, confirmed `GET /api/glossary` returns 67 terms (13 new `category="agent"`) via `curl`. Headless-Chromium hover test: `architecture-reviewer` row shows its real frontmatter description on hover; `finalizer` row (a non-agent-file workflow label) shows no hint icon and zero console errors.

## Files Changed
- src/api/agent_ops_dashboard/ingest.py (`_load_agent_role_descriptions()` + 3rd merge source)
- dashboard-frontend/src/views/StatsView.tsx (Top Agents `Agent` column wrapped in `GlossaryTooltip`)
- dashboard-frontend/src/api.ts (`_resetGlossaryCacheForTests()` test-only export)
- tests/tools/test_agent_ops_dashboard_glossary.py (3 new tests, real-corpus test extended)
- dashboard-frontend/src/test/StatsView.test.tsx (2 new tests, cache-reset wiring)
- docs/observability/agent_ops_dashboard_contract.md (glossary section describes the 3rd merge source)

## Completion Summary
`GET /api/glossary` now merges a third source — every `.claude/agents/*.md`
role file's own frontmatter description, under `category="agent"` — growing
from 54 to 67 total terms. The Stats view's Top Agents table shows the real
description on hover for any row whose agent name matches a real role file,
and correctly shows nothing for workflow/orchestrator labels with no
matching file. A genuine pre-existing test-isolation bug in `useGlossary()`'s
module-level cache was found and fixed along the way. All claims
independently re-verified: 87 backend + 90 frontend tests passing, clean
TypeScript/build, and live headless-browser confirmation of both the
positive (real description shown) and negative (graceful degradation, no
crash) cases.

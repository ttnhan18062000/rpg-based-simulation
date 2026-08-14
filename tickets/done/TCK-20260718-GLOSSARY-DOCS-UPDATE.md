---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-DOCS-UPDATE
phase: done
date: 2026-07-18
tags: [dashboard, observability, documentation]
---

# TCK-20260718-GLOSSARY-DOCS-UPDATE

## Title
Document the new glossary registry, `/api/glossary` endpoint, and dashboard hover tooltips

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Final child of `TCK-20260718-GLOSSARY-TOOLTIPS-EPIC`, depends on
`TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND` (now DONE). The epic's three implementation tickets
(registry, API, frontend) are all done but `docs/observability/agent_ops_dashboard_contract.md`
and `docs/guides/agent_ops_dashboard.md` do not yet describe any of it — same closing pattern as
`TCK-20260718-STATS-DOCS-UPDATE` did for the Stats-tab epic.

## Scope
- `docs/observability/agent_ops_dashboard_contract.md`: add `GET /api/glossary` to the backend
  routes table; add `GlossaryEntry`/`GlossaryResponse` to the response-models section (including
  the layer-note merge-at-read-time design decision); add `get_glossary()` to the ingest/cache
  section; add `GlossaryTooltip`/`useGlossary` to the frontend SPA structure section.
- `docs/guides/agent_ops_dashboard.md`: add a short "Hover tooltips" subsection describing what's
  covered (Tier/Layer/ticket-status/Priority in Tickets, event status in Replay, chart/table
  labels in Stats) and the deliberate Gantt/Legend exclusion.
- New parity ledger entry(ies) in `docs/parity_ledger/infrastructure.yaml` for the glossary
  registry + API + frontend wiring (three tickets' worth of behavior, not yet recorded).
- `make knowledge-index-update` (docs changed).

## Out of Scope
- Any further code change — this ticket is documentation-only.
- Re-litigating the Gantt/Legend exclusion decision — already made and verified in
  `TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`'s investigation.md; this ticket only writes it down
  in the user-facing guide.

## Acceptance Criteria
- [x] `agent_ops_dashboard_contract.md`'s routes table, response-models section, ingest/cache
      section, and frontend-structure section all mention the glossary feature.
- [x] `agent_ops_dashboard.md` has a hover-tooltips subsection.
- [x] `docs/parity_ledger/infrastructure.yaml` has an entry covering the glossary
      registry/API/frontend, `status: verified` (new `INFRA-280`, the frontend-consumption
      counterpart to the already-existing `INFRA-279`).
- [x] `make knowledge-index-update` run after doc edits (14 files re-embedded).
- [x] No code files touched.

## Related Tickets
- TCK-20260718-GLOSSARY-TOOLTIPS-EPIC (parent epic — closes after this ticket)
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND (depended on)
- TCK-20260718-GLOSSARY-API (depended on transitively)
- TCK-20260718-GLOSSARY-REGISTRY (depended on transitively)

## Related Docs
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md
- docs/plans/agent_ops_dashboard/proposal_glossary_tooltips.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260718-GLOSSARY-DOCS-UPDATE/

## Related Code Areas
None — documentation only.

## Assumptions / Open Questions
None.

## Implementation Notes
Executed directly (Read/Edit/Bash/Write) — no Agent-tool subagent access in this execution
context, same as tickets 1-3 of this epic. Ticket file, plan, investigation, and test_plan were
all written before implementation, per the coordinator's explicit instruction for this ticket
(unlike tickets 1-3, which had documentation written after implementation).

While re-reading `docs/guides/agent_ops_dashboard.md`'s Stats section to place the new tooltips
subsection, found and fixed one pre-existing, unrelated staleness bug discovered incidentally:
line 126 still described "a table of tickets with incomplete staging artifacts" in the Ticket
Corpus section, but that table was removed from `StatsView.tsx` earlier this session (per a
direct user request, prior to this epic) — confirmed via `grep -n "incomplete"
dashboard-frontend/src/views/StatsView.tsx` returning zero matches. Fixed the doc line in the same
edit pass rather than leaving a known doc/code mismatch unstated, since this ticket was already
touching that exact paragraph.

Added a new parity ledger entry `INFRA-280` rather than extending the existing `INFRA-279` —
`INFRA-279`'s own `support_boundary` text explicitly defers frontend-tooltip coverage to "the
dependent sibling ticket," so a separate entry keeps each entry's evidence scoped to what it
actually verified. Noted (not fixed, out of this docs-only ticket's scope) that `proof_type:
feature` is used for the new entry, matching 13 other pre-existing entries in this same file
including `INFRA-279` itself, even though the stricter `docs/parity_ledger/schema.json` enum
only lists `parity`/`contract`/`differential`/`regression`/`null` — a pre-existing drift between
schema and established practice in this ledger, not something introduced by this ticket.

## Test Summary
No code test suite applies (documentation-only ticket). Verified: `git status --porcelain --
docs/ dashboard-frontend/src/ src/api/agent_ops_dashboard/` confirms only
`docs/observability/agent_ops_dashboard_contract.md`, `docs/guides/agent_ops_dashboard.md`, and
`docs/parity_ledger/infrastructure.yaml` were touched by this ticket (all other listed paths
predate this ticket, from tickets 1-3 of this epic). `python3 -c "import yaml;
yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` parses cleanly (285 entries).
`make knowledge-index-update` completed: "14 files changed/new, 0 deleted, 2131 unchanged."

## Files Changed
- docs/observability/agent_ops_dashboard_contract.md (glossary route/models/ingest/frontend
  sections, `## Related` entries)
- docs/guides/agent_ops_dashboard.md (new "Hover tooltips" subsection; fixed stale
  incomplete-artifacts-table reference)
- docs/parity_ledger/infrastructure.yaml (new `INFRA-280`)

## Completion Summary
`agent_ops_dashboard_contract.md` and `agent_ops_dashboard.md` now fully describe the glossary
registry, `/api/glossary` endpoint, and frontend hover-tooltip wiring shipped by the epic's three
prior tickets. New `INFRA-280` parity ledger entry records the frontend-consumption evidence
`INFRA-279` explicitly deferred. Incidentally fixed one pre-existing stale doc line found during
this ticket's own read-through. Knowledge index refreshed. Closes out
`TCK-20260718-GLOSSARY-TOOLTIPS-EPIC`.

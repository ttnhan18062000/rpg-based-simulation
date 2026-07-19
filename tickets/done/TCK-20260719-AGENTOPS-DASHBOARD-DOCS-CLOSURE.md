---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE
phase: open
date: 2026-07-19
tags: [dashboard, observability, documentation]
---

# TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE

## Title
Archive the six fully-shipped Agent Ops Dashboard planning docs and fix cross-references

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
User asked to "update all related documents and docs/plans/agent_ops_dashboard as well, closing
this epic feature" once the Agent Ops Dashboard's v1 build plus its three follow-on epics
(canonical field enums, stats board, glossary tooltips) were all shipped and committed. Self-evident
documentation housekeeping: apply this repo's established archiving convention (frontmatter
`maturity: shipped` + `archived:` date, an "Archived:" summary line under the H1 citing the shipping
ticket IDs, a rewritten SHIPPED maturity blockquote, physical move to `docs/plans/archive/{topic}/`)
to every planning doc in `docs/plans/agent_ops_dashboard/` whose described work is fully shipped, and
leave the one doc whose work is still genuinely unimplemented in place.

## Scope
- Move 6 of 7 docs from `docs/plans/agent_ops_dashboard/` to a new
  `docs/plans/archive/agent_ops_dashboard/` folder (`git mv`, preserving history):
  `idea_agent_ops_dashboard.md`, `proposal_ui_review_findings.md`,
  `proposal_canonical_ticket_field_enums.md`, `proposal_stats_board.md`,
  `proposal_glossary_tooltips.md`, `proposal_agent_glossary.md`.
- Each archived doc: frontmatter gains `maturity: shipped` + `archived: 2026-07-19`, `status`
  changed `idea`/`active` → `historical`; body gains a new "**Archived:** 2026-07-19 — ..." line
  under the H1 citing the exact shipping ticket ID(s); the original maturity blockquote/paragraph
  rewritten from PROPOSAL/IDEA to a SHIPPED summary.
- Fix the 3 cross-references in the one doc staying in place
  (`idea_agent_monitoring_live_phase_label.md`) to point at the new archived path, annotated
  "(archived — shipped)".
- Fix `proposal_stats_board.md`'s own internal cross-reference to `idea_agent_ops_dashboard.md`
  (now co-located in the same archive folder).
- Fix the one live-code reference to the old path (`src/api/agent_ops_dashboard/ingest.py`'s
  `get_glossary()` docstring).
- Regenerate `docs/REGISTRY.yaml` (`make docs-registry`) and the semantic index
  (`make knowledge-index-update`); run `graphify update .` for the `ingest.py` comment change.

## Out of Scope
- `idea_agent_monitoring_live_phase_label.md` itself — confirmed still genuinely unimplemented
  (`docs/guides/agent_ops_dashboard.md` still documents "phase unknown — run still in progress" as
  an unconditional known gap). Not archived; only its cross-references were updated.
- `experiments/agent_ops_dashboard/` — left untouched, matching the established precedent that
  other `experiments/*` folders for shipped ideas (`cost_proxy_calibration`, `model_routing`) are
  not cleaned up once their idea doc ships.
- References inside closed tickets (`tickets/done/*.md`) and `stored_artifacts/*/investigation.md`
  / `plan.md` to the old pre-archive path — confirmed via `git log --follow` on the precedent
  archive move (`idea_agent_cost_observability.md`, commit `254115a4`) that closed tickets are left
  as historical point-in-time records, not retroactively rewritten when a doc later moves.
- The 13 pre-existing `status: idea`/`status: proposal` frontmatter violations found repo-wide by
  `validate_frontmatter.py` across unrelated `docs/plans/*.md` files — confirmed pre-existing (not
  introduced by this ticket) and out of scope, matching this repo's established judgment for
  legacy/unrelated data-quality gaps.
- No code behavior change — pure documentation/comment housekeeping.

## Acceptance Criteria
- [x] 6 docs physically moved to `docs/plans/archive/agent_ops_dashboard/` via `git mv`.
- [x] Each archived doc's frontmatter and maturity blockquote correctly reflect `shipped` status
      with accurate shipping ticket-ID citations, verified against `tickets/working_log.csv`.
- [x] `idea_agent_monitoring_live_phase_label.md` remains in `docs/plans/agent_ops_dashboard/`,
      unarchived, with its 3 cross-references updated to the new path.
- [x] `python3 tools/validate_frontmatter.py --content-type doc <each touched file>` passes clean
      for all 7 touched docs.
- [x] `make docs-registry` regenerates `docs/REGISTRY.yaml` with the new paths (old paths: 0
      occurrences; confirmed via grep).
- [x] `make knowledge-index-update` runs clean (7 files changed/new, 6 deleted, incremental).
- [x] Repo-wide grep for the 6 old doc paths turns up only expected historical-record hits
      (closed tickets, stored_artifacts, `agent-monitoring/tools.jsonl`) — no live doc or code
      cross-reference left stale.

## Related Tickets
TCK-20260716-AGENTOPS-DASHBOARD-BACKEND, TCK-20260716-AGENTOPS-ACTIVITY-GANTT,
TCK-20260716-AGENTOPS-TICKETS-VIEW, TCK-20260716-AGENTOPS-REPLAY-TIMELINE,
TCK-20260717-AGENTOPS-DASHBOARD-DOCS, TCK-20260717-CSS-LAYER-PADDING-FIX,
TCK-20260717-GANTT-TIME-AXIS, TCK-20260717-TICKET-TITLE-PARSE-FIX,
TCK-20260717-TICKETS-TABLE-PAGINATION, TCK-20260717-TICKETS-TAG-SEARCH,
TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT, TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC,
TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM, TCK-20260718-LAYER-REGISTRY-CONVERSION,
TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP, TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL,
TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE, TCK-20260718-AGENTOPS-STATS-BOARD-EPIC,
TCK-20260718-RETRO-STATS-REFACTOR, TCK-20260718-AGENTOPS-STATS-API,
TCK-20260718-TICKET-CORPUS-REPORT, TCK-20260718-STATS-TAB-FRONTEND,
TCK-20260718-STATS-DOCS-UPDATE, TCK-20260718-GLOSSARY-TOOLTIPS-EPIC,
TCK-20260718-GLOSSARY-REGISTRY, TCK-20260718-GLOSSARY-API,
TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND, TCK-20260718-GLOSSARY-DOCS-UPDATE,
TCK-20260719-AGENT-ROLE-GLOSSARY

## Related Docs
- docs/plans/archive/agent_ops_dashboard/ (6 newly archived docs)
- docs/plans/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md (stays, cross-refs fixed)
- docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md (precedent/template used)

## Related Stored Artifacts
None — hotfix tier, self-evident doc-housekeeping intent captured in this ticket directly.

## Related Code Areas
- docs/plans/agent_ops_dashboard/
- docs/plans/archive/agent_ops_dashboard/
- src/api/agent_ops_dashboard/ingest.py (one docstring path comment)
- docs/REGISTRY.yaml (regenerated)

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Followed the exact archiving convention discovered by reading
`docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` in full (the template
for a prior, structurally identical archive move). Verified via `git log --follow --diff-filter=R`
on that same file that the established precedent leaves closed tickets' `Related Docs` references
pointing at the pre-archive path — a closed ticket is treated as a point-in-time record, not
retroactively rewritten — so this ticket deliberately does not touch `tickets/done/*.md` or
`stored_artifacts/*/investigation.md`/`plan.md` files that reference the old paths.

Gathered exact shipping-ticket-ID citations per archived doc via `grep` against
`tickets/working_log.csv` rather than from memory, to avoid citing a stale or incorrect ticket ID
in a permanent archived record.

## Test Summary
- `python3 tools/validate_frontmatter.py --content-type doc <each of the 7 touched files>` — all
  pass clean.
- `make docs-registry` — 1450 entries regenerated; confirmed via grep the 6 new archive paths are
  present and the 6 old paths have zero occurrences in `docs/REGISTRY.yaml`.
- `make knowledge-index-update` — incremental update, 7 files changed/new, 6 deleted, 2146
  unchanged, completed clean.
- `graphify update .` — 21459 nodes, 49011 edges, 1131 communities, completed clean (comment-only
  change in `ingest.py`).
- Repo-wide `grep -rl` sweep for all 6 old doc paths — remaining hits are exclusively closed
  tickets, stored_artifacts, and `agent-monitoring/tools.jsonl` (append-only historical log),
  matching the established precedent for what does and doesn't get rewritten on an archive move.

## Files Changed
- docs/plans/archive/agent_ops_dashboard/idea_agent_ops_dashboard.md (moved + archived)
- docs/plans/archive/agent_ops_dashboard/proposal_ui_review_findings.md (moved + archived)
- docs/plans/archive/agent_ops_dashboard/proposal_canonical_ticket_field_enums.md (moved + archived)
- docs/plans/archive/agent_ops_dashboard/proposal_stats_board.md (moved + archived, internal
  cross-ref fixed)
- docs/plans/archive/agent_ops_dashboard/proposal_glossary_tooltips.md (moved + archived)
- docs/plans/archive/agent_ops_dashboard/proposal_agent_glossary.md (moved + archived)
- docs/plans/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md (3 cross-refs updated)
- src/api/agent_ops_dashboard/ingest.py (1 docstring path comment fixed)
- docs/REGISTRY.yaml (regenerated)

## Completion Summary
All six Agent Ops Dashboard planning docs whose described work has fully shipped (the original
dashboard build, the UI-review fixes, canonical field enums, the Stats board, and glossary
tooltips) are now archived to `docs/plans/archive/agent_ops_dashboard/` with accurate
shipping-ticket-ID citations, following this repo's established archiving convention exactly. The
one still-unimplemented sibling idea (`idea_agent_monitoring_live_phase_label.md`) remains in place
with its cross-references updated to point at the new archive location. `docs/REGISTRY.yaml` and
the semantic search index were regenerated to reflect the moves; a repo-wide grep sweep confirmed
no live doc or code cross-reference was left pointing at a stale path.

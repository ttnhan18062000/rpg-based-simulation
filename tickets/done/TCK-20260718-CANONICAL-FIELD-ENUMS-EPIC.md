---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC
phase: done
date: 2026-07-18
tags: [frontmatter, observability, data-quality]
---

# TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC

## Title
Epic: Canonical closed enums for ticket Tier/Layer/Status/Priority, hard-validated at close time, and dashboard filter facets that reflect them

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Scoped from a live UX bug report during today's Agent Ops Dashboard fix
session: the Tickets view's Tier/Layer/Priority filter dropdowns compute
their option lists from the currently-filtered ticket set, so selecting one
filter narrows what values other filters can offer — a prior fix
(TCK-20260718-FILTER-SELECT-DROPOUT) patched the visible symptom for the
already-selected value but not the underlying narrowing. Investigation
found that `Layer` already has the right mechanism — a closed, hardcoded
enum (`LAYER_VALUES` in `tools/validate_frontmatter.py`) hard-validated at
ticket-close time — but `Tier` and `Priority` (ticket body fields) have no
such enum or enforcement at all, and `Priority` already shows real corpus
drift (`"P1: High"` x2, same class of bug as the `## Status` drift fixed
earlier today). This epic: (1) defines canonical `TIER_VALUES`/
`PRIORITY_VALUES` and wires hard validation into the Finalize/Verify gate,
matching how `layer:` already works; (2) fully re-scans the existing ticket
corpus for any Tier/Priority drift beyond the 2 known cases and fixes it;
(3) makes the dashboard's Tier/Layer/Priority filter facets fixed canonical
lists instead of corpus-derived (Status was already fixed this session);
(4) updates the agent-facing docs/rules that currently describe these
fields informally or incompletely (including a `CLAUDE.md` doc bug — its
Ticket Format section lists Priority as `P0 | P1 | P2`, missing `P3`, which
the real corpus uses 24 times).

## Scope
- Define canonical `TIER_VALUES` and `PRIORITY_VALUES`; decide (and
  document) whether to consolidate with the existing `LAYER_VALUES` and
  `WORKFLOW_STATUS_VALUES` into one shared source-of-truth module.
- Add hard validation for body-section `## Tier`/`## Priority` to the
  Finalize/Verify gate (a ticket cannot close with a non-canonical value).
- Re-scan the full ticket corpus (`tickets/done/`, `tickets/inprogress/`,
  `tickets/todos/`) for Tier/Priority drift and fix everything found.
- Make `src/api/agent_ops_dashboard/ingest.py`'s `facets["tiers"]`,
  `facets["layers"]`, `facets["priorities"]` fixed canonical lists (mirroring
  `facets["statuses"]`, already fixed by
  TCK-20260718-STATUS-FACET-CANONICAL).
- Remove `TicketsView.tsx`'s `FilterSelect` synthetic-option workaround for
  Tier/Layer/Status/Priority if it becomes genuinely dead code once all four
  are canonical (verify via test, don't just assert).
- Update `CLAUDE.md`, relevant `.claude/agents/*.md` files, and the
  dashboard's contract/guide docs to describe the new mechanism accurately.

## Out of Scope
- Any change to how `Tag` works (open-vocabulary, registry-governed,
  multi-value by design — correct as-is, not part of this epic).
- Retrofitting the frontmatter `status`/`authority`/`audience`/`phase`
  fields — those already have working enums and enforcement.
- Any further UI/UX redesign of the Tickets view beyond canonical facets.

## Acceptance Criteria
- [x] `TIER_VALUES` and `PRIORITY_VALUES` exist as real, imported (not
      duplicated) canonical sets. (`tools/ticket_field_values.py`, plus
      `LAYER_VALUES` re-exported from the new registry-backed
      `tools/layer_registry.py` — the epic grew this scope mid-flight per
      an explicit user design decision.)
- [x] A ticket cannot reach `tickets/done/` with a non-canonical body
      `## Tier` or `## Priority` value — proven by an actual test that
      attempts it and confirms the gate blocks it (genuine-catch proof via
      `git stash`, not just asserted).
- [x] Zero non-canonical Tier/Priority values remain anywhere in the current
      ticket corpus (excluding any explicitly-documented, narrow exemptions
      — e.g. pre-TCK-naming legacy files — following this session's
      established precedent for such exemptions). 2 found and fixed
      (`"P1: High"` x2), confirmed via the real check function, not an
      ad-hoc scan.
- [x] `GET /api/tickets`'s `facets.tiers`/`facets.layers`/`facets.priorities`
      always return their full canonical lists, independent of active
      filters — verified live against the real running dashboard (curl +
      headless browser against a freshly-built server), not just unit
      tests.
- [x] `CLAUDE.md`'s Ticket Format section correctly lists all four Priority
      values including `P3`, plus a new Layer-registry paragraph.

## Related Tickets
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
- TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP
- TCK-20260718-LAYER-REGISTRY-CONVERSION
- TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL
- TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_canonical_ticket_field_enums.md
- tools/validate_frontmatter.py
- docs/guidelines/tag_taxonomy.md (for the Layer-vs-Tag contrast)
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md

## Related Stored Artifacts
None — epic tier, no staging artifacts for the epic ticket itself.

## Related Code Areas
- tools/validate_frontmatter.py
- tools/gate_checks/done_checker_static.py
- tools/gate_checks/status_drift_check.py
- src/api/agent_ops_dashboard/ingest.py
- dashboard-frontend/src/views/TicketsView.tsx
- CLAUDE.md

## Assumptions / Open Questions
- Whether to consolidate all four canonical enums into one new shared
  module vs. leaving `LAYER_VALUES` in `validate_frontmatter.py` and adding
  `TIER_VALUES`/`PRIORITY_VALUES` alongside it — left for the enum/gate
  child ticket's own investigation and plan to decide and document.

## Implementation Notes
Scoped from a live UX bug report ("filter dropdown reverts to All") plus a
follow-up design question ("should Layer-style closed enums exist for
Tier/Priority too, and how does Layer differ from Tag") raised during
today's Agent Ops Dashboard fix session (2026-07-18). Full investigation
already captured in the proposal doc cited above — child-ticket
Investigate phases should build on it, not redo it. Epic-tier: scope only,
no direct implementation on this ticket.

## Test Summary
See each child ticket's own Test Summary for full detail. Aggregate: 235+
backend tests and 60 frontend tests passing across the epic's final state,
plus 2 genuine-catch proofs (via `git stash`) confirming the new
`ticket_field_values_valid` gate and the `TicketsView.tsx` filter fix both
actually catch what they claim to, and 2 independent before/after
full-corpus scans (Tier/Priority drift-cleanup, Layer-registry conversion)
confirming zero regressions via direct comparison rather than a single
post-hoc check.

## Files Changed
See each child ticket's own Files Changed section. Summary by area:
`tools/ticket_field_values.py` + `tools/layer_registry.py` (new modules),
`docs/guidelines/layer_registry.jsonl` (new, seeded registry),
`tools/validate_frontmatter.py` + `tools/gate_checks/done_checker_static.py`
(wiring), `src/api/agent_ops_dashboard/ingest.py` (dashboard facets),
`dashboard-frontend/src/views/TicketsView.tsx` (comment-only), 4 corpus
ticket files (drift fixes), `CLAUDE.md` + `.claude/agents/*.md` (2 files) +
`.claude/workflows/*.js` (3 files) + 2 dashboard docs (documentation),
`docs/parity_ledger/infrastructure.yaml` (2 new/extended entries, INFRA-278
and INFRA-275).

## Completion Summary
All 5 child tickets DONE, all acceptance criteria met. What started as a
single UX bug report ("selecting Layer then Status resets Layer to All")
led to discovering that `Layer` already had exactly the closed-enum,
hard-validated mechanism the fix needed — `Tier`/`Priority` didn't, and
`Priority` already had 2 real corpus-drift cases. Mid-epic, the user asked
for `Layer` itself to become registry-backed like `Tag` (structurally
distinct — single-value, uncategorized — not a copy of `Tag`'s mechanism),
which was incorporated as a 5th child ticket without disrupting the
already-finished corpus-cleanup work. Every dashboard filter facet
(Tier/Layer/Status/Priority) is now a fixed canonical list, independent of
active filters — verified live, not just in unit tests — while `Tags`
correctly remains open-vocabulary and corpus-derived. Agent-facing
instructions (`CLAUDE.md`, 2 `.claude/agents/*.md` files, 3
`.claude/workflows/*.js` files, 2 dashboard docs) were updated to describe
the final mechanism accurately, closing the loop the user explicitly asked
for ("remember to update related agent's settings"). Nothing in this epic
was committed to git — left for the user to review as a batch.

---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS
phase: open
date: 2026-08-12
tags: [observability, documentation, economy]
---

# TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS

## Title
`docs/simulation_quality/event_type_coverage.md`'s `source` column is stale for every
push-shaper-migrated event row — still lists `event_extractor` where live derivation moved to a
`run_shadow_shapers()`-delivered shaper

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Filed as the required follow-up ticket for a deferral made in
`TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`'s Verify phase (DoD condition 11 — a
known, deliberately-deferred gap must have an explicit ticket reference, not just be noted in
staging artifacts). That ticket's own Verify phase separately fixed the `resource_harvested`/
`item_crafted` rows directly (the 2 rows its own investigation named) to satisfy a distinct DoD
static check (`docs_to_update_coverage`) — this ticket's scope has been narrowed accordingly to
cover the *remaining* stale rows only.

`docs/simulation_quality/event_type_coverage.md` (status: authoritative, `last_verified:
2026-07-04`) has a `source` column that names which code path derives each scored event type. Since
`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` (commit `11b83f37`) and its sibling migration
tickets, live derivation for many of these event types moved from `EventExtractor.extract()`'s
legacy per-domain loops to `run_shadow_shapers()`-delivered shaper classes in
`src/observability/event_shapers.py` (`EconomyShaper`, and equivalents for COMBAT/FACTION, plus
later QUEST/AGENCY-domain migrations referenced in that ticket's investigation) — with the old
`event_extractor.py` loops now flag-gated dead-by-default rollback paths (`_push_shapers_active` /
`_push_shapers_phase2_active` / `_push_shapers_quest_active` / `_push_shapers_agency_active`, all
defaulting `"ON"` i.e. shaper-path-live).

The doc's `source` column was never updated at any of these migration points. As of this filing,
`resource_harvested`/`item_crafted` (lines 109-110) have already been corrected directly by
`TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`'s own Verify phase (the 2 rows its own
investigation named). It still reads stale `event_extractor` for the remaining ECONOMY-domain rows
(`shop_transaction`, `trade_executed`, `quest_reward_dispensed`, `gold_sink_fired`,
`paid_information_transaction`, `paid_info_transaction`, `conservation_law_verified` — lines
~111-117 as of this filing) — and per
`TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`'s investigation, this same staleness was
already independently flagged-not-fixed once before, by `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s
own investigation, for the COMBAT/FACTION/QUEST/AGENCY rows too. This is the **third** time this
gap has been surfaced without being corrected in full.

## Scope
- Investigate-phase: enumerate every remaining row in `event_type_coverage.md` whose event type is
  now derived (in the default/live configuration) by a `SHAPER_REGISTRY` class in
  `src/observability/event_shapers.py` rather than `event_extractor.py`'s legacy loops —
  `resource_harvested`/`item_crafted` (lines 109-110) are already fixed; do not assume the remaining
  ECONOMY-row list above is complete; re-derive it from current source.
- Correct the `source` column for every such row to name the real live path (e.g. `event_shapers
  (EconomyShaper)` or equivalent naming convention established in this doc's existing table, to be
  decided at Investigate/Plan time) while noting the flag-gated legacy `event_extractor.py` path
  remains the rollback mechanism, not the terminus.
- Cross-check `docs/parity_ledger/*.yaml` entries whose `test_path`/`support_boundary` also cite
  `event_extractor.py` as the terminus for any of these same event types (the exact class of
  staleness `TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`'s Parity phase found and fixed
  twice within a single ledger entry, `STRAT-246`) — this doc and the parity ledger should not
  diverge on the same factual claim.

## Out of Scope
- Any change to the actual event-derivation code (`event_extractor.py`, `event_shapers.py`,
  `kernel.py`) — this is a documentation-accuracy ticket only, no behavior change.
- Fixing the `0`-hit calibration counts themselves for any ECONOMY row — those are a separate,
  already-tracked routing/calibration gap (`ENABLE_ADVENTURE_ROUTING` default-off, per
  `STRAT-246`'s `support_boundary`), not a doc-staleness issue.
- `docs/event_ledger/entity.yaml` — a separate, complementary ledger per this doc's own "See also"
  note; not in scope unless Investigate finds it shares the same staleness.

## Acceptance Criteria
- [ ] Every `event_type_coverage.md` row whose live derivation moved to a push-shaper has its
      `source` column corrected, verified against current `SHAPER_REGISTRY` contents, not assumed
      from this ticket's own preliminary ECONOMY-row list
- [ ] Doc's `last_verified` frontmatter field updated to the date of this ticket's completion
- [ ] Any `docs/parity_ledger/*.yaml` entry found to share the same stale-terminus claim during
      cross-check is corrected in the same session
- [ ] No behavior/code change — diff is `docs/` only

## Related Tickets
- TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION (the ticket that deferred this gap and
  filed this follow-up per DoD condition 11)
- TCK-20260807-QUEST-EVENT-PUSH-MIGRATION (the first ticket to flag this same staleness, for
  COMBAT/FACTION/QUEST/AGENCY rows, without fixing it)
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION (the migration that introduced the
  ECONOMY/COMBAT/FACTION shaper-delivery path this doc never caught up to)

## Related Docs
- docs/simulation_quality/event_type_coverage.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
- stored_artifacts/TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION/ (where this staleness
  was most recently re-confirmed and deferred, with reasoning for the deferral)

## Related Code Areas
- src/observability/event_shapers.py (SHAPER_REGISTRY, per-domain shaper classes)
- src/observability/event_extractor.py (legacy flag-gated rollback loops)
- docs/simulation_quality/event_type_coverage.md

## Assumptions / Open Questions
- The exact naming convention for the corrected `source` column value (e.g. whether to name the
  specific shaper class, or a more general "event_shapers (push path)" label) is not pre-decided —
  Plan phase should pick something consistent with the doc's existing conventions.
- Whether every COMBAT/FACTION/QUEST/AGENCY row flagged by `TCK-20260807-QUEST-EVENT-PUSH-
  MIGRATION`'s own investigation is still stale today (vs. partially fixed since) is not verified
  here — Investigate must re-check current doc state, not assume the prior ticket's finding still
  holds unchanged.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS
phase: done
date: 2026-08-24
tags: [social, testing]
---

# TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS

## Title
Add Unit Test Coverage for check_nemesis_promotion()/tick_place_attachment()

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
A depth-audit of the Grief/Nemesis trigger idea found that check_nemesis_promotion()/tick_place_attachment() in src/systems/social_systems/memory.py have zero test coverage. The author's scoping intent (make reachable, measurable, tested) requires this pair to be given standalone unit tests, tracked separately since they are a completely unrelated code path from the Campaign-mode grief/nemesis work.

## Scope
- Add unit tests covering the branch conditions of check_nemesis_promotion() (src/systems/social_systems/memory.py)
- Add unit tests covering the branch conditions of tick_place_attachment() (src/systems/social_systems/memory.py)

## Out of Scope
- Any change to CampaignOrchestrator/GriefUrgencyImporter/NemesisRelationImporter reachability, event wiring, or in-episode triggering -- tracked separately as TCK-20260824-GRIEF-NEMESIS-REACHABILITY; confirmed completely unrelated code path

## Acceptance Criteria
- [x] check_nemesis_promotion() has unit tests covering each of its branch conditions
- [x] tick_place_attachment() has unit tests covering each of its branch conditions

## Related Tickets
- TCK-20260824-GRIEF-NEMESIS-REACHABILITY

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/memory.py

## Assumptions / Open Questions
- Independent of TCK-20260824-GRIEF-NEMESIS-REACHABILITY (C9a) -- testing these orphaned functions doesn't unblock or interact with the Campaign-mode work
- layer set to `systems` (src/systems/social_systems/memory.py) since no dedicated `social` layer is registered in registries/layer_registry.jsonl; `systems` is the closest registered fit for this file's location.

## Implementation Notes
Implemented plan.md Steps 1-3 exactly, as a pure test addition. No `src/` file was touched —
`src/systems/social_systems/memory.py:12-52` was read and confirmed byte-for-byte consistent with
the plan's and investigation's line-by-line branch description before writing any test (both
`if not region_id:` guards, the `0.001` increment, the `3.0`/`>=` threshold, and the `not in
nemesis_ids` compound condition all match exactly what plan.md/investigation.md described — no
plan inaccuracy or production bug found).

Created `tests/unit/social/test_social_memory_service.py` (new file) with 13 tests:
- 6 for `tick_place_attachment()`: explicit region_id (skips validation entirely, tested against an
  empty `state.regions`), auto-detect via containing region bounds, no-match returns `None`,
  no-regions-at-all returns `None`, inclusive boundary-edge match (`ex == xmax`), and the
  `region_id=""` truthy-falsy pin (falls back to auto-detect, matching `region_id=None` — confirmed
  as pre-existing behavior being pinned, not changed).
- 6 for `check_nemesis_promotion()`: empty grudge_history, below-threshold entry, already-nemesis
  exclusion, qualifying promotion, exact `3.0` threshold boundary, and a 3-entry mixed case
  asserting the exact list `[103]` (not set membership) to pin both per-entry filtering and
  `grudge_history` iteration-order determinism.
- 1 optional architecture-guard test (`test_social_memory_service_functions_are_pure_and_do_not_mutate_entity`)
  calling both functions against one entity/state pair with real work to do for each, then asserting
  `entity == entity_before` and `state == state_before`. This is a machine-verified check of the
  project's "decision logic reads state, does not mutate it" rule for this file; it passes
  structurally because `EntityState`/`AuthoritativeState` are frozen dataclasses, so it required no
  source change to satisfy.

`docs/parity_ledger/social_narrative.yaml` (SOC-050/SOC-066, both P0 with `test_path: null`) was
deliberately left untouched, per plan.md Step 4's explicit decision: SOC-050's legacy wording
("PlaceAttachment... supports sentiment") and SOC-066's ("Nemesis milestone creation") both use
terminology absent from the current V2 shape (`SocialComponent.place_attachment: Dict[str, float]`
has no `sentiment` field; "milestone" appears nowhere in `memory.py`/`updates.py`/`models/social.py`).
Pointing `test_path` at the new file would overstate parity evidence for those specific
legacy-checklist claims. The P0/`test_path: null` gap on both entries remains open and is
recommended as a separate follow-up ticket scoped to resolving the ambiguous legacy-to-V2 mapping.
No other `docs/` file required a change (investigation.md confirmed no `docs/mechanics/` chapter
documents the "PH4 Law" place-attachment/nemesis-promotion mechanics by name — a pre-existing,
independent documentation gap, not something this test-only ticket introduces or is scoped to fix).

## Test Summary
Command: `pytest tests/unit/social/test_social_memory_service.py -v`
Result: 13 passed, 0 failed, 0 skipped (0.27s).

Tests added (13 total, all new):
- `test_tick_place_attachment_uses_explicit_region_id`
- `test_tick_place_attachment_auto_detects_containing_region`
- `test_tick_place_attachment_returns_none_when_no_region_contains_position`
- `test_tick_place_attachment_returns_none_when_no_regions_exist`
- `test_tick_place_attachment_boundary_position_matches_region_edge`
- `test_tick_place_attachment_empty_string_region_id_falls_back_to_auto_detect`
- `test_check_nemesis_promotion_empty_grudge_history_returns_none`
- `test_check_nemesis_promotion_below_threshold_not_promoted`
- `test_check_nemesis_promotion_already_nemesis_not_repromoted`
- `test_check_nemesis_promotion_qualifying_entry_promoted`
- `test_check_nemesis_promotion_exact_threshold_boundary_promoted`
- `test_check_nemesis_promotion_mixed_entries_only_new_qualifying_promoted`
- `test_social_memory_service_functions_are_pure_and_do_not_mutate_entity`

No existing test was modified. This was run as an informal pre-check by the implementer; the formal
Test phase runs separately per the pipeline.

## Files Changed
- `tests/unit/social/test_social_memory_service.py` (new file)
- `staging_artifacts/TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS/investigation.md` (no substantive rewrite
  needed — read and confirmed accurate, not modified)
- `staging_artifacts/TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS/plan.md` (Deviations section appended)
- `tickets/inprogress/TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS.md` (this ticket: Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

No `src/` file was changed. `docs/parity_ledger/social_narrative.yaml` and all other `docs/` files
were left untouched, per plan.md Step 4's explicit decision (see Implementation Notes above).

## Completion Summary
Added standalone unit test coverage (13 tests) for `SocialMemoryService.tick_place_attachment()`
and `.check_nemesis_promotion()` (`src/systems/social_systems/memory.py`), which previously had zero
test coverage. Both acceptance criteria are met: each distinct branch condition of both functions
(explicit vs. auto-detected region_id, boundary-inclusive region match, no-match/no-regions paths,
grudge-threshold promotion/exclusion/boundary, and mixed-entry filtering with exact-order assertion)
is covered by a dedicated test, plus an optional architecture-guard test confirming neither function
mutates its inputs. No `src/` logic was changed — both functions are confirmed dead code today
(unreachable outside direct unit-test invocation) and this ticket does not alter that. No docs or
parity ledger entries were changed; the pre-existing P0/`test_path: null` gap on
`docs/parity_ledger/social_narrative.yaml` SOC-050/SOC-066 is explicitly left open with reasoning
recorded above, and recommended as separate follow-up work. Sibling ticket
TCK-20260824-GRIEF-NEMESIS-REACHABILITY is confirmed fully unrelated (different code path,
Campaign-mode grief/nemesis event wiring).

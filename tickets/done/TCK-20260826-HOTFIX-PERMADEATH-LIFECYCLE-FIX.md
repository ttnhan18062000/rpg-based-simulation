---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX
phase: done
date: 2026-08-26
tags: [content]
---

# TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX

## Title
Generation-4+ Hero "permadeath" doesn't actually deactivate the entity

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found and confirmed during `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s "Known open
items" review: `src/engine/combat.py` sets `outcome_kind="PERMADEATH"` when a rebirth-eligible
target (a Hero) dies at `generation >= 4` (no more rebirth generations available) -- the most final
death outcome the engine has. But `LifecycleSystem.resolve_lifecycle()`
(`src/systems/lifecycle_systems/lifecycle.py:43`) only checked
`ent_upd.combat.outcome_kind == "KILL"`, never `"PERMADEATH"`. A "permanently dead" Hero therefore
never actually got `lifecycle.active` flipped to `False` -- it stayed active and kept acting in
the simulation despite being narratively permanently dead. Confirmed by direct source read before
any change (not assumed from the roadmap doc's own description).

## Scope
- `src/systems/lifecycle_systems/lifecycle.py`: route `outcome_kind in ("KILL", "PERMADEATH")`
  through the identical deactivation/`death_reason="COMBAT"` path, instead of `== "KILL"` alone.
- Confirm (read, not assume) that `docs/parity_ledger/combat_movement.yaml` COMB-309's own
  `death_reason=="COMBAT"` event-crediting fallback gate correctly picks up PERMADEATH deaths once
  this fix lands, with no separate change needed to that gate.
- Confirm (read, not assume) whether `src/observability/event_shapers.py::CombatShaper`'s own
  `outcome_kind=="KILL"`-only ownership boundary needs a matching change, or whether it's a
  correct, unrelated boundary that PERMADEATH deaths should fall through past (into the COMB-309
  fallback path) rather than be owned by.
- New regression test.
- Add a parity ledger entry for this fix.

## Out of Scope
- Any change to `CombatShaper`'s own `outcome_kind=="KILL"` check -- confirmed during Implement
  that PERMADEATH deaths correctly fall through to the COMB-309 fallback crediting path instead
  (not "shaper-owned"), so no change needed there.
- Any change to `combat.py`'s own PERMADEATH-assignment logic -- already correct, this ticket only
  fixes the downstream consumer that failed to recognize the outcome.

## Acceptance Criteria
- [x] `LifecycleSystem.resolve_lifecycle()` deactivates an entity on both `"KILL"` and
      `"PERMADEATH"` outcome_kind
- [x] New regression test (`test_permadeath_death_classification`) covers this directly, mirroring
      the existing `test_combat_death_classification` KILL test
- [x] Confirmed via direct source read that COMB-309's fallback event-crediting gate and
      `CombatShaper`'s ownership boundary both behave correctly with no further change needed
- [x] Full `tests/unit/combat/`, `tests/unit/progression/`, `tests/unit/observability/` suites
      still pass
- [x] Parity ledger entry added

## Related Tickets
None -- flagged directly in `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s "Known open
items" section as a real bug independent of any of the 65 roadmap design ideas, with no prior
ticket.

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_design_roadmap.md (source of this finding)
- docs/parity_ledger/combat_movement.yaml (COMB-309, COMB-311 -- new entry this ticket adds)

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py
- src/engine/combat.py (read-only reference, confirmed correct, not modified)
- src/observability/event_extractor.py (read-only reference, confirmed correct, not modified)
- src/observability/event_shapers.py (read-only reference, confirmed correct, not modified)

## Assumptions / Open Questions
None.

## Implementation Notes
Traced the full downstream consequence chain before implementing, not just the direct fix: with
`death_reason="COMBAT"` now correctly set for PERMADEATH deaths, `event_extractor.py`'s COMB-309
fallback (`death_reason=="COMBAT"` gate, added specifically to filter non-combat mortality out of
`combat_kill`/`entity_killed` SimQ events) now correctly credits genuine PERMADEATH kills too --
previously these deaths generated zero SimQ combat credit at all, since the entity never
deactivated in the first place. `CombatShaper`'s own live `outcome_kind=="KILL"`-only check
(`src/observability/event_shapers.py`) was deliberately left unchanged after confirming PERMADEATH
deaths are not meant to be "shaper-owned" -- `event_extractor.py`'s `is_shaper_owned_kill` check
only matches literal `"KILL"`, so PERMADEATH deaths correctly fall through to the COMB-309 fallback
path for crediting either way, with or without push-shapers active.

## Test Summary
`tests/unit/progression/test_lifecycle.py` -- 6/6 passing (5 pre-existing + 1 new,
`test_permadeath_death_classification`). Broader sweep:
`tests/unit/combat/ tests/unit/progression/ tests/unit/observability/` -- 1183 passed, 1 skipped
(pre-existing, unrelated), 1 warning (pre-existing, unrelated).

## Files Changed
- src/systems/lifecycle_systems/lifecycle.py
- tests/unit/progression/test_lifecycle.py
- docs/parity_ledger/combat_movement.yaml (COMB-311 added)

## Completion Summary
A confirmed, real, gameplay-visible bug is fixed: a Hero that dies for the final time (no rebirths
left) now actually stops acting in the simulation, matching the narrative "permanently dead"
outcome. Traced and confirmed the full downstream event/reward-crediting chain rather than fixing
only the direct symptom.

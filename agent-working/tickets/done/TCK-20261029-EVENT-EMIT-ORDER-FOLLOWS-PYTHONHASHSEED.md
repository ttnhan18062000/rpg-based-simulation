---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED
phase: done
date: 2026-10-29
tags: [determinism, observability]
---

# TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED

## Title
Within one tick, the emit order of progression and equipment events follows the process hash seed. Sort at the emit loops.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
codebase-implementer found this during codebase M7 batch 2 characterization, and codebase-planner checked it against the source. rpg-planner-ubuntu re-verified it on main 33da13604 and widened it.

Several emit loops iterate a Python `set` of strings or of `EquipSlot` enums. An Enum hashes by its name string. String hashes are randomized per process by `PYTHONHASHSEED`. So when one entity gets two or more IDs of the same kind in one tick, the order of those events differs between processes on the same world and seed.

Harness and gate runs pin `PYTHONHASHSEED=0`, and are reproducible:
- `tools/rpg_measure/paired.py:102`
- `tools/test_architecture/rpg_gate_harness.py:158`
- `tools/perf/rerun_baselines.py:403`

Unpinned CLI and server runs are not reproducible.

rpg-planner ruled on 2026-10-29 that the work splits in two. The ruling is in `agent-working/staging_artifacts/TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md`. This ticket is (A), the event side only. The state side is TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (B).

## Scope
Sort at emission, with a stable key: the enum `.value` or the string ID itself, never `str(obj)`. These are the sites on 33da13604:
1. `src/observability/event_extractor.py:351`. It iterates `set(eq_slots) | set(prior_eq_slots)` and emits `item_equipped`/`item_unequipped`. Use `sorted(..., key=lambda s: s.value)`. The block is not flag-gated.
2. `src/observability/event_extractor.py:379`. It iterates `set(eq_dur) | set(prior_eq_dur)` and emits `equipment_durability_changed`. Use the same key. Verify that the durability keys are `EquipSlot`; `src/core/equipment.py:260` uses `durability.get(slot, ...)`. If any key is a plain string, use a key that handles both and say so.
3. `src/observability/event_extractor.py:1163` (`skill_unlocked`), `:1173` (`trait_expressed`) and `:1183` (`pillar_trait_unlocked`). These are set differences on the rollback path (`ENABLE_PUSH_EVENT_SHAPERS_PHASE2` OFF). Use `sorted(...)` with an explicit stable key for the element type: the id, or `.value` for an Enum. Don't rely on the natural ordering of mixed or Enum types. The test asserts the element type (rpg-planner ruling 2).
4. `src/observability/event_shapers.py`, `ProgressionShaper` (around line 1031-1050), on the default path. It iterates `id_upd.learned_skills`, `traits_add` and `breakthroughs_add` in list order. Use `sorted(...)`.
   - Those lists come from `list(set(...))` in `src/core/updates.py:276-281` and `src/engine/evolution.py:120`, so their order follows the hash seed.
   - Sorting here makes emission independent of the producers' order.
5. Sweep `src/observability/event_extractor.py` and `src/observability/event_shapers.py` for any other emit loop over a `set`/`frozenset`, or over a list built from one. List each one in the ticket.
   - Fix it here only if it is emission-only.
   - Report anything that reaches state, rather than fixing it.
   - Dict iteration is insertion-ordered and out of scope.

`src/engine/evolution.py:120` is **not edited** in this ticket. Its list goes into `IdentityUpdate.learned_skills`. The apply path folds that list into a set (`src/engine/patches.py:230`, `sk |= set(u_id.learned_skills)`), and state holds `learned_skills: Set[str]` (`src/core/state.py:646`). So its order reaches nothing but emission, and step 4 covers that. rpg-planner accepted this reasoning (ruling 2). Record it in Implementation Notes.

## Out of Scope
- Any state-side ordering: `IdentityUpdate.merge` in `src/core/updates.py`, `src/domains/combat_engagement/learning.py:45`, and set iteration in decision code. All of that is ticket (B).
- Event shape or payload changes.
- Pinning `PYTHONHASHSEED` in non-harness entry points.
- codebase M7's split of `event_extractor.py`. M7 holds its golden fixtures until this ticket lands. Coordinate the merge order through rpg-planner-ubuntu.

## Acceptance Criteria
1. Each site in Scope 1-4 iterates in a sorted, stable-key order. Any extra Scope 5 site is listed with its disposition.
2. Unit tests that are deterministic in-process:
   - With PHASE2 ON, one entity whose update carries `learned_skills`, `traits_add` and `breakthroughs_add` with 3 or more IDs each, in non-sorted list order, emits them in sorted order.
   - The same holds on the rollback path, with PHASE2 OFF and prior/current state sets.
   - Two or more equipment slots changing in one tick emit in `EquipSlot.value` order, for both the equip and the durability loops.
3. A cross-process test runs a fixed short run twice in subprocesses, at `PYTHONHASHSEED=0` and at one other value, and asserts that the event streams are identical.
   - It needs a positive control: show that the same comparison fails on main before the fix, or uses a fixture where two or more IDs land in one tick.
   - If no world and tick count makes two or more land in a short run, drive it from a constructed state, and say so.
4. The final STATE hash at `PYTHONHASHSEED=0` is unchanged against main on one short run (world, seed and ticks recorded). Only event order moves. If the hash changes, STOP and report to rpg-planner.
5. Scoped tests pass:
   - `tests/unit/observability/`
   - the extractor and shaper tests
   - `pytest -m "not slow"` on the touched areas.
   Also run `generate_registry --check` and paths-guard before the push ask.
6. The Completion Summary carries the step-5 sweep report: what was fixed and what was only reported. Reported items are appended to (B)'s audit list.

## Related Tickets
- TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (B, state side)
- TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION (introduced ProgressionShaper)
- TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP (introduced the equipment loops)
- codebase M7 batch 2 (event_extractor split; waits on this ticket for its goldens)

## Related Docs
- `docs/engine/kernel.md` (determinism)
- `docs/guidelines/intentional_divergences.md`: no entry expected, since event order is not a Bible law. If rpg-planner says otherwise, use the ubuntu id block 2.144-2.149.

## Related Stored Artifacts
- `agent-working/staging_artifacts/TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md`

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/observability/event_shapers.py`
- tests under `tests/unit/observability/`

## Assumptions / Open Questions
- Assumed: no consumer depends on the current within-tick order of these events. SimQ scorers count by type. Check by grepping the readers of the event streams in `src/` and `frontend/`.
- rpg-planner OK'd the plan on 2026-10-29 (ruling 2, recorded in the ruling file). Dispatch is under S4 (#715 6473439661), after #784's main merge.

- Regression test handoff: codebase-implementer wrote `tests/unit/observability/test_event_extractor_equipment_multislot.py` (4-slot equip; equip+swap+unequip; 4-slot durability). With default flags it shows 4 different emit orders at PYTHONHASHSEED 0-3: LEGS,HEAD,TORSO,MAIN_HAND / LEGS,HEAD,MAIN_HAND,TORSO / LEGS,MAIN_HAND,TORSO,HEAD / TORSO,HEAD,LEGS,MAIN_HAND. codebase-planner is handing it over as a local commit SHA. This ticket adopts it, asserting sorted `EquipSlot.value` order, and uses it as AC3's positive control. M7 batch 2 drops its copy once this lands.

## Implementation Notes
- Sort keys: equipment slots use `getattr(s, "value", s)` (the `EquipSlot.value`; the fallback is there because `TestCapabilityGrowthStalled` feeds plain-string slot keys that hit the loop head before the `new == old` skip, so `s.value` alone raised on a str; production keys are `EquipSlot`). Ids (skills, traits, breakthroughs, recipes, entity ids) use `key=lambda _id: _id`, with the element type asserted in the new tests (str for ids, int for entity ids).
- `src/engine/evolution.py:120` is NOT edited (rpg-planner ruling 2): its list goes into `IdentityUpdate.learned_skills`, which the apply path folds into a set (`src/engine/patches.py:230`) held as `Set[str]` in state, so its order reaches nothing but emission, and the ProgressionShaper sort covers that.
- Readers: SimQ scorers (`src/simulation_quality/scorers/progression.py`, `world_dynamics.py`) and `src/domains/campaigns/*` name these event types; I read them as counting by type and did not trace each campaign reader for order dependence.

## Test Summary
- `tests/unit/observability` with `-m "not slow"`: 1207 passed, 1 skipped, 1 deselected (serial, MemoryMax=3G). `tests/tools/test_agent_working_paths_guard.py`: 11 passed. `generate_registry --check`: in sync (3800 entries).
- New `tests/unit/observability/test_event_emit_order.py` (5 tests: ProgressionShaper, rollback path, recipe_learned, demographic_mortality, cross-process at PYTHONHASHSEED 0-3 with a raw-set-order positive control) plus the adopted `test_event_extractor_equipment_multislot.py` now asserting emit order.
- Positive control: with `src/` reverted to main, the same 8 tests fail at every seed (8, 7, 7, 6 failed at seeds 0-3); with the fix they pass at every seed.
- AC4 hash check: `frontier_living_world`, seed 0, 150 ticks, `PYTHONHASHSEED=0`, flags `no_frame_pacing` + `audit_mode`, via `tests.helpers.scenario.run_scenario`: state hash `0ea7a9a776bbadb99b819a9abf3f1fb1d225c693aa3782307722bae4dc146b1a` on both fixed and main, two runs each (4 runs identical). A first probe without `audit_mode` was non-deterministic run to run on main itself (two main runs differed), so it was discarded as an invalid instrument.

## Files Changed
- `src/observability/event_extractor.py`, `src/observability/event_shapers.py`
- `tests/unit/observability/test_event_emit_order.py` (new), `tests/unit/observability/test_event_extractor_equipment_multislot.py` (cherry-picked 06258c619, then order assertions)

## Completion Summary
Fixed (emission-only): extractor `item_equipped`/`item_unequipped` and `equipment_durability_changed` (slot order), rollback-path `skill_unlocked`/`trait_expressed`/`pillar_trait_unlocked`; ProgressionShaper `learned_skills`/`traits_add`/`breakthroughs_add`.
Scope 5 sweep, also fixed (emission-only): extractor `recipe_learned` (`new_recipes - prior_recipes` set difference) and `WorldDynamicsShaper` `demographic_mortality` (`entities_remove` is `list(set)` from `StateUpdate.merge`).
Swept and left: `territory_add` loops (a tuple built by `military_conflict.py:284`, one id; not set-derived), `contracts_remove`/`leads_remove`/`projects_remove`/`concerns_remove` (concatenated lists, not set-derived; used for dict pops or existence checks), `removed = set(entities_remove)` at shapers:1402 (membership test only).
Reported to (B), not fixed (reach state): `IdentityUpdate.merge` `list(set(...))` for `recipes_learned`, `breakthroughs_add`, `learned_skills`, `traits_add`, `traits_remove` (`src/core/updates.py:269-281`) and `modifiers_add`/`modifiers_remove` (`:882-883`); `src/engine/evolution.py:120`.

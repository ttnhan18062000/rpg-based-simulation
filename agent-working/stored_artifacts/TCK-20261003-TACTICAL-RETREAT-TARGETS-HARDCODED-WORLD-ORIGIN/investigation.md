---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN
artifact_type: investigation
tags: [combat, world, root-cause]
---

# Investigation: tactical retreat and wander targets hardcoded to the world origin

## Context scan

`search_docs` (tactical retreat targets, region lookup) then `graphify query` (the worktree has no
`graphify-out/`, so the main checkout's graph was used, and returned only noise for "target"). Code
reads followed. The semantics are not an open question: the rule owner's 2026-10-03 ruling in the
ticket (`MOV-01`, `LOC-01`, `LOC-03`, `MOV-03`) fixes the derivation, so this ticket implements it.

## Findings

1. **There are four `(0.0, 0.0)` branches in `src/engine/tactical.py`, not the three the ticket lists.**
   The ticket's table covers the `emotion.is_fleeing` gate, `SAFETY_PRESSURE_RETREAT` and the
   `STALEMATE_BREAK` wander. A fourth, in the low-HP engaged branch (`hp_percent < 0.15`, comment "Simple
   fallback to origin for now"), carries the **same** `PANIC_RETREAT` reason tag. It is the same defect in
   the same file with the same ruling applying, so it is fixed here and recorded; the ticket's table is
   corrected in Implementation Notes.
2. `RegionService.find_region_at` (`src/world/regions.py`) falls back to the **nearest region centre**
   when no region's bounds contain the point, so it can never answer "outside every region". The new
   `containing_region` uses strict bounds only and iterates regions in sorted id order.
3. `is_fleeing` (`AuthoritativeState`-independent, `src/engine/cognition.py:142`) can trip with **no hostile
   present** (low HP or regional trauma alone). The PANIC branch therefore derives its threat list with the
   same predicate the appraisal used (`are_entities_hostile`, same `RelationContext`) and, with none, has no
   away-vector: it falls to home region, then holds.
4. `tactical.py` used no RNG. `src/platform/rng.py::DeterministicRNG.get_float(domain, tick, entity_id,
   sub_id)` is stateless and order-independent; `Domain.TACTICAL` exists and was unused. `state.seed` is the
   base seed.
5. Existing tests that pinned the literal: `test_anti_stalemate.py::test_stalemate_break` and
   `test_engagement_behavior.py::test_retreat_behavior`, both on region-less states. Updated.
   `test_pressure_perception_consumers.py::test_safety_pressure_above_threshold_triggers_retreat` still
   passes unchanged (region-less state, so the entity holds); a region-bearing sibling was added.
6. `src/world/raid.py:36` has a comment citing `tactical.py:141` PANIC_RETREAT overwriting a raider's
   target. The raid is retired (§2.64), so the stale line number is left alone.
7. `docs/engine/contracts/tactical_contract.md` §4/§5 described the Safe Zone `(0,0)`; updated.

## Not measured

AC-1's corpus firing-rate counts per branch and entity kind. The ticket's own downgrade note (2026-10-03)
lets the fix proceed on a constructed-scenario instrument, with corpus counts as order-of-magnitude
after-evidence only, because the tactical-path nondeterminism ticket (batch item d) is unresolved.

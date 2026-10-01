---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine]
---

# TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE

## Title
A `DEFEAT` / `REBIRTH` outcome, classified non-lethal, is silently converted into a permanent death by
`apply.py`'s passive HP gate one tick later

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Accepted world rule `docs/world_rules/life-body/lifecycle.md` **LIFE-02** (Disposition: ACCEPT) says that
losing active-participant status "does not, by itself, entail permanent lifecycle termination", and names
`DEFEAT` (non-lethal; `combat.py:136` forces `is_lethal=False` for `EntityRole.HERO`) and `REBIRTH`
(`generation_delta=1`, identity continues) as non-lethal outcomes; only `PERMADEATH` is final.

In the code, a HERO defeated to 0 HP gets `alive_set=False` and keeps `lifecycle.active=True`. Nothing in
`src/` ever sets `combat.alive=True` again (every `alive=True` is construction). One tick later
`ApplyPath._compute_entity_changes` (`src/engine/apply.py:106-109`) computes
`active=(new_hp > 0 and ...)` for the 0-HP entity and deactivates it, with no `death_reason`. So a
non-lethal outcome becomes a silent permanent death, and `REBIRTH` increments `generation` on an entity
that is then deactivated rather than reborn. This is the opposite error from the hazard route (a death
not recorded as one) fixed by `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`.

Production evidence (`frontier_marches`, seed 42, 120 ticks, `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK`):
`DEFEAT` at ticks 20/68/113/115, `REBIRTH` at tick 88; the leftover entities remain combat-dead and
unrecorded (`tests/mechanic_scenarios/test_entity_death_authority_boundary.py`, corpus test).

## Scope
- Decide the intended lifecycle of a defeated / reborn HERO (downed-and-recoverable, revived on rebirth,
  or something else) against LIFE-02 and `docs/mechanics/02_combat_laws.md` (Rebirth).
- Make `apply.py`'s passive HP gate and the combat outcome agree with that decision.
- Own the HERO population end to end: the passive biological-death scan deliberately excludes
  `EntityRole.HERO` (cause not persisted), so a genuinely starving HERO is currently unrecorded.
- Rewrite the corpus test's "DEFEAT/REBIRTH leftovers remain unrecorded" assertion to the new contract.

## Out of Scope
- The hazard route and the passive bio-death scan for non-HEROes (done in
  `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`).
- The hazard-overwrites-KILL defect (`TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND`).

## Acceptance Criteria
1. A `DEFEAT` outcome on a HERO does not end in a permanent, unrecorded deactivation.
2. A `REBIRTH` outcome yields an entity that is actually reborn (or the rule is amended by its owner).
3. A HERO starving to death is recorded with a real `death_reason`, distinguishable from a defeat.
4. Any behaviour change that departs from `docs/mechanics/02_combat_laws.md` is recorded in
   `docs/guidelines/intentional_divergences.md`; LIFE-02's evidence note is updated by its owner.

## Related Tickets
- `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`
- `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK`

## Related Docs
- `docs/world_rules/life-body/lifecycle.md` (LIFE-02, scenario LB-S02)
- `docs/mechanics/02_combat_laws.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/investigation.md`

## Related Code Areas
- `src/engine/apply.py:94-110`, `src/engine/combat.py:136,182-187`, `src/engine/combat_rewards.py:106`,
  `src/systems/lifecycle_systems/lifecycle.py`

## Assumptions / Open Questions
- Which of "downed", "revived" or "dead" is intended for a defeated HERO is a planner / rule-owner decision.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._

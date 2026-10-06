---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-LAW-OCCUPANCY-COLLISION-HARD-LAW-ERRORS-ON-MAIN
phase: done
date: 2026-10-05
tags: [engine, determinism]
---

# TCK-20261005-LAW-OCCUPANCY-COLLISION-HARD-LAW-ERRORS-ON-MAIN

## Title
Ten `LAW-OCCUPANCY-COLLISION` hard-law errors fire on untouched `origin/main` on
`frontier_living_world` — four entities occupying one tile, a hard-law violation nothing currently owns

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Reported by `rpg-implementer` while re-measuring the attack-path ticket, and filed by the planner because
it is a hard-law violation unrelated to that ticket.

**Observed on BOTH trees, so it is pre-existing on `main`.** The implementer ran its `brain_adj` probe on
a clean `origin/main` control worktree and on its own fix branch; both printed **10
`LAW-OCCUPANCY-COLLISION` hard-law errors** on `frontier_living_world`, naming **entity 18 against
entities 53, 55 and 57 on tile (87,50)**. The fix branch does not cause it and does not change the count.

**Why P1.** This is a **hard law**, not a soft guard or an advisory. Four entities resolving onto one tile
means either the occupancy invariant is not enforced on some write path, or the law's own detection is
firing on a state that is legal and the law is wrong. Either way one of the two is incorrect, and the
engine is reporting a law violation on the corpus's main world on every run. A hard law that fires
routinely on `main` trains every session to ignore it, which is the same failure mode as the slow-regression
gate that silently stopped running.

**Why nobody has filed it.** The probe that surfaced it was written for a different question, and
`main`-red findings have been systematically under-reported — the `Slow regression` job's only test step
was skipped in 35 of the last 40 `main` pushes
(`TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN`). This is plausibly one more thing
that gate would have caught.

**Not established:** whether tile (87,50) is special (it sits inside the `bandit_road` / `wolf_den` /
`near_forest` contested area — see the overlap work), whether the collision is transient within a tick or
persists, and whether entity 18's write path differs from 53/55/57's. All of that is scope 1.

## Scope
1. **Reproduce on untouched `origin/main`** and record: the tick each error fires, whether the collision
   persists across ticks or is resolved within the same tick, the movement mode and task of each of the
   four entities, and which write path placed each one.
2. **Determine which of the two is wrong** — the invariant's enforcement or the law's detection. State it
   explicitly; do not fix before answering, because the two fixes are opposite.
3. **Check whether tile (87,50) is incidental.** It falls inside the `bandit_road` ∩ `wolf_den` ∩
   `near_forest` contested region area on `frontier_living_world`. If region resolution is involved, this
   interacts with `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` and the planner must be told
   before either is implemented. If it is incidental, say so and close that thread.
4. **Measure on other corpus worlds.** Ten errors on one world may be ten on all, or specific to this
   world's content.
5. Fix whichever side scope 2 identifies, with a disabling-control test, and record the divergence if the
   law's own semantics change.

## Out of Scope
- The attack-path ticket and its fix. This predates it and must not widen it.
- `src/engine/scheduler.py` — CONTESTED, not granted.
- Suppressing, downgrading or filtering the error output. **If the law is right, the state is wrong; if
  the law is wrong, fix the law.** Silencing it is not an option — see the repo rule on never editing an
  artifact to make a gate pass.

## Acceptance Criteria
- [x] Reproduced on untouched `origin/main` with per-tick detail for all four entities.
- [x] A stated verdict on whether enforcement or detection is at fault, with the evidence.
- [x] Tile (87,50)'s relationship to the contested region area answered either way.
- [x] Other corpus worlds measured.
- [x] Fix applied to the correct side, with a disabling control, or a recorded explanation if the correct
      outcome is to change the law.
- [x] `docs/engine/` and `docs/parity_ledger/` updated if law semantics change.

## Related Tickets
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` — the ticket whose
  probe surfaced it; **not the cause**.
- `TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN` — why a `main`-red hard-law error
  went unnoticed.
- `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` — possible interaction via tile (87,50).

## Related Docs
- `docs/engine/kernel.md` and `docs/engine/authoritative_mutation_pipeline_contract.md` — the occupancy
  invariant and the apply-path law.
- `docs/engine/project_lawbook_m10.md` — the hard-law index, for `LAW-OCCUPANCY-COLLISION`'s own definition.

## Related Stored Artifacts
- The attack-path ticket's `probes/` — `brain_adj` is the probe that printed the errors.

## Related Code Areas
- The occupancy law's definition and its check site.
- The movement apply path in `src/engine/pipeline_phases/movement.py`.
- `src/engine/legality.py` — occupancy/blocking checks at decision time, which may disagree with the
  apply-time law in the same way the hostility predicates do.

## Assumptions / Open Questions
- **Lane.** Lane A (engine movement/apply path), after its current batch. Not urgent enough to pre-empt
  the attack PR.
- Open: is this the same class of defect as the hostility-predicate split — a decision-time check and an
  apply-time law disagreeing? Worth checking first, since that pattern has now appeared twice.

## Implementation Notes
Verdict: ENFORCEMENT is at fault, the law is right. `spawn_monster` placed spawns at a fixed tile without checking occupancy; the hypothesis held (entity 52 spawned onto (110,38) at t300 while entity 22 held it, collision t301), so the ticket moved to Lane B and landed with the spawn-faction ticket (restoring the faction makes spawns survive: 2 -> 837 collisions). Fix: `EntityGenerator.free_spawn_position`: nearest tile with no live entity or same-tick spawn within one tile, deterministic, radius 5, raises when none. A placement policy that avoids the same-tick spawn/move race, not a change to movement/spawn ordering. Tile (87,50) is incidental (the orc respawn tile, not region overlap). Other worlds: 24 measured, 0 collisions after. Detail: the spawn ticket's `investigation.md`.

## Test Summary
`tests/unit/world/test_spawn_monster_catalog_faction.py` placement tests (occupied tile, same-tick, free tile kept, loud failure). 0 `LAW-OCCUPANCY-COLLISION` in all 24 worlds, 10,000 ticks, audit_mode, seed 42.

## Files Changed
`src/systems/world_systems/generator.py`; `tests/unit/world/test_spawn_monster_catalog_faction.py`. No law semantics changed, so `docs/engine/` is unchanged.

## Completion Summary
Closed with TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER (one function, one PR).

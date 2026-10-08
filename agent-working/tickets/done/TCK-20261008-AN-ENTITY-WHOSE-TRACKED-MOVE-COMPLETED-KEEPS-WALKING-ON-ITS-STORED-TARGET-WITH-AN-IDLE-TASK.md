---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-AN-ENTITY-WHOSE-TRACKED-MOVE-COMPLETED-KEEPS-WALKING-ON-ITS-STORED-TARGET-WITH-AN-IDLE-TASK
phase: done
date: 2026-10-08
tags: [combat]
---

# TCK-20261008-AN-ENTITY-WHOSE-TRACKED-MOVE-COMPLETED-KEEPS-WALKING-ON-ITS-STORED-TARGET-WITH-AN-IDLE-TASK

## Title
An entity whose tracked move completed keeps walking on its stored target with an idle task, and a held move beside an engaged hostile stands frozen: CONFLICT-04 at the movement layer

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Lane A's opportunity-attack classification (pinned, seeds 42-46 x 3 worlds, `d671868bb`) found that most free hits were not decisions: an idle `ENTITY_ACT` (empty payload) walking on a stored target (74.2 / 56.4 / 39.0 hits per run) and held moves (102.4 / 92.6 / 40.6). The idle tasks come from completed tracked moves whose `target_clear` survives its tick; the strategic pass (`intelligence.py:665-667`, plus `:674`, group logic, the brain, the cooperation phase) writes a target again later. This ticket absorbs TCK-20261008-A-HELD-REGROUP-MOVE-WALKS-INTO-PERCEIVED-HOSTILES-AND-IS-NEVER-RE-DECIDED (REGROUP is one reason of the held class; investigated, see below).

## Scope
1. `hostility.py`: one perceived-hostile test shared by the tactical pass and the movement layer. 2. `MovementCandidateSelector.movement_target`/`select`: an entity with an engaged, perceived, hostile entity orthogonally adjacent takes no step from a stored target; a decision this tick (target + ENTITY_MOVE task update) moves it; a decided flight (PANIC_RETREAT, SAFETY_PRESSURE_RETREAT, LEASH_RETURN) is exempt. 3. `move_ends_here`: a blocked held move is released to the brain (idle task, target cleared) by both dispatchers. 4. Divergence 2.89, parity COMB-342, mechanisms notes (decision 32), the #424 5-seed report (2.83).

## Out of Scope
- The strategic-pass seeding (`intelligence.py:665-667`); the stale PURSUE movement-mode label (cosmetic). - Scheduler, kernel, governor, policy. - Any step beside a hostile that is not engaged: owner decision 32 ("notice and decide") is a separate feature ticket (TCK-20261008-A-SUBJECT-NOTICES-AN-UNENGAGED-HOSTILE-COMING-ADJACENT-AND-DECIDES-DECISION-32).

## Acceptance Criteria
- [x] Attribution with file and line (investigation.md). - [x] Unit tests, kernel scenario with a control arm, narrowed invariants (no step beside an engaged hostile without a decision; no blocked run beyond the brain cadence + 1 in the pinned run). - [x] Pinned 5x3 report main vs batch with OA classes, deaths by class, alive at t=1000/1100, resolve_move, stall split, two-run digests. - [x] REGROUP closed as investigated. - [x] Gates (mypy, ratchet, lint-imports 17/0, mechanism pin 313 files / 232 unbound).

## Related Tickets
- TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04 (#439). - TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP (2.84, #429). - Absorbed: TCK-20261008-A-HELD-REGROUP-MOVE-WALKS-INTO-PERCEIVED-HOSTILES-AND-IS-NEVER-RE-DECIDED (investigated: REGROUP-last-hit deaths on `frontier_living_world` 13.1 percent before, 5.0 after, under the 15 percent line; on `urban_political` an intermediate arm read 16.4 percent (18/110), an observation with high variance, no action). - TCK-20261008-CHOKEPOINT-HOLD-HAS-NO-ROUTER-HANDLER-AND-ENDS-AS-UNSUPPORTED-ACTION (same PR).

## Related Docs
- `docs/world_rules/capability-progression/conflict-combat.md` (CONFLICT-04, decision 32), `docs/mechanics/02_combat_laws.md` section 7, `docs/engine/contracts/tactical_contract.md`, `docs/guidelines/intentional_divergences.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-AN-ENTITY-WHOSE-TRACKED-MOVE-COMPLETED-KEEPS-WALKING-ON-ITS-STORED-TARGET-WITH-AN-IDLE-TASK/` (investigation.md, plan.md, test_plan.md, probes/)

## Related Code Areas
- `src/engine/candidate_selector.py`, `src/engine/hostility.py`, `src/engine/executor.py`, `src/engine/worker_logic.py`, `src/engine/domain/action_router.py`, `src/engine/pipeline_phases/actions.py`

## Assumptions / Open Questions
- Unattributed resets: 1 of 13 (urban seed 45) and 2 of 3 (living_world seed 42) re-seeded targets were not attributed to a writer; the movement-layer rule covers them regardless of writer.
- Idle tasks beside an engaged hostile can stay blocked up to 19 / 18 / 14 consecutive ticks in the pinned 5x3 (the brain cadence is 10); the invariant test passes on urban seed 45 at 600 ticks (longest 11). Reported to rpg-planner.
- A bare navigation update (no ENTITY_MOVE task update) beside an engaged hostile is not a decision, so hazard-style walkers without a task update are blocked there; none observed.

## Implementation Notes
See the investigation and plan in the stored artifacts.

## Test Summary
New unit file `tests/unit/engine/test_engaged_adjacent_hostile_takes_no_stored_step.py` (rule, flight exemption, release condition, the two dispatchers identical), `tests/mechanic_scenarios/test_conflict04_movement_layer.py` (scenario with control arm, two pinned-run invariants); two existing tests updated. 797 passed in the combat/engine/actions/scenario/pipeline/mechanism sweeps; mypy clean; ratchet OK; lint-imports 17 kept, 0 broken. Determinism: equal digests (urban seed 45).

## Files Changed
src/engine/hostility.py (new), candidate_selector.py, executor.py, worker_logic.py, pipeline_phases/movement.py, tactical.py; tests as above; docs (02_combat_laws, tactical_contract, intentional_divergences 2.83 note + 2.89, parity COMB-342, mechanisms notes).

## Completion Summary
Opportunity-attack hits 185.2 to 162.0, 158.0 to 128.4, 87.4 to 72.0; held-move hits roughly halved; total deaths and alive counts within 1 SD; no held move is blocked more than 1 tick; engaged-only ships, any-hostile does not.

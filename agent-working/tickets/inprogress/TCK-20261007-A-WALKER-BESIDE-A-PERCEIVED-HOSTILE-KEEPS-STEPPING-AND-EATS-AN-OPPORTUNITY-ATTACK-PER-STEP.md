---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP
phase: open
date: 2026-10-07
tags: [combat]
---

# TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP

## Title
A subject walking a held move beside a hostile it perceives keeps stepping, takes an opportunity attack on every step, and never makes a fight-or-flee decision until it dies.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by Lane A during the SURV-07 contact check (urban_political, seed 42, gated arm 7db978edc). It is read-only so far.
- **Who hit the victims:** entities 22, 2 and 28 (a hero, a worker and a merchant) were killed by scouts 14 and 15. The scouts did 37, 38 and 32 hp-removal events at 15 to 17 hp each, all through `MovementSystem.resolve_move` (movement.py:292), on the opportunity-attack trigger (COMB-009/272). Each step the victim took while engaged gave the scout a free swing.
- **Perception:** the attacker was perceived on every sampled tick, at 1 to 3 tiles.
- **Why there was no fight or flight:**
  - Retreat could not fire: `safety_pressure` was 0.0, below the AGENCY-07 cautious threshold of 0.75.
  - Engage did not fire: on most ticks the tactical pass did not run while the held ENTITY_MOVE (mode PURSUE, toward the inn) was in force, probably the sticky-task law. When it did run, it chose WANDER, PURSUE or INTERCEPTING.
  - The raw hunger value, 80 to 100, still beats the combat_engage ceiling (about 100 or less).
- **Not caused by SURV-07:** baseline walkers (town_return) die the same way. SURV-07 makes the defect more visible because it creates about 5 times as many walks.

Under SURV-07, only a present threat outranks a pressing need, and AGENCY-07 says a present threat is acted on. A subject that is adjacent to a perceived hostile and being struck has a present threat, yet no decision is ever made for it.

## Scope (RE-SCOPED by rpg-planner 2026-10-08 after Lane A's two traces; the held-move interrupt, WIP 7f2455353, is abandoned)
Lane A's trace: 4-5% of opportunity-attack hits land on a tick when the victim decided something. 19-41% land on a held ENTITY_MOVE. **55-77% are the "neither" class**: the task is ENTITY_ACT, nothing was decided that tick, and the subject still moved. Mechanism (verified by rpg-planner on 753f98ea9):
- The movement phase (`src/engine/pipeline_phases/movement.py:248-275`) moves an entity on its navigation target alone (the fresh update, else the stored leftover target) and never reads the task. This is by design for errand walks (the WANDER objective walk at `tactical.py` about 341/359 sets only navigation).
- `MovementCandidateSelector.resolve_live_tracking_target` (`candidate_selector.py`) live-retargets for ANY task carrying `payload["target_id"]`, including an ENTITY_ACT ATTACK, so a held attack chases the target's live position.
- The ATTACK/SKILL emissions (`tactical.py` about 770-799) send a TaskUpdate with no NavigationUpdate, so a PURSUE/INTERCEPT target left by an earlier decision survives into the attack.
- A held ENTITY_ACT with a payload is a non-brain scheduler item (`scheduler.py:68-86`), so the tactical pass does not run for it while it moves.

1. **Instrument first (read-only):** (a) what `resolve_move` does for an entity whose live target is adjacent (does it step, and onto which tile); (b) why, after the parked interrupt, an empty-payload ENTITY_ACT at LOD 0 gets no `evaluate_entity_intent` call in 89-96% of ticks (execute_brain early return, or the brain item not being scheduled). Facts and file:line.
2. **Fix: a subject moves only on a movement it decided** (AGENCY-01/02; consistent with CONFLICT-04).
   - An action emission (ATTACK/SKILL; INTERACT where it applies) clears or replaces the navigation target, so no leftover target survives into an action.
   - Live retargeting applies only to the entity-tracking movement modes the comment at `movement.py:252-268` names (PURSUE, INTERCEPT, KITING, BRACKETING, GUARDING_ALLY), not to an action task's `target_id`.
   - The movement phase does not move an entity whose current task is an action payload unless that tick's update set a navigation target.
   Errand walks (navigation-only WANDER) keep working.
3. If 1(b) shows the brain is skipped for a schedulable idle entity, report it before fixing: that may touch the scheduler (ask first; perf #415 owns kernel/governor/phase_governor/governance/profiles/runtime_status).

## Out of Scope
- CONFLICT-04 (hold between blows, the stalemate breaker): its own ticket, TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04, stacked after this one.
- Lane B's held INTERACT on a depleted node (typed unrecoverable failure): its own PR.
- The opportunity-attack rule (COMB-009).

## Acceptance Criteria
- [ ] Instrumentation facts for 1(a) and 1(b), in the ticket's investigation.
- [ ] Unit or constructed tests: a subject holding an ATTACK task with a leftover PURSUE target does not step; a navigation-only WANDER errand still walks; a PURSUE move still live-retargets.
- [ ] Pinned report, seeds 42-46 x 3 worlds, mean (SD), before and after: hits by class (decided, held, neither), DEFEAT deaths, total deaths, alive at t=1000 and t=1100, and chase convergence (attacks landed per engagement), so that we see whether the pursuit fix of TCK-20260809/0810 regresses. Two-run determinism. Report it, don't tune.
- [ ] A Bible or engine-contract line for "movement follows a decided movement, not a leftover target" (kernel.md Sticky-Task Law or Bible 02), with a parity entry in combat_movement.yaml. A divergence entry if behaviour changes (likely Bug Fix).
- [ ] Gates: mypy, ratchet, lint-imports 17/0.

## Related Tickets
- `TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`, the same family of held tasks that are never re-decided.
- `TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07`, where it was found.
- AGENCY-07 (#398).

## Related Docs
- `docs/mechanics/02_combat_laws.md` (opportunity attacks), `docs/world_rules/` AGENCY-07 and SURV-07.

## Related Stored Artifacts
- Lane A's probes `death_trace.py` and the contact trace, once stored with SURV-07.

## Related Code Areas
- `src/systems/.../movement.py:292` (`resolve_move`, the opportunity-attack trigger), `src/ai/tactical.py`, `src/ai/tactical_threat.py`, the sticky-task handling of held ENTITY_MOVE.

## Assumptions / Open Questions
- Whether the sticky-task law is the cause is a hypothesis.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_

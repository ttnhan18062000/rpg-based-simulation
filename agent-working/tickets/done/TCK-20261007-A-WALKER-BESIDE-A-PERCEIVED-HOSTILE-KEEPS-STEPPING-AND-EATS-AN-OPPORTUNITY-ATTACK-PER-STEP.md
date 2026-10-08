---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP
phase: done
date: 2026-10-08
tags: [combat]
---

# TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP

## Title
An entity holding an action task keeps walking on a navigation target an earlier decision left behind, so a subject beside a perceived hostile steps off adjacency and takes an opportunity attack on the step.

## Status
DONE

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
- [x] Instrumentation facts for 1(a) and 1(b), in the ticket's investigation.
- [x] Unit or constructed tests: a subject holding an ATTACK task with a leftover PURSUE target does not step; a navigation-only WANDER errand still walks; a PURSUE move still live-retargets.
- [x] Pinned report, seeds 42-46 x 3 worlds, mean (SD), before and after: hits by class (decided, held, neither), DEFEAT deaths, total deaths, alive at t=1000 and t=1100, and chase convergence (attacks landed per engagement), so that we see whether the pursuit fix of TCK-20260809/0810 regresses. Two-run determinism. Report it, don't tune.
- [x] A Bible or engine-contract line for "movement follows a decided movement, not a leftover target" (kernel.md Sticky-Task Law or Bible 02), with a parity entry in combat_movement.yaml. A divergence entry if behaviour changes (likely Bug Fix).
- [x] Gates: mypy, ratchet, lint-imports 17/0.

## Related Tickets
- `TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`, the same family of held tasks that are never re-decided.
- `TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07`, where it was found.
- AGENCY-07 (#398).

## Related Docs
- `docs/mechanics/02_combat_laws.md` (opportunity attacks), `docs/world_rules/` AGENCY-07 and SURV-07.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP/` (investigation with the instrumentation facts and the five-seed table; `probes/`).

## Related Code Areas
- `src/systems/.../movement.py:292` (`resolve_move`, the opportunity-attack trigger), `src/ai/tactical.py`, `src/ai/tactical_threat.py`, the sticky-task handling of held ENTITY_MOVE.

## Assumptions / Open Questions
- Resolved: the sticky-task law is not the cause of the "neither" class. Movement runs on `navigation.target` whatever the task, live tracking retargeted onto `payload["target_id"]` for any task, and the ATTACK/SKILL emissions left the navigation target in place.
- The live NORMAL policy runs `strategic_intelligence = 10` (`src/engine/policy.py:92`), so an idle entity's brain runs once per 10 ticks; an earlier trace's "cadence 1" was `GovernorPolicy()`'s default and wrong. Open question, NOT built (perf's area, #415): letting a present threat bring an idle entity's brain forward is a governor or policy change.
- Open, owned elsewhere: `urban_political` is worse (see Completion Summary); the held `REGROUP` move is `TCK-20261008-A-HELD-REGROUP-MOVE-WALKS-INTO-PERCEIVED-HOSTILES-AND-IS-NEVER-RE-DECIDED`; the brain path (PURSUE when adjacent, STALEMATE_BREAK) is `TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04`, stacked after this one.

## Implementation Notes
Option (1) of the re-scoped ticket: ATTACK and SKILL emissions (`tactical.py`) carry `NavigationUpdate(target_clear=True)`; `MovementCandidateSelector.resolve_live_tracking_target` follows `payload["target_id"]` only for entity-tracking moves and never for an entity holding an action task; `MovementCandidateSelector.holds_action_task` (ENTITY_ACT with a payload) marks an action holder, and `MovementCandidateSelector.movement_target` is the one rule both `select` and the movement phase use: a fresh target this tick, else (not an action holder) the live-refreshed stored target, else none. Facts (a): of 515 movement calls for an ATTACK holder on frontier_living_world seed 43, 156 had the target already adjacent and still moved (71 with an opportunity-attack swing): the live-retargeted destination is the target's occupied tile, the refused step falls to the sidestep ladder (`movement.py` `_find_sidestep`, called at the ladder's 3.1 step). Facts (b): see Assumptions. One existing test fixture changed: `test_resolve_live_tracking_target_returns_live_position_when_target_alive` now sets `movement_mode=PURSUE`, since live tracking is limited to tracking moves. The parked held-move interrupt (WIP 7f2455353 on `rpg-opportunity-attack`) is not part of this change. Side effect: an attacker whose target steps away no longer closes the gap through live tracking (258 of 515 calls did); it closes after OUT_OF_RANGE returns it to the brain, up to 10 ticks later.

## Test Summary
New `tests/unit/engine/test_action_task_does_not_move.py` (10: an action holder is recognised; live tracking only for tracking moves; the selector does not offer an action holder a move but offers an idle one; a fresh target still moves it; an ATTACK emission clears the target; a kernel-level case where an adjacent ATTACK holder stays on its tile and takes no opportunity attack, which FAILS on `main`; an errand walk still walks and a pursuit still live-retargets). Unit directories (combat, engine, movement, actions, core, tools, systems, ai, strategic, cognition, domains) and `tests/integration` pass. Pinned five-seed corpus, three worlds, main `10944422c` vs this change (mean (SD)): in the investigation and divergence 2.84. Determinism: the same world and seed run twice under the pinned governor gives identical final-state digests (`crowded_frontier` seed 44 `1d44fffed7abed5c`, `urban_political` seed 44 `2d0fcac59f7afead`); the shared-rule refactor leaves a run's digest unchanged (seed 45, both worlds, equal before and after).

## Files Changed
`src/engine/tactical.py`, `src/engine/candidate_selector.py`, `src/engine/pipeline_phases/movement.py`, `tests/unit/engine/test_action_task_does_not_move.py`, `tests/unit/domains/optimization/test_movement_candidate_selector.py` (one fixture), `docs/mechanics/02_combat_laws.md`, `docs/parity_ledger/combat_movement.yaml` (COMB-338), `docs/guidelines/intentional_divergences.md` (2.84), `docs/REGISTRY.yaml`, stored artifacts with probes.

## Completion Summary
An entity holding an action task no longer walks on a leftover navigation target: opportunity-attack hits fall 279 to 179 (crowded_frontier), 276 to 124 (frontier_living_world) and 136 to 110 (urban_political), the "neither" class 162 to 69, 154 to 37 and 105 to 41, and attacks that landed rise about 3 to 4 times. `urban_political` is worse (total deaths 23.8 to 28.0, alive at t=1100 6.8 to 3.2); the extra deaths are COMBAT, DEFEAT from held moves (`REGROUP` 4 to 20 deaths) and moves decided that tick, and are disclosed in divergence 2.84 with the follow-up tickets named above.

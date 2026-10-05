---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES
artifact_type: investigation
tags: [strategy, cognition, combat]
---

# Investigation: entity-targeted combat objectives

## Context scan

`search_docs` (retreat/region lookups; the ticket's own topic is covered by the ticket and
`tactical_contract.md` §3 and §7), then code reads. The planner (`rpg-feature-planning`) closed Scope 1
before dispatch: **typed entity-target distinction, not a live-position re-read**, with the representation
left to the implementer.

## Premise correction (named): the stale fixed point is no longer reached

The ticket's numbers (100% stale `target_position` source, 96.8% / 70% arrive-and-do-nothing, 0 of 111 114
samples non-`ACTIVE`) were **true when measured**, before `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-
DECIDED-OBJECTIVE-KIND` landed. They stay in the ticket as that earlier record, superseded here. Measured on
this branch (cut from `origin/main` `9bf34765b`), `crowded_frontier`, seed 42, 2000 ticks, real
`Kernel.tick_once()`, `audit_mode`, `max_tick_budget_ms=1e9`, `LocalSequentialExecutor` (probe not in the
repo): a combat objective is `defeat_enemy` in every sample; `_resolve_target_position` was called with an
entity target **0 times**. A `defeat_enemy` objective is skipped by both objective-pursuit branches in
`tactical.py`, which only run when no hostile is perceived; engagement is the hostile branch. The stale
point survives only through a resumed `COMBAT_ENGAGE` committed intention (`REACH_LOCATION` on an entity id,
`target_pos=None`), which is typed here too.

## Measurement traps found, and a retraction

1. **`objective.id` names the target, not the objective.** It is built as `f"{kind}_{target_id}"`, so ten
   projects chasing one enemy share one id. Any probe that counts "distinct objectives" by `objective.id`
   counts distinct *targets*. My first probe reported 4 (the earlier probes' 27 and 36 counted
   `proj_<kind>_<tick>` project ids). Count projects by `(entity id, project.id)`.
2. **Dead holders keep their strategic state.** My first probe did not exclude entities with
   `combat.alive == False`, so it reported "target dead while objective current: 3078 of 6891 (45%)".
   **That figure is retracted.** With live holders only the same run gives 28 of 3839 (`crowded_frontier`).
   Filter on `holder.combat.alive`.

## Corrected A/B (live holders only)

Control arm disables **only** the termination hook (the strategic-pass block and the work-queue tier-3 rule);
the typed field and live resolve are identical in both arms. 2000 ticks, seed 42.

| | crowded control | crowded fixed | living_world control | living_world fixed |
|---|---|---|---|---|
| live combat-objective samples | 3839 | 3839 | 9282 | 4603 |
| distinct combat projects | 5 | 5 | 13 | 44 |
| projects ever terminal | 0 | 1 | 0 | 37 |
| of which COMPLETED / ABANDONED | 0 / 0 | 1 / 0 | 0 / 0 | 2 / 35 |
| live holder, target **dead** | 28 | 28 | 980 | 39 |
| live holder, target **out of 10 tiles** | 0 | 0 | 4266 | 670 |
| nav target 4+ tiles from live target | 37 | 37 | 5448 | 769 |

`frontier_living_world` is conclusive on its own (0 of 13 vs 37 of 44, one hook toggled, same seed).
`crowded_frontier` has almost nothing to terminate. Out-of-radius dominates (46% of control live samples) over
dead (10.6%); they may overlap and are not additive. The residual in the fixed arm is the 10-tick strategic
cadence stagger. Combat projects rise 13 to 44 because an abandoned objective is re-won against a new target:
the slot is released, not looped. The third condition (target gone from `state.entities`) was **never
observed**, because dead entities stay in state; it is kept only as the total fallthrough for an absent id.

**Attacks did not change.** Decision-path attack dispatches (`CombatActions.execute_attack`), control vs
fixed: `crowded_frontier` 0 / 0; `frontier_living_world` 5 / 5 (`resolve_attack_calls` 0 / 0 and 1 / 1). So the
37 terminal projects are slot release plus re-win churn, not an engagement improvement. The counter does not
see the incidental opportunity-attack mechanic, so it says nothing about total combat volume.

**Residual and its attribution.** `SystemCadence().strategic_intelligence` is 10. All 37 projects the fixed
arm closed on `frontier_living_world` closed 11 to 20 ticks after their end condition first held (max 20;
none inside 10, none beyond 20; `crowded_frontier`: one close, at 18), about two cadence periods (a queue pass
plus the stagger). This is consistent with the 670 / 39 residual; a cadence sweep to show it scales was not
run. **Open:** end conditions that held and never closed by end of run (age over 50 ticks): 3 (living_world)
and 2 (crowded) in the fixed arm, 9 and 3 in control. Candidates are the project no longer being current
(suspended or replaced) or the holder dying; the probe does not distinguish them.

The `10` is the radius of `CombatEngageScorer`'s neighbour view. It was a literal repeated at about eight
call sites; it now has a named home, `ENTITY_TARGET_PERCEPTION_RADIUS`, which the scorer also reads.

The work queue was part of the fix: an entity holding an ACTIVE project is otherwise evaluated only when
dirty or on the sweep, so the dead target went unnoticed (first A/B: dead-holder counts unchanged).

## Scope 4 audit: scorers that put an entity id in `target_id`

All `target_id=` sites under `src/ai/goals/`:

| scorer | `target_id` | entity id? |
|---|---|---|
| `CombatEngageScorer` | `str(nearest_hostile.id)` | **yes** (this ticket) |
| `SocialContractScorer` (`social_contract_scorer.py:68`) | `str(contract.source_id)` | **yes, a second live case**: the contract counterparty, with `target_pos` frozen at goal-win time; its own comment admits `_resolve_target_position` never resolves `state.entities`. Cooperation contracts are live in corpus runs. **Not widened into this ticket; reported to the planner.** |
| `CombatRetreatScorer`, `TownScorer`, `RecoverScorer` (fallback) | `"town_center"` | no |
| `HarvestScorer`, `EatScorer`/`HungerScorer`, `SleepScorer`, `GuildNeedScorer`, `RecoverScorer` (building) | node / building id | no |
| `ResolveBlockerScorer` | blocker target | no |
| `AdventureGoalScorer` | node id, opportunity id, or `adventure:<family>` | no |
| `OccupationChangeScorer`, `RegionStabilizationScorer` | region id | no |
| committed-intention resume (`intelligence.py`) | `head.target_hint` | **yes when `COMBAT_ENGAGE`** (handled here) |

## Other findings

1. `ScoreModifierSystem.apply_modifiers` rebuilt each `GoalScore` field by field, so any new `GoalScore`
   field was silently dropped between the scorer and the objective. Replaced with `dataclasses.replace`.
2. The int-cast in `_resolve_target_position` is a latent collision: an entity id equal to a resource-node
   or building id resolves to that node or building. A typed target avoids it by construction.
3. `ObjectiveState` is serialised into the canonical dict with `asdict`, so a new field moves the hash of
   every state with objectives. The new field is omitted from the canonical dict when `None`, so only states
   with an entity-typed objective change.
4. Existing completion logic for other project kinds lives in `evaluate_strategic_intent`'s lifecycle block
   (harvesting, hunger, fatigue, career_change, resolve_blocker timeout). The entity-target termination
   follows that pattern.

## Not decided here

A bounded give-up cap (a fourth Scope 2 option) was not added: the three declared conditions end every
observed case without creating re-win churn, and the ticket lists the conditions as alternatives.

---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES
phase: open
date: 2026-10-02
tags: [strategy, cognition, combat]
---

# TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES

## Title
An objective whose `target` is a moving entity is pursued through a fixed-point mechanism and never
terminates — entities navigate to where the enemy *was*, arrive, emit an empty update forever, and hold
a project slot permanently

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by the measurement run for
`TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND`, and filed separately because
it is **not about the decided objective kind at all** — it would survive that ticket's fix intact.

`CombatEngageScorer` (`src/ai/goals/scorers.py:126-130`) sets `target_id=str(nearest_hostile.id)` — an
**entity** id. The objective-pursuit path can only resolve a *place*:
`TacticalDecisionSystem._resolve_target_position` (`src/engine/tactical.py:796+`) int-casts `obj.target`,
looks for `state.resource_nodes[id]` then `state.buildings[id]`, finds neither for an entity id, leaves
`node_id`/`building_id` as `None`, and falls through to the `obj.target_position` fallback.

**That fallback is correct for its own purpose and wrong here.** It was added by
`TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG` for scorers whose `target_id` is a non-int-castable
string like `"town_center"`, where `target_position` genuinely carries the right fixed location. An
entity id *is* int-castable, so the parse succeeds, finds nothing, and the fallback silently converts
**"a moving entity"** into **"a fixed point frozen at goal-win time."**

Measured on current code (real `Kernel.tick_once()`, seed 42, 2000 ticks, `crowded_frontier` 38
entities and `frontier_living_world` 49, reusing
`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`'s method):

| observation | `crowded_frontier` | `frontier_living_world` |
|---|---|---|
| position source = `obj.target_position` (stale), `node_id`/`building_id` both `None` | **100%** | **100%** |
| arrived-and-do-nothing branch (`tactical.py:297-299`, bare `EntityUpdate(entity_id=…)`) | **209/216 (96.8%)** | **14/20 (70%)** |
| live target ≥3 tiles from the stale point navigated to | **183/212 (86%)** | 13/20 |
| `movement_mode` while pursuing | `WANDER`, not `PURSUE` | `WANDER` |
| objective samples in any status other than `ACTIVE` | **0 of 50 279** | **0 of 60 835** |

Distance to the **live** target at those moments (`crowded_frontier`): 9 calls at 0-1, 20 at 2-3,
**176 at 4-10**, 8 at >10. So entities are not adjacent-and-failing-to-swing; they stand still at a
point the enemy has left.

**Two distinct durable-state problems:**
1. **Wrong target semantics.** A combat objective's target is an entity that moves; the pursuit path
   models it as a fixed coordinate captured once. Nothing re-reads the entity's current position.
2. **The objective never terminates.** Zero samples in any non-`ACTIVE` status across 111 114 objective
   samples. There is no completion, failure or abandonment condition for "reach this entity", so the
   project slot is held indefinitely — a durable-state lifecycle gap, not a tuning issue.

## Scope
1. Decide and record how an entity-targeted objective resolves its position: re-read the target
   entity's current position each tick, or an explicit typed "entity target" distinct from a place
   target. The repo's durable-state rule applies — if an objective can target an entity, that is a
   typed distinction with a defined lifecycle, not an overloaded `target` string.
2. Give the entity-targeted objective a **termination condition** — reached, target dead, target no
   longer perceivable, or a bounded give-up — so it cannot be held forever.
3. Leave `_resolve_target_position`'s existing `target_position` fallback working unchanged for the
   `"town_center"`-shaped cases it was built for (`TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`).
   This ticket must not regress those.
4. Audit which other scorers put an **entity** id in `target_id` and record them. `CombatEngageScorer`
   is the confirmed case; `CombatRetreatScorer` and others are unchecked and may share the shape.

## Out of Scope
- The objective **kind** discard and the scorer hostility source — both owned by
  `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND`. This ticket assumes nothing
  about whether that has landed.
- The raw-legacy-enum hostility sweep — `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` owns it.
- Changing `ProjectState.kind` from `GoalKind` to `ProjectKind`. That silently flips the score scale
  from the 100.0 ceiling to 2.9 (`_score_scale_max`, `intelligence.py:111-128`) and is tracked
  elsewhere (D22/C4).
- Balance or tuning of combat volume.

## Acceptance Criteria
- [ ] An entity-targeted objective navigates toward the target's **current** position, asserted
      end-to-end through a real `Kernel.tick_once()` loop with a target that moves after the objective
      is created.
- [ ] The objective terminates under every declared condition from Scope 2, each covered by a test.
      "Never observed non-`ACTIVE`" must become "observed terminal in these cases".
- [ ] The arrived-and-do-nothing rate for combat objectives drops from the measured 96.8% / 70%, and
      the new rate is reported whatever it is.
- [ ] `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`'s own cases still pass — the `"town_center"`,
      `RecoverScorer` and `ResolveBlockerScorer` paths are explicitly re-tested.
- [ ] The Scope 4 audit of entity-id-in-`target_id` scorers is recorded in `investigation.md`.
- [ ] Determinism holds: canonical/replay/fingerprint/hash sweep green; any recorded-hash fixture that
      moves is explained, not silently regenerated.
- [ ] Durable-state review: if an "entity target" becomes a typed distinction, it has a model, a stable
      location in state, a defined lifecycle, inspection visibility and tests.

## Related Tickets
- `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` — sibling; its measurement
  found this. Independent fixes; see Out of Scope.
- `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG` (done) — added the `target_position` fallback this
  ticket must preserve while stopping it from masking entity targets.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (done) — the measurement method reused
  here.
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — the chain this sits under.

## Related Docs
- `docs/engine/contracts/tactical_contract.md` §7 — objective target resolution
- `docs/mechanics/04_strategic_cognition.md` — goal hierarchy and objective lifecycle

## Related Stored Artifacts
- `stored_artifacts/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION/`

## Related Code Areas
- `src/engine/tactical.py:796+` (`_resolve_target_position`), `:262-299` (the `reach_location` inline
  branch and the arrived-noop return)
- `src/ai/goals/scorers.py:126-130` (`CombatEngageScorer` sets an entity id as `target_id`)
- `src/systems/strategic_systems/intelligence.py:1707-1714` (where the objective is constructed)

## Assumptions / Open Questions
- Whether the right fix is live position re-read or a typed entity-target distinction is **open** and is
  Scope 1's decision. Live re-read is the smaller change; a typed distinction is what the durable-state
  rule points at. Not pre-judged here.
- The 96.8% / 70% arrived-noop rates and the ±~3% drift in tactical **call counts** come from the
  sibling ticket's probe. Simulation *outcomes* were exactly reproducible across four identical-seed
  runs; the call-count drift is believed to be the governor's latency-adaptive brain scheduling and was
  **not** chased to root cause.
- "0 objectives ever non-`ACTIVE`" is a **floor claim**: live projects were sampled per tick, so a
  project deleted between ticks would vanish rather than show a terminal status. 27 and 36 distinct
  combat-engage projects did churn over 2000 ticks, so churn exists — what is absent is any observed
  terminal status.
- `quest_dense_frontier` contributes nothing (0 combat-engage wins in 410 competitions), so the
  measurement rests on two worlds. `hero_guild_routing` and `metropolis` were not run.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_

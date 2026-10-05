---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES
phase: done
date: 2026-10-02
tags: [strategy, cognition, combat]
---

# TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES

## Title
An objective whose `target` is a moving entity is pursued through a fixed-point mechanism and never
terminates — entities navigate to where the enemy *was*, arrive, emit an empty update forever, and hold
a project slot permanently

## Status
DONE

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
**Premise correction (2026-10-05, measured on a branch cut from `origin/main` `9bf34765b`).** The
measurements in this ticket (100% stale `target_position` source, 96.8% / 70% arrived-and-do-nothing,
0 of 111 114 samples non-`ACTIVE`) were true when taken and **are kept as that record, superseded**:
`TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` has since landed, a combat
objective is now `defeat_enemy`, and `_resolve_target_position` is called with an entity target 0 times on
the live path. Problem 1 (stale fixed point) is no longer reached there; Problem 2 (never terminates) is
confirmed, and the typed distinction stays because of a separate latent bug: an entity id equal to a
resource-node or building id resolves, through the int-cast, to that node or building. Full numbers, two
measurement traps (objective ids name the target; dead holders keep strategic state, and a first-draft
"45% dead target" figure is retracted) and the corrected A/B are in `investigation.md`.

- [x] **AC1 (kept, now a regression guard, not a fix).** The navigation target of a combat objective
      tracks the target entity's current position, end to end through `Kernel.tick_once()` with a target
      that moves: `tests/mechanic_scenarios/test_entity_target_navigation_tracks_live_position_through_kernel.py`.
      It guards a property that holds today because of the sibling fix.
- [x] **AC2.** The objective terminates under the evidenced conditions: target dead -> `RESOLVED`/`COMPLETED`;
      target beyond 10 tiles -> `FAILED`/`ABANDONED`, each with unit tests directly and through
      `evaluate_strategic_intent`, plus the work-queue rule. Kernel-level, same seed, one hook toggled
      (probe, not in the repo): `frontier_living_world` projects ever terminal 0 of 13 (control) vs 37 of 44.
      The third branch, target absent from `state.entities`, is a documented total-function fallthrough: it
      has a unit test and was **never observed** (dead entities stay in state). It is not claimed as a
      working condition.
- [~] **AC3 (restated; the original numbers are unmeasurable).** The arrived-and-do-nothing rate cannot be
      compared against 96.8% / 70% because the path it measured no longer carries combat objectives.
      Restated, in its original spirit "report the rate whatever it is": the share of **live-holder**
      combat-objective samples whose target is dead or beyond 10 tiles. `frontier_living_world`: control
      dead 980 and out-of-radius 4266 of 9282 (not additive), fixed 39 and 670 of 4603.
      `crowded_frontier`: dead 28 in both arms of 3839, out-of-radius 0. Decision-path attack dispatches did
      **not** change (0 / 0 and 5 / 5); the terminal projects are slot release plus re-win churn, not an
      engagement improvement.
- [x] `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`'s own cases still pass: `"town_center"`, an
      int-castable node id and a coordinate string are re-tested in `TestLegacyPlaceTargetsUnchanged`, and
      the existing `RecoverScorer` / `ResolveBlockerScorer` tests pass unchanged. (Those two scorers have no
      new dedicated test beyond the unchanged existing ones.)
- [x] The Scope 4 audit is recorded in `investigation.md`: exactly two scorers put an entity id in
      `target_id` (`CombatEngageScorer`, here; `SocialContractScorer`, filed separately), plus the
      committed-intention resume of `COMBAT_ENGAGE`, typed here.
- [x] Determinism: certification, regression, architecture, engine, integrity, scenario suites and the
      strategic/social/ai/combat/engine/core/domains/world/systems unit trees: 3074 passed, 3 skipped,
      1 xfailed, 1 failed. The failure, `test_behavioral_5k_regression`, is a conftest 60 s `TimeoutError`
      that fails identically on the base `tactical.py`. **No recorded-hash fixture moved**, because
      `target_entity_id` is omitted from the canonical dict when `None`. State hashes do differ between the
      A/B arms in both worlds, which is the intended behaviour change.
- [x] Durable-state review. Model: `ObjectiveState.target_entity_id` (typed). Stable location:
      `entity.strategic.projects[*].objectives[*]`. Lifecycle: created from `GoalScore.target_entity_id`,
      ended by `entity_target_outcome`, scheduled by `StrategicWorkQueue` tier 3. Inspection: part of the
      canonical entity dict (and so of state hashes) when set; it is **not** added to the cognition trace
      recorder's objective view. Tests: listed in Test Summary.

## Related Tickets
- `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` — sibling; its measurement
  found this. Independent fixes; see Out of Scope.
- `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG` (done) — added the `target_position` fallback this
  ticket must preserve while stopping it from masking entity targets.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (done) — the measurement method reused
  here.
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — the chain this sits under.
- `TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT` — the second
  scorer that puts an entity id in `target_id`; sequenced after this ticket and consumes
  `target_entity_id` rather than adding it.
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` — where the unchanged
  decision-path attack count goes next: on `crowded_frontier` entities navigate within 1 tile of a live
  target in 3779 of 3839 samples and dispatch 0 attacks. This ticket did not change it and does not claim to.

## Related Docs
- `docs/engine/contracts/tactical_contract.md` §7 — objective target resolution
- `docs/mechanics/04_strategic_cognition.md` — goal hierarchy and objective lifecycle

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION/`

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
- Representation (direction ruled by `rpg-feature-planning`; shape mine): a typed
  `ObjectiveState.target_entity_id: Optional[int]` plus `GoalScore.target_entity_id`, not a target union.
  `target` (the string) is unchanged for every existing consumer. Contested-surface hold for
  `src/core/strategic.py` and the objectives region of `src/core/state.py` was granted by the planner.
- `src/systems/strategic_systems/entity_target_objective.py` (new): `entity_target_outcome` and
  `ENTITY_TARGET_PERCEPTION_RADIUS`. The 10 is the radius of `CombatEngageScorer`'s neighbour view; it had no
  named home (the literal repeats at about eight neighbour-view call sites, which are left alone), and the
  scorer now reads the constant so the targeting radius and the objective lifecycle cannot drift apart.
- Termination: `evaluate_strategic_intent`'s lifecycle block, plus a tier-3 rule in `StrategicWorkQueue`
  (an ACTIVE project is otherwise evaluated only when dirty or on the sweep; the first A/B showed the hook
  firing too late without it). Dead -> `RESOLVED`/`COMPLETED`; beyond 10 tiles or absent ->
  `FAILED`/`ABANDONED`. The absent branch was never observed and is a total-function fallthrough.
- `ScoreModifierSystem` rebuilt each `GoalScore` field by field and dropped any new field; it now uses
  `dataclasses.replace`. A resumed `COMBAT_ENGAGE` committed intention carries the typed id too.
- Canonical dict omits `target_entity_id` when `None`, so no recorded hash of a state without an
  entity-typed objective moved.
- **Residual delay.** `SystemCadence().strategic_intelligence` is 10. All 37 projects the fixed arm closed on
  `frontier_living_world` closed 11 to 20 ticks after their end condition first held (max 20), about two
  cadence periods. This is consistent with the 670 / 39 residual; a cadence sweep to show it scales was not
  run, so the attribution is consistent-with, not proven-by.
- **Open, unexplained residual:** end conditions that held and never closed by end of run (age over 50
  ticks): fixed arm 3 (`frontier_living_world`) and 2 (`crowded_frontier`); the **control arm is worse**, 9
  and 3, so the fix reduces it. Candidates: the project no longer current (suspended or replaced), or the
  holder dying; the probe does not distinguish them. Not chased.
- Sibling test `tests/mechanic_scenarios/test_combat_engage_objective_kind_through_kernel.py` attributes the
  two-entity world's no-attack to this ticket's fixed point. Measured here, navigation targets stay within one
  tile of the opponent's live position at every sample while HP never changes, so that attribution does not
  hold for that world (consistent with `docs/engine/known_limitations.md` section 1.1, not investigated).
  The sibling's docstring is left untouched.
- Out of scope, found: decision-path attack dispatches are unchanged by this fix (0 / 0 and 5 / 5), the
  `SocialContractScorer` second case, and the repeated radius literal. Each is a separate ticket or noted
  above.
- `ruff` is not installed in this environment, so lint was not run; no function-local imports were added.

## Test Summary
- New `tests/unit/strategic/test_entity_target_objective.py` (24 tests) and
  `tests/mechanic_scenarios/test_entity_target_navigation_tracks_live_position_through_kernel.py` (3).
- Wide sweep (certification, regression, architecture, engine, integrity, mechanic_scenarios, scenarios, and
  the strategic/social/ai/combat/engine/core/domains/world/systems unit trees, `-m "not slow"`): 3074 passed,
  3 skipped, 1 xfailed, 1 failed. The failure, `tests/regression/test_behavioral_5k.py::
  test_behavioral_5k_regression`, is a **pre-existing local 60 s conftest `TimeoutError`**: it fails
  identically with the base `tactical.py` (control arm), it is also seen on the retreat ticket, and
  `tests/regression/` is the push-to-main "Slow regression" job, skipped on PRs. Not chased.
- No recorded-hash fixture moved.

## Files Changed
`src/core/strategic.py`, `src/core/state.py` (objectives canonical region only), `src/ai/goals/base.py`,
`src/ai/goals/scorers.py`, `src/ai/score_modifiers.py`, `src/engine/tactical.py`,
`src/systems/strategic_systems/entity_target_objective.py` (new), `.../intelligence.py`, `.../work_queue.py`,
`tests/unit/strategic/test_entity_target_objective.py` (new),
`tests/mechanic_scenarios/test_entity_target_navigation_tracks_live_position_through_kernel.py` (new),
`docs/engine/contracts/tactical_contract.md`, `docs/guidelines/intentional_divergences.md`,
`docs/parity_ledger/combat_movement.yaml`.

## Completion Summary
A combat objective now names its target entity (typed `target_entity_id`), resolves it to the live position,
and ends when the target dies (`RESOLVED`/`COMPLETED`) or leaves the 10-tile perception radius
(`FAILED`/`ABANDONED`). On `frontier_living_world`, same seed with only the termination hook toggled, 0 of 13
combat projects reached a terminal status before and 37 of 44 after. **Decision-path attack counts did not
change** (0 / 0 and 5 / 5), so this is slot release and re-win churn, not an engagement improvement. The
stale-fixed-point premise was already superseded by the sibling fix and is recorded as a named correction;
AC3 is restated; a first-draft "45% dead target" figure is retracted in `investigation.md`. Open: the
never-closed residual, the unverified cadence scaling, and the attack path itself, which belongs to
`TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK`.

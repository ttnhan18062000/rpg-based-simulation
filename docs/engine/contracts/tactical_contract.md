---
status: active
layer: engine
authority: P1
audience: developer
---

# Bounded Tactical Engagement Contract

This document defines the authoritative logic for local tactical decisions in the `src` engine.

## 1. Tactical Evaluation Boundary
Tactical decisions are triggered when an entity is `active` and `alive`. **`readiness >= 100` is NOT a
precondition for tactical evaluation** — cognition (the `ENTITY_BRAIN` work item, which runs
`TacticalDecisionSystem.evaluate_entity_intent()`) is explicitly readiness-exempt by design ("Action
Readiness Law, COMB-266", `src/engine/scheduler.py`); it consumes 0 readiness and is instead gated by
the `strategic_intelligence` cadence (default: every tick). The `readiness >= 100` gate applies only to
committing the *result* of a tactical decision — `ENTITY_ACT` / `ENTITY_MOVE` — not to evaluating one.
AI logic is bounded to **Local Visibility** (Default radius: 10.0 tiles) and must not consult long-horizon strategic data.

## 2. Target Selection Rules (GAP-T01)
Targets are selected from hostiles within the visibility radius using the following deterministic priority chain (`TacticalDecisionSystem.target_score()`, `src/engine/tactical.py`; this section was previously stale — it omitted the group/hysteresis/pressure terms below even before the capability-driven term was added, per `TCK-20260831-CAPABILITY-DRIVEN-TARGETING`):

1. **Group Focus-Fire Bias**: If the entity's group has a `shared_target_id`, that hostile is biased toward higher priority based on the entity's trust in the group leader (`VANGUARD` roles bias further).
2. **Target Stickiness / Hysteresis**: The entity's current `target_id` (if still a hostile) gets a small priority bonus, avoiding target flip-flop.
3. **Capability-Driven Priority** (Logic ID COMB-316): For a hostile resolvable into `CapabilityContext.combat_enemies` (via the hostile's `kind`), the entity's own subjective `CapabilityEstimateService.estimate(...)` result against that specific enemy kind is folded in — a hostile the entity subjectively believes it is more likely to beat is prioritized higher, ahead of raw HP/distance. This is an ad-hoc, call-site-local, read-only call: it does not go through `SelfModelUpdatePhase`, and `entity.self_model.capabilities.estimates` remains empty in production either way (see `docs/cognition/capability_and_knowledge_contract.md`). **Source of the belief (KNOW-04, divergence 2.82):** the estimate is read from the acting entity's own common-knowledge fact about the hostile's species (`entity.self_model.knowledge.facts["danger.<species>"]`, seeded at spawn from the species' declared `common_knowledge`, held at certainty 0.3). A species with no declared belief is estimated neutrally and recorded as `UNINFORMED`, so it cannot be told apart from another uninformed species. Humans share one prior (no visible role is declared). The old built-in per-kind table is removed.
4. **Lowest HP**: Prioritize finishing off weak targets.
5. **Closest Distance** (pressure-scaled): Prioritize immediate threats (Manhattan distance, reduced by territory/duty pressure to make territorial/duty-bound entities more aggressive).
6. **Lowest Entity ID**: Final tie-breaker for absolute determinism.

**Note on `select_best_target()`**: `TacticalDecisionSystem` also exposes a separate public
static helper, `select_best_target()` (`src/engine/tactical.py`), documented in its own docstring
as matching the original legacy `TacticalEvaluator.SelectTarget` literally — `Lowest HP` >
`Closest Distance` > `Lowest Entity ID` only, with none of the group/hysteresis/pressure/
capability terms above. It is exercised only by its own contract test
(`tests/unit/combat/test_target_selection_contract.py`) and is not called from the live tactical
decision loop (`TacticalDecisionSystem.evaluate_entity_intent()` uses `target_score()` above, not
this helper) — confirmed via a repo-wide reference search finding no production caller. This ticket
(`TCK-20260831-CAPABILITY-DRIVEN-TARGETING`) did not modify `select_best_target()`.

## 3. Engagement & Pursuit Rules (GAP-T02/T04)
- **Stickiness**: Entities retain their current `target_id` if the target is still alive and within a **Stickiness Radius** (Default: 15.0).
- **Pursuit**: If a target is outside combat range but within visibility, the entity sets its navigation target to the target's current position. Tactical re-evaluation itself is cadence-gated (`SystemCadence.strategic_intelligence`, default every ~10 ticks); movement execution runs every tick and, while a real `target_id` is active in the entity's own task payload, re-derives the live target position each tick rather than walking to a stale snapshot from the last tactical decision (`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`). This live-retargeting logic is centralized in `MovementCandidateSelector.resolve_live_tracking_target()` (`src/engine/candidate_selector.py`) and is applied at **all four** real places a stale `navigation.target`/`payload["target_position"]` snapshot can otherwise leak through unrefreshed: `MovementPhase.route_movement_intent()`'s own per-entity movement step, `MovementCandidateSelector.select()`'s own, separate movement-candidacy gate (which has its own independent "already at target" check and, pre-fix, silently excluded a pursuer that had "arrived" at a stale snapshot from candidacy before `route_movement_intent`'s live-retarget logic ever got a chance to run for it), and both real `ENTITY_MOVE` work-item dispatchers (`src/engine/executor.py`, `src/engine/worker_logic.py`'s `default_simulation_worker`) — both of which re-emit `NavigationUpdate(target_set=...)` from the same static `task.payload["target_position"]` snapshot every tick a pursuit task is scheduled, which `route_movement_intent`'s own `has_fresh_decision` check (`target_set is not None`) misreads as a genuine new tactical decision, silently defeating its own live-retarget fallback (`TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS`). Confirmed via live corpus trace: two mutually-pursuing entities were frozen at a fixed Manhattan distance for 990+ consecutive ticks despite `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`'s own fix already being merged, because that fix's own retargeting logic never actually engaged for them. With that gap closed, the same specific pair still does not converge — it enters a real, deterministic diagonal-orbit deadlock instead, a known, disclosed, low-prevalence limitation of `NavigationSystem.get_next_step()`'s own single-axis stepping — see `docs/engine/known_limitations.md` §1.1 (`TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK`) for the full mechanism and real, measured corpus prevalence.

**Pursuit completion (`TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK`).** A pursuit
`ENTITY_MOVE` (movement mode `PURSUE`, `payload["target_id"]` set) **ends when the live target is within the entity's attack
reach** (Manhattan; a melee entity needs distance 1; no weather multiplier, legality still arbitrates the attack itself).
Both `ENTITY_MOVE` dispatchers (`executor.py`, `worker_logic.py`, via
`MovementCandidateSelector.tracked_move_complete`) then emit `tracked_move_completion_update`: the task returns to the idle
encoding (`ENTITY_ACT` with an empty payload, which the scheduler reclassifies as a brain tick) **and the navigation target is
cleared**, because movement is driven by `navigation.target`. Before this nothing ended a pursuit move, so under the Sticky-Task
Law (`docs/engine/kernel.md`) the decision pass was never re-run and an entity adjacent to a live target at full readiness never
chose `ATTACK`. The same condition covers every entity-tracking combat move, keyed on (movement mode, payload `reason`): `PURSUE`, `INTERCEPT`,
`REPOSITION` with reason `BRACKETING`, and `RETREAT` with reason `KITING`. **A dead, inactive or missing target ends all four**
(`TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION`; measured: one `PURSUE` held 986 ticks
by a live entity after its target died at tick 4); the in-reach end applies to all but kiting, which intends to hold range. A group guard
move ends under the same dead-target rule (`TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER`): `GUARD` with reason
`CONTRACT_OBLIGATION_GUARD` (a hireling guarding its leader) also ends when the mover no longer shares the leader's group, and `GUARD`
with reason `GUARDING_ALLY` ends only when the ally is dead, inactive or gone; neither ends on reach, and a leader merely pausing between
interactions does not end the obligation (INTERACT runs have gaps of up to 11 ticks). **`BRACKETING` is de-facto pursuit** (`TCK-20261006-LIVE-TRACKING-TARGET-HELPER-IGNORES-MOVEMENT-MODE`, planner ruling 2026-10-06): the
flank tile `bracket_pos` gates whether the move is issued (walkable, not the current tile) and is the destination on the issuing tick only; from
the next tick `MovementCandidateSelector.resolve_live_tracking_target` replaces it with the live position of `payload["target_id"]`, and
a comment at `pipeline_phases/movement.py:242-243` names `BRACKETING` among the entity-tracking modes. It is left that way on purpose: a flank tile is one step past
the target, so a diagonal flank is Manhattan distance 2, outside a melee entity's reach of 1, and since arriving never ends a move a
fixed-point `BRACKETING` move would hold at the tile. Cover-seeking moves also carry a `target_id` and keep
their own lifecycle; by the same helper a `SEEK_COVER` move would head toward its threat, which is latent (0 corpus moves) and parked as
`TCK-20261006-SEEK-COVER-LIVE-TRACKED-TOWARD-ITS-THREAT-LATENT-TRIGGER`. The idle
entity is then decided at its next brain cadence (`strategic_intelligence`, 10 ticks); that wait is not changed here.
**The completion also stops the walk in the same tick** (`TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED`):
`MovementPhase.route_movement_intent` skips an entity whose update carries `navigation.target_clear` with no new target, because it
reads the tick-start target and would otherwise step the entity once more, off the adjacency it had just reached. Melee adjacency is
orthogonal (Manhattan <= 1, world rule MOV-07), so a diagonal pair is out of reach and closes by one orthogonal step; a held `ATTACK`
that returns `OUT_OF_RANGE` ends its task so the brain re-decides (the tactical pass pursues whenever an attack is not legal). The first strike of a
diagonal pair lands within two brain cadences (20 ticks): one to decide the pursuit, one to decide the attack. Strategy does
not write a navigation point for an entity-typed objective (`ObjectiveState.target_entity_id`): the redirection writers in
`intelligence.py` and `redirection.py` leave the point unset and tactics resolve the live position.

## 4. Retreat & Disengage Rules (GAP-T03)
- **Retreat Threshold**: Triggered when `hp < max_hp * 0.2`.
- **Behavior**: Entity clears current combat intent and moves away from the perceived threats, clamped to stay inside its current region (`src/engine/tactical_destinations.py::retreat_destination`, one perception radius of 10 beyond itself). If no away-vector keeps it inside the region (cornered, or no threat vector), it heads for the centre of its own `strategic.home_region_id` region when set; otherwise it **holds position**. The destination is never a sentinel coordinate: the previous "Safe Zone (0,0)" was outside every region in the corpus worlds (World Rules `MOV-01`, `LOC-01`, `LOC-03`, `MOV-03`; `docs/guidelines/intentional_divergences.md` §2.66, `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN`). The same derivation serves the `PANIC_RETREAT` and `SAFETY_PRESSURE_RETREAT` reasons.
- **Safety-disposition retreat (`SAFETY_PRESSURE_RETREAT`, World Rule `AGENCY-07`)**: a cautious entity (`safety_pressure > 0.75`, a static trait from its catalog need and drive profiles) retreats only from a **present threat** to itself, never from a hostile it merely perceives (`src/engine/tactical_threat.py::safety_retreat_warranted`). A present threat is any of: its HP below 0.7 of max (`WOUNDED`); a hostile within Manhattan distance 1 (`ADJACENT`); a hostile whose task targets it (`TARGETED`, at any range); a hostile within 4 tiles that is nearer than at its previous position (`CLOSING`); or hostiles within 4 tiles whose summed apparent power is at least 1.5 times its own (`OUTMATCHED`, `apparent_power` from `src/domains/combat_engagement/power.py`). The constants are engineering choices recorded for a later tuning pass, not Rule text. `docs/guidelines/intentional_divergences.md` §2.76.

## 5. Anti-Stalemate Rules (GAP-T05)
- **Deadlock Detection**: Tracks `stale_ticks` in the task payload.
- **Trigger**: If `stale_ticks > 10` without a target change or outcome, the entity forces a `STALEMATE_BREAK`. An ATTACK or SKILL emission is an outcome: it sets `stale_ticks` to 0 (read at emission, not at landing). The breaker never fires while the target is adjacent (CONFLICT-04: a pair trading blows is not a stalemate).
- **Hold between blows (CONFLICT-04)**: adjacent to the target with only readiness missing, the decision is a held `ATTACK` (payload reason `HOLD_BETWEEN_BLOWS`), never a `PURSUE` step. `target_score` ranks an adjacent hostile first. While held the entity is a non-brain item (scheduler readiness gate), so it cannot decide to flee until the swing or a release (`OUT_OF_RANGE`, `TARGET_INCAPACITATED`).
- **Behavior**: A different semantic from Retreat: a `WANDER` to a seeded (`DeterministicRNG`, `Domain.TACTICAL`, scoped by tick and entity id), nearby (half-width 5), region-contained point (`wander_destination`). An entity that is itself outside every region holds position.

## 6. Known Exclusions
- **Group Coordination**: Entities currently act as individuals (group coordination not yet implemented).
- **Cover Seeking**: Static obstacle awareness is currently unsupported.
- **Kiting**: Ranged entities do not yet attempt to maintain maximum distance.

## 7. Objective Target Resolution (TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG)

`TacticalDecisionSystem._resolve_target_position(state, obj)` turns a `reach_location`
objective's `target` field into a concrete world position for the Pillar 5.1 arrival-dispatch
branch (`evaluate_entity_intent`). Resolution order:

1. **Int-castable `target`**: looked up first against `state.resource_nodes`, then
   `state.buildings`. A match also yields `node_id`/`building_id`, which drive the
   INTERACT/EAT/REST arrival-dispatch branches once the entity reaches the position.
2. **Stringified coordinate `target`** (e.g. `"(3.0, 4.0)"`): parsed via `ast.literal_eval`.
3. **`target_position` fallback**: if neither above yields a position, falls back to the
   objective's own `target_position` field (set at objective-creation time from the winning
   `GoalScore.target_pos` — see `evaluate_strategic_intent()`'s `ObjectiveState(...)`
   construction). This exists because some scorers (`TownScorer`, `RecoverScorer`'s no-inn
   fallback, `ResolveBlockerScorer`'s non-coordinate blocker-id case) set `target_id` to a value
   that never parses under (1) or (2) — e.g. `TownScorer`'s literal `"town_center"` — even though
   the real target position was already known and carried on `target_position` all along.
   Mirrors `StrategicIntelligenceSystem._resolve_active_objective()`'s own "detour" case, which
   already prefers `target_position` this same way.

**Typed entity target (`TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES`).**
When `obj.target_entity_id` is set, resolution **precedes** steps 1-3 and replaces them: the position is the
live entity's `navigation.position` from `state.entities`; a dead or missing entity yields
`(None, None, None)` with **no** `target_position` fallback (the snapshot is exactly the stale value the
typed field exists to avoid, and the int-cast in step 1 could resolve an entity id equal to a node or
building id to the wrong place). The strategic pass ends such an objective
(`StrategicIntelligenceSystem._entity_target_outcome`): target dead -> objective `RESOLVED`, project
`COMPLETED`; target gone from state or beyond `ENTITY_TARGET_PERCEPTION_RADIUS` (10, Manhattan) -> objective
`FAILED`, project `ABANDONED`. Every objective without the field takes steps 1-3 unchanged. In the live
tree a combat objective is `defeat_enemy`, which neither pursuit branch handles (engagement is the hostile
branch), so the typed resolve is exercised by `reach_location` objectives that carry the field, such as a
resumed `COMBAT_ENGAGE` committed intention.

**Node 3 never yields `node_id`/`building_id`** — an objective resolved only via the
`target_position` fallback still navigates to the position, but arrival dispatches to a bare
idle `EntityUpdate` rather than INTERACT/EAT/REST (no ID to act on). This is accepted, disclosed
scope for this ticket: it fixes "does the entity ever navigate there," not "what happens once it
arrives" — extending arrival-dispatch for `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` project kinds
(mirroring the `GUILD` kind's own dedicated `GuildVisitPhase`,
`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`) is a separate, not-yet-filed follow-up.

**Note (`TCK-20260824-TOWN-CENTER-POINTER-FIX`):** As of this ticket, `WorldCompiler.compile()`
sets `state.town_center` to a real compiled value (the centroid of the first `type=="town"`
region in declaration order — see `docs/world/compiler_contract.md` step 2a and
`docs/mechanics/06_worldbuilding_foundation.md` § Town Center Derivation) rather than always
leaving it at the `(0.0, 0.0)` dataclass default. Nothing above this note asserted anything
factually false under the old behavior, but the examples and resolution logic in this section
should now be read as describing a real-value world, not a `(0,0)`-only one.

## 8. Wound/Scar Tactical Signals (TCK-20260824-TACTICAL-WOUND-SCAR-WIRING)

`evaluate_entity_intent` reads the structured wound/scar penalty aggregates already exposed by
`WoundService` (never re-deriving them) as additional, strictly additive OR-conditions layered on
top of the existing `hp_percent`/`hp_ratio` checks in this contract's §4 and §6:

- **Cover-seeking/retreat gate** (`tactical.py:483-494`): fires independently of `hp_percent` when
  summed active-wound penalties (`WoundService.get_wound_stat_penalties(...)`) reach `>= 9.0`
  (equivalent to a single wound at `severity >= 0.6`). Separately, the gate's own `hp_percent`
  threshold is raised by `0.01` per aggregate scar-penalty point
  (`WoundService.get_scar_stat_penalties(...)` summed), capped at `+0.10`.
- **Guarding logic, PROTECTOR role** (`tactical.py:542-582`): an ally (or the group leader)
  qualifies as guard-priority when combined wound+scar distress reaches `>= 5.0` (equivalent to a
  single wound at `severity >= 0.4`), alongside the existing `hp_ratio < 0.8` (leader) /
  `< 0.7` (other allies) checks.

Both are pure read-only decision signals over already-committed authoritative wound/scar state —
they do not create, heal, or otherwise mutate any `WoundState`/`ScarState`. For zero-wound/
zero-scar entities both reduce to exactly the pre-ticket `hp_percent`/`hp_ratio`-only behavior.
See `docs/mechanics/02_combat_laws.md` § 5 for the full formula derivation and
`docs/parity_ledger/combat_movement.yaml` for parity status.

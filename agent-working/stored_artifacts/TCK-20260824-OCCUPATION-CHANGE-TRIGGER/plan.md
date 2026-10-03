---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-OCCUPATION-CHANGE-TRIGGER
artifact_type: plan
tags: [combat, economy, social, world]
---

# Implementation Plan — TCK-20260824-OCCUPATION-CHANGE-TRIGGER

## Summary

Add a new tier-5 goal, `GoalKind.OCCUPATION_CHANGE`, that fires for `EntityRole.CITIZEN` entities
whose home region has an open slot for `SHOPKEEPER`/`WORKER`/`GUARD` (config-driven density target,
mirroring `spawn.py`'s monster-density pattern) and who clear a baseline aptitude check on the
attribute associated with that role family (`entity.attributes`, not `AptitudeComponent` or
`known_recipes` — both were checked and found unusable as a live signal, see Design Decisions
below). The goal materializes through a bespoke branch in
`StrategicIntelligenceSystem.evaluate_strategic_intent` (mirroring `RegionStabilizationGoalScorer`'s
own precedent and explicitly avoiding its documented score-scale-mismatch pitfall), resolves through
the existing `ObjectiveIntentResolver` → `ActionIntentAdapter` pipeline (the same general-purpose
"every other `ObjectiveKind`" path already used by `ASK_INFORMATION`/`REQUEST_CRAFT`/`BUY_ITEM`,
traced directly in `src/engine/tactical.py:264-310`), and commits the transition as a plain
`EntityUpdate(identity=IdentityUpdate(role_set=<int>))` — the same typed-update shape
`extract_patches()` (`src/engine/patches.py:700-702`) already folds into an `IdentityPatch`, so no
new mutation path is introduced. A tick-scan completion check marks the project `COMPLETED` once the
entity's role is no longer `CITIZEN`. No new `EntityRole` value is added — the recommendation in
investigation.md (`CITIZEN` as source, `SHOPKEEPER`/`WORKER`/`GUARD` as destinations, all four
pre-existing) is followed exactly, so the ticket's Out-of-Scope constraint holds without any
blocking conflict (see "EntityRole Extension Check" below — resolved, not a blocker).

### Design Decisions (grounded in source reads this session, not the investigation's inferences)

1. **Skill/aptitude signal = `entity.attributes`, not `known_recipes`/`AptitudeComponent`.**
   Verified `src/core/recipes.py:15-40`: all three hardcoded entries in `RecipeRegistry._recipes`
   leave `required_role` at its `None` default (`recipes.py:13`), and a repo-wide grep confirms
   `crafting.py:33` is the *only* consumer of `Recipe.required_role` — no content-driven catalog
   populates it (`RecipeDefinition` in `src/content/schema.py:306-312` has no `required_role`
   field at all). Using `known_recipes` × `required_role` as the skill signal would make
   `OCCUPATION_CHANGE` permanently unreachable (`utility` always `0.0`), directly breaking AC #1 and
   test_plan.md tests 2/5/6/8/9. Also checked `AptitudeComponent` (`src/core/state.py:515-528`): a
   repo-wide grep for its per-stat fields (`str_apt`, `end_apt`, `cha_apt`, etc.) outside
   `state.py` itself returns zero hits — it has no live consumer anywhere, so there is no evidence
   its values are ever meaningfully differentiated at spawn. `AttributeComponent`
   (`src/core/state.py:439-450`, fields `strength/agility/vitality/endurance/intelligence/spirit/
   wisdom/perception/charisma`, each defaulting to `5`) is the only candidate that is (a) always
   populated on every entity, (b) has real, documented live consumers elsewhere (derived combat
   stats, progression — Mechanics Bible Ch01), and (c) requires no new durable state. The match
   condition uses the field's own dataclass default (`>= 5`) rather than an invented magic
   threshold — this guarantees the gate is not accidentally unreachable the way the recipe-based
   design would have been, while still being a real (if permissive) condition, consistent with the
   ticket's own "entry-level" framing (a citizen minimally qualified for *an* open entry job, not a
   highly selective specialist gate).
2. **Role→attribute family mapping** (new ground, no existing occupation-to-attribute mapping
   exists per investigation.md Risk #3): `SHOPKEEPER → charisma` (trade/negotiation),
   `WORKER → endurance` (physical labor), `GUARD → strength` (patrol/combat-adjacent duty) —
   chosen to align with `RoleSemanticsService`'s existing family groupings cited in
   investigation.md (`is_civilian` groups `CITIZEN`+`SHOPKEEPER`; `is_worker` is `WORKER`-only
   labor family; `GUARD` is in the `is_combatant` family) rather than an arbitrary pairing.
3. **Open-slot signal = config-driven target density, mirroring `spawn.py`'s
   `region_monster_count`/`target_count` pattern exactly** (confirmed via direct read of
   `src/world/spawn.py:53-79` and `src/world/spawn_config.py`). No building-capacity field exists
   on `BuildingState` (investigation confirmed, `state.py:1020-1030`), so the building-derived
   alternative investigation.md floated is not implementable without new durable state — ruled out.
4. **Execution path is `ObjectiveIntentResolver` → `ActionIntentAdapter`, not
   `CoreActions`/`ActionRouter`** — investigation.md Risk #5 flagged this as an untraced gap and
   guessed `CoreActions.execute_change_occupation`. Traced directly this session:
   `src/engine/tactical.py:264-310` routes **every** `ObjectiveKind` other than `REACH_LOCATION`/
   `DEFEAT_ENEMY` through `ObjectiveIntentResolver.resolve()` → `ActionIntentAdapter.execute()`.
   `ActionIntentAdapter.execute()` (`src/engine/intent/action_intent.py`) already has a
   precedented "cheap intent, no material/gold gate, direct `EntityUpdate` early-return" pattern
   (`ASK_INFORMATION` branch, lines ~131-176) — `CHANGE_OCCUPATION` follows that exact shape
   instead of routing through `ActionRouter.execute_action`/`CoreActions`, which is reserved for
   intents needing the router's requirement-gated dispatch. This is a **narrower, more accurate**
   mechanism than investigation.md's own guess; no `core_actions.py`/`action_router.py` file needs
   to change.
5. **Target-string encoding avoids a real collision hazard found this session.**
   `TacticalDecisionSystem._resolve_target_position` (`src/engine/tactical.py:703-753`) treats a
   truthy `obj.target` as *first* an int-castable resource-node/building id
   (`state.resource_nodes.get(candidate_id)` / `state.buildings.get(candidate_id)`) before falling
   back to `obj.target_position`. Setting `obj.target` to a bare small integer (e.g. `"1"` for
   `SHOPKEEPER`) would risk silently resolving to an unrelated resource node or building with that
   same id. Following the existing `"town_center"`-style precedent already used by `TownScorer`/
   `RecoverScorer` (cited in `_resolve_target_position`'s own docstring, `tactical.py:714-726`),
   `obj.target` is set to a non-int-castable, non-coordinate string (`f"role_{dest_role}"`), which
   safely falls through to the `obj.target_position` fallback (the region centroid, set explicitly
   — mirrors `RegionStabilizationGoalScorer`'s own centroid pattern,
   `region_stabilization_scorer.py:69-72`) and is parsed back out by prefix-stripping in
   `ActionIntentAdapter`, mirroring the existing `"opp_craft_"`/`"opp_buy_"` prefix-parsing
   precedent already in that same file (`action_intent.py:70-71,229-230`).
6. **`CAREER_CHANGE` gets an explicit completion check; `REGION_STABILIZATION` does not, and that's
   fine.** Checked directly: no `ProjectKind.STABILIZE` (or `"stabilize"`) completion branch exists
   anywhere in `intelligence.py`'s per-tick project scan — that project apparently never explicitly
   completes (it is only ever abandoned via the consecutive-rejection backoff or superseded). This
   is acceptable for `REGION_STABILIZATION`'s open-ended nature but not appropriate to copy for
   `CAREER_CHANGE`, which is a discrete, verifiable, one-shot transition (`entity.identity.role`
   flips from `CITIZEN` to a real destination role) — an explicit condition-based completion check
   (mirroring the existing `hunger`/`fatigue` checks' style at `intelligence.py:1360-1378`, not the
   string-ID-parsing `harvesting` style) is added so the project does not permanently occupy the
   entity's `max_active_projects` budget after a successful transition.

## Steps

### Step 1 — New strategic enum values
**Files:** `src/core/strategic.py`
**Change:** Add three new enum members, each with an inline Design-Decision-style comment
explaining non-collision (mirroring the existing convention at `strategic.py:133-147` for
`ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`/`REGION_STABILIZATION`, and at `strategic.py:164-167` for
`ProjectKind.STABILIZE`):
- `GoalKind.OCCUPATION_CHANGE = "occupation_change"` (added after `REGION_STABILIZATION` in the
  `GoalKind` enum, `strategic.py:121-147`). Comment must document its tie-break position under
  `intelligence.py:1495`'s `sort(key=lambda x: (-x.utility, x.kind))`: alphabetically it sorts
  after `combat_engage`/`combat_retreat`/`fatigue`/`guild`/`harvesting`/`hunger` (loses ties to
  those six — consistent, since `harvesting` already precedes `hunger` alphabetically today, i.e.
  this codebase's tie-break scheme is not a strict global tier-priority encoding, only pairwise
  collision avoidance) and before `recover`/`region_stabilization`/`resolve_blocker`/`social`/
  `social_contract`/`town_return`/`z_adventure_route` (wins ties against those seven). Does not
  collide with any existing `GoalKind`/`ProjectKind`/`ObjectiveKind` value (verified by reading
  `strategic.py:104-167` in full this session).
- `ObjectiveKind.CHANGE_OCCUPATION = "change_occupation"` (added to the `ObjectiveKind` enum,
  `strategic.py:104-118`, after `RETURN_TOWN`). None of the 13 existing values fit an occupation
  transition (verified by reading the full list, `strategic.py:106-118`).
- `ProjectKind.CAREER_CHANGE = "career_change"` (added to the `ProjectKind` enum,
  `strategic.py:150-167`, after `STABILIZE`). None of the 12 existing values fit (verified by
  reading the full list, `strategic.py:152-164`).
**Do NOT touch:** Any existing enum member's value or position; `DirectiveKind`, `BlockerKind`,
`ContractKind`, `ConcernKind`, `TurningPointKind` (unrelated enums in the same file).
**Verify:** No standalone test for this step alone (enums have no behavior); covered by Step 3's
`test_occupation_change_goal_registered_in_goal_registry` and Step 4's materialization test, which
both fail to import/construct correctly if these values are missing or misnamed.

### Step 2 — New occupation-slot config
**Files:** `src/world/occupation_config.py` (new file)
**Change:** Mirror `src/world/spawn_config.py`'s `BASE_MONSTER_DENSITY`/area-formula pattern
(read in full this session — `spawn_config.py:38-39`, formula applied at `spawn.py:75-79`) for the
three civilian occupation roles:
```python
from src.core.enums import EntityRole

# Target headcount per 100x100 area unit for each civilian occupation role (mirrors
# spawn_config.py's BASE_MONSTER_DENSITY exactly — same area-normalization formula, applied
# per-region in occupation_change_scorer.py, not here).
BASE_OCCUPATION_DENSITY: dict[int, float] = {
    EntityRole.SHOPKEEPER: 0.5,
    EntityRole.WORKER: 1.0,
    EntityRole.GUARD: 0.5,
}
# Floor so every active region has at least one open slot per role, even a small region — mirrors
# spawn.py's `target_count = max(2, target_count)` monster-density floor pattern (spawn.py:76),
# using 1 instead of 2 since civilian roles are intentionally sparser than monster density.
MIN_OCCUPATION_SLOTS = 1
```
**Do NOT touch:** `src/world/spawn_config.py` itself (monster-density config is out of scope — this
is a new sibling file, not an edit to the existing one) or `src/world/spawn.py` (monster spawn
logic, unrelated to civilian occupation).
**Verify:** No standalone test (pure config data); exercised indirectly by Step 3's tests.

### Step 3 — New `OccupationChangeGoalScorer` + registration
**Files:** `src/ai/goals/occupation_change_scorer.py` (new file), `src/ai/goals/__init__.py`
**Change:** New `OccupationChangeGoalScorer` class implementing the `GoalScorer` protocol
(`src/ai/goals/base.py:16-18`, read this session), structured to mirror
`RegionStabilizationGoalScorer` (`src/ai/goals/region_stabilization_scorer.py`, read in full this
session) exactly:
1. Role gate: `if entity.identity.role != EntityRole.CITIZEN: return GoalScore(kind=GoalKind.OCCUPATION_CHANGE, utility=0.0, target_id=None)`.
2. Resolve entity's region via `LegalityServiceV2.get_region_for_position(entity.navigation.position, state)` (same call shape used by `RegionStabilizationGoalScorer.score()`, `region_stabilization_scorer.py:31` — lazy import per that file's own documented reason, `region_stabilization_scorer.py:41-44`); return `utility=0.0` if `region is None`.
3. Single-pass count: iterate `state.entities.values()` once, tallying live (`combat.alive`) entities per candidate role (`SHOPKEEPER`, `WORKER`, `GUARD`, in that fixed ascending-int-value order) whose own region (via the same `get_region_for_position` call) matches. This bounds the scan to one pass regardless of how many of the 3 roles are checked (documented perf note, not a blocker — same per-entity-per-tick cost class as the existing `RegionStabilizationGoalScorer`/`spawn.py` region lookups).
4. Compute `target_count = max(MIN_OCCUPATION_SLOTS, int((area / 10000.0) * BASE_OCCUPATION_DENSITY[role]))` per candidate role, using `region.bounds` exactly as `spawn.py:73-76` does (`xmin, ymin, xmax, ymax = region.bounds; area = (xmax-xmin)*(ymax-ymin)`).
5. Skill/aptitude check per Design Decision 1/2 above: `getattr(entity.attributes, _ROLE_APTITUDE_ATTR[role]) >= 5` where `_ROLE_APTITUDE_ATTR = {EntityRole.SHOPKEEPER: "charisma", EntityRole.WORKER: "endurance", EntityRole.GUARD: "strength"}`.
6. Pick the first candidate role (fixed order: `SHOPKEEPER`, `WORKER`, `GUARD`) where both `current_count < target_count` AND the skill check passes. If none, `return GoalScore(kind=GoalKind.OCCUPATION_CHANGE, utility=0.0, target_id=None)`.
7. Else, build `target_pos` as the region centroid (byte-identical formula to `region_stabilization_scorer.py:69-72`), `raw_score = _ADVENTURE_ROUTE_SCORE_MAX * 0.9` (flat constant — Design Decision: unlike `RegionStabilizationGoalScorer`'s urgency-proportional score, this trigger is a binary match/no-match condition, not a graduated signal, so a flat near-ceiling constant honestly represents "conditions met, fire now" without inventing a fake continuous metric), `utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` (both constants imported lazily from `intelligence.py`, mirroring `region_stabilization_scorer.py:45-48`'s own documented lazy-import reason), and return `GoalScore(kind=GoalKind.OCCUPATION_CHANGE, utility=utility, target_id=region.id, target_pos=target_pos, metadata={"region_id": region.id, "dest_role": int(dest_role), "raw_score": raw_score, "proj_kind": ProjectKind.CAREER_CHANGE, "obj_kind": ObjectiveKind.CHANGE_OCCUPATION})`.

In `src/ai/goals/__init__.py`: add `from src.ai.goals.occupation_change_scorer import OccupationChangeGoalScorer` and `GoalRegistry.register(GoalKind.OCCUPATION_CHANGE, OccupationChangeGoalScorer())`, following the exact existing pattern (`__init__.py:5,25`).
**Do NOT touch:** `RegionStabilizationGoalScorer`, `AdventureGoalScorer`, `SocialContractGoalScorer`, or any of the 10 `scorers.py` classes — read-only precedent, not modified.
**Verify:** New file `tests/unit/strategic/test_occupation_change_scorer.py` — implements test_plan.md tests 1, 3, 4:
- `test_occupation_change_scorer_returns_zero_utility_for_non_eligible_role`
- `test_occupation_change_scorer_does_not_fire_without_open_slot`
- `test_occupation_change_goal_registered_in_goal_registry` (also assert `GoalKind.OCCUPATION_CHANGE not in _COMMITTED_INTENTION_ELIGIBLE_KINDS`, imported from `intelligence.py:101-105` — Anti-Drift Test Guard #3 from test_plan.md; this set is a bespoke-materialization allowlist and `OCCUPATION_CHANGE` must not silently join it)
- test_plan.md test 2 (`test_occupation_change_scorer_fires_when_open_slot_and_skill_match`) also belongs in this file — construct a `CITIZEN` entity with `attributes.charisma >= 5` (default `5` already qualifies) in a region with zero existing `SHOPKEEPER`s, asserting non-zero utility and a resolvable `target_id`.

### Step 4 — Materialization branch in `evaluate_strategic_intent`
**Files:** `src/systems/strategic_systems/intelligence.py`
**Change:** Add an `elif best_candidate.kind == GoalKind.OCCUPATION_CHANGE:` branch immediately
after the existing `elif best_candidate.kind == GoalKind.REGION_STABILIZATION:` branch
(`intelligence.py:1592-1626`, read in full this session), following its exact structure:
```python
elif best_candidate.kind == GoalKind.OCCUPATION_CHANGE:
    region_id = best_candidate.metadata.get("region_id")
    dest_role = best_candidate.metadata.get("dest_role")
    proj_kind = best_candidate.metadata.get("proj_kind")
    obj_kind = best_candidate.metadata.get("obj_kind")
    obj = ObjectiveState(
        id=f"obj_career_{region_id}_t{current_tick}",
        kind=obj_kind,
        target=f"role_{dest_role}",
        target_position=best_candidate.target_pos,
        status=ObjectiveStatus.ACTIVE,
    )
    candidate_proj = ProjectState(
        id=f"project_career_{region_id}_t{current_tick}",
        kind=proj_kind,
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id=obj.id,
        lock_until_tick=min(current_tick + 10, current_tick + 50),
        created_tick=current_tick,
        score=best_candidate.metadata.get("raw_score", 0.0),  # NEVER best_candidate.utility —
        # see region_stabilization_scorer.py's own New Finding #7 comment and
        # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG; _score_scale_max()
        # (intelligence.py:108-126) classifies ProjectKind.CAREER_CHANGE onto the 2.9-ceiling
        # scale, not the 100-ceiling utility scale.
    )
```
This must be inserted **before** the generic `else:` branch (`intelligence.py:1627-1645`), exactly
where `REGION_STABILIZATION`'s branch already sits, so a bespoke `ObjectiveKind.CHANGE_OCCUPATION`
never falls into the generic branch's synthetic `ObjectiveState(kind="reach_location", ...)`.
**Do NOT touch:** The `ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`/`REGION_STABILIZATION` branches
themselves, `RouteToProjectMapper`, `_score_scale_max()`, `_ADVENTURE_ROUTE_SCORE_MAX`,
`_GOAL_UTILITY_SCORE_MAX` (read-only constants — reused, never modified, per Scope Guards).
**Verify:** New integration-style unit test in `tests/unit/strategic/test_occupation_change_scorer.py`
(test_plan.md test 5, `test_occupation_change_materializes_into_project_with_correct_kind`) —
construct a `CITIZEN` entity in a qualifying region, call
`StrategicIntelligenceSystem.evaluate_strategic_intent` directly (or drive it via
`GoalRegistry`/`ScoreModifierSystem` far enough to reach tier 5), assert the winning candidate
materializes a `ProjectState` with `kind == ProjectKind.CAREER_CHANGE` and `score` sourced from
`raw_score` (not `utility`), and that `_score_scale_max(ProjectKind.CAREER_CHANGE) ==
_ADVENTURE_ROUTE_SCORE_MAX` (Anti-Drift Test Guard #2 from test_plan.md — the tie-break/scale
class this test exists specifically to catch a third time).

### Step 5 — Completion check in the per-tick project scan
**Files:** `src/systems/strategic_systems/intelligence.py`
**Change:** Add `from src.core.enums import EntityRole` to the module's imports (not currently
imported — verified by grepping the file's import block this session). Add a new completion-check
block immediately after the existing `fatigue` block (`intelligence.py:1370-1378`, before the
`resolve_blocker` timeout block at `:1380`), mirroring the `hunger`/`fatigue` condition-based style
(not the string-ID-parsing `harvesting` style, since there is no node/building id to parse here —
completion is a pure role-state check):
```python
if project.kind == ProjectKind.CAREER_CHANGE and entity.identity.role != EntityRole.CITIZEN:
    return StrategicUpdate(
        projects_add_or_update=[replace(project, status=ProjectStatus.COMPLETED)],
        current_project_id_set="",
        current_objective_id_set="",
        boredom_delta=boredom_upd,
        leads_add_or_update=memory_upd.leads_add_or_update,
        leads_remove=memory_upd.leads_remove
    )
```
Per Design Decision 6, this deliberately differs from `REGION_STABILIZATION`, which has no
completion-check branch anywhere in this scan (verified directly this session) — that omission is
appropriate for an open-ended stabilization effort but not for `CAREER_CHANGE`'s discrete,
one-shot role transition, which would otherwise permanently occupy a `max_active_projects` slot
once the role has already changed.
**Do NOT touch:** The `harvesting`/`hunger`/`fatigue`/`resolve_blocker`/`shopping` completion
blocks themselves (`intelligence.py:1343-1427`) — this is an additive insertion, not a
restructuring of the existing scan.
**Verify:** Unit test in `tests/unit/strategic/test_occupation_change_scorer.py` — hand-construct
an entity+`StrategicComponent` with an active `CAREER_CHANGE` project and `entity.identity.role`
already set to a non-`CITIZEN` value, call the scan function, assert the returned
`StrategicUpdate.projects_add_or_update` contains the project with `status ==
ProjectStatus.COMPLETED`.

### Step 6 — `ObjectiveIntentResolver` mapping
**Files:** `src/domains/adventure/resolver.py`
**Change:** Add one `elif` branch to `ObjectiveIntentResolver.resolve()`
(`src/domains/adventure/resolver.py:24-89`, read in full this session), placed after the existing
`elif objective.kind == ObjectiveKind.RETURN_TOWN: kind = "RETURN_TOWN"` branch and before the
final `else: kind = "MOVE_TO"` fallback:
```python
elif objective.kind == ObjectiveKind.CHANGE_OCCUPATION:
    kind = "CHANGE_OCCUPATION"
```
No other change to this function — `target_id = objective.target` (already set at the top of the
function, line 44) and the `intent_payload["position"]` handling (lines 46-47) are unconditional
and already correct for this new kind.
**Do NOT touch:** Any other `elif` branch in this function.
**Verify:** Unit test (new, `tests/unit/domains/adventure/test_occupation_change_resolver.py` or
appended to an existing `resolver.py` test file if one exists — search before creating) asserting
`ObjectiveIntentResolver.resolve(entity_id, ObjectiveState(kind=ObjectiveKind.CHANGE_OCCUPATION,
target="role_1", ...), payload={}).kind == "CHANGE_OCCUPATION"`.

### Step 7 — `ActionIntentAdapter` dispatch branch
**Files:** `src/engine/intent/action_intent.py`
**Change:** Add `IdentityUpdate` to the existing `from src.core.updates import ...` line
(`action_intent.py:6` — currently imports `EntityUpdate, NavigationUpdate, InventoryUpdate,
BiologicalUpdate, ResourceTransferIntent`, confirmed `IdentityUpdate` is absent). Append
`CHANGE_OCCUPATION` to the `ActionIntent.kind` docstring comment listing known kind values
(`action_intent.py:15`). Add a new `elif intent.kind == "CHANGE_OCCUPATION":` branch to
`ActionIntentAdapter.execute()`, placed alongside the other direct-`EntityUpdate`-return branches
(`ASK_INFORMATION`, `REQUEST_CRAFT`, `BUY_ITEM` — lines ~131-255) and before the final `else:
router_payload["action"] = intent.kind` fallback (line 257):
```python
elif intent.kind == "CHANGE_OCCUPATION":
    role_str = intent.target_id.removeprefix("role_") if isinstance(intent.target_id, str) else None
    valid = bool(role_str) and role_str.isdigit()
    trace = IntentTrace(
        intent_kind=intent.kind,
        actor_id=intent.actor_id,
        why_selected=intent.reason or "change occupation",
        opportunity_source_id=intent.source_opportunity_id,
        requirements_checked=tuple(reqs),
        execution_result="SUCCESS" if valid else "FAILED_REQUIREMENTS: unparseable_role_target",
    )
    cls._traces.append(trace)
    if not valid:
        return {entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}
    return {entity.id: EntityUpdate(
        entity_id=entity.id,
        identity=IdentityUpdate(role_set=int(role_str)),
    )}
```
This is the **sole new producer of `IdentityUpdate(role_set=...)` in the entire codebase** — it
constructs a plain `EntityUpdate`, exactly the same typed-update shape every other branch in this
function already returns (e.g. `ASK_INFORMATION`'s `EntityUpdate(entity_id=..., inventory=...)`,
lines 143-146). It does not call `replace()` on `EntityState`/`IdentityComponent` directly and does
not construct an `IdentityPatch` itself — `extract_patches()` (`src/engine/patches.py:700-702`)
and `IdentityPatch.apply()` (`patches.py:170-228`) remain the only code that ever builds or applies
an `IdentityPatch`, satisfying AC #2 and the CLAUDE.md Durable State Rule.
**Do NOT touch:** The `MOVE_TO`, `REST_AT_INN`, `REPAIR_GEAR`, `HARVEST_RESOURCE`, `ATTACK_TARGET`,
`ASK_INFORMATION`, `REQUEST_CRAFT`, `BUY_ITEM` branches, or the trailing
`ActionRouter.execute_action(...)` fallback call (line 260) — this new branch always returns early,
it never reaches that fallback.
**Verify:** New test file `tests/unit/engine/intent/test_action_intent_occupation_change.py` (search
first for an existing `action_intent.py` test file to append to instead, per test_plan.md's own
"search before creating" convention) — implements test_plan.md test 6
(`test_occupation_change_completion_issues_role_set_identity_update`): construct an `ActionIntent(
kind="CHANGE_OCCUPATION", actor_id=<id>, target_id="role_4")`, call
`ActionIntentAdapter.execute(entity, intent, ...)`, assert the returned
`EntityUpdate.identity.role_set == 4`. Also add the architecture-guard test (test_plan.md test 7,
`test_role_set_applies_through_identity_patch_only`) in `tests/architecture/` — a static grep-style
scan (mirroring `test_legacy_enum_usage_boundaries.py`'s own scan style) confirming
`IdentityUpdate(` with a `role_set=` keyword argument, or any direct `IdentityComponent(`/
`replace(..., role=` construction, appears nowhere in `src/` outside `action_intent.py` (this
step's new branch) and `patches.py`/`apply.py` (the existing authoritative path).

### Step 8 — End-to-end reachability, `entity_role_changed` event, ENTITY-007 update
**Files:** `tests/integration/strategic/` or `tests/integration/` (new file — search first),
`tests/unit/observability/test_event_extractor_identity.py`, `docs/event_ledger/entity.yaml`
**Change:**
1. New integration test mirroring `test_recipe_learned_fires_through_real_kernel_tick_once`
   (`tests/unit/observability/test_event_extractor_identity.py:129-160`, read in full this
   session): load `sandbox_world`, construct/patch a `CITIZEN` entity with a qualifying attribute
   (or rely on the default `5` baseline already qualifying, per Design Decision 1) in a region with
   room under the `WORKER`/`SHOPKEEPER`/`GUARD` target count, run a real `Kernel.tick_once()` loop
   for a bounded number of ticks, and assert `entity.identity.role` changed to the expected
   destination role by the end (test_plan.md test 8,
   `test_occupation_change_reachable_through_real_kernel_tick_once`). This directly proves AC #1.
2. Append `test_entity_role_changed_event_fires_on_real_occupation_transition` to
   `tests/unit/observability/test_event_extractor_identity.py` (test_plan.md test 9) — same
   real-`Kernel.tick_once()` scenario as (1), asserting `EventExtractor.extract(...)` produces a
   `SimulationEvent(event_type="entity_role_changed", payload={"role": <new>, "previous_role":
   <old>})`, using the exact diff-block logic already at `event_extractor.py:403-409` (read this
   session — unmodified, this test only proves it now fires through a live producer).
3. Update `docs/event_ledger/entity.yaml` ENTITY-007's `notes` field (`entity.yaml:55-60`, read in
   full this session): change the `unscored_intentional` framing to record that
   `entity_role_changed`/`entity_faction_changed`... — specifically only the `role_set` half —
   is now `verified/live`, citing this ticket and the new test as `v2_evidence`-equivalent proof.
   `entity_faction_changed` stays `unscored_intentional` (out of scope — no `faction_set` producer
   is added by this ticket).
**Do NOT touch:** The 6 other pre-existing tests in `test_event_extractor_identity.py` (recipe/
cooldown/suppression/zero-delta tests) — append only, do not modify their assertions (AC #5 /
test_plan.md's "4 existing identity-event tests still pass unmodified" — all 8 existing functions,
not just 4, per test_plan.md's own wording-ambiguity note).
**Verify:** The two new tests above, plus a full run of
`tests/unit/observability/test_event_extractor_identity.py` confirming all pre-existing functions
still pass byte-for-byte unmodified.

### Step 9 — Flag (not fix) the cooperation `role == 1` magic number
**Files:** `src/domains/cooperation/providers.py`, `src/domains/cooperation/evaluators.py`
**Change:** Add a `# TODO(TCK-20260824-OCCUPATION-CHANGE-TRIGGER):` comment immediately above each
of the three sites — `providers.py:52` (`if cand.identity.role != 1:`), `providers.py:88` (`cost =
20 if cand.identity.role == 1 else 0`), `evaluators.py:180` (`if candidate.identity.role == 1:`) —
stating plainly: `EntityRole(1)` is `SHOPKEEPER` (`src/core/enums.py:8`), not a distinct
"Hireling"/"Guild Merchant" role; now that `role_set` is runtime-reachable via `OCCUPATION_CHANGE`,
any entity that transitions into `SHOPKEEPER` will be silently treated as a Hireling/Guild Merchant
here — disclosed, not fixed, per this ticket's scope. This is a comment-only change — **no
conditional logic, comparison operator, or numeric literal at any of the three sites may change.**
**Do NOT touch:** The `role_fit`/`cost`/`poor_penalty` computation logic surrounding these lines,
or any other line in either file. The `_has_hostiles_or_dead_cache` invalidation gap
(`apply.py:307-309`) and the missing `"identity"` dirty tag (`apply_plan.py:333-341`) — both
confirmed-harmless, explicitly out of scope per investigation.md Anti-Drift Hazards — **must not be
touched by this ticket at all**, not even a comment.
**Verify:** (Optional, recommended per test_plan.md test 10)
`test_cooperation_role_1_magic_number_flagged_not_fixed` in `tests/unit/domains/cooperation/` —
locks in the current (disclosed) behavior so any future fix is a deliberate, visible test change.
A `git diff` review of `providers.py`/`evaluators.py` at Verify time must show comment-only changes.

### Step 10 — Architecture guard: register the new module
**Files:** `tests/architecture/test_legacy_enum_usage_boundaries.py`
**Change:** Add `"src/ai/goals/occupation_change_scorer.py"` to `ALLOWED_MODULES`
(`test_legacy_enum_usage_boundaries.py:42-79`, read this session) with a one-line rationale comment
matching the convention already used for `occupancy_snapshot.py`/`legality.py`/`evolution.py`/
`regional_sovereignty.py`/`spawn.py`/`combat.py`/`combat_rewards.py` (per investigation.md's
Architecture guard note) — this new file reads `EntityRole.CITIZEN`/`EntityRole.SHOPKEEPER`/
`EntityRole.WORKER`/`EntityRole.GUARD` directly.
**Do NOT touch:** `FORBIDDEN_MODULES`, or any other existing `ALLOWED_MODULES` entry.
**Verify:** `tests/architecture/test_legacy_enum_usage_boundaries.py` (all functions) still passes;
`test_report_untracked_migration_targets` no longer reports the new file.

### Step 11 — Docs
**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`
**Change:**
1. In `04_strategic_cognition.md` §1's Tier table (lines ~13-20, read this session), add a row:
   `**Tier 4: Economic** | occupation_change | Taking an open, skill-matched job when idle
   (CITIZEN).` alongside the existing `harvest`/`trade`/`craft` row, or as an additional bullet in
   the same Tier 4 cell.
2. Correct the "**Sole live tier-5 candidate**" sentence (line 30, read this session — already
   false, since `SocialContractGoalScorer` and `RegionStabilizationGoalScorer` are also registered)
   to instead name all four live tier-5 candidates registered in `src/ai/goals/__init__.py`
   (`AdventureGoalScorer`, `SocialContractGoalScorer`, `RegionStabilizationGoalScorer`,
   `OccupationChangeGoalScorer`) — this correction is required regardless of this ticket, since the
   sentence is already stale, and adding a fourth candidate without fixing it makes the inaccuracy
   strictly worse (investigation.md Anti-Drift Hazards).
3. Add a new entry to `docs/parity_ledger/strategic_cognition.yaml` (schema per
   `docs/parity_ledger/schema.json`, format matching the existing `STRAT-258` entry read in full
   this session): `id` (next available `STRAT-NNN`), `text` describing the occupation-change
   mechanic, `status: verified`, `priority: P1` (matches the ticket's own `## Priority`), `v2_evidence`
   citing `src/ai/goals/occupation_change_scorer.py`,
   `src/systems/strategic_systems/intelligence.py` (materialization + completion branches),
   `src/engine/intent/action_intent.py` (the `IdentityUpdate(role_set=...)` producer), `test_path`
   citing the Step 3/4/8 tests, and a `divergence_note` explaining this is genuinely new ground (no
   prior occupation/career entry existed anywhere in `docs/parity_ledger/*.yaml`, confirmed by
   investigation.md's grep).
**Do NOT touch:** `docs/engine/authoritative_pipeline.md`,
`docs/engine/authoritative_mutation_pipeline_contract.md`, `docs/core/entities.md`,
`docs/parity_ledger/town_resource.yaml` — investigation.md confirmed none require a scoped edit for
this ticket.
**Verify:** `tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage` passes (fails
Verify if `04_strategic_cognition.md` is cited in the ticket's Related Docs / investigation.md
required-bullet list but `git status` shows it untouched).

### Step 12 — Full regression sweep (AC #4)
**Files:** None (verification only).
**Change:** None.
**Do NOT touch:** N/A.
**Verify:** Run the exact scoped pytest command block from test_plan.md:
```
pytest tests/unit/observability/test_event_extractor_identity.py \
       tests/unit/strategic/ \
       tests/unit/domains/adventure/ \
       tests/unit/domains/cooperation/ \
       tests/unit/domains/faction/ \
       tests/unit/domains/optimization/ \
       tests/unit/world/ \
       tests/unit/combat/ \
       tests/architecture/test_legacy_enum_usage_boundaries.py \
       -m "not slow"

pytest tests/integration/strategic/ tests/integration/ -k "occupation or identity or role" -m "not slow"

pytest tests/unit/world/test_economy_contract.py -m "not slow"
```
All of these must pass green, including the 12 confirmed consumers' existing suites listed in
test_plan.md (spawn density, occupancy tile priority, combat legality readiness, crafting
`required_role` gate, adventure route scoring, routine role-boost, combat rewards/lethality,
military conflict GUARD check, cooperation phase-7 suite, evolution/regional-sovereignty HERO
checks if coverage exists) and all 8 functions in `test_event_extractor_identity.py`. `evolution.py`
and `regional_sovereignty.py` HERO checks have no dedicated test file (test_plan.md items 11/12) —
re-search for coverage before assuming none exists; this ticket does not need to add coverage for
that pre-existing gap, only confirm it is not newly broken.

## Scope Guards

- **Do not extend the `EntityRole` enum** (`src/core/enums.py:6-12`). This plan's design uses only
  `CITIZEN` (source) and `SHOPKEEPER`/`WORKER`/`GUARD` (destinations), all four already present —
  verified no new value is needed anywhere in this design (see "EntityRole Extension Check" below).
- **Do not modify `src/domains/cooperation/providers.py:52,88` or `evaluators.py:180` beyond adding
  the `# TODO` comment specified in Step 9.** No conditional/comparison/numeric-literal change at
  those sites under any circumstance in this ticket.
- **Do not touch `src/engine/apply_plan.py`'s dirty-tag precompute** (no `"identity"` tag exists,
  confirmed harmless per investigation.md) **or `src/engine/apply.py:307-309`'s
  `_has_hostiles_or_dead_cache` invalidation** (confirmed harmless — no hostility check reads
  `identity.role`). Both are real, disclosed, out-of-scope findings; fixing either is a separate
  future ticket.
- **Do not modify `RegionStabilizationGoalScorer`, `SocialContractGoalScorer`,
  `AdventureGoalScorer`, or any of the 10 `scorers.py` classes.** Read-only precedent only.
- **Do not modify `_score_scale_max()`, `_ADVENTURE_ROUTE_SCORE_MAX`, `_GOAL_UTILITY_SCORE_MAX`, or
  `_COMMITTED_INTENTION_ELIGIBLE_KINDS`** (`intelligence.py:32-126`) — reused as-is;
  `GoalKind.OCCUPATION_CHANGE` must NOT be added to `_COMMITTED_INTENTION_ELIGIBLE_KINDS` (asserted
  by a guard test in Step 3).
- **Do not modify `src/world/spawn.py` or `src/world/spawn_config.py`** — Step 2 adds a new sibling
  config file, not an edit to the monster-density system.
- **Do not route the new action through `src/engine/domain/core_actions.py` or
  `src/engine/domain/action_router.py`** — Design Decision 4 traced the real dispatch path to
  `ActionIntentAdapter`/`ObjectiveIntentResolver`; neither `core_actions.py` nor `action_router.py`
  needs any change for this ticket.
- **Do not fix the `EntityRole(1)`/`"Hireling"` naming mismatch itself** — flag only (Step 9).

### EntityRole Extension Check (resolved, not a blocker)

Investigation.md's own Out-of-Scope reminder asked this plan to flag it explicitly if the trigger
design required a new `EntityRole` value. It does not: `CITIZEN` (source), `SHOPKEEPER`, `WORKER`,
`GUARD` (all three destinations) are all pre-existing values (`src/core/enums.py:6-12`). No step in
this plan references or requires a value outside that set. This is not listed under "Unresolved
Questions" below because it was checked and resolved during planning, not left open.

## Dependency Map

- Step 1 (enums) has no dependencies; must land before Steps 3, 4, 5, 6, 7.
- Step 2 (config) has no dependencies; independent of Step 1; must land before Step 3.
- Step 3 (scorer + registration) depends on Steps 1 and 2.
- Step 4 (materialization branch) depends on Steps 1 and 3 (reads `GoalKind.OCCUPATION_CHANGE` and
  the scorer's `metadata` shape).
- Step 5 (completion check) depends on Step 1 (`ProjectKind.CAREER_CHANGE`, `EntityRole` import).
  Independent of Steps 3/4/6/7 — can be implemented and unit-tested in isolation with a
  hand-constructed project/entity.
- Step 6 (resolver mapping) depends on Step 1 (`ObjectiveKind.CHANGE_OCCUPATION`). Independent of
  Steps 3/4/5.
- Step 7 (action-intent dispatch) depends on Step 6's target-string encoding convention
  (`f"role_{dest_role}"` / `"role_"` prefix) but not on its code directly — both must agree on the
  encoding, documented once in Design Decision 5 and referenced by both steps.
- Step 8 (end-to-end tests + doc) depends on Steps 1, 3, 4, 5, 6, 7 all being complete (it is the
  full-chain proof).
- Step 9 (cooperation flag) is fully independent of every other step — can be done first, last, or
  in parallel.
- Step 10 (architecture guard) depends on Step 3 (the new file must exist to be added to
  `ALLOWED_MODULES`).
- Step 11 (docs) depends on Steps 1-8 being functionally complete (docs describe the shipped
  mechanic and cite its test paths).
- Step 12 (regression sweep) depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A new AI-selectable action/goal produces `IdentityUpdate(role_set=...)` reachable through a real `Kernel.tick_once()` run | Steps 1, 2, 3, 4, 5, 6, 7 | Step 8: `test_occupation_change_reachable_through_real_kernel_tick_once` |
| The existing authoritative apply path commits the value with no bespoke parallel mutation | Step 7 (sole new producer, plain `EntityUpdate`) | Step 7: `test_role_set_applies_through_identity_patch_only` (architecture guard) |
| `event_extractor.py`'s `entity_role_changed` fires with correct payload on a real transition; ENTITY-007's note updated to verified/live | Step 8 | Step 8: `test_entity_role_changed_event_fires_on_real_occupation_transition` |
| All 12 confirmed consumers read the new role consistently with no stale-cache regression | Steps 1-9 (no consumer file is modified; only `IdentityUpdate` producer added) | Step 12: full scoped regression sweep |
| All 4 (8, per test_plan.md's wording note) existing identity-event tests still pass unmodified | Step 8 (append-only change to the test file) | Step 8 + Step 12: full run of `test_event_extractor_identity.py` |

## Anti-Drift Notes

- **Score-scale mismatch (the recurring TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
  class):** Step 4's materialization branch must pass `best_candidate.metadata.get("raw_score",
  0.0)` as `ProjectState.score`, **never** `best_candidate.utility`. This is the third time this
  exact class of bug has been documented as a pitfall (`ADVENTURE_ROUTE`, `SOCIAL_CONTRACT`,
  `REGION_STABILIZATION` all carry the same warning) — Step 4's verify test explicitly re-checks
  `_score_scale_max(ProjectKind.CAREER_CHANGE)` for this reason.
- **Tie-break ordering:** `GoalKind.OCCUPATION_CHANGE`'s string value (`"occupation_change"`) was
  chosen deliberately (Step 1) — do not rename it without re-deriving its position in
  `sort(key=lambda x: (-x.utility, x.kind))` relative to all 13 existing values.
- **`_COMMITTED_INTENTION_ELIGIBLE_KINDS` must stay unchanged** — `OCCUPATION_CHANGE` uses a bespoke
  materialization branch (Step 4) with synthetic `metadata` a committed intention has no legitimate
  way to populate, exactly like `ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`/`REGION_STABILIZATION` before
  it (`intelligence.py:97-105`).
- **The single-pass region-entity scan in Step 3 is an O(n) cost per entity per tier-5 evaluation**
  — this is the same cost class `RegionStabilizationGoalScorer`/`spawn.py` already pay for their
  own region lookups; not a new performance regression class, but worth noting if a future
  performance-contract review scopes tier-5 scorer costs.
- **`entity.attributes >= 5` is a deliberately permissive gate**, not a fabricated selective
  threshold — Design Decision 1 explains why (using the field's own dataclass default avoids
  accidentally making the trigger unreachable, the way the recipe-based alternative would have
  been). If empirical testing during implementation (Step 8's real-`Kernel.tick_once()` run) shows
  this fires too rarely or too often against `sandbox_world`'s actual spawn distribution, the
  threshold constant may be adjusted without changing the underlying mechanism — this is expected
  implementation-time calibration, not a plan deviation.
- **`obj.target` encoding (`f"role_{dest_role}"`) is load-bearing for avoiding a real collision
  hazard** (Design Decision 5) — do not change it to a bare integer string; `
  TacticalDecisionSystem._resolve_target_position` would silently misresolve it against an
  unrelated resource node or building id.

## Unresolved Questions

None. The one question investigation.md flagged as a potential blocker for this plan — whether the
trigger design would require extending the `EntityRole` enum — was checked directly during planning
and resolved: it does not (see "EntityRole Extension Check" above). All other investigation.md open
questions (which `EntityRole` is "entry-level," which attribute/skill signal to use, how the open
slot is computed, where the `IdentityUpdate` producer lives) were genuine multiple-valid-
implementation decisions this plan was directed to make, and each is recorded above under "Design
Decisions" with its supporting evidence.

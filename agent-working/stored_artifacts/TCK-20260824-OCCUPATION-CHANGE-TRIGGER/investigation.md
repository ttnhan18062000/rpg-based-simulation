---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-OCCUPATION-CHANGE-TRIGGER
artifact_type: investigation
tags: [combat, economy, social, world]
---

# Investigation — TCK-20260824-OCCUPATION-CHANGE-TRIGGER

**Search-before-grep note:** `mcp__knowledge-search__search_docs` returned
`{"error":"index not found","action":"run make knowledge-index"}` for the ticket topic query. The
documented fallback, `python3 tools/knowledge_search.py query "..." --top-k 5`, also returned
`knowledge index not found — run make knowledge-index`. Both semantic-search tools were
unavailable this session (pre-existing environment gap, not caused by this investigation).
`graphify query` (three separate queries: `"occupation change trigger role_set IdentityUpdate goal
hierarchy"`, `"GoalHierarchy goal scoring domain action"`, `"EntityRole SHOPKEEPER role==1
cooperation"`) ran successfully and returned generic BFS node dumps (`IdentityUpdate`, `EntityRole`,
`Domain`/`Action`, etc.) confirming file locations already known from the ticket and the
orchestrator's own prior query, but no additional topic-specific edges beyond what direct source
reads below establish. All findings below are grounded in direct source reads following the
graphify node list.

## Current Behavior

### `EntityRole` enum and role semantics
- `src/core/enums.py:6-12`: `EntityRole(IntEnum)` = `HERO=0, SHOPKEEPER=1, MONSTER=2, CITIZEN=3,
  WORKER=4, GUARD=5`. No "UNEMPLOYED" or "ENTRY_LEVEL" value exists.
- **No explicit "entry-level/unemployed" role value exists**, but `CITIZEN` functions as the de
  facto default/entry-level role across every content-resolution fallback path:
  - `src/content_semantics/role.py:36,41` (`RoleSemanticsService.get_legacy_entity_role`): falls
    back to `EntityRole.CITIZEN` when a role string can't be matched, and again on `KeyError`.
  - `src/worldbuilding/compiler.py:55`: same `CITIZEN` default when role family can't be resolved.
  - `src/content_semantics/role.py:67-72` (`is_civilian`): groups `CITIZEN` and `SHOPKEEPER` as
    the "civilian"/"service"/"trade" family, distinct from `is_worker` (`WORKER` only,
    "worker"/"labor" family) and `is_combatant` (`HERO`, `MONSTER`, `GUARD`,
    "combatant"/"adventurer"/"recon"/"attacker"/"ecological_predator"/"ecological_leader").
  - `src/content/schema.py:181`: `valid_roles = {"HERO","SHOPKEEPER","MONSTER","CITIZEN","WORKER","GUARD"}`
    — the full and only legal set.
  - This makes **`EntityRole.CITIZEN` the strongest existing candidate for "entry-level/
    unemployed"** — it is the generic catch-all with no combat/trade/labor specialization — but
    this is an inference, not an explicit "unemployed" semantic anywhere in the codebase. Flagged
    as an open question below (not decided here, per the ticket's own instruction that only the
    trigger *shape* is pre-decided).

### `IdentityUpdate.role_set` and the authoritative apply path
- `src/core/updates.py:220-236` (`IdentityUpdate`): `role_set: Optional[int] = None` is one of 15
  fields; `is_noop()`/`merge()` already handle it correctly (`updates.py:239,251`).
- `src/engine/patches.py:148-228` (`IdentityPatch.apply`): the **sole** site that reads
  `role_set` and commits it: `patches.py:193` — `if u_id.role_set is not None: rl =
  u_id.role_set` — then folds it into the `replace(new_id, role=rl, ...)` call at
  `patches.py:223-228`. `extract_patches()` (`patches.py:683-745`) is the only place
  `IdentityPatch` gets constructed from an `EntityUpdate`, and `ApplyPath._apply_entity_update_to_dict`
  (`src/engine/apply.py:448-457`) is the only caller of `extract_patches`, itself only reachable
  through `ApplyPath.apply_generation`/`apply_partial`/`_apply_entity_update` — the single
  authoritative state-commit surface (`src/engine/apply.py`). **Confirmed: `IdentityPatch.apply`
  is the ONLY sanctioned path that can commit `role_set` into durable `IdentityComponent.role`.**
  There is no bespoke parallel mutation path anywhere for role.
- **Confirmed via `grep -rn "IdentityUpdate(" src/`** (excluding the two definition files): zero
  call sites anywhere in `src/` pass `role_set=...`. Every existing `IdentityUpdate(...)`
  construction (progression/leveling.py, blacksmith.py, evolution.py, skill_actions.py,
  core_actions.py, class_hall.py, intelligence.py, lifecycle.py, conservation.py) sets other
  fields only (`evolution_points_delta`, `recipes_learned`, `cooldown_updates`,
  `unspent_ap_delta`, `craft_target`). This matches the ticket's claim exactly: no `role_set=`
  assignment site exists anywhere in `src/` today.

### The existing goal-scoring pipeline (the plug-in point)
This is the concrete mechanism the ticket calls "the existing goal-scoring pipeline":
- `src/ai/goals/base.py`: `GoalScore` (frozen dataclass: `kind`, `utility`, `target_id`,
  `target_pos`, `metadata`), `GoalScorer` (Protocol with one `score(entity, state) -> GoalScore`
  method), `GoalRegistry` (class-level dict `GoalKind -> GoalScorer`, `register()`,
  `get_all_scores()` — returns scores in deterministic key-sorted order).
- `src/core/strategic.py:121-147` (`GoalKind(str, Enum)`): 13 current values —
  `HARVESTING, FATIGUE, HUNGER, SOCIAL, TOWN_RETURN, COMBAT_ENGAGE, COMBAT_RETREAT, RECOVER,
  RESOLVE_BLOCKER, GUILD, ADVENTURE_ROUTE ("z_adventure_route"), SOCIAL_CONTRACT,
  REGION_STABILIZATION`. Comments on the last three document a deliberate tie-break sort-order
  design (`sort(key=lambda x: (-x.utility, x.kind))` at `intelligence.py:1495`) — any new
  `GoalKind` value's *string* ordering relative to existing values needs the same deliberate
  reasoning applied when it's chosen (Plan-phase decision, not decided here).
- `src/ai/goals/__init__.py`: registers 13 scorer instances against their `GoalKind` at import
  time — 10 "generic" scorers (`src/ai/goals/scorers.py`: `HarvestScorer`, `SleepScorer`,
  `EatScorer`, `SocialScorer`, `TownScorer`, `CombatEngageScorer`, `CombatRetreatScorer`,
  `RecoverScorer`, `ResolveBlockerScorer`, `GuildNeedScorer`) plus 3 dedicated-file scorers
  (`AdventureGoalScorer`, `SocialContractGoalScorer`, `RegionStabilizationGoalScorer`).
- `src/systems/strategic_systems/intelligence.py:1459-1652`
  (`StrategicIntelligenceSystem.evaluate_strategic_intent`, tier 5 "Goal Scoring & Routine
  Biasing"): calls `GoalRegistry.get_all_scores(entity, state)` (`:1460`), applies routine/role
  biasing via `RoutineService.get_routine_utility_boost`/`get_role_utility_boost` (`:1484-1489`),
  leadership influence (`:1492`) and `ScoreModifierSystem.apply_modifiers` (`:1494`), sorts by
  `(-utility, kind)` (`:1495`), and picks the first candidate with `utility >= 20.0` and a
  resolvable `target_id`/`target_pos` (`:1498-1502`). The winning `GoalKind` is then materialized
  into a `ProjectState`/`ObjectiveState` — either through a **dedicated branch**
  (`GoalKind.ADVENTURE_ROUTE` at `:1527`, `GoalKind.SOCIAL_CONTRACT` at `:1555`,
  `GoalKind.REGION_STABILIZATION` at `:1592`, each needing bespoke `ProjectKind`/`ObjectiveKind`
  resolved upstream in the scorer's `metadata`) or the **generic "else" branch** (`:1627-1645`)
  used by all 10 plain `scorers.py` kinds, which builds a `ProjectState(kind=best_candidate.kind,
  ...)` directly with a synthetic `ObjectiveState(kind="reach_location", ...)`.
  `RegionStabilizationGoalScorer` (`src/ai/goals/region_stabilization_scorer.py`) is the most
  recent precedent for adding a brand-new goal end-to-end and documents its own design decisions
  in inline comments — the closest structural analog for `OCCUPATION_CHANGE` if it needs a
  bespoke `ProjectKind`/`ObjectiveKind` (which it likely does, since none of the 13 existing
  `ObjectiveKind` values — `REACH_LOCATION, ACQUIRE_ITEM, DEFEAT_ENEMY, INVESTIGATE,
  REACH_SERVICE, ASK_INFORMATION, BUY_ITEM, REQUEST_CRAFT, REACH_RESOURCE, HARVEST_RESOURCE,
  ACCEPT_QUEST, REST, RETURN_TOWN` — `src/core/strategic.py:104-118` — obviously represents
  "change occupation").
- `_COMMITTED_INTENTION_ELIGIBLE_KINDS` (`intelligence.py:101-105`) is a separate, narrower
  allowlist (only the 10 "generic" `scorers.py` kinds) for a different feature (committed
  intentions materializing without a live scorer this tick) — a new `GoalKind` does **not** need
  to join this set unless the committed-intention feature is also explicitly extended to it
  (out of scope per the ticket unless Plan decides otherwise).
- **What actually produces the `IdentityUpdate(role_set=...)`**: the goal-scoring pipeline above
  only gets an entity as far as an *active `ProjectState`/`ObjectiveState` with a target*. No
  existing project-completion branch in `intelligence.py` (harvesting/hunger/fatigue/
  resolve_blocker/shopping completion checks, `:1343-1427`) issues any further `EntityUpdate`
  beyond a `ProjectStatus` transition. The actual `IdentityUpdate` commit precedent lives in
  `src/engine/domain/core_actions.py`'s `CoreActions.execute_*` handlers (dispatched via
  `src/engine/domain/action_router.py`'s `ActionRouter.execute_action` on an explicit
  `payload["action"]` string, e.g. `execute_train` at `core_actions.py:178-213` issues
  `IdentityUpdate(recipes_learned=...)` through a `ResourceTransferIntent.identity_upd`). A new
  `CoreActions.execute_change_occupation` (or equivalent), reached once the `OCCUPATION_CHANGE`
  objective is satisfied (e.g. entity reaches the target building/region and a completion check
  analogous to the existing harvesting/shopping ones fires), is the natural place to construct
  `IdentityUpdate(role_set=...)` following the `execute_train`/`execute_repair` pattern of routing
  the actual state change through a `ResourceTransferIntent`-style flow or a direct
  `EntityUpdate(identity=IdentityUpdate(role_set=...))`. This wiring detail (exact completion
  trigger → action dispatch → `IdentityUpdate` construction) is Plan-phase work, not decided here.

### "Open occupation slot" — does NOT currently exist as tracked state
Searched all listed Related Code Areas for a capacity/slot concept tied to civilian roles
(SHOPKEEPER/WORKER/GUARD) and found **none**:
- `src/engine/occupancy_snapshot.py` (`OccupancySnapshot.from_state`, `:22-45`): a **per-tile
  tie-break priority** read model (`HERO`→100, `MONSTER`→50 base, +100 if low-HP), fully
  recomputed every tick from scratch — not a per-region job-capacity concept, and not cached
  across ticks (no staleness concern for it specifically).
- `src/world/spawn.py` (`SpawnService.process_spawns`, `:22-121`): tracks **monster density per
  region** only (`region_monster_count`, `:53-60`, compared against a computed `target_count`
  derived from region area × `BASE_MONSTER_DENSITY` × hazard — `spawn_config.py`). No equivalent
  density/target tracking exists for `SHOPKEEPER`/`WORKER`/`GUARD`.
- `src/core/state.py:236-291` (`RegionState`): no `capacity`/`slots`/`headcount` field for any
  role. `src/core/state.py:1020-1030` (`BuildingState`): no capacity/slot field either — just
  `hp`, `functional`, `inventory`, `price_modifiers`.
- `src/world/regional_sovereignty.py`, `src/world/camp.py`: both read `EntityRole.HERO`/
  `EntityRole.MONSTER` for taxation/spawning logic; neither tracks job slots.
- **Conclusion: "open occupation slot" must be computed, not read from existing state.** The
  closest existing precedent is `spawn.py`'s `region_monster_count` density-counting pattern
  (count live entities with a given role in a region, compare to a config-driven target). A
  concrete implementation will need either (a) a new config-driven "target headcount per
  role per region" constant (mirroring `spawn_config.py`'s `BASE_MONSTER_DENSITY`/
  `DIFFICULTY_ZONES`), or (b) a building-driven definition (e.g. a functional `BuildingState` of
  the relevant kind in the region implies N open slots for its role, currently untracked). This is
  a genuine open design question for Plan — flagged below, not resolved here.

### "Skill/aptitude" — what exists on entity state
- `src/core/state.py:515-528` (`AptitudeComponent`): `learning_rate`, `stamina_efficiency`, and
  per-stat genetic multipliers (`str_apt`, `agi_apt`, `vit_apt`, `end_apt`, `int_apt`, `spi_apt`,
  `wis_apt`, `per_apt`, `cha_apt`) — growth-rate multipliers, not occupation-relevant skill
  levels.
- `IdentityComponent.learned_skills` (via `IdentityUpdate.learned_skills`,
  `updates.py:233`) and `IdentityComponent.known_recipes` are the closest things to an
  occupation-relevant "skill" — e.g. a `WORKER`-slot match could plausibly check
  `known_recipes`/`learned_skills` against a recipe/skill tagged to that occupation family
  (`RoleSemanticsService.get_role_family`/`is_worker` already classify roles this way, just not
  entities' skills against them). `entity.attributes` (raw STR/AGI/VIT/etc.) is the other
  candidate "aptitude" signal. Which of these constitutes "skill/aptitude match" for this ticket
  is a genuine multiple-valid-implementations decision for Plan — not decided here.

### The 12 confirmed role-reading consumers (file:line)
1. `src/world/spawn.py:55` — `SpawnService.process_spawns`: `entity.identity.role ==
   EntityRole.MONSTER` (density counting; unaffected by civilian role changes).
2. `src/engine/occupancy_snapshot.py:33-35` — `OccupancySnapshot.from_state`: `role ==
   EntityRole.HERO`/`MONSTER` tile-priority base. Test:
   `tests/unit/domains/optimization/test_occupancy_snapshot.py`,
   `tests/unit/domains/optimization/test_cache_invalidation_policy.py`.
3. `src/engine/legality.py:504-505` — same `HERO`/`MONSTER` priority pattern (readiness/turn
   ordering). Tests: `tests/unit/combat/test_phase5_combat_legality.py`,
   `tests/unit/combat/test_combat_legality_regression.py`.
4. `src/systems/economy_systems/crafting.py:33` — `CraftingSystem.craft`: `if
   recipe.required_role is not None and entity.identity.role != recipe.required_role: return
   None, "INSUFFICIENT_RANK"`. Test: `tests/unit/world/test_economy_contract.py` (and related
   economy tests).
5. `src/domains/adventure/scoring.py:139,144,151,353` —
   `AdventureRouteScorer.score`: `GUARD`+`HUNT_WEAK_ENEMY`, `SHOPKEEPER`+trade routes, `HERO`+
   quest-opportunity urgency boosts, plus `HERO` class-synergy multiplier and non-`HERO`
   quest-attractiveness halving (`:174-200`). Tests:
   `tests/unit/domains/adventure/test_phase3_route_scoring.py`,
   `tests/unit/domains/adventure/test_memory_informed_scoring.py`,
   `tests/unit/domains/adventure/test_capability_confidence_scoring.py`.
6. `src/systems/world_systems/routine.py:130-147` — `RoutineService.get_role_utility_boost`:
   `SHOPKEEPER`+SHOPKEEPING, `HERO`+QUEST, `WORKER`+HARVESTING, `GUARD`+PATROLLING boosts, called
   every tick from `intelligence.py:1487` for **every** `GoalScore` (including a new
   `OCCUPATION_CHANGE` one — it will receive this boost call with whatever `project_kind` string
   the new scorer's `kind.lower()` resolves to; harmless no-op unless a matching branch is added).
   Test: `tests/unit/strategic/test_role_biasing.py`.
7. `src/engine/combat_rewards.py:35-117` — `RewardClassificationService`: `_CLASSIFICATIONS`
   dict keyed by `EntityRole.MONSTER`/`HERO`; `defender_role == EntityRole.HERO` gates
   `rebirth_eligible`. Tests: `tests/unit/combat/test_combat_rewards.py`,
   `tests/unit/combat/test_combat_reward_trace.py`.
8. `src/engine/combat.py:136,610-615` — `defender.identity.role != EntityRole.HERO` gates
   lethality; `attacker.identity.role == EntityRole.HERO` picks `SLASH` vs `CRUSH` damage kind.
   Tests: `tests/unit/combat/` (multiple; combat regression suite).
9. `src/engine/military_conflict.py:122-136` —
   `MilitaryConflictService._find_guard_entities_in_region`: `identity.role ==
   EntityRole.GUARD`. Tests: `tests/unit/domains/faction/test_military_conflict_phase.py`,
   `test_siege_ledger.py`, `test_war_exhaustion.py`, `test_siege_model.py`,
   `test_territory_transfer.py`.
10. `src/domains/cooperation/providers.py:52` (actual line: `cand.identity.role != 1` at `:52`
    and `cost = 20 if cand.identity.role == 1 else 0` at `:88`) and
    `src/domains/cooperation/evaluators.py:180` — both use the **bare int magic number `1`**
    instead of `EntityRole.SHOPKEEPER`, with an inline comment calling role `1` "Hireling"/
    "Guild Merchant/Hireling" — **confirmed mismatch**: `EntityRole(1)` is actually
    `SHOPKEEPER` per `core/enums.py:8`, not a distinct "Hireling"/"Guild Merchant" role (no such
    `EntityRole` value exists). Tests:
    `tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py`,
    `test_phase7_cooperation_decision_service.py`, `test_phase7_party_objective_alignment.py`,
    `test_phase7_cooperation_learning.py`, `test_phase7_cooperation_postures.py`.
11. `src/engine/evolution.py:111-112` — `entity.identity.role == EntityRole.HERO` gates a
    hero-specific evolution/reward branch. No dedicated test file found by targeted search;
    flagged as a coverage gap below (existing generic evolution/progression tests may cover it
    indirectly — not independently re-verified).
12. `src/world/regional_sovereignty.py:48,82` —
    `RegionalSovereigntyService.process_taxation`/`apply_sovereignty_debuffs`: `entity.identity.role
    == EntityRole.HERO` gates hero-only taxation and the "conquered" debuff. No dedicated test
    file found by targeted search (`tests/architecture/test_legacy_enum_usage_boundaries.py` only
    covers the enum-usage-boundary architecture guard, not sovereignty behavior) — flagged as a
    coverage gap below.

Additionally, three **presentation/observability consumers** (not decision-branching logic, but
pass the raw `role` int through to external surfaces — will pick up new values automatically with
zero code change, listed for completeness since they're in Related Code Areas):
- `src/api/presenters/state_presenter.py:118` — `"role": entity.identity.role` (raw int passthrough).
- `src/observability/live/entity_inspector.py:25,139-140,177` — `role: Optional[int]` dataclass field.
- `src/observability/personality/recorder.py:89,94,105` — `role: Optional[int]`, read from
  `identity.role`.

### The dirty-tag / cache-invalidation surface (AC4: "no stale-cache regression")
- `src/engine/apply_plan.py:333-341` (dirty tag precompute): tags are
  `movement/biological/combat/strategic/social/lifecycle/inventory/attribute` — **there is no
  `"identity"` tag**, so an `IdentityPatch`-only change (including a future `role_set` change) is
  invisible to `dirty_tags_by_entity`. Checked whether this matters: `src/core/dirty.py:14-38`
  (`get_relevant_entity_ids`)'s domain list (`interactions, redirection, groups, shop, capacity,
  town, all`) has no domain keyed to an "identity" tag either, so no existing incremental-scan
  consumer currently depends on identity changes being dirty-tagged. Not a regression risk for
  this ticket's scope, but noted as a pre-existing gap (see Anti-Drift Hazards).
- `src/engine/apply.py:307-309` — `pass_hostile` (the `_has_hostiles_or_dead_cache` invalidation
  check) is invalidated only on `update.entities_add` or `u.identity.faction_set is not None` —
  **`role_set` changes do NOT invalidate this cache.** Confirmed this is currently safe because
  every hostile-detection read site found (`adventure/scoring.py`, combat code) compares
  `identity.faction`, never `identity.role`, for hostility — so a role-only transition correctly
  does not need to bust this particular cache. Documented here so a future consumer that keys
  hostility off role doesn't silently rely on a cache that was never designed to invalidate for it.

### Architecture guard relevant to any new `EntityRole.X` reference
- `tests/architecture/test_legacy_enum_usage_boundaries.py`: scans all of `src/` for
  `EntityRole.<MEMBER>`/`Faction.<MEMBER>` usage and enforces zero occurrences in
  `FORBIDDEN_MODULES` (a short, unrelated allowlist of clean catalog-driven modules — none of
  this ticket's likely touch points are in it). Any new module this ticket adds
  (e.g. a new `src/ai/goals/occupation_change_scorer.py` reading `EntityRole.CITIZEN`) will show
  up as an **"untracked migration target"** (`test_report_untracked_migration_targets`) —
  reported via `capsys`, does **not** fail CI — but the convention followed by every other
  scorer/consumer file touched by this ticket (`occupancy_snapshot.py`, `legality.py`,
  `evolution.py`, `regional_sovereignty.py`, `spawn.py`, `combat.py`, `combat_rewards.py` are all
  explicitly in `ALLOWED_MODULES` with a comment) is to add the new file to `ALLOWED_MODULES` with
  a one-line rationale comment, not leave it untracked.

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md` §1 "Goal Hierarchy & Prioritization"**: defines the
  Tier 1-4 concern table (Survival/Biological/Social/Economic) and states `AdventureGoalScorer` is
  the "**Sole live tier-5 candidate**" (line 30). **This claim is already stale as of this
  investigation** — `SocialContractGoalScorer` and `RegionStabilizationGoalScorer` are also
  registered tier-5 candidates in `src/ai/goals/__init__.py` today, and the doc was not updated
  when either shipped. Adding a fourth tier-5 candidate (`OCCUPATION_CHANGE`) makes this
  inaccuracy strictly worse if left unaddressed — the doc must be corrected regardless of
  which specific new goal ships next.
- **§2 "Interruption Resistance"**: `Switch_Allowed = New_Goal_Score > (Current_Goal_Score +
  Interruption_Margin)` — the general goal-switching law (`GoalRegistry`'s tier-5 competition via
  `evaluate_project_switch`) that any new `GoalKind.OCCUPATION_CHANGE` candidate is automatically
  subject to; no special-casing needed, but the doc's tier table itself has no "occupation
  change"/career row and needs one describing what tier it competes at (most likely Tier 4
  Economic, alongside `harvest`/`trade`/`craft`, given the ticket's own "Careers &
  Apprenticeships" framing).
- **Durable State Rule (`CLAUDE.md`)**: role_set must be represented as a typed `IdentityUpdate`
  field committed only through `IdentityPatch.apply` — already true structurally (§ above); the
  new goal/action code must not invent a bespoke mutation path (e.g. must not construct
  `EntityState`/`IdentityComponent` directly with `replace()` outside `ApplyPath`).
- **Strategic/Tactical Rule (`CLAUDE.md`)**: the new `OCCUPATION_CHANGE` goal is enduring-direction
  (strategic) — correctly modeled as a `GoalKind`/`ProjectState`, not as extra tactical scoring
  stacked onto an existing goal.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §1's Tier 1-4 concern table has no row for
  occupation/career change, and its "Sole live tier-5 candidate" claim (line 30) is already false
  and must be corrected to describe the (now four) live tier-5 `GoalKind` candidates once
  `OCCUPATION_CHANGE` ships.
- `docs/event_ledger/entity.yaml`: ENTITY-007's `notes` field explicitly states `role_set/
  faction_set have zero real producers anywhere in src/ ... the event exists but is currently
  unreachable by any path since the mechanic itself is unimplemented` — this sentence becomes
  false the moment a real `role_set=` producer exists and must be updated to `verified/live`
  (the ticket's own AC #3 names this exact change).
- `docs/parity_ledger/strategic_cognition.yaml`: no existing entry covers occupation/career
  transition (`grep -n "occupation\|career"` across all `docs/parity_ledger/*.yaml` returns zero
  hits). A new entry is required recording the new goal-hierarchy mechanic, its `v2_evidence`
  (file:line of the new scorer/materialization branch), and a `test_path` — required regardless of
  priority tier chosen, but especially if this is scoped `P0` given the CLAUDE.md rule that P0
  entries require a passing `test_path`.

The following docs were considered but are **not** required to change for this ticket's scope:
`docs/engine/authoritative_pipeline.md` and `docs/engine/authoritative_mutation_pipeline_contract.md`
document the general apply-path/mutation-rule law, not per-field semantics — `IdentityPatch.apply`
already covers `role_set` structurally in the existing contract text (no new mutation *rule* is
introduced, only a new *producer* of an existing field), so neither needs a scoped edit. Similarly
`docs/core/entities.md` documents entity lifecycle/identity in general terms already accurate for
this change (identity `role` was already a documented mutable field via `IdentityUpdate`) and
`docs/parity_ledger/town_resource.yaml` (the economy/resource subsystem file, path:
`docs/parity_ledger/town_resource.yaml`, under `docs/`) was checked for an existing
"open occupation slot" or town-employment entry and found to have none related to this scope —
if Plan decides the "open occupation slot" computation belongs conceptually to the economy/town
subsystem rather than strategic cognition, a new entry could alternatively land there instead of
`strategic_cognition.yaml`; this is a Plan-phase placement decision, not something this
investigation resolves, so neither file is listed under the required-bullet format above.

## Parity Ledger Overlap

- No existing `docs/parity_ledger/*.yaml` entry references "occupation" or "career" anywhere
  (confirmed via `grep -rn "occupation\|career" docs/parity_ledger/*.yaml` — zero hits). This is
  genuinely new ground, not a divergence from an already-tracked entry.
- Entries that reference `role` and are adjacent to this ticket's blast radius (for awareness,
  none require a status change from this ticket alone unless the Plan phase decides the new
  scorer/consumer interaction changes their behavior):
  - `docs/parity_ledger/strategic_cognition.yaml` — `test_initial_role_derivation`,
    `test_dynamic_role_transition_with_hysteresis`, `test_role_bias_influence`,
    `test_role_aware_tactical_biases` entries (lines ~1948-1979) already describe *role-related*
    goal-hierarchy behavior (initial role derivation, hysteresis-based dynamic role transition) —
    worth reading in full during Plan, since `test_dynamic_role_transition_with_hysteresis` in
    particular sounds adjacent to "occupation change" and should be confirmed as describing a
    different, already-implemented mechanic (e.g. combat `tactical_role`, not `EntityRole`) before
    concluding no overlap. Not independently re-verified in this pass — flagged as an open
    question below.
  - `docs/parity_ledger/strategic_cognition.yaml:2942-3000` — the HERO-role adventure-eligibility
    entries (`TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER`) are a precedent for how a role-gate
    parity entry is written, but describe eligibility filtering, not role mutation.
  - `docs/parity_ledger/progression.yaml:1122-1123` — HERO-role class assignment at world
    compilation (`spawn_tables.yaml`) — spawn-time only, unaffected by a runtime trigger.
- No P0-priority entry was found anywhere referencing role/occupation, so the "P0 requires
  passing `test_path`" rule does not currently bind any existing entry for this scope — it will
  bind whatever priority Plan assigns the new entry it creates.

## Prior Work

- **`TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP`** (Related Ticket): this is the
  ticket that built `entity_role_changed`/`entity_faction_changed` in `event_extractor.py` and
  wrote ENTITY-007's ledger note in its current `unscored_intentional` form — the direct
  predecessor this ticket completes. No `stored_artifacts/TCK-20260808-ENTITY-IDENTITY-ROLE-
  FACTION-OBSERVABILITY-GAP/` directory exists (checked directly — not present), so no
  investigation.md/plan.md could be read from it; its findings are reconstructed here from the
  event_extractor.py/entity.yaml source directly instead.
- **`TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD`**, **`TCK-20260808-MONSTER-ROLE-MISTAGGING-
  INVESTIGATION`**, **`TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION`** (Related
  Tickets): none have a `stored_artifacts/{ticket_id}/` directory either (checked directly). No
  `docs/REGISTRY.yaml` exists in this worktree to cross-reference via the registry path instead
  (checked: absent), so the fallback path (scan `tickets/done/` by name similarity) was used, and
  none of the four named related tickets had recoverable stored artifacts to read beyond their own
  `tickets/done/{ticket_id}.md` files, which were not independently re-read in full given they are
  already named/summarized directly in this ticket's own "Related Tickets" section context.
- **`RegionStabilizationGoalScorer`** (`src/ai/goals/region_stabilization_scorer.py`,
  from `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`) is the closest and most recent structural
  precedent for "add a brand-new `GoalKind` end-to-end" — its own extensive inline comments
  document real worked-through pitfalls (score-scale mismatch between the tier-5 100-ceiling
  competition scale and the materialized `ProjectState.score`'s `_score_scale_max()`-governed
  scale; the "wins but stalls" defect from an unresolvable `target_pos`) that a Plan for
  `OCCUPATION_CHANGE` should explicitly re-check against, since both are new bespoke-materialization
  goals.
- **`TCK-20260812-COMMITTED-INTENTION-SEQUENCE`**: established `_COMMITTED_INTENTION_ELIGIBLE_KINDS`
  as a deliberately narrow allowlist — precedent that a new `GoalKind` does not automatically need
  to join every existing goal-adjacent mechanism.

## Risks and Open Questions

1. **Which `EntityRole` represents "entry-level/unemployed"?** `CITIZEN` is the strongest
   candidate (generic default/fallback across every role-resolution path — see Current Behavior)
   but this is inferred, not explicitly documented anywhere as "unemployed." **Recommendation**:
   use `EntityRole.CITIZEN` as the trigger-eligible source role, since it is already the
   catalog's own generic/default role and using it keeps this ticket within its Out-of-Scope
   constraint (no new `EntityRole` value). This is a decision Plan should make explicitly and
   record, not silently assume.
2. **"Open occupation slot" has no existing tracked representation** (see Current Behavior) — it
   must be computed fresh, most plausibly via a `spawn.py`-style per-region role-count vs.
   config-driven-target comparison. The exact target/capacity source (new config constant vs.
   building-derived) is unresolved and blocks a concrete implementation until Plan decides it.
3. **"Skill/aptitude match" is ambiguous between `learned_skills`/`known_recipes` and raw
   `attributes`/`AptitudeComponent`** — no existing occupation-to-skill mapping exists to match
   against. Plan must pick one and, if using recipes/skills, define (or confirm an existing)
   mapping from occupation role → required skill/recipe tag.
4. **Whether `OCCUPATION_CHANGE` needs a bespoke materialization branch (like
   `REGION_STABILIZATION`) or can use the generic branch** depends on whether a new `ObjectiveKind`
   is needed (very likely, since none of the 13 existing values fit) — if a new `ObjectiveKind` is
   added, the generic branch's synthetic `ObjectiveState(kind="reach_location", ...)` no longer
   applies and a bespoke branch mirroring `REGION_STABILIZATION`'s pattern is required. Not
   resolved here — Plan-phase design work.
5. **The actual `IdentityUpdate(role_set=...)` producer is a genuinely new piece of code** — no
   existing `ProjectState` completion branch in `intelligence.py` issues a further `EntityUpdate`
   on completion; every existing example of an `IdentityUpdate`-producing action (`execute_train`,
   `execute_repair`) is dispatched via `ActionRouter`/`CoreActions` on an explicit action-payload
   string, not via project completion. Plan must decide exactly how "objective reached" transitions
   into "issue `IdentityUpdate(role_set=...)`" — likely a new `CoreActions.execute_change_occupation`
   reached through a new `payload["action"] == "CHANGE_OCCUPATION"` branch in
   `ActionRouter.execute_action`, dispatched once the objective's target is reached (mirroring how
   `TacticalDecisionSystem` resolves other `ObjectiveKind`s into concrete actions — not
   independently traced end-to-end in this pass since `tactical.py` was not in Related Code Areas;
   flagged as a residual investigation gap if Plan needs the exact resolution call site).
6. **`docs/parity_ledger/strategic_cognition.yaml`'s existing `test_dynamic_role_transition_with_
   hysteresis` entry (line ~1958) was not independently re-read in full** — its name is close
   enough to "occupation change" that Plan should confirm it describes a genuinely different
   mechanic (most likely combat `tactical_role`, a `CombatComponent` field, not `EntityRole`)
   before concluding zero parity overlap.
7. **Gap in Related Code Areas**: `src/entities/identity_resolver.py` (listed as Related Code
   Area) is a read path only (`EntityIdentityResolver.resolve`, projecting `EntityRole`/`Faction`
   to string catalog IDs) — it has no write/consumer role in committing `role_set`, but its
   `_ROLE_COMPAT` dict (`identity_resolver.py:13-20`) will need the projection to keep working
   correctly after a runtime role change (it already reads `entity.identity.role` live each call,
   so no staleness concern — confirmed, not a gap).

## Anti-Drift Hazards

- **The cooperation/providers.py:52,88 and evaluators.py:180 `role == 1` magic-number bug**
  (flagged per ticket scope, not to be fixed here): today this is latent because no runtime path
  ever changes `role` to `1` (`SHOPKEEPER`) for an entity that wasn't already spawned as a
  `SHOPKEEPER`. Once `IdentityUpdate(role_set=...)` becomes live and reachable through
  `Kernel.tick_once()`, **any entity that transitions into `SHOPKEEPER` (role value `1`) via the
  new `OCCUPATION_CHANGE` goal will be silently reclassified by these two call sites as "Hireling"/
  "Guild Merchant"** (per their own inline comments) for cooperation-partner selection and cost
  calculation — a real behavior bug exposed by this ticket's own change, not a new one introduced
  by it. Both sites should at minimum be flagged with a `# TODO` cross-reference to this ticket
  if not fixed outright (fixing is out of this ticket's stated scope — "Flag (not necessarily
  fix)").
- **The `docs/mechanics/04_strategic_cognition.md` "Sole live tier-5 candidate" claim drifting
  further out of sync**: it is already wrong (misses `SOCIAL_CONTRACT`/`REGION_STABILIZATION`);
  do not let the `OCCUPATION_CHANGE` implementation add a fourth candidate without fixing the
  sentence — a natural place to silently skip a doc update because "the doc's already wrong
  anyway."
- **Scope creep into `EntityRole` enum extension**: the Out-of-Scope section explicitly forbids
  adding new `EntityRole` values unless the chosen trigger design requires it. Given the
  recommendation to treat `CITIZEN` as the source role and target `SHOPKEEPER`/`WORKER`/`GUARD` as
  destination roles (all four already exist), there should be no genuine need to add a new value —
  any implementation reaching for a new `EntityRole.APPRENTICE` or similar should be treated as a
  scope violation requiring a stop-and-report, not a quiet addition.
- **Scope creep into fixing the cooperation magic-number bug, the dirty-tag "identity" gap, or
  the `_has_hostiles_or_dead_cache` role-blind invalidation** — all three are real, disclosed
  findings from this investigation but are explicitly out of this ticket's stated scope (flag
  only for the first; the other two were not even asked to be flagged, found incidentally while
  verifying AC4's "no stale-cache regression" — do not fix either while implementing the trigger).
- **The 10-tier-5-scorer sort-order comment convention**: `GoalKind.ADVENTURE_ROUTE`,
  `SOCIAL_CONTRACT`, `REGION_STABILIZATION` each carry an inline comment explaining exactly why
  their string value was chosen relative to the others for deterministic tie-breaking. A new
  `GoalKind.OCCUPATION_CHANGE` value must carry the same class of reasoning (not just "pick a
  string") — omitting it would be a quality regression against the pattern this exact file has
  established three times running.

---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE
artifact_type: plan
tags: [testing, cognition, adventure, feature-flags]
---

# Implementation Plan — TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE

## Summary

Add one new test file, `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`,
that proves `AdventureDecisionPhase.apply()` (the currently-live path) and
`AdventureGoalScorer().score()` (the new, not-yet-wired path) are read-only and produce identical
route-family/raw_score decisions when driven by the same real `AuthoritativeState`. Coverage of
AC2's "15 route families" is split into two explicitly-labeled tiers, per investigation.md's
Critical Finding and this plan's own decision below: **6 families get real end-to-end shadow
comparisons** (the only families `AdventureRouteGenerator.generate()`'s hardcoded `kind_map` /
forced-route logic can actually produce from a real state today — `generator.py:38-45,98-163`),
and **all 15 families get a mapper-level-only parity check** against the shared
`RouteToProjectMapper.map_to_states()` function both paths call. No production code under `src/`
changes — this ticket is test-writing plus one manual `/simq-audit` invocation (AC5) plus three doc
updates. Two of investigation.md's flagged open questions are resolved here as explicit decisions,
not left open: STRAT-185's `test_path` stays `null` (wrong subject match — see Step 6), and the
6-vs-9 coverage split is adopted as final scope for AC2 (see Step 2/Step 3).

**Load-bearing correction to test_plan.md found during Plan-phase verification** (Fact-Verification
Requirement #1): test_plan.md's test #2 description says to read "the trace's `score` field,
`phase.py:185`" as the phase-side raw score. Reading `phase.py:176-193` directly: the `trace_records`
dict built at lines 182-187 (which contains `"score": result.selected.score`) is a **local variable
that is never attached to the returned `EntityUpdate`/`StateUpdate`** — it is built and then
immediately discarded; the only thing packed into `entity_updates[hero.id]` is
`EntityUpdate(entity_id=hero.id, strategic=strat_upd, property_updates=prop_upd)`, and `prop_upd`
(lines 177-180) carries only `last_routing_tick`/`last_routing_family`, no score. There is **no
accessible "trace" field on the value `AdventureDecisionPhase.apply()` returns.** The only real,
accessible source of the phase-side raw score is `entity_updates[hero.id].strategic.projects_add_or_update[0].score`
— confirmed by reading `StrategicIntelligenceSystem.evaluate_project_switch()`
(`src/systems/strategic_systems/intelligence.py:955-998`): when the entity has no
`current_project_id` (the case for every fresh fixture in this plan — builder-default entities have
no existing project), it returns `StrategicUpdate(projects_add_or_update=[candidate_project], ...)`
where `candidate_project` is exactly `result.proposed_project` built by
`AdventureDecisionService.decide()` at `src/domains/adventure/service.py:141-148` via
`RouteToProjectMapper.map_to_states(..., score=selected.score, ...)` — and `map_to_states()` sets
`ProjectState.score = score` verbatim (`mapper.py:101`, further confirmed already regression-tested by
`test_map_to_states_carries_real_score_not_hardcoded_placeholder`,
`tests/unit/domains/adventure/test_phase3_route_families.py:56-80`). Step 2 below uses this path, not
`trace_records`.

## Steps

### Step 1 — Test file scaffold + shared `_diff_routes()` helper + AC1 no-mutation test

**Files:** `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py` (new)

**Change:** Create the new test file. Imports: `AuthoritativeState`, `EntityState` from
`src.core.state`; `CanonicalStateHasher` from `src.engine.checkpoint`
(`src/engine/checkpoint.py:38-49`, confirmed `get_hash(state) -> str` static method, SHA-256 of
canonical JSON, no `HashScheduleViolation` gate applies to direct calls — see
`checkpoint.py:29-33`/`218-244`, the gate only wraps `CanonicalHashScheduler`, never direct
`get_hash()`); `V2EntityBuilder` from `src.core.builder`; `AdventureDecisionPhase` from
`src.domains.adventure.phase`; `AdventureGoalScorer` from `src.ai.goals.adventure_scorer`. Copy the
`_state(entities)` builder helper verbatim from
`tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py:18-47` (confirmed read
directly — it builds a complete, valid `AuthoritativeState` with every required field; do not
hand-roll a different one).

**Also add the shared `_diff_routes()` itemized-diff-report helper in this same file, before any
test function.** Plan-phase correction (architecture-reviewer finding): the ticket's own Scope text
ties "surfacing normalization miscalibration as a named itemized diff report (not single pass/fail)"
directly to the per-family route comparisons (AC2), not only to a standalone diff-shape unit test.
`_diff_routes()` therefore moves here, ahead of Step 2/3, so both of those steps can route their real
family/raw_score comparisons through it instead of bare `assert a == b`. Step 4 exercises this exact
definition (does not redefine it) against two synthetic cases proving the report's shape. Helper is
test-only tooling, not production code (test_plan.md and the ticket's Out-of-Scope section both scope
diff-report machinery as test-only):
```python
def _diff_routes(phase_family, phase_raw_score, scorer_family, scorer_raw_score,
                  phase_utility=None, scorer_utility=None):
    report = {"family_mismatches": [], "raw_score_mismatches": [], "utility_mismatches": []}
    if phase_family != scorer_family:
        report["family_mismatches"].append({"phase": phase_family, "scorer": scorer_family})
    if phase_raw_score != scorer_raw_score:
        report["raw_score_mismatches"].append({"phase": phase_raw_score, "scorer": scorer_raw_score})
    if phase_utility is not None and scorer_utility is not None and phase_utility != scorer_utility:
        report["utility_mismatches"].append({"phase": phase_utility, "scorer": scorer_utility})
    return report
```

Add `test_shadow_scenario_neither_path_mutates_state`:
```python
hero = V2EntityBuilder(1).kind("hero").replace_combat(
    CombatComponent(hp=20, max_hp=100, atk=10, def_stat=2)
).build()  # low_health forces a RECOVER candidate, giving both paths non-trivial work to do
state = _state([hero])
hash_before = CanonicalStateHasher.get_hash(state)
entity_before = state.entities[hero.id]

AdventureDecisionPhase.apply(state, factions=state.factions)  # discard returned StateUpdate
assert CanonicalStateHasher.get_hash(state) == hash_before
assert state.entities[hero.id] == entity_before

score_result = AdventureGoalScorer().score(hero, state)
assert CanonicalStateHasher.get_hash(state) == hash_before
assert state.entities[hero.id] == entity_before

# AC1's wording explicitly covers "AdventureGoalScorer.score(entity,state)/materialization
# independently" -- the materialization half is RouteToProjectMapper.map_to_states(), the same
# call intelligence.py:1450-1457 makes for a winning ADVENTURE_ROUTE candidate. It takes no
# `state` argument at all (mapper.py:67-74: family/entity_id/target/target_pos/tick/score only),
# so it cannot mutate state by construction -- call it anyway so the proof is explicit, not
# merely inferred from the function's signature.
from src.domains.adventure.mapper import RouteToProjectMapper
RouteToProjectMapper.map_to_states(
    family=score_result.metadata["route_family"], entity_id=hero.id,
    target=score_result.target_id, target_pos=score_result.target_pos,
    tick=state.tick, score=score_result.metadata["raw_score"],
)
assert CanonicalStateHasher.get_hash(state) == hash_before
assert state.entities[hero.id] == entity_before
```
Call `AdventureDecisionPhase.apply(state, factions=state.factions)` explicitly with `factions=`
passed (investigation.md Risk #3 — do not rely on the `factions=None` vs `factions=state.factions`
coincidence in `scoring.py:133`'s escort branch remaining true). Hash after each call separately
(not just once at the end) so a mutation introduced by either individual call is attributable to
that call, not just detected in aggregate.

**Do NOT touch:** `src/domains/adventure/phase.py`, `src/ai/goals/adventure_scorer.py`,
`src/domains/adventure/service.py`, `src/domains/adventure/generator.py`,
`src/domains/adventure/scoring.py`, `src/domains/adventure/mapper.py`,
`src/systems/strategic_systems/intelligence.py`, `src/engine/pipeline.py`. This test only calls
existing methods; it must not require any production-code edit to pass, since both paths are already
confirmed pure (frozen dataclasses, read-only field access — investigation.md's Current Behavior
section, independently re-confirmed this session by reading `phase.py:82-198` and
`adventure_scorer.py:30-168` directly — no assignment/mutation of anything reachable from `state` in
either).

**Verify:** `pytest tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py::test_shadow_scenario_neither_path_mutates_state -v`

---

### Step 2 — AC2 tier 1: 6 real end-to-end per-family shadow parity tests

**Files:** `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

**Change:** Add 6 tests, one per generator-reachable family
(`RECOVER, BUY_UPGRADE, CRAFT_UPGRADE, GATHER_RESOURCE, ASK_INFORMATION, FORM_PARTY` —
confirmed exhaustive by reading `generator.py:38-181` directly: `kind_map` is a closed 6-key dict
plus 3 forced/structural branches plus 1 fallback, none of which construct the other 9
`RouteFamily` members). Each test builds one `AuthoritativeState` via `_state()` engineered so the
target family is the **only valid (unblocked) candidate** `generate()` produces, so which candidate
`decide()` selects is not ambiguous — this sidesteps needing to reverse-engineer
`AdventureRouteScorer.score()`'s relative cross-family weights in `scoring.py`. Critical
structural fact verified this session: `AdventureDecisionPhase.apply()` and `AdventureGoalScorer.score()`
each independently call `ResourceOpportunityProvider.get_opportunities(entity, state)` +
`ServiceOpportunityProvider.get_opportunities(entity, state)` **themselves**, reading real
`state.resource_nodes` / `ServiceRegistry.all()` / `RecipeRegistry.all()` — neither accepts
externally-injected `Opportunity` objects the way `test_phase3_route_generator.py`'s unit tests do.
Content registries are **not empty by default**: `src/core/registries.py`'s module tail
(`registries.py:715` area, confirmed read directly) calls
`seed_phase1_content(mode=RuntimeContentMode.LEGACY_FALLBACK)` at import time, which
`ResourceRegistry.bootstrap()`s 5 real resource kinds (`registries.py:676-682`:
`node_wood→wood(near_forest)`, `node_herb→herb(near_forest,moon_cave)`,
`node_iron→iron_ore(old_mine, requires pickaxe)`, `node_resin→moon_resin(moon_cave)`,
`node_flower→healing_flower(near_forest)`) and `ServiceRegistry.bootstrap()`s 5 real hometown
services (`registries.py:~703-710`: `shop_hometown(buy,sell)`, `blacksmith_hometown(craft,repair)`,
`guide_hometown(ask_info, restricted to wood/herb/iron_ore/healing_flower/moon_resin)`,
`guild_hometown(quest,info)`, `inn_hometown(rest)`), and `RecipeRegistry.bootstrap()`s 3 real
recipes (`iron_sword`, `hunter_blade`, `small_potion`). `tests/conftest.py:154-196` has 3 autouse
fixtures that restore `ItemRegistry`/`ResourceRegistry`/registries-module `ItemRegistry` to this same
canonical post-import state before and after every test, so this content is reliably present with no
per-test seeding required. Blocking mechanics: `AdventureRouteGenerator.generate()` only checks
`has_gold`/`has_item` requirements when building the `blockers` tuple (`generator.py:56-68`) — a
blocked candidate is excluded from `AdventureDecisionService.decide()`'s `valid_candidates`
(`service.py:82-96`), so an opportunity that exists but is under-resourced never wins, which is the
mechanism used below to isolate each family:

For each sub-test, build `hero = V2EntityBuilder(1).kind("hero")...build()` with the stated
component overrides, `state = _state([hero])` (plus a second entity for FORM_PARTY), run:
```python
result_apply = AdventureDecisionPhase.apply(state, factions=state.factions)
result_score = AdventureGoalScorer().score(hero, state)

phase_upd = result_apply.entity_updates[hero.id]
phase_family = phase_upd.property_updates["last_routing_family"]        # phase.py:179
phase_raw_score = phase_upd.strategic.projects_add_or_update[0].score   # see Summary's correction

diff = _diff_routes(
    phase_family=phase_family, phase_raw_score=phase_raw_score,
    scorer_family=result_score.metadata["route_family"].value,
    scorer_raw_score=result_score.metadata["raw_score"],
)
assert diff["family_mismatches"] == []
assert diff["raw_score_mismatches"] == []
```
**Plan-phase correction (architecture-reviewer finding):** these 6 tests must route their real
family/raw_score comparison through the shared `_diff_routes()` helper defined in Step 1 and assert
on its returned mismatch-category lists being empty, not on a bare `phase_family == scorer_family`
equality — this is what the ticket's own Scope text means by "surfacing normalization miscalibration
as a named itemized diff report (not single pass/fail)" applied to AC2's per-family comparisons, not
just to Step 4's standalone diff-shape unit test. `utility_mismatches` is not asserted here (left at
its default empty list) since neither path exposes a comparable `utility` value for the committed
decision — see Step 4's synthetic Case B for that dimension's coverage.

**`ServiceRegistry`/`RecipeRegistry` test-isolation hazard (other writers to this shared resource,
confirmed this session, not previously flagged by investigation.md or test_plan.md):**
`src/runtime/bootstrap.py:106-113`'s `_bootstrap_empty()` calls `ItemRegistry.bootstrap({})`,
`RecipeRegistry.bootstrap({})`, `ServiceRegistry.bootstrap({})`, `RegionRegistry.bootstrap({})`,
`ResourceRegistry.bootstrap({})`, `EnemyRegistry.bootstrap({})` — all emptied — under certain
`RuntimeContentMode`/catalog-load-failure conditions, and `_bootstrap_from_catalog()`
(`bootstrap.py:122-154`) separately overwrites all 6 with catalog-derived content on the real
catalog-mode path. `tests/conftest.py:154-196` (confirmed read this session) has autouse fixtures
that snapshot-and-restore `ItemRegistry`/`ResourceRegistry`/registries-module-`ItemRegistry`
specifically because "any test exercising it left [the registry] empty for the rest of the process"
(conftest.py's own comment, `:174-177`) — this is the identical documented hazard, from the
identical function, for `ServiceRegistry`/`RecipeRegistry` too, but **conftest.py has no
`_reset_service_registry`/`_reset_recipe_registry` fixture** (confirmed absent by reading the whole
file). This ticket's BUY_UPGRADE/CRAFT_UPGRADE/ASK_INFORMATION fixtures below depend on
`ServiceRegistry`/`RecipeRegistry` holding specific real entries — if an earlier test in the same
pytest session exercised `_bootstrap_empty()` (e.g. via `tests/unit/runtime/test_fallback_restrict_modes.py`
or `tests/unit/content/test_runtime_content_mode.py`, both of which call `seed_phase1_content`/
runtime-bootstrap-adjacent code per this session's grep) and left these two registries empty or
catalog-substituted, these 3 fixtures would silently produce zero or different opportunities
(family selection would go to `DEFER_WITH_REASON` or an unintended family instead of the target one)
— a flaky, test-order-dependent failure, not a loud one. **Do not depend on ambient registry state.**
Add one local, non-autouse pytest fixture to this same test file:
```python
@pytest.fixture
def _isolated_service_recipe_registries():
    """No autouse reset exists for these two registries in tests/conftest.py (unlike
    ItemRegistry/ResourceRegistry, which ARE protected against src/runtime/bootstrap.py's
    _bootstrap_empty() — see this ticket's plan.md Step 2 for the full citation). Snapshot
    and explicitly re-bootstrap real content so these 3 tests are deterministic regardless
    of what ran earlier in the same pytest session, then restore afterward so later tests
    are unaffected either way."""
    from src.core.registries import ServiceRegistry, RecipeRegistry, ServiceDef, RecipeDef
    services_before = dict(ServiceRegistry._services)
    recipes_before = dict(RecipeRegistry._recipes)
    ServiceRegistry.bootstrap({
        "shop_hometown": ServiceDef("shop_hometown", "hometown", ("buy", "sell")),
        "blacksmith_hometown": ServiceDef("blacksmith_hometown", "hometown", ("craft", "repair")),
        "guide_hometown": ServiceDef("guide_hometown", "hometown", ("ask_info",),
                                      ("wood", "herb", "iron_ore", "healing_flower", "moon_resin")),
    })
    RecipeRegistry.bootstrap({
        "iron_sword": RecipeDef("iron_sword", {"iron_ore": 2, "wood": 1}, "blacksmith", 40, "iron_sword"),
        "hunter_blade": RecipeDef("hunter_blade", {"iron_ore": 2, "beast_fang": 1, "moon_resin": 1}, "blacksmith", 50, "hunter_blade"),
        "small_potion": RecipeDef("small_potion", {"healing_flower": 1, "crystal_shard": 1}, "blacksmith", 10, "small_potion"),
    })
    yield
    ServiceRegistry.bootstrap(services_before)
    RecipeRegistry.bootstrap(recipes_before)
```
Confirmed exact field shapes this session: `ServiceDef(id, region_id, supported_affordances,
knowledge_scope=())` and `RecipeDef(id, requires_items: Dict[str,int], service_req, gold_cost,
output_item_id)` (`registries.py:39-52`); `ServiceRegistry._services`/`RecipeRegistry._recipes` are
the exact internal dict attribute names (`registries.py:130,152`), and `.bootstrap(data)` does
`cls._x = dict(data)` (`registries.py:133-134,155-156`) — same snapshot/restore shape
`tests/conftest.py` already uses for `ResourceRegistry._resources`. The BUY_UPGRADE, CRAFT_UPGRADE,
and ASK_INFORMATION sub-tests below take this fixture as a parameter (`def test_shadow_parity_buy_upgrade_family(_isolated_service_recipe_registries):`
etc.); RECOVER, GATHER_RESOURCE, and FORM_PARTY do not need it — RECOVER/FORM_PARTY are forced
structurally regardless of `ServiceRegistry` content (an empty registry only removes potential
*competing* candidates, which does not break their isolation), and GATHER_RESOURCE's region switch
to `"near_forest"` already excludes every hometown-only `ServiceRegistry` entry by construction
(Step 2's GATHER_RESOURCE recipe below), and depends only on `ResourceRegistry`, which conftest.py
already protects.

Per-family fixture recipes (all verified against real registry content and generator/provider
branch conditions this session — see file:line citations above):

1. **RECOVER** — `CombatComponent(hp=20, max_hp=100, ...)` (low_health via
   `self_model.self_awareness.perceived_weaknesses=("low_health",)` and
   `needs.active_needs={"healing": ...}`, mirroring `test_low_hp_generates_recover_route`'s pattern,
   `test_phase3_route_generator.py:51-58`) forces RECOVER structurally (`generator.py:98-109`), no
   opportunity needed. `InventoryComponent(gold=0)` (no items) so hometown's default `buy_item`
   (needs gold≥15, `services.py:109`) and all 3 `craft_item` options (need gold≥10/40/50 plus
   items) are blocked, not valid. Sociability 0.0 (default) keeps FORM_PARTY unforced. No
   `resource_nodes`.
2. **BUY_UPGRADE** — `InventoryComponent(gold=15)`, no items, no weaknesses. Default region
   ("hometown", since `navigation.region_id` defaults to `None` and providers fall back to
   `"hometown"` — `state.py:376` field default, `resources.py`/`services.py`'s
   `getattr(...,"region_id",None) or "hometown"`). `shop_hometown`'s `buy_item` opportunity (needs
   gold≥15 — exactly met) is valid; all 3 `craft_item` options are blocked (`iron_sword`/`hunter_blade`
   need gold 40/50 > 15; `small_potion` needs gold 10 ≤ 15 but also `healing_flower`+`crystal_shard`
   items the entity doesn't have → `missing_item` blocker, `generator.py:61-68`).
3. **CRAFT_UPGRADE** — `InventoryComponent(gold=10, items=[ItemStack("healing_flower",1),
   ItemStack("crystal_shard",1)])`. `small_potion`'s craft opportunity (gold≥10, needs those exact 2
   items) is valid; `buy_item` (needs gold≥15) is blocked (only have 10). The other 2 craft options
   may or may not also be valid/blocked depending on gold (10 < 40/50, so blocked) — irrelevant since
   they're the same family regardless.
4. **GATHER_RESOURCE** — `NavigationComponent(region_id="near_forest")` (builder:
   `b.replace_navigation(NavigationComponent(region_id="near_forest"))`), `resource_nodes={1:
   ResourceNodeState(id=1, kind="node_flower", position=(0.0,0.0), yields_item="healing_flower",
   remaining_charges=5, max_charges=5, required_ticks=1)}` — `node_flower`'s `source_region_tags=
   ("near_forest",)` matches, `required_tool=None` so no extra `has_item` blocker
   (`registries.py:681`). Switching region to `near_forest` also means none of the 5 hometown
   `ServiceRegistry` entries match (`s_def.region_id == current_region` fails,
   `services.py:48`), so `ServiceOpportunityProvider` returns `[]` entirely — no buy/craft
   competition to block.
5. **ASK_INFORMATION** — Default `"hometown"` region. `StrategicComponent(blockers={"b1":
   BlockerState(id="b1", kind=BlockerKind.MATERIAL, subject="iron_ore", resolved=False)})` sets
   `has_material_blocker=True`, so `guide_hometown`'s `ask_information` opportunity is generated
   (`services.py:85-98`, needs gold≥10). `InventoryComponent(gold=10)`, no items: `ask_information`
   valid (gold≥10 exactly met); `buy_item` blocked (needs 15); `craft_item` `small_potion` needs
   gold≥10 (met) but also the 2 items (missing) → blocked; `iron_sword`/`hunter_blade` blocked on
   gold.
6. **FORM_PARTY** — `PersonalityComponent(sociability=0.5)` (≥0.2 threshold, `generator.py:129`), a
   second ally entity `V2EntityBuilder(2).kind("hero").build()` in `_state([hero, ally])`
   (non-`MONSTER` role — builder default `.kind("hero")` sets `identity.role=EntityRole.HERO`,
   confirmed via existing precedent test construction throughout this file's sibling test files).
   `InventoryComponent(gold=0)`, no items, default region: FORM_PARTY is added unconditionally once
   sociability/candidates clear (`generator.py:125-163`, no `if not any(...)` guard unlike
   ASK_INFORMATION's forced branch), and it is the only *valid* candidate since hometown's
   buy/craft opportunities are blocked on gold as in the RECOVER case.

**Do NOT touch:** same production files as Step 1. Do not hand-construct `AdventureRouteOption`
objects or call `AdventureDecisionService.decide()` directly for these 6 tests (that is
`test_phase3_adventure_decision_scenarios.py`'s bypass pattern, explicitly rejected by
investigation.md's Anti-Drift Hazards as the wrong reuse source for *this* ticket, since it never
exercises the opportunities→`generate()` wrapping difference that is the actual parity risk here).
**Do not add a `_reset_service_registry`/`_reset_recipe_registry` autouse fixture to
`tests/conftest.py`** — that is a suite-wide test-isolation fix with a much larger blast radius
(every test in the repo, not just this ticket's new file) than this ticket's scope; the local,
non-autouse `_isolated_service_recipe_registries` fixture above is the narrow, ticket-scoped fix.
Widening the fix to `conftest.py` is worth a separate, dedicated follow-up ticket (mirroring
`TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET`'s own scope for `ResourceRegistry`), not
folded into this one.

**Verify:** `pytest tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py -k "parity_recover_family or parity_buy_upgrade_family or parity_craft_upgrade_family or parity_gather_resource_family or parity_ask_information_family or parity_form_party_family" -v`

---

### Step 3 — AC2 tier 2: mapper-level parity check across all 15 families

**Files:** `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

**Change:** Add `test_shadow_parity_mapper_level_all_15_families`, parametrized over
`RouteToProjectMapper._MAP`'s 15 keys (`mapper.py:31-47`, confirmed read directly this session —
exactly the 15 named in the ticket, `DEFER_WITH_REASON` excluded). For each family `f`, call
`RouteToProjectMapper.map_to_states()` **twice with identical arguments** — one call standing in for
what `AdventureDecisionService.decide()` does (`service.py:141-148`), one for what the scorer-side
materialization branch does (`intelligence.py:1450-1457`), since both real call sites pass the same
`family`/`score`/`target`/`target_pos`/`tick` shape into this one shared function — then diff the two
results through the same shared `_diff_routes()` helper defined in Step 1, plus retain the
`get_kinds()` schema check (a dimension `_diff_routes()` does not cover):
```python
project_phase, obj_phase = RouteToProjectMapper.map_to_states(
    family=f, entity_id=1, tick=5, score=1.7, target="t", target_pos=(1.0, 2.0)
)
project_scorer, obj_scorer = RouteToProjectMapper.map_to_states(
    family=f, entity_id=1, tick=5, score=1.7, target="t", target_pos=(1.0, 2.0)
)
diff = _diff_routes(
    phase_family=project_phase.kind, phase_raw_score=project_phase.score,
    scorer_family=project_scorer.kind, scorer_raw_score=project_scorer.score,
)
assert diff["family_mismatches"] == []
assert diff["raw_score_mismatches"] == []

expected_p_kind, expected_o_kind = RouteToProjectMapper.get_kinds(f)
assert project_phase.kind == expected_p_kind
assert obj_phase.kind == expected_o_kind
```
**Plan-phase correction (architecture-reviewer finding):** the previous single-call-plus-bare-equality
form of this test (`assert project.score == 1.7` etc.) is exactly the "single pass/fail" pattern the
ticket's Scope text explicitly rejects for the 15-family comparison. Routing through `_diff_routes()`
even though both calls are guaranteed to match today (same function, same args) gives a real itemized
artifact that will show a populated `family_mismatches`/`raw_score_mismatches` list, not just a
silent `AssertionError`, if a future change makes `map_to_states()` non-deterministic or
caller-order-sensitive — the exact design-doc §4 defect shape reintroduced at mapper scale. This is
the **only** parity claim provably exercisable end-to-end for the 9 generator-unreachable
families today (`TRAIN_SKILL, TAKE_EASY_QUEST, HUNT_WEAK_ENEMY, SELL_LOOT_FOR_GOLD, SCOUT_LOCATION,
RETURN_TOWN, QUEST_OPPORTUNITY, PROTECT_TARGET, OWN_SURVIVAL`) — both
`AdventureDecisionService.decide()` (`service.py:141-148`) and the tier-5 materialization branch
(`intelligence.py:1450-1457`, confirmed read directly this session, both call
`RouteToProjectMapper.map_to_states()`) route through this exact same function, so mapper-level
purity is a real, shared-code guarantee, not a coincidence. The test's own docstring/name **must**
say "mapper-level only for families not reachable via `generate()` today" so a reader does not
mistake it for end-to-end coverage (investigation.md's explicit anti-drift hazard).

**Do NOT touch:** `src/domains/adventure/generator.py`'s `kind_map` (extending it to cover more
families is out of scope — see Scope Guards). Do NOT delete or weaken Step 2's 6 end-to-end tests
in favor of this broader-but-shallower one; they prove different things (real wrapping-logic parity
vs. shared-mapper purity) and both are required by AC2 as resolved in this plan.

**Verify:** `pytest tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py::test_shadow_parity_mapper_level_all_15_families -v`

---

### Step 4 — AC3: diff-report shape separating raw_score from utility mismatches

**Files:** `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

**Change:** `_diff_routes()` is **already defined** in Step 1 (moved there per Plan-phase correction —
architecture-reviewer finding — specifically so Steps 2 and 3's real family/raw_score comparisons
could route through it, satisfying the ticket's Scope text that ties the itemized-diff-report
requirement to the per-family comparison, not only to a standalone unit test). **Do not redefine it
here** — this step only adds tests that exercise that same shared definition.

Add `test_shadow_diff_report_separates_raw_score_from_utility_mismatches` with 2 synthetic cases
called directly against `_diff_routes` (no state/pipeline involved — this is a pure shape test):
- Case A: `phase_raw_score=1.5, scorer_raw_score=2.0` (mismatched), no utility args →
  `raw_score_mismatches` has 1 entry, `utility_mismatches` is empty.
- Case B: `phase_utility=40.0, scorer_utility=55.0` (mismatched, hypothetical — `AdventureDecisionPhase`
  never actually produces a `utility` value, per investigation.md's Current Behavior; this is a
  synthetic case proving the report *shape* keeps the two categories apart, catching the design
  doc §4 scale-mismatch bug shape by construction) with matching `raw_score` →
  `utility_mismatches` has 1 entry, `raw_score_mismatches` is empty.
These 2 synthetic cases exercise `_diff_routes()`'s own shape/correctness in isolation. They are
**no longer the only place `_diff_routes()` is exercised** — Step 2's 6 real family tests and Step
3's 15-family mapper-level test both now assert against its returned mismatch-category lists too
(mandatory, not optional, per the Plan-phase correction above), so this step's synthetic cases add
coverage of edge shapes (e.g. the `utility_mismatches` category, which the real family tests never
populate since neither path exposes a comparable `utility` for the committed decision) rather than
carrying the entire itemized-diff-report requirement alone.

**Do NOT touch:** Do not add a `_diff_routes`-equivalent under `src/` — no production diff-report
infrastructure is in scope (ticket Out of Scope: "Reimplementing /simq-audit's ... Report
machinery" — this is a distinct but same-spirited boundary: this ticket's own diff report is a
test-only artifact, not a new production reporting subsystem). Do not define a second, competing
`_diff_routes()` in this step — Step 1's definition is the single shared one.

**Verify:** `pytest tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py::test_shadow_diff_report_separates_raw_score_from_utility_mismatches -v`

---

### Step 5 — AC4: ticket-text gate regression guard

**Files:** `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`

**Change:** Add `test_delete_adventure_decision_phase_ac1_already_encodes_the_gate`. Read
`tickets/todos/adventure-cognition-merge/TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE.md` from disk
(confirmed present and containing the required text this session,
`DELETE-ADVENTURE-DECISION-PHASE.md:44`: `"This ticket's Implement phase does not proceed until
TCK-20260811-ADVENTURE-GOAL-SCORER (C1) and TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (C4) are
both in tickets/done/..."`). Assert the file's Acceptance Criteria section contains both literal
substrings `"TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (C4)"` and `"both in tickets/done/"`. This
is a **regression guard**, not a claim that this ticket edits that file — the gate text already
exists (investigation.md's Prior Work section, independently re-confirmed by reading the file
directly this session) and needs no new authoring, only a cheap test so a future accidental edit to
that ticket can't silently drop the hard dependency.

**Do NOT touch:** `tickets/todos/adventure-cognition-merge/TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE.md`
itself — read-only assertion target, not an edit target, for this ticket.

**Verify:** `pytest tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py::test_delete_adventure_decision_phase_ac1_already_encodes_the_gate -v`

---

### Step 6 — Docs: parity ledger entry, STRAT-252 addendum, design doc status note

**Files:** `docs/parity_ledger/strategic_cognition.yaml`,
`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`

**Change:**
1. Add a new entry to `docs/parity_ledger/strategic_cognition.yaml` documenting the shadow-mode
   proof: `status: verified`, `priority: P1` (matches investigation.md's reasoning — `DELETE-
   ADVENTURE-DECISION-PHASE`'s own AC1 hard-gates on this ticket being DONE, but nothing *live*
   depends on it yet, so P1 not P0), `v2_evidence` citing
   `tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py`, `test_path` set
   to that file, and `text`/`divergence_note` explicitly stating the 6-vs-9 split (which 6 families
   got real end-to-end verification vs. which 9 got mapper-level-only verification) so the entry
   does not overstate coverage — this is the same anti-drift requirement Step 2/3 already encode in
   the tests' own docstrings, mirrored here in the ledger.
2. **Do not create or fill a `test_path` for STRAT-185** (`strategic_cognition.yaml:1987-1996`,
   confirmed this session: `text: "Strategic project retention is bounded by interruption
   resistance."`, `priority: P0`, `test_path: null`). **Decision, not left open**: this ticket's
   shadow test proves route-family/raw_score cross-path *parity* — it asserts nothing about
   `evaluate_project_switch()`'s `retention_margin`/`effective_current_score`/lock-bypass logic
   (`intelligence.py:1000-1015`), which is what STRAT-185's text actually claims. Closing STRAT-185
   here would be a poor-fit citation — a future reader following `test_path` to this ticket's test
   would find route-family-matching assertions, not a retention-bound proof. STRAT-185 belongs to
   TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG's subject matter (a sibling ticket
   already in `tickets/done/` per the git log), not this one; if that ticket didn't already close it,
   it should be closed by a dedicated retention-margin test, not backfilled here just because a
   design doc flagged it as "a real opportunity."
3. `STRAT-252`'s existing entry (`strategic_cognition.yaml:3255-3288`, confirmed read this session)
   currently says `AdventureGoalScorer` "is NOT yet the live/wired decision path" and cites "that
   wiring/cutover is separate, later-ticket scope (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`,
   gated on this ticket plus `TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE` landing first)". Add a
   one-line addendum to that `text` field once this ticket's test exists and passes: "this
   prerequisite is now satisfied (see the new shadow-parity entry above)."
4. `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` §7
   (Migration/rollout plan, confirmed at line 293, "### 7. Migration / rollout plan") — add a short
   "Status: done, see TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE" note under step 2 specifically
   (not the whole section — steps 1/3/4 belong to sibling tickets with their own status).

**Do NOT touch:** `STRAT-186`/`STRAT-187` (already `test_path`-filled, not this ticket's concern
per investigation.md), `STRAT-236` (unaffected — this ticket only observes existing behavior).

**Verify:** No pytest test — verified by `parity-updater`/`doc-updater` review during Verify phase;
confirm `docs/parity_ledger/strategic_cognition.yaml` still passes its schema validation
(`python3 tools/validate_frontmatter.py` or equivalent parity-ledger schema check, whichever this
repo's Verify phase already runs).

---

### Step 7 — AC5: manual `/simq-audit` invocation and verdict recording

**Files:** `tickets/inprogress/TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE.md` (Implementation
Notes / Completion Summary sections only — not a code or test change)

**Change:** This is a **manual workflow step, not a pytest test**, per the ticket's own AC5 wording
("AC asserts the audit was run and its verdict recorded, not that new SimQ infrastructure was
built") and investigation.md's explicit resolution. At or near the end of Implement/Verify:
1. Run `/simq-audit mode=full` (per `.claude/skills/simq-audit/SKILL.md:10-12`, confirmed read this
   session — `mode=full` re-runs all fast ≤500t scenarios and diffs against `grade_anchors.json`;
   `mode=slow` additionally runs the 1000t/2000t tier).
2. The workflow's Report phase returns one of exactly 4 terminal statuses, confirmed against
   `SKILL.md:62-84`: `DONE_NO_TICKET` (Classify Drift verdict `no_regression`), `NEEDS_TICKET`
   (verdict `regression` or `needs_da_decision`, returns a new ticket ID), `ANCHORS_STILL_FAILING`,
   or `BLOCKED`.
3. Record the exact returned status string, the underlying Classify Drift `verdict`, and the
   `runId` (`SIMQ-AUDIT-<timestamp>`) verbatim in this ticket's own Implementation Notes/Completion
   Summary sections.
4. Per CLAUDE.md's rule against editing to make a gate pass: if the result is not
   `DONE_NO_TICKET`/`no_regression`, that is correct information to report as this ticket's
   pre-cutover finding — do **not** attempt to fix a regression `/simq-audit` finds inside this
   ticket's own scope (explicitly excluded by the ticket's Out of Scope section), and do not treat a
   non-passing verdict as blocking this ticket's own closure (the design's migration step 4 gates
   the *later* `DELETE-ADVENTURE-DECISION-PHASE` cutover, not this ticket's own DONE state).

**Do NOT touch:** Do not write any new SimQ scoring/audit code under `src/simulation_quality/` —
explicitly out of scope per the ticket's own Out of Scope section.

**Verify:** Manual verification only — the Implementation Notes/Completion Summary sections contain
the recorded verdict string, Classify Drift verdict, and `runId`. `done-checker` confirms these
sections are non-empty and traceable, not that a specific verdict value was returned.

## Scope Guards

- **Do not fix the pre-existing `target_pos` gap in the currently-active path.**
  `AdventureDecisionService.decide()` (`src/domains/adventure/service.py:135`, confirmed read this
  session: `target_pos = None` set unconditionally and never reassigned anywhere else in the
  function) means the **currently-live** `AdventureDecisionPhase` path has never set `target_pos`
  for the 3 forced/structural families (`RECOVER`, `ASK_INFORMATION`, `FORM_PARTY`) — the same "wins
  but stalls forever" class of bug ticket 1 (`ADVENTURE-GOAL-SCORER`) found and fixed, but only on
  the *new*, not-yet-wired `AdventureGoalScorer` path via `_resolve_placeholder_target_pos()`
  (`adventure_scorer.py:170-230`, confirmed already landed and in the current source tree this
  session). This is a real, independently-discovered, currently-live production gap — but it is out
  of this ticket's scope for two independent reasons: (1) AC2 as resolved in this plan only compares
  `family` + `raw_score`, never `target_pos`/tactical resolvability, so this ticket's own tests
  cannot and do not catch it either way; (2) fixing it would require editing
  `src/domains/adventure/service.py`, which is not in this ticket's Related Code Areas as a
  modification target (only as a read-only shadow-comparison target), and the ticket's Out of Scope
  section already excludes "Building AdventureGoalScorer itself" — editing the *other* path's
  service logic is further still outside that boundary. File a separate follow-up ticket for this;
  do not fold a fix into this ticket's Implement phase even opportunistically.
- **Do not extend `AdventureRouteGenerator.generate()`'s `kind_map`** to make more of the 9
  currently-unreachable families constructible — that would silently expand this ticket's scope into
  generator/pipeline behavior change, not test-writing, and is explicitly excluded by the ticket's
  "Building AdventureGoalScorer itself" Out-of-Scope boundary (extending the generator is further
  still outside that boundary than the scorer itself).
- **Do not touch `src/engine/pipeline.py`.** No wiring/registration change — `AdventureGoalScorer`
  stays unwired into the live tick pipeline; that is `DELETE-ADVENTURE-DECISION-PHASE`'s job, gated
  on this ticket being done, not the other way around.
- **Do not build new SimQ infrastructure.** AC5 is satisfied by invoking the existing `/simq-audit`
  workflow and recording its verdict in the ticket body (Step 7) — no new scorer, no new
  Recalibrate/Classify-Drift/Report logic under `src/simulation_quality/`.
- **Do not close STRAT-185.** Decision made in Step 6: wrong subject match (interruption-resistance
  retention bound vs. this ticket's cross-path family/raw_score parity claim). Leave `test_path:
  null`.
- **Do not modify `AdventureDecisionPhase`, `AdventureDecisionService`, `AdventureRouteGenerator`,
  `AdventureRouteScorer`, `RouteToProjectMapper`, or `AdventureGoalScorer` themselves.** Every step
  in this plan is either a new test file or a docs-only change. All 6 of those classes are read-only
  shadow-comparison targets.
- **Do not use Python's built-in `hash()`/`__hash__` on `AuthoritativeState`.** It raises `TypeError`
  given the dict-typed fields (`entities`, `resource_nodes`, `factions`, etc.) — always route through
  `CanonicalStateHasher.get_hash()`.
- **Do not reuse `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`'s
  construction pattern** (hand-built `AdventureRouteOption` + direct `AdventureDecisionService.decide()`
  call) as the shadow test's state-construction source — it bypasses the exact
  opportunities→`generate()` wrapping logic that is the real parity risk between the two paths.
- **Do not add a suite-wide `_reset_service_registry`/`_reset_recipe_registry` fixture to
  `tests/conftest.py`.** The real test-isolation hazard is confirmed (Step 2) and real, but fixing
  it suite-wide is a separate, larger-blast-radius ticket, not this one — this ticket's own new
  test file protects only itself via a local fixture.

## Dependency Map

- Steps 1–5 (new test file) are independent of each other in principle but **share one file** —
  implement in the listed order to keep diffs reviewable, but each step's tests can be verified in
  isolation via the per-step `pytest -k`/exact-test-id commands above.
- **Steps 2, 3, and 4 now have a real (not just file-sharing) dependency on Step 1**: Step 1 defines
  the shared `_diff_routes()` helper, and Steps 2/3's real family/raw_score assertions and Step 4's
  synthetic-case tests all call that same definition rather than each defining their own — Step 1
  must land first (or at minimum, its helper definition must exist in the file) before Steps 2, 3, or
  4 can be implemented or verified. This is a genuine ordering dependency introduced by the Plan-phase
  correction that moved `_diff_routes()` out of Step 4 and into Step 1, not merely the pre-existing
  "shares one file" convenience note above.
- Step 6 (docs) depends on Steps 1–5 existing and passing (the parity ledger entry cites the test
  file as `v2_evidence`/`test_path`; the STRAT-252 addendum states "this prerequisite is now
  satisfied," which is only true once the tests exist and pass).
- Step 7 (`/simq-audit`) is independent of Steps 1–6 and can run at any point in Implement/Verify,
  but is listed last since it is the natural "final gate before calling this ticket done" step.
- No step in this plan is a dependency for any other in-progress or todo ticket except
  `DELETE-ADVENTURE-DECISION-PHASE`'s own AC1 (already satisfied by pre-existing ticket text — see
  Step 5, no edit required there).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — shadow test constructs one `AuthoritativeState` scenario, runs both paths, asserts neither mutates `state` | Step 1 | `test_shadow_scenario_neither_path_mutates_state` |
| AC2 — for each of the 15 route families, both paths select the same winning family and raw_score, for representative scenario fixtures, surfaced as an itemized diff report (not single pass/fail) | Step 1 (shared `_diff_routes()` helper definition) + Step 2 (6 end-to-end families, asserted via `_diff_routes()`) + Step 3 (mapper-level parity across all 15, asserted via `_diff_routes()`) | `test_shadow_parity_{recover,buy_upgrade,craft_upgrade,gather_resource,ask_information,form_party}_family` + `test_shadow_parity_mapper_level_all_15_families` |
| AC3 — diff report explicitly separates raw_score mismatches from utility mismatches | Step 1 (helper definition) + Step 4 (synthetic shape tests, including the `utility_mismatches` category the real family tests never populate) — reinforced in practice by Step 2/3's real usage of the same helper | `test_shadow_diff_report_separates_raw_score_from_utility_mismatches` (+ the 6 Step 2 family tests and `test_shadow_parity_mapper_level_all_15_families` as real-data exercises of the same report shape) |
| AC4 — `DELETE-ADVENTURE-DECISION-PHASE` removal is gated on this ticket, encoded as a hard dependency | Step 5 (regression guard only; the gate text already pre-exists in that ticket) | `test_delete_adventure_decision_phase_ac1_already_encodes_the_gate` |
| AC5 — migration step 4 scoped as invoking `/simq-audit` and recording its verdict, not building new SimQ infra | Step 7 | Manual verification: verdict/`runId` recorded verbatim in this ticket's Implementation Notes/Completion Summary — not a pytest test |

## Anti-Drift Notes

- **The 6-vs-9 split must stay visible everywhere it's claimed.** Step 2's 6 tests and Step 3's
  1 parametrized test must never be merged or renamed in a way that implies "all 15 tested
  end-to-end" — both the test docstrings (per-step Change text above) and the Step 6 parity ledger
  entry must state the split explicitly. If a future ticket extends `generator.py`'s `kind_map` to
  cover more families, the newly-reachable family should graduate from Step 3's mapper-level test
  into a new Step-2-style end-to-end test, and both the test docstring and the parity ledger entry
  must be updated in that same change — a stale "9 unreachable" claim would itself become a drift
  bug (test_plan.md's own anti-drift guard, adopted verbatim here).
- **Step 2's per-family fixtures rely on gold/item thresholds to isolate the winning family** (see
  Step 2's exact recipes) — these thresholds are load-bearing test data, not incidental values. If
  `services.py`'s hardcoded `Requirement(kind="has_gold", quantity=...)` values ever change (e.g.
  `buy_item`'s 15, `rest_inn`'s 10, recipe gold costs), these fixtures will silently start producing
  a different (possibly ambiguous, possibly wrong) winning family instead of failing loudly — a
  comment in the test file at each fixture should cite the exact `services.py`/`registries.py`
  line the threshold comes from, so a future reader can tell this is deliberate, not arbitrary.
- **The phase-side raw score must be read from `entity_updates[hero.id].strategic.projects_add_or_update[0].score`,
  never from `phase.py`'s local `trace_records` dict** (built at `phase.py:182-187`, confirmed
  discarded/never attached to the returned value this session — see Summary's correction). A future
  edit that "simplifies" the assertion back to something resembling test_plan.md's original "trace
  field" wording would silently fail with an `AttributeError`/`KeyError`, not a wrong-value bug — a
  loud failure, but worth flagging so implementation doesn't get stuck re-deriving this.
- **Guard against the `factions=None` vs `factions=state.factions` coincidence becoming load-bearing
  silently** (investigation.md Risk #3, adopted verbatim): every `AdventureDecisionPhase.apply(...)`
  call across all new tests must pass `factions=state.factions` explicitly. If a future "simplification"
  drops this back to the bare default, a later change to `AdventureRouteScorer.score()`'s escort
  branch (`scoring.py:133`) could introduce a real, silent divergence between the two paths with no
  test failure until much later.
- **`test_shadow_scenario_neither_path_mutates_state` must call the real
  `CanonicalStateHasher.get_hash()`**, never a hand-rolled hash or `repr(state)` string comparison.
- **BUY_UPGRADE/CRAFT_UPGRADE/ASK_INFORMATION must keep using the `_isolated_service_recipe_registries`
  fixture, never fall back to ambient `ServiceRegistry`/`RecipeRegistry` state.** These two
  registries have no autouse reset protection in `tests/conftest.py` (confirmed absent this
  session — only `ItemRegistry`/`ResourceRegistry` are protected), and are wiped to `{}` by
  `src/runtime/bootstrap.py:106-113`'s `_bootstrap_empty()` on some code paths already exercised
  elsewhere in the test suite. If a future edit drops the fixture "for simplicity," these 3 tests
  become order-dependent and can pass or fail depending on what ran earlier in the same pytest
  session — a flaky-test regression that would be hard to root-cause later without this note.
- **Do not let AC5's manual verification step get treated as satisfied by merely running the command
  once informally** — the ticket's Implementation Notes/Completion Summary must contain the literal
  verdict string, Classify Drift verdict, and `runId`, checkable by `done-checker` as a traceability
  requirement even though it is not a pytest assertion.
- **Steps 2 and 3's real family/raw_score comparisons must route through `_diff_routes()` and assert
  on its returned mismatch-category lists (`diff["family_mismatches"] == []`,
  `diff["raw_score_mismatches"] == []`) — this is not optional coverage, it is what the ticket's own
  Scope text requires.** The ticket's Scope explicitly says the per-family comparison must surface
  "normalization miscalibration as a named itemized diff report (not single pass/fail)." An earlier
  draft of this plan used bare `assert phase_family == scorer_family` / `assert phase_raw_score ==
  scorer_raw_score` in Step 2 and a single-call bare-equality form in Step 3, and treated
  `_diff_routes()` usage inside those steps as merely "optional... strengthens the coverage story" —
  an architecture-reviewer pass caught this as a real, undisclosed narrowing of the ticket's Scope. If
  a future edit "simplifies" Steps 2/3 back to bare equality asserts to save a few lines, it silently
  reintroduces the exact gap this correction closed — re-read this ticket's Scope bullet, not just its
  AC2 checkbox text, before making that change.

## Deviations (recorded during Implement)

- **Step 1's `_state()` helper needed one field correction, not a verbatim copy.** Plan.md instructed
  copying `_state(entities)` verbatim from `test_phase3_adventure_decision_phase.py:18-47`, including
  `building_tiles=()`. That file's own tests never call `CanonicalStateHasher.get_hash()`, so the
  wrong-type default (a tuple where `AuthoritativeState.building_tiles` is declared
  `Dict[tuple[int,int], str]`, `state.py:1137`) never surfaces there. This ticket's AC1 test
  (`test_shadow_scenario_neither_path_mutates_state`) is the first consumer of that helper to call
  `get_hash()`, and `CanonicalStateHasher.to_canonical_data()` does `state.building_tiles.items()`
  (`checkpoint.py:102`), which raises `AttributeError: 'tuple' object has no attribute 'items'` against
  a tuple. Fixed locally in this ticket's own copy of `_state()` (changed `building_tiles=()` to
  `building_tiles={}`) — the source file being copied from (`test_phase3_adventure_decision_phase.py`)
  was left untouched, since it is not in this ticket's Related Code Areas and its own tests do not
  exercise this code path. Everything else in the copied helper (all other fields/values) matches the
  source verbatim.
- **`test_shadow_parity_mapper_level_all_15_families`'s Step 3 description in `test_plan.md`** was
  updated in this same Implement pass to describe the actual, final two-call/`_diff_routes()`-diffed
  design (matching this plan.md's Step 3 exactly) instead of the stale single-call/
  `project.score == 1.7` bare-equality description test_plan.md still carried from before the
  Plan-phase architecture-reviewer correction. Flagged as a non-blocking documentation-sync task by
  the second plan review pass; resolved here rather than deferred further.

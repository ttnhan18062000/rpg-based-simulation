"""
tests/integration/domains/adventure/test_adventure_shadow_migration_parity.py

TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE

Shadow-mode parity test suite proving `AdventureDecisionPhase.apply()` (the
currently-live decision path) and `AdventureGoalScorer().score()` (the new,
not-yet-wired path built by TCK-20260811-ADVENTURE-GOAL-SCORER) are read-only
and produce equivalent route-family/raw_score decisions when driven by the
same real `AuthoritativeState`. Does NOT wire anything into
`src/engine/pipeline.py` -- both paths remain exactly as live/dormant as they
were before this ticket.

Coverage of "all 15 route families" is explicitly split into two tiers (see
staging_artifacts/TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE/investigation.md's
Critical Finding):
  - 6 families (RECOVER, BUY_UPGRADE, CRAFT_UPGRADE, GATHER_RESOURCE,
    ASK_INFORMATION, FORM_PARTY) are the only families
    `AdventureRouteGenerator.generate()`'s real, hardcoded `kind_map` /
    forced-route logic can ever produce from a real `AuthoritativeState`
    today -- these get real end-to-end shadow comparisons.
  - All 15 families (including the 9 currently unreachable through
    `generate()`) get a mapper-level-only parity check against the shared
    `RouteToProjectMapper.map_to_states()` function both paths call --
    this is the only parity claim provably exercisable end-to-end for the
    9 generator-unreachable families today. This is NOT end-to-end coverage
    for those 9; do not read it as such.
"""

from __future__ import annotations

from dataclasses import replace as dc_replace
from pathlib import Path

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import (
    AuthoritativeState,
    CombatComponent,
    BiologicalComponent,
    PersonalityComponent,
    NavigationComponent,
    InventoryComponent,
    ItemStack,
    ResourceNodeState,
)
from src.core.self_model import (
    SelfModelBundle,
    SelfAwarenessComponent,
    NeedInterpretationComponent,
    InterpretedNeed,
)
from src.core.strategic import BlockerState, BlockerKind
from src.engine.checkpoint import CanonicalStateHasher
from src.domains.adventure.phase import AdventureDecisionPhase
from src.domains.adventure.mapper import RouteToProjectMapper
from src.ai.goals.adventure_scorer import AdventureGoalScorer


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=5,
        seed=1,
        world_time=100,
        entities=ent_map,
        groups={},
        regions={},
        resource_nodes={},
        buildings={},
        chests={},
        ground_items={},
        corpses={},
        camps={},
        local_scars={},
        global_resources={},
        town_tiles=(),
        # building_tiles must be a dict (Dict[tuple[int,int], str], state.py:1137), not the
        # tuple used by test_phase3_adventure_decision_phase.py's own _state() helper --
        # that file never calls CanonicalStateHasher.get_hash() so the wrong-type default
        # never surfaces there. This ticket's AC1 test does call get_hash() (checkpoint.py:102
        # does `state.building_tiles.items()`), so it must be a real dict here. See this
        # ticket's plan.md Deviations note.
        building_tiles={},
        terrain=(),
        home_storage={},
        town_center=(0, 0),
        periodic_due_ticks={},
        work_debt={},
        movement_count=0,
        maturity=0,
        last_calamity_tick=0,
        blocked_tiles=(),
        town_entity_ids=(),
    )


def _diff_routes(phase_family, phase_raw_score, scorer_family, scorer_raw_score,
                  phase_utility=None, scorer_utility=None):
    """Itemized diff report -- required by the ticket's own Scope text ("surfacing
    normalization miscalibration as a named itemized diff report, not single pass/fail"),
    not just a standalone unit test. Both Step 2's real 6-family comparisons and Step 3's
    15-family mapper-level parity check route through this exact definition rather than
    bare equality asserts, so a future regression shows up as a populated mismatch list,
    not just a silent AssertionError. raw_score and utility mismatches are kept in
    separate keys so the design doc's scale-mismatch defect shape (raw_score vs. utility
    getting conflated) is caught by the report's own shape, not just its content."""
    report = {"family_mismatches": [], "raw_score_mismatches": [], "utility_mismatches": []}
    if phase_family != scorer_family:
        report["family_mismatches"].append({"phase": phase_family, "scorer": scorer_family})
    if phase_raw_score != scorer_raw_score:
        report["raw_score_mismatches"].append({"phase": phase_raw_score, "scorer": scorer_raw_score})
    if phase_utility is not None and scorer_utility is not None and phase_utility != scorer_utility:
        report["utility_mismatches"].append({"phase": phase_utility, "scorer": scorer_utility})
    return report


@pytest.fixture
def _isolated_service_recipe_registries():
    """No autouse reset exists for these two registries in tests/conftest.py (unlike
    ItemRegistry/ResourceRegistry, which ARE protected against src/runtime/bootstrap.py's
    _bootstrap_empty() -- see this ticket's plan.md Step 2 for the full citation). Snapshot
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


# ─────────────────────────────────────────────────────────────────────────────
# AC1 -- neither path mutates state
# ─────────────────────────────────────────────────────────────────────────────

def test_shadow_scenario_neither_path_mutates_state():
    """Hash state before/after EACH call individually (not just once at the end) so a
    mutation introduced by any one call is attributable to that call, not just detected
    in aggregate. Uses CanonicalStateHasher.get_hash() -- AuthoritativeState is a frozen
    dataclass with dict-typed fields, so Python's builtin hash() would raise TypeError."""
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .replace_combat(CombatComponent(hp=20, max_hp=100, atk=10, def_stat=2))
        .build()
    )
    state = _state([hero])
    hash_before = CanonicalStateHasher.get_hash(state)
    entity_before = state.entities[hero.id]

    AdventureDecisionPhase.apply(state, factions=state.factions)
    assert CanonicalStateHasher.get_hash(state) == hash_before
    assert state.entities[hero.id] == entity_before

    score_result = AdventureGoalScorer().score(hero, state)
    assert CanonicalStateHasher.get_hash(state) == hash_before
    assert state.entities[hero.id] == entity_before

    # AC1's wording explicitly covers "AdventureGoalScorer.score(entity,state)/materialization
    # independently" -- the materialization half is RouteToProjectMapper.map_to_states(), the
    # same call intelligence.py:1450-1457 makes for a winning ADVENTURE_ROUTE candidate. It
    # takes no `state` argument at all (mapper.py:67-74), so it cannot mutate state by
    # construction -- called anyway so the proof is explicit, not merely inferred from the
    # function's signature.
    RouteToProjectMapper.map_to_states(
        family=score_result.metadata["route_family"], entity_id=hero.id,
        target=score_result.target_id, target_pos=score_result.target_pos,
        tick=state.tick, score=score_result.metadata["raw_score"],
    )
    assert CanonicalStateHasher.get_hash(state) == hash_before
    assert state.entities[hero.id] == entity_before


# ─────────────────────────────────────────────────────────────────────────────
# AC2 tier 1 -- 6 real end-to-end per-family shadow parity tests
# (only families AdventureRouteGenerator.generate()'s kind_map/forced-route logic
# can actually produce from a real AuthoritativeState -- generator.py:38-181)
# ─────────────────────────────────────────────────────────────────────────────

def _run_shadow_comparison(hero, state):
    result_apply = AdventureDecisionPhase.apply(state, factions=state.factions)
    result_score = AdventureGoalScorer().score(hero, state)

    phase_upd = result_apply.entity_updates[hero.id]
    phase_family = phase_upd.property_updates["last_routing_family"]
    # Phase-side raw score MUST be read from the committed StrategicUpdate, never
    # phase.py's local `trace_records` dict (built at phase.py:182-187) -- that dict is
    # discarded, never attached to the returned StateUpdate (see plan.md Summary's
    # load-bearing correction).
    phase_raw_score = phase_upd.strategic.projects_add_or_update[0].score

    diff = _diff_routes(
        phase_family=phase_family, phase_raw_score=phase_raw_score,
        scorer_family=result_score.metadata["route_family"].value,
        scorer_raw_score=result_score.metadata["raw_score"],
    )
    assert diff["family_mismatches"] == []
    assert diff["raw_score_mismatches"] == []
    return phase_family


def test_shadow_parity_recover_family():
    # Low HP forces RECOVER structurally (generator.py:98-109), no opportunity needed.
    # gold=0 blocks all buy_item (needs gold>=15, services.py:109) and craft_item (needs
    # gold>=10/40/50, registries.py's small_potion/iron_sword/hunter_blade recipes) options.
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .replace_combat(CombatComponent(hp=20, max_hp=100, atk=10, def_stat=2))
        .replace_inventory(InventoryComponent(gold=0))
        .replace_self_model(SelfModelBundle(
            self_awareness=SelfAwarenessComponent(perceived_weaknesses=("low_health",)),
            needs=NeedInterpretationComponent(
                active_needs={"healing": InterpretedNeed(key="healing", urgency=0.9, confidence=1.0, reason="low_hp")},
                dominant_need="healing",
            ),
        ))
        .build()
    )
    state = _state([hero])
    family = _run_shadow_comparison(hero, state)
    assert family == "recover"


def test_shadow_parity_buy_upgrade_family(_isolated_service_recipe_registries):
    # gold=15 exactly meets shop_hometown's buy_item requirement (services.py:109). All 3
    # craft_item options are blocked: iron_sword/hunter_blade need gold 40/50 > 15;
    # small_potion needs gold 10 <= 15 but also healing_flower+crystal_shard items the
    # entity doesn't have -> missing_item blocker (generator.py:61-68).
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .replace_inventory(InventoryComponent(gold=15))
        .build()
    )
    state = _state([hero])
    family = _run_shadow_comparison(hero, state)
    assert family == "buy_upgrade"


def test_shadow_parity_craft_upgrade_family(_isolated_service_recipe_registries):
    # small_potion's craft opportunity (gold>=10, needs healing_flower+crystal_shard) is
    # valid; buy_item (needs gold>=15) is blocked (only have 10).
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .replace_inventory(InventoryComponent(
            gold=10,
            items=[ItemStack("healing_flower", 1), ItemStack("crystal_shard", 1)],
        ))
        .build()
    )
    state = _state([hero])
    family = _run_shadow_comparison(hero, state)
    assert family == "craft_upgrade"


def test_shadow_parity_gather_resource_family():
    # node_flower's source_region_tags=("near_forest",) matches; required_tool=None so no
    # extra has_item blocker (registries.py:681). Switching region to near_forest also
    # excludes every hometown-only ServiceRegistry entry (services.py:48's
    # s_def.region_id == current_region check fails) -- no buy/craft competition to block,
    # so this test does not need _isolated_service_recipe_registries.
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .replace_navigation(NavigationComponent(region_id="near_forest"))
        .build()
    )
    state = _state([hero])
    state = dc_replace(state, resource_nodes={
        1: ResourceNodeState(
            id=1, kind="node_flower", position=(0.0, 0.0), yields_item="healing_flower",
            remaining_charges=5, max_charges=5, required_ticks=1,
        ),
    })
    family = _run_shadow_comparison(hero, state)
    assert family == "gather_resource"


def test_shadow_parity_ask_information_family(_isolated_service_recipe_registries):
    # An unresolved MATERIAL blocker sets has_material_blocker=True, generating
    # guide_hometown's ask_information opportunity (services.py:85-98, needs gold>=10).
    # gold=10 exactly meets it; buy_item is blocked (needs 15); small_potion craft needs
    # gold>=10 (met) but also the 2 items (missing) -> blocked; iron_sword/hunter_blade
    # blocked on gold.
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .replace_inventory(InventoryComponent(gold=10))
        .strategic(blockers={
            "b1": BlockerState(id="b1", kind=BlockerKind.MATERIAL, subject="iron_ore", resolved=False),
        })
        .build()
    )
    state = _state([hero])
    family = _run_shadow_comparison(hero, state)
    assert family == "ask_information"


def test_shadow_parity_form_party_family():
    # sociability=0.5 clears the >=0.2 threshold (generator.py:129); a second, non-MONSTER,
    # alive ally entity is present. FORM_PARTY is added unconditionally once
    # sociability/candidates clear (generator.py:125-163, no forced-branch guard unlike
    # ASK_INFORMATION), and is the only valid candidate since gold=0 blocks buy/craft as in
    # the RECOVER case.
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .identity(personality=PersonalityComponent(sociability=0.5))
        .replace_inventory(InventoryComponent(gold=0))
        .build()
    )
    ally = V2EntityBuilder(2).kind("hero").build()
    state = _state([hero, ally])
    family = _run_shadow_comparison(hero, state)
    assert family == "form_party"


# ─────────────────────────────────────────────────────────────────────────────
# AC2 tier 2 -- mapper-level parity check across all 15 families
# (the only parity claim provably exercisable end-to-end for the 9 families
# generate() cannot construct today -- see module docstring)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("family", list(RouteToProjectMapper._MAP.keys()), ids=lambda f: f.value)
def test_shadow_parity_mapper_level_all_15_families(family):
    """Mapper-level only for families not reachable via generate() today. Both
    AdventureDecisionService.decide() (service.py:141-148) and the scorer-side
    materialization branch (intelligence.py:1450-1457) route through this exact shared
    RouteToProjectMapper.map_to_states() function -- calling it twice with identical
    arguments and diffing through _diff_routes() proves that shared-code purity directly,
    rather than asserting a bare `project.score == 1.7` (the previous, reviewer-rejected
    single-pass/fail form of this test)."""
    project_phase, obj_phase = RouteToProjectMapper.map_to_states(
        family=family, entity_id=1, tick=5, score=1.7, target="t", target_pos=(1.0, 2.0)
    )
    project_scorer, obj_scorer = RouteToProjectMapper.map_to_states(
        family=family, entity_id=1, tick=5, score=1.7, target="t", target_pos=(1.0, 2.0)
    )

    diff = _diff_routes(
        phase_family=project_phase.kind, phase_raw_score=project_phase.score,
        scorer_family=project_scorer.kind, scorer_raw_score=project_scorer.score,
    )
    assert diff["family_mismatches"] == []
    assert diff["raw_score_mismatches"] == []

    expected_p_kind, expected_o_kind = RouteToProjectMapper.get_kinds(family)
    assert project_phase.kind == expected_p_kind
    assert obj_phase.kind == expected_o_kind


# ─────────────────────────────────────────────────────────────────────────────
# AC3 -- diff report shape separates raw_score from utility mismatches
# ─────────────────────────────────────────────────────────────────────────────

def test_shadow_diff_report_separates_raw_score_from_utility_mismatches():
    """Exercises the shared _diff_routes() definition (Step 1) against 2 synthetic cases,
    proving the report *shape* keeps raw_score and utility mismatches apart -- catching the
    design doc's scale-mismatch bug shape (raw_score/utility conflation) by construction.
    Step 2's 6 real family tests and the mapper-level test above already exercise this same
    helper against real data; these 2 cases add coverage of the utility_mismatches category,
    which the real family tests never populate (neither path exposes a comparable utility
    for the committed decision)."""
    # Case A: raw_score differs, family matches, no utility args supplied.
    diff_a = _diff_routes(
        phase_family="recover", phase_raw_score=1.5,
        scorer_family="recover", scorer_raw_score=2.0,
    )
    assert len(diff_a["raw_score_mismatches"]) == 1
    assert diff_a["family_mismatches"] == []
    assert diff_a["utility_mismatches"] == []

    # Case B: utility differs (hypothetical -- AdventureDecisionPhase never actually
    # produces a utility value), raw_score and family match.
    diff_b = _diff_routes(
        phase_family="recover", phase_raw_score=1.5,
        scorer_family="recover", scorer_raw_score=1.5,
        phase_utility=40.0, scorer_utility=55.0,
    )
    assert len(diff_b["utility_mismatches"]) == 1
    assert diff_b["raw_score_mismatches"] == []
    assert diff_b["family_mismatches"] == []


# ─────────────────────────────────────────────────────────────────────────────
# AC4 -- ticket-text gate regression guard
# ─────────────────────────────────────────────────────────────────────────────

def test_delete_adventure_decision_phase_ac1_already_encodes_the_gate():
    """Regression guard, not a claim this ticket edits that file: the gate text already
    exists in TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE.md's own Acceptance Criteria.
    This test only guards against a future accidental edit silently dropping the hard
    dependency this ticket's own AC4 relies on."""
    repo_root = Path(__file__).resolve().parents[4]
    gate_path = (
        repo_root / "tickets" / "todos" / "adventure-cognition-merge"
        / "TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE.md"
    )
    text = gate_path.read_text()
    assert "TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (C4)" in text
    assert "both in tickets/done/" in text

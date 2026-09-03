# tests/unit/world/test_reproduction_humanoid_cadence.py
# TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE
import inspect

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.state import AuthoritativeState, RegionState, LifeStage
from src.core.updates import StateUpdate
from src.domains.demographics.cohort import PopulationCohort
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence, should_run
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.world_systems.generator import EntityGenerator
from src.world.reproduction_humanoid import HumanoidReproductionService


def _region(region_id="town", cohorts=None, bounds_=(0, 0, 100, 100)):
    return RegionState(
        id=region_id, name=f"Region {region_id}", kind="town", bounds=bounds_,
        population_cohorts=cohorts or {},
    )


def _adult(entity_id, kind="villager", pos=(5.0, 5.0), role=EntityRole.CITIZEN):
    return (V2EntityBuilder(entity_id)
            .kind(kind)
            .location(*pos)
            .identity(role=role)
            .build())


def _offspring(entities_add):
    return [e for e in entities_add if e.identity.life_stage == LifeStage.CHILD]


def _generator_for(state, seed=42):
    """Mirror src/engine/pipeline.py's own generator setup
    (`generator._last_id = state.next_entity_id - 1`) so spawned offspring never collide
    with a pre-seeded parent's hardcoded test id -- EntityGenerator.get_next_id() otherwise
    starts counting from 1 regardless of what ids already exist in state.entities."""
    generator = EntityGenerator(seed=seed)
    generator._last_id = state.next_entity_id - 1
    return generator


def test_new_cadence_entry_fires_per_should_run_pattern():
    """reproduction_humanoid follows SystemCadence's existing global should_run() pattern:
    tick % cadence == 0 with entity_id=None."""
    cadence = SystemCadence()
    assert cadence.reproduction_humanoid == 200
    assert should_run(400, None, cadence.reproduction_humanoid) is True
    assert should_run(401, None, cadence.reproduction_humanoid) is False
    assert should_run(0, None, cadence.reproduction_humanoid) is True


def test_eligible_adult_alive_same_location_same_race_pair_produces_birth():
    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=200, seed=42, entities={1: parent_a, 2: parent_b})
    generator = _generator_for(state)

    update = HumanoidReproductionService.process_reproduction(state, generator)

    offspring = _offspring(update.entities_add)
    assert len(offspring) == 1
    child = offspring[0]
    assert child.lifecycle.parent_a_entity_id == 1
    assert child.lifecycle.parent_b_entity_id == 2
    assert child.lifecycle.birth_tick == 200
    assert child.lifecycle.birth_city_id is None
    assert child.lifecycle.genetic_profile is not None


def test_no_marriage_contract_referenced_in_humanoid_reproduction_path():
    """AC3: no marriage-contract state is read or checked anywhere in this eligibility path."""
    from src.world import reproduction_humanoid as repro_module
    from src.systems.world_systems import generator as generator_module

    for source in (
        inspect.getsource(repro_module.HumanoidReproductionService.process_reproduction),
        inspect.getsource(generator_module.EntityGenerator.spawn_humanoid_offspring),
    ):
        assert "ContractKind.MARRIAGE" not in source
        assert "MarriageState" not in source
        assert "ContractState" not in source

    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=200, seed=42, entities={1: parent_a, 2: parent_b})
    generator = _generator_for(state)

    update = HumanoidReproductionService.process_reproduction(state, generator)

    offspring = _offspring(update.entities_add)
    assert len(offspring) == 1
    assert offspring[0].strategic.contracts == {}


def test_no_population_cohorts_write_when_birth_region_unresolved():
    """When SpatialQueryService.get_region_at() resolves no region (no regions declared
    in state), there is no region to attribute the nudge to -- skipped, not defaulted."""
    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=200, seed=42, entities={1: parent_a, 2: parent_b})
    generator = _generator_for(state)

    update = HumanoidReproductionService.process_reproduction(state, generator)

    assert update.world_updates == {}


def test_humanoid_birth_nudges_young_cohort_by_one():
    """TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE (AC#1/AC#2): a successful
    humanoid birth nudges the birth region's population_young_births_delta by exactly +1,
    additive-only -- never a population_cohorts_set resync."""
    region = _region()
    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(
        tick=200, seed=42, entities={1: parent_a, 2: parent_b}, regions={"town": region},
    )
    generator = _generator_for(state)

    update = HumanoidReproductionService.process_reproduction(state, generator)

    assert update.world_updates["town"].population_young_births_delta == 1
    assert update.world_updates["town"].population_cohorts_set is None


def test_social_bond_seeded_between_each_parent_and_child_at_high_familiarity_sentiment():
    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=200, seed=42, entities={1: parent_a, 2: parent_b})
    generator = _generator_for(state)

    update = HumanoidReproductionService.process_reproduction(state, generator)
    child = _offspring(update.entities_add)[0]

    assert set(child.social.bonds.keys()) == {1, 2}
    for parent_id in (1, 2):
        bond = child.social.bonds[parent_id]
        assert bond.familiarity == 0.8
        assert bond.sentiment == 0.8

    for parent_id in (1, 2):
        parent_update = update.entity_updates[parent_id]
        assert parent_update.social is not None
        bond_update = parent_update.social.bond_updates[0]
        assert bond_update.target_id == child.id
        assert bond_update.familiarity_delta == 0.8
        assert bond_update.sentiment_delta == 0.8


def test_both_parents_cooldown_set_and_repeat_check_before_cooldown_clears_produces_no_second_birth():
    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=200, seed=42, entities={1: parent_a, 2: parent_b})
    generator = _generator_for(state)

    first_update = HumanoidReproductionService.process_reproduction(state, generator)
    assert len(_offspring(first_update.entities_add)) == 1

    next_state = ApplyPath.apply_generation(state, first_update, 201, 201)

    assert next_state.entities[1].lifecycle.reproduction_cooldowns.get(2) == 200 + HumanoidReproductionService.REPRODUCTION_COOLDOWN_TICKS
    assert next_state.entities[2].lifecycle.reproduction_cooldowns.get(1) == 200 + HumanoidReproductionService.REPRODUCTION_COOLDOWN_TICKS

    repeat_state = AuthoritativeState(
        tick=201, seed=42,
        entities={1: next_state.entities[1], 2: next_state.entities[2]},
    )
    second_update = HumanoidReproductionService.process_reproduction(repeat_state, _generator_for(repeat_state))
    assert _offspring(second_update.entities_add) == []


def test_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold():
    cohort = PopulationCohort(bracket="young", count=10, migration_threshold=0.7)
    region = _region(cohorts={"young": cohort})
    from src.core.state import ResourceNodeState
    depleted = ResourceNodeState(
        id=1, kind="WOOD", position=(5.0, 5.0), yields_item="wood_log",
        remaining_charges=0, max_charges=5, required_ticks=10,
    )
    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(
        tick=200, seed=42,
        entities={1: parent_a, 2: parent_b},
        regions={"town": region},
        resource_nodes={1: depleted},
    )
    generator = _generator_for(state)

    update = HumanoidReproductionService.process_reproduction(state, generator)

    assert _offspring(update.entities_add) == []


def test_eligibility_allowed_when_regional_scarcity_below_migration_threshold():
    cohort = PopulationCohort(bracket="young", count=10, migration_threshold=0.7)
    region = _region(cohorts={"young": cohort})
    from src.core.state import ResourceNodeState
    full = ResourceNodeState(
        id=1, kind="WOOD", position=(5.0, 5.0), yields_item="wood_log",
        remaining_charges=5, max_charges=5, required_ticks=10,
    )
    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(
        tick=200, seed=42,
        entities={1: parent_a, 2: parent_b},
        regions={"town": region},
        resource_nodes={1: full},
    )
    generator = _generator_for(state)

    update = HumanoidReproductionService.process_reproduction(state, generator)

    assert len(_offspring(update.entities_add)) == 1


def test_ineligible_pairs_produce_no_birth():
    # Not same kind.
    a = _adult(1, kind="villager", pos=(5.0, 5.0))
    b = _adult(2, kind="goblin_warrior", pos=(5.0, 5.0))
    state = AuthoritativeState(tick=200, seed=42, entities={1: a, 2: b})
    assert _offspring(HumanoidReproductionService.process_reproduction(state, _generator_for(state)).entities_add) == []

    # Not co-located (outside HUMANOID_PAIRING_RADIUS).
    a = _adult(1, pos=(0.0, 0.0))
    b = _adult(2, pos=(50.0, 50.0))
    state = AuthoritativeState(tick=200, seed=42, entities={1: a, 2: b})
    assert _offspring(HumanoidReproductionService.process_reproduction(state, _generator_for(state)).entities_add) == []

    # Not alive.
    a = _adult(1, pos=(5.0, 5.0))
    b = (V2EntityBuilder(2).kind("villager").location(5.0, 5.0).combat(alive=False).build())
    state = AuthoritativeState(tick=200, seed=42, entities={1: a, 2: b})
    assert _offspring(HumanoidReproductionService.process_reproduction(state, _generator_for(state)).entities_add) == []

    # Not ADULT.
    a = _adult(1, pos=(5.0, 5.0))
    b = (V2EntityBuilder(2).kind("villager").location(5.0, 5.0).identity(life_stage=LifeStage.CHILD).build())
    state = AuthoritativeState(tick=200, seed=42, entities={1: a, 2: b})
    assert _offspring(HumanoidReproductionService.process_reproduction(state, _generator_for(state)).entities_add) == []


def test_flag_off_produces_no_birth_regression_guard():
    """Regression guard: with the flag left at its default OFF, WorldDynamicsSystem's
    resolve_dynamics() call site must never invoke HumanoidReproductionService."""
    from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode

    manager = FeatureFlagManager()
    assert manager.get_flag_mode("ENABLE_REPRODUCTION_HUMANOID_PATH") == FeatureMode.OFF
    assert "ENABLE_REPRODUCTION_HUMANOID_PATH" in manager.get_all_flags()

    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=200, seed=42, entities={1: parent_a, 2: parent_b})
    generator = _generator_for(state)
    cadence = SystemCadence(world_dynamics=1, reproduction_humanoid=1)

    update = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), generator, cadence)

    assert _offspring(update.entities_add) == []


def test_genetics_uses_real_parent_role_data_for_combat_lean():
    """Anti-drift guard: both parents EntityRole.HERO must produce a combat-lean child
    GeneticProfile, proving parent_a_role/parent_b_role are actually threaded through this
    ticket's own call site (investigation.md Risk #6), not just covered by
    combine_profiles()'s pre-existing unit tests."""
    parent_a = _adult(1, pos=(5.0, 5.0), role=EntityRole.HERO)
    parent_b = _adult(2, pos=(5.0, 5.0), role=EntityRole.HERO)
    state = AuthoritativeState(tick=200, seed=42, entities={1: parent_a, 2: parent_b})
    generator = _generator_for(state)

    combat_lean_update = HumanoidReproductionService.process_reproduction(state, generator)
    combat_lean_child = _offspring(combat_lean_update.entities_add)[0]

    parent_c = _adult(3, pos=(5.0, 5.0), role=EntityRole.CITIZEN)
    parent_d = _adult(4, pos=(5.0, 5.0), role=EntityRole.CITIZEN)
    neutral_state = AuthoritativeState(tick=200, seed=42, entities={3: parent_c, 4: parent_d})
    neutral_update = HumanoidReproductionService.process_reproduction(neutral_state, _generator_for(neutral_state))
    neutral_child = _offspring(neutral_update.entities_add)[0]

    combat_lean_total = (combat_lean_child.lifecycle.genetic_profile.strength_mult
                          + combat_lean_child.lifecycle.genetic_profile.agility_mult)
    neutral_total = (neutral_child.lifecycle.genetic_profile.strength_mult
                      + neutral_child.lifecycle.genetic_profile.agility_mult)
    assert combat_lean_total != neutral_total


def test_humanoid_reproduction_commits_through_authoritative_apply_path():
    """Integration: the 3.10 call site wiring produces a StateUpdate that, applied through
    the normal authoritative apply path, lands a new tracked-parent child entity plus both
    parents' cooldown writes in the next AuthoritativeState."""
    parent_a = _adult(1, pos=(5.0, 5.0))
    parent_b = _adult(2, pos=(5.0, 5.0))
    state = AuthoritativeState(
        tick=200, seed=42,
        entities={1: parent_a, 2: parent_b},
        feature_flags={"ENABLE_REPRODUCTION_HUMANOID_PATH": "ON"},
    )
    generator = _generator_for(state)
    cadence = SystemCadence(world_dynamics=1, reproduction_humanoid=1)

    update = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), generator, cadence)
    next_state = ApplyPath.apply_generation(state, update, 201, 201, cadence=cadence)

    children = [e for e in next_state.entities.values() if e.id not in (1, 2)]
    assert len(children) == 1
    child = children[0]
    assert child.lifecycle.parent_a_entity_id == 1
    assert child.lifecycle.parent_b_entity_id == 2

    expiry = 200 + HumanoidReproductionService.REPRODUCTION_COOLDOWN_TICKS
    assert next_state.entities[1].lifecycle.reproduction_cooldowns.get(2) == expiry
    assert next_state.entities[2].lifecycle.reproduction_cooldowns.get(1) == expiry

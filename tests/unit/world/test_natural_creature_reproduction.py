# tests/unit/world/test_natural_creature_reproduction.py
# TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH
import inspect

import pytest

from src.core.state import AuthoritativeState, RegionState, CampState, LifeStage, ResourceNodeState
from src.domains.demographics.cohort import PopulationCohort
from src.systems.world_systems.generator import EntityGenerator
from src.world.camp import CampService
from src.ai.life_stage import LifeStageService


def _region(region_id="forest", cohorts=None, bounds_=(0, 0, 100, 100)):
    return RegionState(
        id=region_id, name=f"Region {region_id}", kind="forest", bounds=bounds_,
        population_cohorts=cohorts or {},
    )


def _node(node_id, position, remaining_charges, max_charges=5):
    return ResourceNodeState(
        id=node_id, kind="WOOD", position=position, yields_item="wood_log",
        remaining_charges=remaining_charges, max_charges=max_charges, required_ticks=10,
    )


def _camp(camp_id="camp_1", kind="goblin", position=(50.0, 50.0), maturity=90.0, last_raid_tick=0):
    return CampState(id=camp_id, kind=kind, position=position, maturity=maturity, last_raid_tick=last_raid_tick)


def _natural_creature_offspring(entities_add):
    return [e for e in entities_add if e.identity.life_stage == LifeStage.CHILD]


def test_camp_maturity_threshold_spawns_natural_creature_offspring():
    """Flag ON, camp at/above RAID_MATURITY_THRESHOLD on the CAMP_SPAWN_INTERVAL cadence, no
    cohort data seeded (eligible by default per Decision 2) -> a same-kind offspring spawns."""
    state = AuthoritativeState(
        tick=60, seed=42,
        regions={"forest": _region()},
        camps={"camp_1": _camp()},
        feature_flags={"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": "ON"},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    offspring = _natural_creature_offspring(update.entities_add)
    assert len(offspring) == 1
    assert offspring[0].kind == "goblin_warrior"
    assert offspring[0].position == (50.0, 50.0)


def test_natural_creature_offspring_has_no_tracked_parents():
    generator = EntityGenerator(seed=42)
    offspring = generator.spawn_natural_creature_offspring(
        (10.0, 20.0), state=AuthoritativeState(tick=100, seed=1), kind="goblin_warrior",
        difficulty_tier=1, birth_tick=100,
    )

    assert offspring.lifecycle.parent_a_entity_id is None
    assert offspring.lifecycle.parent_b_entity_id is None
    assert offspring.lifecycle.birth_tick == 100
    assert offspring.lifecycle.birth_city_id is None
    assert offspring.social.bonds == {}


def test_natural_creature_offspring_short_maturation_clock():
    generator = EntityGenerator(seed=42)
    offspring = generator.spawn_natural_creature_offspring(
        (0.0, 0.0), state=AuthoritativeState(tick=0, seed=1), birth_tick=0,
    )

    short_clock_age = 3000 - CampService.CAMP_SPAWN_INTERVAL
    assert offspring.lifecycle.age_ticks == short_clock_age
    assert offspring.identity.life_stage == LifeStage.CHILD

    # Not yet ADULT at the pre-seeded age.
    assert LifeStageService.get_stage_for_age(short_clock_age) == LifeStage.CHILD
    # After exactly CAMP_SPAWN_INTERVAL more ticks (one spawn-cadence cycle), ADULT is reached.
    assert LifeStageService.get_stage_for_age(short_clock_age + CampService.CAMP_SPAWN_INTERVAL) == LifeStage.ADULT
    # One tick short of the boundary is still CHILD.
    assert LifeStageService.get_stage_for_age(short_clock_age + CampService.CAMP_SPAWN_INTERVAL - 1) == LifeStage.CHILD


def test_spawn_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold():
    cohort = PopulationCohort(bracket="young", count=10, migration_threshold=0.7)
    region = _region(cohorts={"young": cohort})
    depleted = _node(1, (50.0, 50.0), remaining_charges=0, max_charges=5)
    state = AuthoritativeState(
        tick=60, seed=42,
        regions={"forest": region},
        camps={"camp_1": _camp()},
        resource_nodes={1: depleted},
        feature_flags={"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": "ON"},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    assert _natural_creature_offspring(update.entities_add) == []


def test_spawn_eligibility_allowed_when_regional_scarcity_below_migration_threshold():
    cohort = PopulationCohort(bracket="young", count=10, migration_threshold=0.7)
    region = _region(cohorts={"young": cohort})
    full = _node(1, (50.0, 50.0), remaining_charges=5, max_charges=5)
    state = AuthoritativeState(
        tick=60, seed=42,
        regions={"forest": region},
        camps={"camp_1": _camp()},
        resource_nodes={1: full},
        feature_flags={"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": "ON"},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    assert len(_natural_creature_offspring(update.entities_add)) == 1


def test_spawn_eligibility_allowed_when_region_has_no_population_cohorts():
    """Explicit no-cohort-data-treated-as-eligible branch (Decision 2), mirroring
    cohort.py's own skip-when-empty convention -- not "assume worst case"."""
    region = _region(cohorts={})
    state = AuthoritativeState(
        tick=60, seed=42,
        regions={"forest": region},
        camps={"camp_1": _camp()},
        feature_flags={"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": "ON"},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    assert len(_natural_creature_offspring(update.entities_add)) == 1


def test_natural_creature_reproduction_does_not_write_population_cohorts():
    state = AuthoritativeState(
        tick=60, seed=42,
        regions={"forest": _region()},
        camps={"camp_1": _camp()},
        feature_flags={"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": "ON"},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    assert update.world_updates == {}


def test_natural_creature_reproduction_does_not_reference_genetics():
    """Behavioral-form guard: the natural-creature spawn path must never import or call
    GeneticsSystem/GeneticProfile -- explicitly out of scope per the ticket."""
    from src.world import camp as camp_module
    from src.systems.world_systems import generator as generator_module

    for source in (
        inspect.getsource(camp_module.CampService.process_camps),
        inspect.getsource(generator_module.EntityGenerator.spawn_natural_creature_offspring),
    ):
        assert "Genetics" not in source


def test_flag_off_by_default_does_not_spawn_natural_creature_offspring():
    """Regression guard: with the flag left at its default OFF, existing behavior
    (garrison spawn/raid trigger) must be byte-for-byte unaffected."""
    state = AuthoritativeState(
        tick=60, seed=42,
        regions={"forest": _region()},
        camps={"camp_1": _camp()},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    assert _natural_creature_offspring(update.entities_add) == []


def test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile():
    """TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE anti-drift guard: neither
    spawn path calls birth_record() with parent genetic profiles, so the produced
    entity's lifecycle.genetic_profile must stay None -- this ticket's inheritance
    wiring is human/humanoid-only, via V2EntityBuilder.birth_record()'s new optional
    kwargs, and must never be exercised by the natural-creature or magical/demonic
    parentless spawn paths."""
    state = AuthoritativeState(tick=60, seed=42)
    generator = EntityGenerator(seed=42)

    natural_creature = generator.spawn_natural_creature_offspring(
        (10.0, 20.0), state=state, kind="goblin_warrior", difficulty_tier=1, birth_tick=60,
    )
    assert natural_creature.lifecycle.genetic_profile is None

    magical_demonic = generator.spawn_magical_demonic_entity(
        (10.0, 20.0), state=state, difficulty_tier=4, birth_tick=60,
    )
    assert magical_demonic.lifecycle.genetic_profile is None

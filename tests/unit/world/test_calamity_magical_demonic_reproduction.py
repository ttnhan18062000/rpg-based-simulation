# tests/unit/world/test_calamity_magical_demonic_reproduction.py
# TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH
import inspect

from src.core.state import AuthoritativeState, RegionState, LifeStage
from src.systems.world_systems.generator import EntityGenerator
from src.world.calamity import CalamityService


def _region(region_id="wild", calamity_intensity=0.6, bounds=(0, 0, 100, 100)):
    return RegionState(
        id=region_id, name=f"Region {region_id}", bounds=bounds,
        calamity_intensity=calamity_intensity,
    )


def _trigger_state(regions=None, feature_flags=None, tick=5000):
    return AuthoritativeState(
        tick=tick, seed=42,
        last_calamity_tick=0,
        regions=regions or {"wild": _region()},
        feature_flags=feature_flags or {},
    )


def _magical_demonic_entities(entities_add):
    return [e for e in entities_add if e.kind == "magical_demonic_entity"]


def test_calamity_trigger_spawns_magical_demonic_entity_when_flag_on():
    """Flag ON, calamity trigger conditions met (tick - last_calamity_tick >=
    CALAMITY_MIN_INTERVAL, tick % CALAMITY_FORCE_INTERVAL == 0, a region with
    calamity_intensity > 0.3) -> a magical_demonic_entity spawns alongside the world_boss."""
    state = _trigger_state(feature_flags={"ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH": "ON"})
    generator = EntityGenerator(seed=42)

    update = CalamityService.process_world_dynamics(state, generator)

    spawned = _magical_demonic_entities(update.entities_add)
    assert len(spawned) == 1
    assert any(e.kind == "world_boss" for e in update.entities_add)


def test_magical_demonic_entity_spawns_as_adult_with_no_maturation_clock():
    """AC2: ADULT life stage, no CHILD kwarg, and no pre-seeded age_ticks (default 0, not
    the natural-creature sibling's 2970 short-clock value)."""
    generator = EntityGenerator(seed=42)
    entity = generator.spawn_magical_demonic_entity(
        (10.0, 20.0), state=AuthoritativeState(tick=5000, seed=1), birth_tick=5000,
    )

    assert entity.identity.life_stage == LifeStage.ADULT
    assert entity.lifecycle.age_ticks == 0


def test_magical_demonic_entity_has_parentless_birth_record():
    """AC3: parentless birth record, correct birth_tick, no birth_city_id, position
    inside the target region's bounds."""
    generator = EntityGenerator(seed=42)
    entity = generator.spawn_magical_demonic_entity(
        (10.0, 20.0), state=AuthoritativeState(tick=5000, seed=1), birth_tick=5000,
    )

    assert entity.lifecycle.parent_a_entity_id is None
    assert entity.lifecycle.parent_b_entity_id is None
    assert entity.lifecycle.birth_tick == 5000
    assert entity.lifecycle.birth_city_id is None
    assert entity.social.bonds == {}
    assert entity.navigation.position == (10.0, 20.0)


def test_flag_off_by_default_does_not_spawn_magical_demonic_entity():
    """Regression guard: with the flag left at its default OFF, existing world_boss
    spawn behavior must be byte-for-byte unaffected."""
    state = _trigger_state()
    generator = EntityGenerator(seed=42)

    update = CalamityService.process_world_dynamics(state, generator)

    assert _magical_demonic_entities(update.entities_add) == []
    assert len(update.entities_add) == 1
    assert update.entities_add[0].kind == "world_boss"


def test_magical_demonic_reproduction_does_not_reference_genetics():
    """Behavioral-form guard: the magical/demonic spawn path must never import or call
    GeneticsSystem/GeneticProfile -- explicitly out of scope per the ticket."""
    from src.world import calamity as calamity_module
    from src.systems.world_systems import generator as generator_module

    for source in (
        inspect.getsource(calamity_module.CalamityService.process_world_dynamics),
        inspect.getsource(generator_module.EntityGenerator.spawn_magical_demonic_entity),
    ):
        assert "Genetics" not in source


def test_magical_demonic_reproduction_does_not_write_population_cohorts():
    """Decision 1: purely calamity-intensity-driven, no population-pressure gate and no
    population_cohorts_set write."""
    state = _trigger_state(feature_flags={"ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH": "ON"})
    generator = EntityGenerator(seed=42)

    update = CalamityService.process_world_dynamics(state, generator)

    assert update.world_updates == {}


def test_flag_registered_as_its_own_distinct_key():
    """Flag-name-uniqueness guard: ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH is its own
    key in feature_flags.py, not aliased to ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH."""
    from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode

    manager = FeatureFlagManager()
    assert manager.get_flag_mode("ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH") == FeatureMode.OFF
    assert "ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH" in manager.get_all_flags()
    assert "ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH" in manager.get_all_flags()

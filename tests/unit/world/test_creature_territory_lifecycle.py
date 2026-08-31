# Compliance IDs: WORLD-118, WORLD-119
import pytest
from src.core.state import (
    AuthoritativeState, RegionState, CampState, EntityState,
    IdentityComponent, NavigationComponent, CombatComponent,
)
from src.core.enums import EntityRole
from src.systems.world_systems.generator import EntityGenerator
from src.world.creature_territory import CreatureTerritoryService
from src.engine.world_dynamics import WorldDynamicsSystem
from src.engine.cadence import SystemCadence
from src.core.updates import StateUpdate


def _monster_entity(entity_id: int, kind: str = "goblin_warrior", position=(50.0, 50.0),
                     territory_maturity: float = 0.0) -> EntityState:
    return EntityState(
        id=entity_id,
        kind=kind,
        identity=IdentityComponent(role=EntityRole.MONSTER, territory_maturity=territory_maturity),
        navigation=NavigationComponent(position=position),
        combat=CombatComponent(alive=True),
    )


def _state_with_camp(trauma_score: float, monster: EntityState, feature_flags=None) -> AuthoritativeState:
    return AuthoritativeState(
        tick=1,
        seed=42,
        regions={"forest": RegionState(id="forest", name="The Deep Woods", kind="forest",
                                        bounds=(0, 0, 100, 100), trauma_score=trauma_score)},
        camps={"camp_1": CampState(id="camp_1", kind="goblin", position=(50, 50), maturity=10.0)},
        entities={monster.id: monster},
        feature_flags=feature_flags or {},
    )


def test_creature_maturity_delta_scales_with_region_trauma():
    generator = EntityGenerator(seed=42)

    low_trauma_state = _state_with_camp(40.0, _monster_entity(1))
    low_update = CreatureTerritoryService.process_territories(low_trauma_state, generator)
    low_delta = low_update.entity_updates[1].identity.territory_maturity_delta

    high_trauma_state = _state_with_camp(60.0, _monster_entity(1))
    high_update = CreatureTerritoryService.process_territories(high_trauma_state, generator)
    high_delta = high_update.entity_updates[1].identity.territory_maturity_delta

    assert high_delta == pytest.approx(low_delta * 1.5)


def test_per_species_pacing_constants_are_inspectable():
    assert len(CreatureTerritoryService.TERRITORY_MATURITY_RATES) >= 2
    assert len(set(CreatureTerritoryService.TERRITORY_MATURITY_RATES.values())) >= 2


TRAUMA_SAMPLES = [0.0, 40.0, 50.0, 50.01, 51.0, 80.0, 100.0]


def _delta_for_trauma(trauma_score: float, species: str = "goblin_warrior") -> float:
    generator = EntityGenerator(seed=42)
    state = _state_with_camp(trauma_score, _monster_entity(1, kind=species))
    update = CreatureTerritoryService.process_territories(state, generator)
    return update.entity_updates[1].identity.territory_maturity_delta


@pytest.mark.parametrize("i", range(len(TRAUMA_SAMPLES) - 1))
def test_region_trauma_increase_never_decreases_maturity_growth_rate(i):
    t1, t2 = TRAUMA_SAMPLES[i], TRAUMA_SAMPLES[i + 1]
    delta_t1 = _delta_for_trauma(t1)
    delta_t2 = _delta_for_trauma(t2)
    assert delta_t2 >= delta_t1, (
        f"trauma {t1}->{t2} decreased maturity delta: {delta_t1} -> {delta_t2}"
    )


def test_creature_reaches_maturity_threshold_spawns_or_transitions():
    generator = EntityGenerator(seed=42)

    below_state = _state_with_camp(
        0.0, _monster_entity(1, territory_maturity=CreatureTerritoryService.TERRITORY_MATURITY_THRESHOLD - 10.0)
    )
    below_update = CreatureTerritoryService.process_territories(below_state, generator)
    assert not below_update.entities_add
    below_delta = below_update.entity_updates[1].identity.territory_maturity_delta
    assert (CreatureTerritoryService.TERRITORY_MATURITY_THRESHOLD - 10.0) + below_delta < \
        CreatureTerritoryService.TERRITORY_MATURITY_THRESHOLD

    pre_tick_maturity = CreatureTerritoryService.TERRITORY_MATURITY_THRESHOLD - 0.01
    crossing_state = _state_with_camp(
        60.0, _monster_entity(1, kind="goblin_warrior", territory_maturity=pre_tick_maturity)
    )
    crossing_update = CreatureTerritoryService.process_territories(crossing_state, generator)
    assert len(crossing_update.entities_add) == 1
    assert crossing_update.entities_add[0].kind == "goblin_warrior"
    emitted_delta = crossing_update.entity_updates[1].identity.territory_maturity_delta
    assert emitted_delta == pytest.approx(-pre_tick_maturity)
    assert pre_tick_maturity + emitted_delta == pytest.approx(0.0)


def test_creature_territory_lifecycle_flag_on_activates_maturity_processing():
    state = _state_with_camp(60.0, _monster_entity(1),
                              feature_flags={"ENABLE_CREATURE_TERRITORY_LIFECYCLE": "ON"})
    generator = EntityGenerator(seed=42)

    result = WorldDynamicsSystem.resolve_dynamics(
        state, StateUpdate(), generator, cadence=SystemCadence(world_dynamics=1)
    )

    assert not result.is_noop()
    assert 1 in result.entity_updates
    assert result.entity_updates[1].identity is not None
    assert result.entity_updates[1].identity.territory_maturity_delta != 0.0


def test_creature_territory_lifecycle_flag_default_off_no_behavior_change():
    from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode
    assert FeatureFlagManager().get_flag_mode("ENABLE_CREATURE_TERRITORY_LIFECYCLE") == FeatureMode.OFF

    state_off = _state_with_camp(60.0, _monster_entity(1))
    state_on = _state_with_camp(60.0, _monster_entity(1),
                                 feature_flags={"ENABLE_CREATURE_TERRITORY_LIFECYCLE": "ON"})

    generator_off = EntityGenerator(seed=42)
    generator_on = EntityGenerator(seed=42)

    update_off = WorldDynamicsSystem.resolve_dynamics(
        state_off, StateUpdate(), generator_off, cadence=SystemCadence(world_dynamics=1)
    )
    update_on = WorldDynamicsSystem.resolve_dynamics(
        state_on, StateUpdate(), generator_on, cadence=SystemCadence(world_dynamics=1)
    )

    assert 1 not in update_off.entity_updates or update_off.entity_updates[1].identity is None
    assert 1 in update_on.entity_updates
    assert update_on.entity_updates[1].identity.territory_maturity_delta != 0.0


def test_fast_replace_identity_preserves_territory_maturity_on_intent_only_update():
    """Regression: ApplyPath._fast_replace_identity hand-builds IdentityComponent
    via object.__new__ + per-field object.__setattr__, bypassing replace(). An
    EntityUpdate carrying only intent_results (no identity/group_id/property
    delta) — the exact shape of a shop buy/sell or quest-reward intent — takes
    this fast path (IdentityPatch.apply, patches.py) instead of the normal
    replace() path (patches.py's else branch). territory_maturity was missing
    from the fast path's field list, silently resetting it on every such update.
    """
    from src.core.state import IntentResult
    from src.core.updates import EntityUpdate
    from src.engine.apply import ApplyPath

    monster = _monster_entity(1, territory_maturity=7.5)
    state = AuthoritativeState(tick=1, seed=42, entities={1: monster})

    intent_only_update = EntityUpdate(
        entity_id=1,
        intent_results=[IntentResult(
            transaction_id="tx-1", accepted=True, reason=None,
            source_kind="shop", source_id=10,
        )],
    )
    assert intent_only_update.identity is None
    assert intent_only_update.group_id_set is None
    assert not intent_only_update.property_updates

    new_state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: intent_only_update}))

    assert new_state.entities[1].identity.territory_maturity == pytest.approx(7.5)


def test_monster_kind_entities_remain_outside_generic_biological_needs():
    state = _state_with_camp(60.0, _monster_entity(1),
                              feature_flags={"ENABLE_CREATURE_TERRITORY_LIFECYCLE": "ON"})
    generator = EntityGenerator(seed=42)

    result = WorldDynamicsSystem.resolve_dynamics(
        state, StateUpdate(), generator, cadence=SystemCadence(world_dynamics=1)
    )

    assert result.entity_updates[1].biological is None

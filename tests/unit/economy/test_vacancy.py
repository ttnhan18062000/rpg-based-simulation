"""Unit tests for EconomicVacancyService (TCK-20260903-ECONOMIC-VACANCY-SIGNAL, idea 64)."""
from src.core.state import AuthoritativeState, RegionState
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.economy.vacancy import EconomicVacancyService
from src.domains.world_emergence.schema import WorldEventCategory


def _region(region_id="region_01"):
    return RegionState(id=region_id, name="Test Region", bounds=(0, 0, 100, 100))


def test_sole_shopkeeper_death_emits_vacancy_event():
    dying = (V2EntityBuilder(1)
             .location(10.0, 10.0)
             .identity(role=EntityRole.SHOPKEEPER)
             .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: dying}, regions={"region_01": _region()})

    update = EconomicVacancyService.check_and_emit(state, [dying])

    assert len(update.world_events_add) == 1
    event = update.world_events_add[0]
    assert event.category == WorldEventCategory.PRODUCTION_ROLE_VACATED
    assert event.region_id == "region_01"
    assert event.subject == "1"
    assert event.payload == {"vacated_role": float(int(EntityRole.SHOPKEEPER))}


def test_non_sole_occupant_death_does_not_emit_vacancy_event():
    dying = (V2EntityBuilder(1)
             .location(10.0, 10.0)
             .identity(role=EntityRole.SHOPKEEPER)
             .build())
    surviving_peer = (V2EntityBuilder(2)
                       .location(20.0, 20.0)
                       .identity(role=EntityRole.SHOPKEEPER)
                       .build())
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: dying, 2: surviving_peer},
        regions={"region_01": _region()},
    )

    update = EconomicVacancyService.check_and_emit(state, [dying])

    assert update.world_events_add == []


def test_role_and_region_scope_of_sole_occupant_check():
    """A living peer of the same role but a different region does not mask the vacancy; a
    living entity of a different role in the same region also does not mask it."""
    dying = (V2EntityBuilder(1)
             .location(10.0, 10.0)
             .identity(role=EntityRole.SHOPKEEPER)
             .build())
    same_role_other_region = (V2EntityBuilder(2)
                               .location(200.0, 200.0)
                               .identity(role=EntityRole.SHOPKEEPER)
                               .build())
    other_role_same_region = (V2EntityBuilder(3)
                               .location(15.0, 15.0)
                               .identity(role=EntityRole.WORKER)
                               .build())
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: dying, 2: same_role_other_region, 3: other_role_same_region},
        regions={
            "region_01": _region("region_01"),
            "region_02": RegionState(id="region_02", name="Other", bounds=(150, 150, 250, 250)),
        },
    )

    update = EconomicVacancyService.check_and_emit(state, [dying])

    assert len(update.world_events_add) == 1
    assert update.world_events_add[0].region_id == "region_01"


def test_non_production_role_death_does_not_emit_vacancy_event():
    dying_guard = (V2EntityBuilder(1)
                   .location(10.0, 10.0)
                   .identity(role=EntityRole.GUARD)
                   .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: dying_guard}, regions={"region_01": _region()})

    update = EconomicVacancyService.check_and_emit(state, [dying_guard])

    assert update.world_events_add == []


def test_old_age_death_of_prior_occupant_does_not_mask_vacancy():
    """Regression for the review-flagged liveness-filter mismatch: an entity that died of
    OLD_AGE earlier never gets combat.alive_set=False (only lifecycle.active=False is ever
    written for that death reason -- see src/systems/lifecycle_systems/lifecycle.py's
    death-marking block). A stale corpse with lifecycle.active=False but combat.alive still True
    must not be counted as a still-living occupant, or the vacancy check would silently miss the
    real vacancy left when the last live SHOPKEEPER in the region also dies."""
    stale_old_age_corpse = (V2EntityBuilder(2)
                             .location(12.0, 12.0)
                             .identity(role=EntityRole.SHOPKEEPER)
                             .lifecycle(active=False)
                             .combat(alive=True)
                             .build())
    dying = (V2EntityBuilder(1)
             .location(10.0, 10.0)
             .identity(role=EntityRole.SHOPKEEPER)
             .build())
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: dying, 2: stale_old_age_corpse},
        regions={"region_01": _region()},
    )

    # A combat.alive-only filter (mirroring OccupationChangeGoalScorer exactly) would treat
    # entity 2 as still occupying the region and miss the vacancy entirely.
    assert stale_old_age_corpse.combat.alive is True
    assert stale_old_age_corpse.lifecycle.active is False

    update = EconomicVacancyService.check_and_emit(state, [dying])

    assert len(update.world_events_add) == 1
    assert update.world_events_add[0].region_id == "region_01"


def test_multiple_deaths_only_emits_for_sole_occupant_roles():
    sole_shopkeeper = (V2EntityBuilder(1)
                        .location(10.0, 10.0)
                        .identity(role=EntityRole.SHOPKEEPER)
                        .build())
    non_sole_worker = (V2EntityBuilder(2)
                        .location(11.0, 11.0)
                        .identity(role=EntityRole.WORKER)
                        .build())
    surviving_worker = (V2EntityBuilder(3)
                         .location(12.0, 12.0)
                         .identity(role=EntityRole.WORKER)
                         .build())
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: sole_shopkeeper, 2: non_sole_worker, 3: surviving_worker},
        regions={"region_01": _region()},
    )

    update = EconomicVacancyService.check_and_emit(state, [sole_shopkeeper, non_sole_worker])

    assert len(update.world_events_add) == 1
    assert update.world_events_add[0].subject == "1"


def test_no_recent_deaths_returns_empty_update():
    state = AuthoritativeState(tick=100, seed=42, entities={}, regions={"region_01": _region()})
    update = EconomicVacancyService.check_and_emit(state, [])
    assert update.world_events_add == []

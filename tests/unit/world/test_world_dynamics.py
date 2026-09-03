import pytest
from src.core.state import AuthoritativeState, RegionState, CampState
from src.core.updates import StateUpdate
from src.engine.cadence import SystemCadence
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.world_systems.generator import EntityGenerator

def test_world_dynamics_maturity_advancement():
    # Setup state at tick 1000 (MATURITY_INTERVAL)
    region = RegionState(id="forest", name="Forest", bounds=(0,0,10,10))
    state = AuthoritativeState(tick=1000, seed=42, regions={"forest": region})
    generator = EntityGenerator(42)
    update = StateUpdate()
    
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    
    assert refined.maturity_set == 1

def test_calamity_boss_spawn():
    # Setup state with high intensity region and force interval tick
    region = RegionState(
        id="badlands", 
        name="Badlands", 
        bounds=(50,50,60,60), 
        calamity_intensity=0.8
    )
    # FORCE_INTERVAL is 5000
    state = AuthoritativeState(
        tick=5000, 
        seed=42, 
        regions={"badlands": region},
        last_calamity_tick=0
    )
    generator = EntityGenerator(42)
    update = StateUpdate()
    
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    
    assert len(refined.entities_add) > 0
    boss = next(e for e in refined.entities_add if e.kind == "world_boss")
    assert boss.kind == "world_boss"
    assert boss.position == region.center
    assert refined.last_calamity_tick_set == 5000

def test_regional_transformation():
    # Setup Forest with high trauma
    region = RegionState(
        id="f1", 
        name="Ancient Forest", 
        bounds=(0,0,20,20), 
        kind="FOREST",
        trauma_score=60.0 # Threshold for BURNT_FOREST is 50.0
    )
    state = AuthoritativeState(tick=10, seed=42, regions={"f1": region})
    generator = EntityGenerator(42)
    update = StateUpdate()
    
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    
    assert refined.world_updates["f1"].kind_set == "BURNT_FOREST"

def test_world_dynamics_raid_spawning():
    # RAID_INTERVAL_DAYS=5, TICKS_PER_DAY=100 -> 500 ticks
    state = AuthoritativeState(tick=500, seed=42)
    generator = EntityGenerator(42)
    update = StateUpdate()
    
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    
    # Raiders should be added (default 3 + maturity 0 = 3)
    raiders = [e for e in refined.entities_add if e.kind == "goblin_raider"]
    assert len(raiders) == 3


def test_boss_spawn_is_idempotent_even_if_existing_boss_left_region():
    """
    LAW:
        A region must not spawn a second boss while its original boss is still
        active/alive, even if that boss has moved outside the region bounds.

    Fraud this catches:
        - boss idempotency depends on current position
        - original boss wanders out of region and region spawns duplicate boss
    """
    from dataclasses import replace

    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState, RegionState
    from src.systems.world_systems.generator import EntityGenerator
    from src.world.boss import BossService

    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=30.0,
    )

    existing_boss = (
        V2EntityBuilder(100)
        .kind("world_boss")
        .location(150.0, 150.0)  # Outside original region.
        .combat(
            hp=500,
            max_hp=500,
            alive=True,
        )
        .lifecycle(active=True)
        .build()
    )

    existing_boss = replace(
        existing_boss,
        identity=replace(
            existing_boss.identity,
            properties={
                **existing_boss.identity.properties,
                "boss_region_id": "region_1",
            },
        ),
        strategic=replace(
            existing_boss.strategic,
            home_region_id="region_1",
        ),
    )

    state = AuthoritativeState(
        tick=853,
        seed=42,
        maturity=90,
        regions={
            "region_1": region,
        },
        entities={
            100: existing_boss,
        },
    )

    update = BossService.check_for_boss_spawn(
        state,
        EntityGenerator(42),
    )

    assert update.entities_add == []


def test_lair_spawn_fills_empty_lair_place_when_no_occupant_exists():
    """TCK-20260904-LAIR-ENTITY-ANCHOR: check_for_lair_spawn generalizes the boss
    idempotency pattern to Place-scoping. A LAIR-kind Place with no existing occupant
    (no entity carries a matching identity.properties["lair_place_id"]) spawns a new
    dragonkin occupant once the region gate is met."""
    from src.core.state import AuthoritativeState, PlaceKind, PlaceState, RegionState
    from src.systems.world_systems.generator import EntityGenerator
    from src.world.boss import BossService

    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=30.0,
    )

    place = PlaceState(
        place_id="lair_1",
        region_id="region_1",
        kind=PlaceKind.LAIR,
        position=(50.0, 50.0),
    )

    state = AuthoritativeState(
        tick=853,
        seed=42,
        maturity=90,
        regions={"region_1": region},
        places={"lair_1": place},
    )

    update = BossService.check_for_lair_spawn(
        state,
        EntityGenerator(42),
    )

    assert len(update.entities_add) == 1
    occupant = update.entities_add[0]
    assert occupant.kind == "dragonkin"
    assert occupant.identity.properties["lair_place_id"] == "lair_1"


def test_lair_spawn_is_idempotent_per_place_with_multiple_lairs_in_one_region():
    """Two LAIR-kind Places in the same Region, each already occupied by its own
    dragonkin, must not collide -- proves per-place_id keying, not per-region_id
    (the exact multi-Lair-per-Region collision the ticket's AC describes)."""
    from dataclasses import replace

    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState, PlaceKind, PlaceState, RegionState
    from src.systems.world_systems.generator import EntityGenerator
    from src.world.boss import BossService

    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=30.0,
    )

    place_1 = PlaceState(
        place_id="lair_1",
        region_id="region_1",
        kind=PlaceKind.LAIR,
        position=(20.0, 20.0),
    )
    place_2 = PlaceState(
        place_id="lair_2",
        region_id="region_1",
        kind=PlaceKind.LAIR,
        position=(80.0, 80.0),
    )

    def _make_occupant(entity_id, place_id):
        occupant = (
            V2EntityBuilder(entity_id)
            .kind("dragonkin")
            .location(0.0, 0.0)
            .combat(hp=200, max_hp=200, alive=True)
            .lifecycle(active=True)
            .build()
        )
        return replace(
            occupant,
            identity=replace(
                occupant.identity,
                properties={
                    **occupant.identity.properties,
                    "lair_place_id": place_id,
                },
            ),
        )

    occupant_1 = _make_occupant(200, "lair_1")
    occupant_2 = _make_occupant(201, "lair_2")

    state = AuthoritativeState(
        tick=853,
        seed=42,
        maturity=90,
        regions={"region_1": region},
        places={"lair_1": place_1, "lair_2": place_2},
        entities={200: occupant_1, 201: occupant_2},
    )

    update = BossService.check_for_lair_spawn(
        state,
        EntityGenerator(42),
    )

    assert update.entities_add == []


def test_lair_spawn_does_not_double_spawn_when_one_of_two_lairs_already_occupied():
    """With two LAIR-kind Places in one Region, one occupied and one empty, exactly one
    new occupant is spawned -- for the empty Place only. Guards against a naive
    generalization where any existing Lair occupant is treated as filling every LAIR
    Place in the region."""
    from dataclasses import replace

    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState, PlaceKind, PlaceState, RegionState
    from src.systems.world_systems.generator import EntityGenerator
    from src.world.boss import BossService

    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=30.0,
    )

    occupied_place = PlaceState(
        place_id="lair_1",
        region_id="region_1",
        kind=PlaceKind.LAIR,
        position=(20.0, 20.0),
    )
    empty_place = PlaceState(
        place_id="lair_2",
        region_id="region_1",
        kind=PlaceKind.LAIR,
        position=(80.0, 80.0),
    )

    existing_occupant = (
        V2EntityBuilder(200)
        .kind("dragonkin")
        .location(0.0, 0.0)
        .combat(hp=200, max_hp=200, alive=True)
        .lifecycle(active=True)
        .build()
    )
    existing_occupant = replace(
        existing_occupant,
        identity=replace(
            existing_occupant.identity,
            properties={
                **existing_occupant.identity.properties,
                "lair_place_id": "lair_1",
            },
        ),
    )

    state = AuthoritativeState(
        tick=853,
        seed=42,
        maturity=90,
        regions={"region_1": region},
        places={"lair_1": occupied_place, "lair_2": empty_place},
        entities={200: existing_occupant},
    )

    update = BossService.check_for_lair_spawn(
        state,
        EntityGenerator(42),
    )

    assert len(update.entities_add) == 1
    assert update.entities_add[0].identity.properties["lair_place_id"] == "lair_2"


def test_lair_occupant_death_does_not_dissolve_or_transform_the_lair_place():
    """Anti-drift guard (idea 48 boundary): killing a Lair occupant must NOT mutate
    PlaceState.kind/prior_kind/transformed_tick. Dissolution/transformation-on-death
    belongs to idea 48 (place-type transitions), which has no ticket yet and must not
    be silently half-built by this ticket's spawn/occupancy mechanism. This should pass
    trivially today -- it exists to fail loudly if a future edit accidentally
    introduces dissolution-on-death logic inside check_for_lair_spawn or its callers."""
    from dataclasses import replace

    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState, PlaceKind, PlaceState, RegionState
    from src.systems.world_systems.generator import EntityGenerator
    from src.world.boss import BossService

    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=30.0,
    )

    place = PlaceState(
        place_id="lair_1",
        region_id="region_1",
        kind=PlaceKind.LAIR,
        position=(50.0, 50.0),
    )

    dead_occupant = (
        V2EntityBuilder(200)
        .kind("dragonkin")
        .location(50.0, 50.0)
        .combat(hp=0, max_hp=200, alive=False)
        .lifecycle(active=True)
        .build()
    )
    dead_occupant = replace(
        dead_occupant,
        identity=replace(
            dead_occupant.identity,
            properties={
                **dead_occupant.identity.properties,
                "lair_place_id": "lair_1",
            },
        ),
    )

    state = AuthoritativeState(
        tick=900,
        seed=42,
        maturity=90,
        regions={"region_1": region},
        places={"lair_1": place},
        entities={200: dead_occupant},
    )

    # The dead occupant no longer counts as active/living, so the slot re-opens and a
    # fresh occupant spawns -- but nothing in that path ever touches PlaceState.kind/
    # prior_kind/transformed_tick as a side effect.
    BossService.check_for_lair_spawn(state, EntityGenerator(42))

    unchanged_place = state.places["lair_1"]
    assert unchanged_place.kind == PlaceKind.LAIR
    assert unchanged_place.prior_kind is None
    assert unchanged_place.transformed_tick is None


def test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update():
    """TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE: regression guard for the
    world_dynamics.py:174-182 dropped-world_updates bug -- camp_state_update.world_updates/
    calamity_update.world_updates were never folded into the function's final returned
    StateUpdate.world_updates. A CampService-level-only test would still pass even if this
    bug reappeared, since the drop happens one layer up, inside resolve_dynamics() itself;
    this drives the full call and asserts the reproduction-path nudge survives the fold-in."""
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 100, 100))
    camp = CampState(id="camp_1", kind="goblin", position=(50.0, 50.0), maturity=90.0, last_raid_tick=0)
    state = AuthoritativeState(
        tick=60, seed=42,
        regions={"forest": region},
        camps={"camp_1": camp},
        feature_flags={"ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH": "ON"},
    )
    generator = EntityGenerator(42)
    cadence = SystemCadence(world_dynamics=1)

    refined = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), generator, cadence)

    assert refined.world_updates["forest"].population_young_births_delta == 1
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, RegionState, EntityState, IdentityComponent
from src.core.updates import StateUpdate
from src.core.enums import Faction
from src.world.influence import FactionInfluenceService
from src.content.repository import CatalogRepository
from src.content_semantics.faction import configure_faction_semantics_service, reset_faction_semantics_service

def test_influence_shift_on_death():
    from src.core.builder import V2EntityBuilder
    # Initial state with a region
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=0.0)
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region}
    )
    
    # 1. Hero death -> -5.0 influence
    hero = (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .identity(faction=Faction.HERO_GUILD)
        .build())
    update = FactionInfluenceService.process_influence_shift(state, [hero])
    
    assert "forest" in update.world_updates
    assert update.world_updates["forest"].influence_delta == -5.0
    
    # 2. Monster death -> +5.0 influence
    monster = (V2EntityBuilder(2)
        .kind("goblin")
        .location(6.0, 6.0)
        .identity(faction=Faction.MONSTER_HORDE)
        .build())
    update = FactionInfluenceService.process_influence_shift(state, [monster])
    assert update.world_updates["forest"].influence_delta == 5.0

def test_conquest_and_liberation_thresholds():
    from src.core.builder import V2EntityBuilder
    # Region near conquest threshold
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=-46.0)
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region}
    )
    
    # Hero death -> influence becomes -51.0 (<= -50.0) -> Conquered
    hero = (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .identity(faction=Faction.HERO_GUILD)
        .build())
    update = FactionInfluenceService.process_influence_shift(state, [hero])
    
    assert update.world_updates["forest"].owner_faction_id_set == Faction.MONSTER_HORDE.value
    
    # Region near liberation threshold
    region_conquered = replace(region, influence=46.0, owner_faction_id=Faction.MONSTER_HORDE.value)
    state_conquered = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region_conquered}
    )
    
    # Monster death -> influence becomes 51.0 (>= 50.0) -> Liberated
    monster = (V2EntityBuilder(2)
        .kind("goblin")
        .location(6.0, 6.0)
        .identity(faction=Faction.MONSTER_HORDE)
        .build())
    update_lib = FactionInfluenceService.process_influence_shift(state_conquered, [monster])
    
    assert update_lib.world_updates["forest"].owner_faction_id_set == -1 # Sentinel for None


@pytest.fixture(autouse=False)
def catalog_semantics():
    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_faction_semantics_service(repo)
    yield repo
    reset_faction_semantics_service()


def test_clean_catalog_entity_hero_triggers_influence_shift(catalog_semantics):
    """Clean entity with faction_id='hero_guild' in properties uses is_protector() path."""
    from src.core.builder import V2EntityBuilder
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=0.0)
    state = AuthoritativeState(tick=1, seed=1, regions={"forest": region})

    hero = (V2EntityBuilder(10)
        .kind("hero")
        .location(5.0, 5.0)
        .properties({"faction_id": "hero_guild"})
        .build())
    update = FactionInfluenceService.process_influence_shift(state, [hero])

    assert "forest" in update.world_updates
    assert update.world_updates["forest"].influence_delta == -5.0


def test_clean_catalog_entity_invader_triggers_influence_shift(catalog_semantics):
    """Clean entity with faction_id='goblin_warband' (invader bucket) uses is_invader() path."""
    from src.core.builder import V2EntityBuilder
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=0.0)
    state = AuthoritativeState(tick=1, seed=1, regions={"forest": region})

    goblin = (V2EntityBuilder(11)
        .kind("goblin")
        .location(5.0, 5.0)
        .properties({"faction_id": "goblin_warband"})
        .build())
    update = FactionInfluenceService.process_influence_shift(state, [goblin])

    assert "forest" in update.world_updates
    assert update.world_updates["forest"].influence_delta == 5.0


def test_mixed_legacy_and_clean_entities_coexist(catalog_semantics):
    """Legacy enum hero + clean catalog goblin both contribute correct influence deltas."""
    from src.core.builder import V2EntityBuilder
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=0.0)
    state = AuthoritativeState(tick=1, seed=1, regions={"forest": region})

    legacy_hero = (V2EntityBuilder(20)
        .kind("hero")
        .location(5.0, 5.0)
        .identity(faction=Faction.HERO_GUILD)
        .build())
    clean_goblin = (V2EntityBuilder(21)
        .kind("goblin")
        .location(5.0, 5.0)
        .properties({"faction_id": "goblin_warband"})
        .build())

    update = FactionInfluenceService.process_influence_shift(state, [legacy_hero, clean_goblin])
    # Hero: -5.0, Goblin: +5.0 → net 0.0
    assert update.world_updates["forest"].influence_delta == 0.0

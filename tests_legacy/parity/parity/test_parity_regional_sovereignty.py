# tests/parity/test_regional_sovereignty.py
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, RegionState
from src.core.enums import EntityRole, Faction
from src.core.builder import V2EntityBuilder
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate
from tests.parity.test_parity_rpg_recovery import create_test_profile

@pytest.fixture
def base_region():
    return RegionState(
        id="wilderness",
        name="The Wilds",
        bounds=(0, 0, 100, 100),
        hazard_level=0.0,
        trauma_score=0.0
    )

@pytest.mark.v2_contract
def test_trauma_accumulation(base_region):
    """Verifies that entity deaths increase regional trauma."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).build())
    goblin = (V2EntityBuilder(2).at((6, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).with_base_stats(hp=1).build())
    # Override HP manually because builder resets it to max in recalc
    goblin = replace(goblin, combat=replace(goblin.combat, hp=1))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin}, regions={"wilderness": base_region})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Run 11 ticks for hero to reach readiness
    for _ in range(11): kernel.tick_once()
    
    # Tick 12: Hero attacks goblin. Goblin should die (atk=12 vs hp=10).
    kernel.tick_once()
    
    # Verify goblin is dead
    assert not kernel.state.entities[2].combat.alive
    # Verify regional trauma increased
    assert kernel.state.regions["wilderness"].trauma_score == pytest.approx(1.0, abs=0.01)

@pytest.mark.v2_contract
def test_dread_panic(base_region):
    """Verifies that high regional trauma biases entities toward flight."""
    # Hero at 40% HP (Normal panic threshold is 20%)
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).build())
    # max_hp=17, so 40% is ~7 HP.
    hero = replace(hero, combat=replace(hero.combat, hp=7))
    
    # Hostile nearby to provide appraisal context
    goblin = (V2EntityBuilder(2).at((6, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build())
    
    # High trauma region
    trauma_region = replace(base_region, trauma_score=2.0)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin}, regions={"wilderness": trauma_region})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    for _ in range(11): kernel.tick_once()
    
    h1 = kernel.state.entities[1]
    # Even at 40% HP, the trauma bias (2.0 * 0.5 = 1.0) should push panic over the threshold (0.4)
    assert h1.task.payload.get("reason") == "PANIC_RETREAT"

@pytest.mark.v2_contract
def test_regional_hazard_drain(base_region):
    """Verifies that regions with hazard levels apply periodic HP drain."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).build())
    start_hp = hero.combat.hp
    
    # Region with hazard level 0.1 (Should deal 1 HP damage per tick)
    hazard_region = replace(base_region, hazard_level=0.1)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero}, regions={"wilderness": hazard_region})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Run 5 ticks
    for _ in range(5): kernel.tick_once()
    
    h1 = kernel.state.entities[1]
    # Should have lost 5 HP (1 per tick)
    assert h1.combat.hp == start_hp - 5

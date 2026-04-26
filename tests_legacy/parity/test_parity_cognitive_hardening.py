# tests/parity/test_cognitive_hardening.py
import pytest
from dataclasses import replace
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.core.strategic import ProjectState
from src_legacy.core.enums import EntityRole, Faction
from src_legacy.core.builder import V2EntityBuilder
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.engine.kernel import Kernel
from src_legacy.core.updates import TaskUpdate, EntityUpdate
from tests_legacy.parity.test_parity_rpg_recovery import create_test_profile

@pytest.mark.v2_contract
def test_cognitive_saliency():
    """Verifies that SensoryFilter prioritizes hostiles."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).build())
    # Ally close by
    ally = (V2EntityBuilder(2).at((6, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).build())
    # Hostile further away
    hostile = (V2EntityBuilder(3).at((8, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: ally, 3: hostile})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Run 11 ticks for hero to become ready
    for _ in range(11): kernel.tick_once()
    
    h1 = kernel.state.entities[1]
    # Hero should have prioritized the hostile (3) over the ally (2) for pursuit
    assert h1.task.payload.get("target_id") == 3

@pytest.mark.v2_contract
def test_cognitive_hysteresis():
    """Verifies that Goal Hysteresis prevents target jitter."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).build())
    goblin1 = (V2EntityBuilder(2).at((7, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).with_base_stats(hp=50).build())
    
    # Initialize hero with a locked project targeting goblin 1
    project = ProjectState(id="hunt_g1", kind="combat", lock_until_tick=20)
    hero = replace(hero, 
        strategic=replace(hero.strategic, 
            projects={"hunt_g1": project},
            current_project_id="hunt_g1"
        ),
        task=replace(hero.task, payload={"target_id": 2, "stale_ticks": 1})
    )
    
    # Introduce a 'better' target (lower HP) at tick 12
    goblin2 = (V2EntityBuilder(3).at((6, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).with_base_stats(hp=10).build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin1, 3: goblin2})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Run enough ticks for hero to reach readiness and decide
    for _ in range(25): kernel.tick_once()
    
    h1 = kernel.state.entities[1]
    # Even though goblin 2 is closer and has less HP, hero should stick to goblin 1 due to lock
    assert h1.task.payload.get("target_id") == 2

@pytest.mark.v2_contract
def test_cognitive_panic():
    """Verifies that entities flee when HP is critically low."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).with_base_stats(hp=2).build())
    # Override HP manually because builder resets it to max in recalc
    hero = replace(hero, combat=replace(hero.combat, hp=2))
    goblin = (V2EntityBuilder(2).at((6, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    for _ in range(11): kernel.tick_once()
    
    h1 = kernel.state.entities[1]
    # Hero should be fleeing to (0,0)
    assert h1.task.payload.get("reason") == "PANIC_RETREAT"
    assert h1.task.payload.get("target_position") == (0.0, 0.0)

@pytest.mark.v2_contract
def test_aptitude_scaling():
    """Verifies that evolution boosts scale with aptitudes."""
    from src_legacy.engine.evolution import EvolutionSystem
    from src_legacy.core.updates import StateUpdate, IdentityUpdate
    
    # Hero with high strength aptitude (2.0)
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).with_aptitudes(str=2.0).build())
    
    # Set evolution points just below threshold
    hero = replace(hero, identity=replace(hero.identity, evolution_points=990))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero})
    # Propose 20 XP gain
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, identity=IdentityUpdate(evolution_points_delta=20))})
    
    # Evaluate evolution
    result = EvolutionSystem.evaluate(state, update)
    
    upd = result.entity_updates[1]
    # Default atk boost is 5. With 2.0 str_apt, it should be int(5 * 2.0) = 10.
    assert upd.combat.atk_delta == 10

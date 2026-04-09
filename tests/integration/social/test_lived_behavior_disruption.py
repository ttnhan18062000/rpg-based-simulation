import pytest
from src.core.models.world_state import WorldState
from src.platform.rng import DeterministicRNG
from src.core.models.vectors import Vector2
from src.core.models.enums import GoalType, LifeRole, AIState
from src.core.world.grid import Grid
from src.systems.spatial_hash import SpatialHash
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.snapshot import Snapshot
from src.ai.brain import AIBrain
from src.systems.gameplay.combat_system import CombatSystem
from src.systems.infrastructure.base import SystemContext
from src.config import SimulationConfig

@pytest.fixture
def base_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(10)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)

def test_role_bias_influence(base_world):
    """Verify that LifeRole affects Goal utility even without specific routines."""
    rng = DeterministicRNG(42)
    from src.core.gameplay.faction import FactionRegistry
    faction_reg = FactionRegistry.default()
    config = SimulationConfig()
    
    # GUARD should have strong bias for GUARD goal
    guard = EntityBuilder(rng, 1).kind("hero").world_role(LifeRole.GUARD).build()
    
    brain = AIBrain(config, rng, faction_reg)
    base_world.tick = 20
    snapshot = Snapshot.from_world(base_world)
    
    _, proposal = brain.decide(guard, snapshot)
    from src.actions.base import MindUpdate
    mind_update = next(u for u in proposal.updates if isinstance(u, MindUpdate) and u.motive_utility_biases is not None)
    
    # 1.5x bias from role
    assert mind_update.motive_utility_biases[GoalType.GUARD] >= 1.5

def test_attack_disruption_suppresses_routines(base_world):
    """Verify that being engaged in combat disrupts routines."""
    rng = DeterministicRNG(42)
    config = SimulationConfig()
    from src.core.gameplay.faction import FactionRegistry
    faction_reg = FactionRegistry.default()
    
    # 1. Setup Hero and Enemy
    hero = EntityBuilder(rng, 1).kind("hero").at(Vector2(50, 50)).build()
    enemy = EntityBuilder(rng, 2).kind("orc").at(Vector2(50, 51)).build() # Cardinal
    
    base_world.entities[1] = hero
    base_world.entities[2] = enemy
    base_world.spatial_index.insert(1, hero.spatial.pos)
    base_world.spatial_index.insert(2, enemy.spatial.pos)
    
    # 2. Run CombatSystem to trigger engagement
    # FactionRegistry needs to know they are hostile
    # HERO_GUILD (0) vs BANDIT_CLAN (1) usually hostile
    from src.core.models.enums import Faction
    hero.identity.faction = Faction.HERO_GUILD
    enemy.identity.faction = Faction.BANDIT_CLAN
    
    system = CombatSystem(config, rng)
    context = SystemContext(config, base_world, rng, None, faction_reg, lambda **k: None)
    
    # Initially not disrupted
    assert hero.mind.routine.disrupted_until_tick == 0
    
    # Run tick
    system.on_tick(context, 10)
    
    # Should be engaged and disrupted
    assert hero.mind.navigation.engaged_ticks > 0
    assert hero.mind.routine.disrupted_until_tick > 10
    
    # 3. Verify RoutineService respects disruption
    from src.core.logic.routine_service import RoutineService
    # Setup a routine that would be active at hour 22
    from src.core.models.lived_structure import RoutineProfile
    hero.mind.routine_profiles.append(RoutineProfile(
        routine_id="night_sleep", routine_type="sleeping", anchor_type="home",
        schedule_window=(22, 6), priority=4.0, ideal_goal=GoalType.SLEEP
    ))
    
    # At tick 10 (hour 2 or something), but let's force hour 22
    biases = RoutineService.calculate_routine_biases(hero, 22, 10)
    # Should be 1.0 because of disruption
    assert biases[GoalType.SLEEP] == 1.0

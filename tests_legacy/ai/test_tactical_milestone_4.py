import pytest
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.world.grid import Grid
from src_legacy.core.models.enums import Material, HeroClass, MovementIntention, ActionType, AIState, Faction
from src_legacy.ai.states.base import AIContext
from src_legacy.ai.tactical.tactical_evaluator import TacticalEvaluator
from src_legacy.ai.tactical.contract import TacticalMode
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.gameplay.faction import FactionRegistry, FactionRelation
from src_legacy.core.models.snapshot import Snapshot
from src_legacy.ai.states.combat import CombatHandler

@pytest.fixture
def world():
    from src_legacy.platform.spatial_hash import SpatialHash
    grid = Grid(width=20, height=20)
    spatial = SpatialHash(cell_size=2)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)

@pytest.fixture
def config():
    from src_legacy.config import SimulationConfig
    return SimulationConfig()

@pytest.fixture
def rng():
    return DeterministicRNG(seed=42)

def test_reactive_cover_seeking(world, config, rng):
    """Verify that actor seeks cover only when a ranged threat is visible."""
    actor = Entity(id=1, kind="hero")
    actor.spatial.pos = Vector2(10, 10)
    actor.spatial.vision_range = 20
    actor.identity.hero_class = HeroClass.WARRIOR # Melee
    actor.combat.hp = 100
    world.add_entity(actor)
    
    # 1. No ranged threat -> No cover seeking
    enemy_melee = Entity(id=2, kind="goblin")
    enemy_melee.spatial.pos = Vector2(15, 10)
    enemy_melee.identity.faction = Faction.GOBLIN_HORDE
    # Default range 1
    world.add_entity(enemy_melee)
    
    # Place a wall nearby
    world.grid.set(Vector2(11, 11), Material.WALL)
    
    faction_reg = FactionRegistry()
    faction_reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
    
    ctx = AIContext(actor, Snapshot.from_world(world), config, rng, faction_reg)
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    assert eval.mode != TacticalMode.COVER
    
    # 2. Ranged threat -> Seek cover
    # Mocking weapon range: Actor is 1, Enemy is 5
    from unittest.mock import patch
    def mock_range(e):
        return 5 if e.id == 2 else 1
        
    with patch("src.ai.tactical.tactical_evaluator.TacticalEvaluator._get_weapon_range", side_effect=mock_range):
        eval = TacticalEvaluator.evaluate_tactics(ctx)
        assert eval.mode == TacticalMode.COVER
        assert eval.target_pos is not None
        tp = Vector2(eval.target_pos[0], eval.target_pos[1])
        assert tp.manhattan(Vector2(11, 11)) == 1

def test_chokepoint_holding(world, config, rng):
    """Verify that actor identifies and holds a 1-tile gap."""
    actor = Entity(id=1, kind="hero")
    actor.spatial.pos = Vector2(10, 10)
    actor.spatial.vision_range = 20
    actor.identity.faction = Faction.HERO_GUILD
    actor.combat.hp = 100
    world.add_entity(actor)
    
    # Create a chokepoint at (11, 10)
    # Walls at (11, 9) and (11, 11)
    world.grid.set(Vector2(11, 9), Material.WALL)
    world.grid.set(Vector2(11, 11), Material.WALL)
    
    enemy = Entity(id=2, kind="goblin")
    enemy.spatial.pos = Vector2(15, 10)
    enemy.identity.faction = Faction.GOBLIN_HORDE
    world.add_entity(enemy)
    
    faction_reg = FactionRegistry()
    faction_reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
    
    ctx = AIContext(actor, Snapshot.from_world(world), config, rng, faction_reg)
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    
    assert eval.mode == TacticalMode.CHOKEPOINT
    assert eval.target_pos == (11, 10)

def test_cardinal_opposite_bracketing(world, config, rng):
    """Verify that two allies bracket a target from opposite sides."""
    target = Entity(id=1, kind="goblin")
    target.spatial.pos = Vector2(10, 10)
    target.identity.faction = Faction.GOBLIN_HORDE
    world.add_entity(target)
    
    # Ally 1 is already at (9, 10)
    ally1 = Entity(id=2, kind="hero")
    ally1.spatial.pos = Vector2(9, 10)
    ally1.identity.faction = Faction.HERO_GUILD
    world.add_entity(ally1)
    
    # Actor (Ally 2) is at (12, 10), should move to (11, 10) to bracket
    actor = Entity(id=3, kind="hero")
    actor.spatial.pos = Vector2(12, 10)
    actor.spatial.vision_range = 20
    actor.identity.hero_class = HeroClass.WARRIOR
    actor.identity.faction = Faction.HERO_GUILD
    actor.combat.hp = 100
    world.add_entity(actor)
    
    faction_reg = FactionRegistry()
    faction_reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
    
    ctx = AIContext(actor, Snapshot.from_world(world), config, rng, faction_reg)
    eval = TacticalEvaluator.evaluate_tactics(ctx)
    
    # Should prefer (11, 10) because it is opposite to (9, 10)
    assert eval.target_pos == (11, 10)
    assert eval.reason.metadata.get("detail") == "Bracketing Target"

def test_tactical_mode_integration_handler(world, config, rng):
    """Verify that CombatHandler respects the tactical target_pos."""
    actor = Entity(id=1, kind="hero")
    actor.spatial.pos = Vector2(10, 10)
    actor.spatial.vision_range = 20
    actor.identity.faction = Faction.HERO_GUILD
    actor.combat.hp = 100
    world.add_entity(actor)
    
    # Set up a COVER mode situation
    world.grid.set(Vector2(11, 11), Material.WALL)
    enemy = Entity(id=2, kind="goblin")
    enemy.spatial.pos = Vector2(15, 10)
    enemy.identity.faction = Faction.GOBLIN_HORDE
    world.add_entity(enemy)
    
    from unittest.mock import patch
    def mock_range(e):
        return 5 if e.id == 2 else 1
        
    with patch("src.ai.tactical.tactical_evaluator.TacticalEvaluator._get_weapon_range", side_effect=mock_range):
        faction_reg = FactionRegistry()
        faction_reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
        ctx = AIContext(actor, Snapshot.from_world(world), config, rng, faction_reg)
        
        # We need to inject the tactical hints
        ctx.tactical_hints["evaluation"] = TacticalEvaluator.evaluate_tactics(ctx)
        
        handler = CombatHandler()
        new_state, proposal = handler.handle(ctx)
        
        # Should propose a MOVE to the cover tile
        assert proposal.verb == ActionType.MOVE
        # Cover tile should be (10, 11) or (11, 10)
        target = proposal.target
        assert target in [Vector2(10, 11), Vector2(11, 10)]

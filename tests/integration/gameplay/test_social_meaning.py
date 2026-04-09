import pytest
import uuid
from src.core.entities.entity import Entity
from src.core.models.world_state import WorldState
from src.core.models.combat import CombatTraceRecord, CombatTraceDetails
from src.core.models.enums import ActionType, InterpretedLifeEventKind, TurningPointKind, EntityRole
from src.core.logic.event_interpreter import EventInterpreterService
from src.core.logic.social_state_applicator import SocialStateApplicator
from src.actions.base import ActionProposal, CombatTraceUpdate
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash

@pytest.fixture
def world():
    grid = Grid(width=100, height=100)
    spatial = SpatialHash(cell_size=10)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)

@pytest.fixture
def hero(world):
    e = Entity(id=1, kind="hero")
    e.identity.display_name = "Arlow"
    e.identity.faction = "hero_guild"
    world.add_entity(e)
    return e

@pytest.fixture
def ally(world):
    e = Entity(id=2, kind="hero")
    e.identity.display_name = "Bryn"
    e.identity.faction = "hero_guild"
    world.add_entity(e)
    return e

@pytest.fixture
def enemy(world):
    e = Entity(id=3, kind="monster")
    e.identity.display_name = "Goblin"
    e.identity.faction = "monsters"
    world.add_entity(e)
    return e

def test_social_event_betrayal(world, hero, ally):
    """Verify that hitting an ally triggers a betrayal event and social bond shift."""
    # 1. Simulate Arlow (Hero) hitting Bryn (Ally)
    trace = CombatTraceRecord(
        tick=10,
        attacker_id=hero.id,
        defender_id=ally.id,
        damage=10,
        details=CombatTraceDetails(is_hit=True)
    )
    
    # 2. Interpret the event
    events = EventInterpreterService.interpret_combat_aftermath(hero, ally, trace, world)
    
    # Must detect betrayal
    assert any(e.kind == InterpretedLifeEventKind.BETRAYAL for e in events)
    
    # 3. Apply the event via Applicator
    for event in events:
        SocialStateApplicator.apply_interpreted_event(event, world)
        
    # 4. Verify Bond Shift in SocialRegistry: Victim (Bryn) trusts Attacker (Arlow) less
    bond = world.social_registry.get_bond(ally.id, hero.id)
    assert bond.trust < 0  # Bryn should trust Arlow less
    assert bond.resentment > 0 # Bryn should resent Arlow
    
    # 5. Verify Reputation Shift
    assert hero.reputation.trustworthiness < 5.0 # Arlow's public trust dropped
    assert "Ally-Slayer" in hero.reputation.reputation_tags # Earned a nasty tag

def test_social_event_near_death_and_tp(world, hero, enemy):
    """Verify that a near-death experience creates a durable turning point."""
    # 1. Simulate Arlow taking massive damage from Goblin
    world.tick = 20 # Sync world tick with trace
    hero.combat.hp = 5 # Manually set to near-death state for interpretation
    hero.combat.max_hp = 100
    trace = CombatTraceRecord(
        tick=20,
        attacker_id=enemy.id,
        defender_id=hero.id,
        damage=95, # Near death!
        details=CombatTraceDetails(is_hit=True)
    )
    
    # 2. Interpret
    events = EventInterpreterService.interpret_combat_aftermath(enemy, hero, trace, world)
    
    # Must detect near death for the defender (hero)
    assert any(e.kind == InterpretedLifeEventKind.NEAR_DEATH and e.actor_id == hero.id for e in events)
    
    # 3. Apply
    for event in events:
        SocialStateApplicator.apply_interpreted_event(event, world)
        
    # 4. Verify Durable Turning Point
    tps = hero.mind.narrative.turning_points
    assert len(tps) > 0
    assert any(tp.kind == TurningPointKind.NEAR_DEATH for tp in tps)
    assert tps[0].emotional_impact > 0.8
    assert tps[0].tick == 20

def test_social_event_first_kill_milestone(world, hero, enemy):
    """Verify that first kill increments reputation and notoriety."""
    # 1. Simulate a killing blow
    world.tick = 30 # Sync world tick
    enemy.combat.hp = 0 # Force death via HP (alive property is read-only)
    hero.identity.kill_count = 1 # Candidate for first kill
    trace = CombatTraceRecord(
        tick=30,
        attacker_id=hero.id,
        defender_id=enemy.id,
        damage=20,
        details=CombatTraceDetails(is_hit=True, fatal_blow=True)
    )
    
    # 2. Interpret
    events = EventInterpreterService.interpret_combat_aftermath(hero, enemy, trace, world)
    
    # Must detect first kill
    assert any(e.kind == InterpretedLifeEventKind.FIRST_KILL for e in events)
    
    # 3. Apply
    for event in events:
        SocialStateApplicator.apply_interpreted_event(event, world)
        
    # 4. Verify Reputation
    assert hero.reputation.heroism_score > 0
    assert hero.reputation.threat_notoriety > 0

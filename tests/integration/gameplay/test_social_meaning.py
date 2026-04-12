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
    e.identity.faction=0
    world.add_entity(e)
    return e

@pytest.fixture
def ally(world):
    e = Entity(id=2, kind="hero")
    e.identity.display_name = "Bryn"
    e.identity.faction=0
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
    
    # 3. Apply the event via Applicator (AOA: Process intents)
    from src.actions.base import PerceptionUpdate, ReputationUpdate, SocialUpdate
    from src.core.logic.relationship_service import RelationshipService
    from src.core.logic.reputation_service import ReputationService
    
    for event in events:
        updates = SocialStateApplicator.apply_interpreted_event(event, world)
        for up in updates:
            if isinstance(up, PerceptionUpdate):
                 # Application handled in service/applicator usually, but here we mock
                 pass 
            elif isinstance(up, ReputationUpdate):
                 target = world.get_entity(up.target_id)
                 if up.heroism_delta: target.reputation.heroism_score += up.heroism_delta
                 if up.trustworthiness_delta: target.reputation.trustworthiness += up.trustworthiness_delta
                 if up.tags_add:
                     for t in up.tags_add:
                         if t not in target.reputation.reputation_tags:
                             target.reputation.reputation_tags.append(t)
            elif isinstance(up, SocialUpdate):
                 RelationshipService.apply_update(world.social_registry, up, world.tick)
        
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
    
    # 3. Apply (AOA: Process intents)
    from src.actions.base import PerceptionUpdate
    for event in events:
        updates = SocialStateApplicator.apply_interpreted_event(event, world)
        for up in updates:
            if isinstance(up, PerceptionUpdate):
                if up.turning_points_add:
                    hero.mind.narrative.turning_points.extend(up.turning_points_add)
        
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
    
    # 3. Apply (AOA: Process intents)
    from src.actions.base import ReputationUpdate
    for event in events:
        updates = SocialStateApplicator.apply_interpreted_event(event, world)
        for up in updates:
            if isinstance(up, ReputationUpdate):
                 # Manual apply for test mock
                 hero.reputation.heroism_score += getattr(up, 'heroism_delta', 0.0)
                 hero.reputation.threat_notoriety += getattr(up, 'threat_notoriety_delta', 0.0)
        
    # 4. Verify Reputation
    assert hero.reputation.heroism_score > 0
    assert hero.reputation.threat_notoriety > 0

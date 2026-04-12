import pytest
from unittest.mock import MagicMock
from src.core.entities.entity import Entity
from src.core.models.life_events import InterpretedLifeEvent, TurningPointRecord
from src.core.models.enums import InterpretedLifeEventKind, TurningPointKind, EntityRole
from src.core.logic.event_interpreter import EventInterpreterService
from src.core.logic.social_state_applicator import SocialStateApplicator
from src.core.logic.relationship_service import RelationshipService
from src.core.logic.reputation_service import ReputationService
from src.core.models.social import SocialRegistry, SocialBond
from src.core.models.combat import CombatTraceRecord, CombatTraceDetails
from src.core.models.world_state import WorldState

@pytest.mark.integration
class TestSocialRealismPipeline:
    """Integration tests for Phase 2 Stage 3-7 Social Pipeline."""

    def test_full_pipeline_combat_event(self):
        """Verifies interpretation to persistent social state application."""
        # 1. Setup
        hero = Entity(id=1, kind="hero")
        villain = Entity(id=2, kind="mob")
        villain.identity.display_name = "The Dark Knight"
        villain.identity.role = EntityRole.WORLD_BOSS # Trigger boss encounter
        
        # Initial state checks
        assert len(hero.mind.narrative.turning_points) == 0
        assert hero.reputation.heroism_score == 0.0
        
        registry = SocialRegistry()
        world = MagicMock(spec=WorldState)
        world.tick = 100
        world.entities = {1: hero, 2: villain}
        world.social_registry = registry
        # Mock get_entity
        world.get_entity.side_effect = lambda eid: world.entities.get(eid)
        
        # 2. Combat Result: Hero attacked by boss, nearly died
        # First, set hero HP low manually to simulate outcome
        hero.combat.hp = 5
        hero.combat.max_hp = 100
        
        combat_result = CombatTraceRecord(
            tick=100,
            attacker_id=villain.id,
            defender_id=hero.id,
            damage=50,
            details=CombatTraceDetails(raw_damage=50)
        )
        
        # 3. Step 1: Interpretation
        events = EventInterpreterService.interpret_combat_aftermath(villain, hero, combat_result, world)
        assert len(events) >= 1
        
        # Find near-death event
        near_death = next((e for e in events if e.kind == InterpretedLifeEventKind.NEAR_DEATH), None)
        assert near_death is not None
        assert near_death.severity > 5.0
        
        # 4. Step 2: Application (AOA: Process intents)
        from src.actions.base import PerceptionUpdate, ReputationUpdate, SocialUpdate
        for ev in events:
            updates = SocialStateApplicator.apply_interpreted_event(ev, world)
            for up in updates:
                if isinstance(up, PerceptionUpdate):
                    if up.turning_points_add:
                        hero.mind.narrative.turning_points.extend(up.turning_points_add)
                elif isinstance(up, ReputationUpdate):
                    # Manual apply for test mock
                    hero.reputation.heroism_score += getattr(up, 'heroism_delta', 0.0)
                elif isinstance(up, SocialUpdate):
                    RelationshipService.apply_update(registry, up, world.tick)
        
        # 5. Verification: Narrative Memory
        assert len(hero.mind.narrative.turning_points) >= 1
        tp = hero.mind.narrative.turning_points[0]
        assert tp.tick == 100
        assert tp.salience_score > 5.0
        assert villain.id in tp.involved_entity_ids
        
        # 6. Verification: Relationship (Bond)
        bond = registry.get_bond(hero.id, villain.id)
        assert bond.fear > 0.0
        
    def test_reputation_titles_and_tags(self):
        """Verifies that reputation service correctly assigns tags based on scores."""
        from src.actions.base import ReputationUpdate
        entity = Entity(id=1, kind="hero")
        
        # Apply heroism update via authoritative service
        update = ReputationUpdate(heroism_delta=2.0)
        ReputationService.apply_update(entity, update)
        assert "Hero" in entity.reputation.reputation_tags
        
        # Apply cowardice update
        update_coward = ReputationUpdate(cowardice_delta=1.5)
        ReputationService.apply_update(entity, update_coward)
        assert "Craven" in entity.reputation.reputation_tags


    def test_knowledge_propagation_indirect(self):
        """Verifies Stage 5 Knowledge Propagation."""
        from src.ai.beliefs import BeliefService
        
        sharer = Entity(id=1, kind="npc")
        recipient = Entity(id=2, kind="npc")
        target = Entity(id=3, kind="hero")
        target.reputation.heroism_score = 5.0
        target.reputation.reputation_tags.append("Saviour")
        
        # Mock memory dicts (sometimes they are MappingProxyType, but here we need mutable for test)
        sharer.mind.perception.entity_memory = {}
        recipient.mind.perception.entity_memory = {}
        
        # Sharer observes target directly
        direct_belief = BeliefService.refresh_belief_from_observation(sharer, target, tick=10)
        sharer.mind.perception.entity_memory[target.id] = direct_belief
        
        # Sharer shares with recipient
        indirect_belief = BeliefService.share_knowledge(sharer, recipient, target.id, tick=20)
        assert indirect_belief is not None
        assert indirect_belief.knowledge_source == "indirect"
        assert indirect_belief.directness < 1.0
        assert indirect_belief.apparent_heroism == 5.0
        assert "Saviour" in indirect_belief.apparent_reputation_tags
        
        # Merge into recipient
        up = BeliefService.merge_indirect_belief(recipient, indirect_belief)
        if up and up.entity_memory:
            recipient.mind.perception.entity_memory.update(up.entity_memory)
            
        stored = recipient.mind.perception.entity_memory[target.id]
        assert stored.knowledge_source == "indirect"
        assert stored.confidence < direct_belief.confidence


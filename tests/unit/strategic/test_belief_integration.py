"""
Unit and integration tests for Belief to Action path in strategic cognition.

Covers:
- Scenario 1: Guild Intel Rumors generate vague beliefs & leads.
- Scenario 2: Direct observation confirms threat, upgrading belief and lead.
- Scenario 3: Contradiction degrades certainty, suppressing future detours.
- Scenario 4: Detour Selection weights source trust & certainty, avoiding infinite detour loops.
"""
import pytest
from dataclasses import replace
from src.core.builder import V2EntityBuilder
from src.core.state import EntityState, AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate
from src.core.enums import Faction
from src.core.strategic import (
    StrategicComponent, LeadState, LeadCertainty, BlockerState,
    CognitionProfile, SourceTrustEntry, ProjectState, ProjectStatus,
    ObjectiveState, ObjectiveStatus
)
from src.systems.strategic_systems.belief import BeliefCycleSystem, BeliefEntry
from src.systems.strategic_systems.detour import DetourSuggestionSystem
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem


def _make_entity_with_leads(leads=None, beliefs=None, source_trust=None, profile=None, blockers=None):
    builder = (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .strategic(
            leads=leads or {},
            source_trust=source_trust or {},
            blockers=blockers or {}
        )
    )
    if profile:
        builder.cognition(
            max_leads=profile.max_leads,
            max_concerns=profile.max_concerns,
            detour_breadth=profile.detour_breadth
        )
    else:
        builder.cognition(max_leads=5, max_concerns=3, detour_breadth=3)
    entity = builder.build()
    if beliefs:
        entity = replace(entity, strategic=replace(entity.strategic, beliefs=beliefs))
    return entity


class TestGuildIntelRumors:
    """Scenario 1: Guild Intel Rumors."""

    def test_guild_intel_creates_rumor_belief_and_lead(self):
        entity = _make_entity_with_leads()
        
        # Simulating rumor process
        update = BeliefCycleSystem.process_rumor(
            entity=entity,
            rumor_subject="goblin_camp",
            rumor_detail="10.0,10.0",
            source_entity_id=42,
            current_tick=100
        )
        
        # Verify StrategicUpdate returned
        assert len(update.leads_add_or_update) == 1
        assert len(update.beliefs_add_or_update) == 1
        
        lead = update.leads_add_or_update[0]
        belief = update.beliefs_add_or_update[0]
        
        assert lead.certainty == LeadCertainty.VAGUE
        assert lead.source_entity_id == 42
        assert lead.subject == "goblin_camp"
        assert lead.detail == "10.0,10.0"
        
        assert belief.certainty == 0.3
        assert belief.source == "rumor"
        assert belief.source_entity_id == 42
        assert belief.subject == "goblin_camp"
        assert belief.claim == "10.0,10.0"


class TestDirectObservationVerification:
    """Scenario 2: Direct observation verification."""

    def test_reaching_coords_with_threat_upgrades_belief_and_lead(self):
        # We need an AuthoritativeState with hostiles at target position to run fused_strategic_pass
        entity = _make_entity_with_leads(
            leads={
                "lead_1": LeadState(
                    id="lead_1",
                    kind="location",
                    subject="goblin_camp",
                    detail="10.0,10.0",
                    certainty=LeadCertainty.VAGUE,
                    discovered_tick=50
                )
            },
            beliefs={
                "belief_1": BeliefEntry(
                    id="belief_rumor_goblin_camp_50",
                    subject="goblin_camp",
                    claim="10.0,10.0",
                    certainty=0.3,
                    source="rumor",
                    created_tick=50
                )
            }
        )
        
        # Place entity at target position
        entity = replace(entity, navigation=replace(entity.navigation, position=(10.0, 10.0)))
        entity = replace(entity, identity=replace(entity.identity, faction=Faction.HERO_GUILD))
        
        # Hostile entity at (10.0, 10.0)
        hostile = (V2EntityBuilder(2)
            .kind("monster")
            .location(10.0, 10.0)
            .identity(faction=Faction.MONSTER_HORDE)
            .build())
        
        state = AuthoritativeState(
            tick=100,
            seed=42,
            entities={1: entity, 2: hostile}
        )
        
        state_update = StateUpdate(entity_updates={
            1: EntityUpdate(entity_id=1)
        })
        
        # Run fused_strategic_pass
        res_update = StrategicIntelligenceSystem.fused_strategic_pass(state, state_update)
        
        # Assert lead/belief is upgraded to precise/1.0
        assert 1 in res_update.entity_updates
        ent_up = res_update.entity_updates[1]
        assert ent_up.strategic is not None
        
        up_leads = ent_up.strategic.leads_add_or_update
        up_beliefs = ent_up.strategic.beliefs_add_or_update
        
        assert len(up_leads) == 1
        assert up_leads[0].certainty == LeadCertainty.PRECISE
        assert up_leads[0].tested is True
        assert up_leads[0].test_outcome == "SUCCESS"
        
        assert len(up_beliefs) == 1
        assert up_beliefs[0].certainty == 1.0


class TestContradictionAndDegradation:
    """Scenario 3: Contradiction degrades certainty and suppresses detours."""

    def test_reaching_coords_without_threat_triggers_contradiction_and_degrades_certainty(self):
        entity = _make_entity_with_leads(
            leads={
                "lead_1": LeadState(
                    id="lead_1",
                    kind="location",
                    subject="goblin_camp",
                    detail="10.0,10.0",
                    certainty=LeadCertainty.VAGUE,
                    discovered_tick=50
                )
            },
            beliefs={
                "belief_1": BeliefEntry(
                    id="belief_rumor_goblin_camp_50",
                    subject="goblin_camp",
                    claim="10.0,10.0",
                    certainty=0.3,
                    source="rumor",
                    created_tick=50,
                    contradictions=0
                )
            }
        )
        
        # Place entity at target position
        entity = replace(entity, navigation=replace(entity.navigation, position=(10.0, 10.0)))
        entity = replace(entity, identity=replace(entity.identity, faction=Faction.HERO_GUILD))
        
        # No hostiles at (10.0, 10.0)
        state = AuthoritativeState(
            tick=100,
            seed=42,
            entities={1: entity}
        )
        
        state_update = StateUpdate(entity_updates={
            1: EntityUpdate(entity_id=1)
        })
        
        # Run fused_strategic_pass
        res_update = StrategicIntelligenceSystem.fused_strategic_pass(state, state_update)
        
        # Assert lead/belief is demoted
        assert 1 in res_update.entity_updates
        ent_up = res_update.entity_updates[1]
        assert ent_up.strategic is not None
        
        up_leads = ent_up.strategic.leads_add_or_update
        up_beliefs = ent_up.strategic.beliefs_add_or_update
        
        assert len(up_leads) == 1
        assert up_leads[0].certainty == LeadCertainty.EXHAUSTED  # Vague demotes to Exhausted
        assert up_leads[0].tested is True
        assert up_leads[0].test_outcome == "FAILURE"
        
        assert len(up_beliefs) == 1
        assert up_beliefs[0].contradictions == 1
        assert up_beliefs[0].certainty == 0.0  # 0.3 - 0.3 = 0.0


class TestDetourSelectionAndTrust:
    """Scenario 4: Detour Selection weights source trust & certainty."""

    def test_detour_prioritizes_higher_source_trust(self):
        # We have a material blocker for goblin_teeth
        blocker = BlockerState(id="b1", kind="material", subject="goblin_teeth", severity=0.8)
        
        # Two rumors for goblin_teeth
        leads = {
            "l_low_trust": LeadState(
                id="l_low_trust", kind="location", subject="goblin_teeth", detail="low_trust_camp",
                certainty=LeadCertainty.VAGUE, source_entity_id=10, discovered_tick=10
            ),
            "l_high_trust": LeadState(
                id="l_high_trust", kind="location", subject="goblin_teeth", detail="high_trust_camp",
                certainty=LeadCertainty.VAGUE, source_entity_id=20, discovered_tick=10
            )
        }
        
        beliefs = {
            "b_low": BeliefEntry(id="b_low", subject="goblin_teeth", claim="low_trust_camp", certainty=0.3, source="rumor", source_entity_id=10),
            "b_high": BeliefEntry(id="b_high", subject="goblin_teeth", claim="high_trust_camp", certainty=0.3, source="rumor", source_entity_id=20)
        }
        
        # Define source trust scores
        source_trust = {
            10: SourceTrustEntry(entity_id=10, trust=0.2),
            20: SourceTrustEntry(entity_id=20, trust=0.9)
        }
        
        entity = _make_entity_with_leads(
            leads=leads,
            beliefs=beliefs,
            source_trust=source_trust,
            blockers={"b1": blocker}
        )
        
        suggestions = DetourSuggestionSystem.suggest_detours(entity, current_tick=100)
        
        assert len(suggestions) == 2
        # The high trust rumor should be ranked first
        assert suggestions[0].lead_id == "l_high_trust"
        assert suggestions[1].lead_id == "l_low_trust"

    def test_contradicted_rumor_detour_score_drops_drastically(self):
        blocker = BlockerState(id="b1", kind="material", subject="goblin_teeth", severity=0.8)
        
        leads = {
            "l_rumor": LeadState(
                id="l_rumor", kind="location", subject="goblin_teeth", detail="camp",
                certainty=LeadCertainty.VAGUE, source_entity_id=10, discovered_tick=10
            )
        }
        
        # Normal belief
        beliefs_normal = {
            "b_rumor": BeliefEntry(id="b_rumor", subject="goblin_teeth", claim="camp", certainty=0.3, source="rumor", source_entity_id=10, contradictions=0)
        }
        
        entity_normal = _make_entity_with_leads(
            leads=leads,
            beliefs=beliefs_normal,
            blockers={"b1": blocker}
        )
        
        suggestions_normal = DetourSuggestionSystem.suggest_detours(entity_normal, current_tick=100)
        score_normal = suggestions_normal[0].score
        
        # Contradicted belief (contradictions = 1)
        beliefs_contradicted = {
            "b_rumor": BeliefEntry(id="b_rumor", subject="goblin_teeth", claim="camp", certainty=0.3, source="rumor", source_entity_id=10, contradictions=1)
        }
        
        entity_contradicted = _make_entity_with_leads(
            leads=leads,
            beliefs=beliefs_contradicted,
            blockers={"b1": blocker}
        )
        
        suggestions_contradicted = DetourSuggestionSystem.suggest_detours(entity_contradicted, current_tick=100)
        score_contradicted = suggestions_contradicted[0].score
        
        # Contradiction penalty should reduce score significantly (by 25.0 points)
        assert score_contradicted == score_normal - 25.0

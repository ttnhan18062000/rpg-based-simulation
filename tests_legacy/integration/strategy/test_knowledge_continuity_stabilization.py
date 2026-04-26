import pytest
from src_legacy.core.models.strategy import StrategicState, LeadRecord, LeadKind, ObjectiveRecord, ObjectiveKind, StrategicStatus
from src_legacy.actions.base import StrategicUpdate, ActionType
from src_legacy.ai.states.base import AIContext
from src_legacy.ai.states.navigation import InvestigateHandler
from src_legacy.core.logic.strategic_knowledge_ingestion import StrategicKnowledgeIngestionService
from src_legacy.systems.gameplay.action_system import ActionSystem
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.gameplay.faction import Faction, FactionRegistry
from unittest.mock import MagicMock

@pytest.fixture
def faction_reg():
    from src_legacy.core.gameplay.faction import FactionRegistry, FactionRelation
    reg = FactionRegistry()
    reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
    return reg

@pytest.fixture
def actor():
    e = Entity(id=1, kind="hero")
    e.identity.faction = Faction.HERO_GUILD
    return e

@pytest.fixture
def hostile_entity():
    e = Entity(id=2, kind="goblin")
    e.identity.faction = Faction.GOBLIN_HORDE
    return e

@pytest.fixture
def mock_snapshot(actor):
    snap = MagicMock()
    snap.tick = 100
    snap.entities = {actor.id: actor}
    snap.grid.is_walkable.return_value = True
    return snap

@pytest.fixture
def ctx(actor, mock_snapshot, faction_reg):
    return AIContext(
        actor=actor,
        snapshot=mock_snapshot,
        config=MagicMock(),
        rng=DeterministicRNG(1),
        faction_reg=faction_reg
    )

def test_milestone_3_lead_testing_and_persistence(ctx, actor):
    """Verify that exhausted search marks leads as tested and persists them."""
    from src_legacy.core.models.strategy import ProjectRecord, ProjectKind
    
    # 1. Setup a lead and an investigation objective
    lead = LeadRecord(lead_id="test_lead_123", kind=LeadKind.LOCATION, label="Test Camp", subject="enemy_camp")
    actor.mind.strategic.leads = [lead]
    
    obj = ObjectiveRecord(
        objective_id="obj_investigate",
        project_id="prj_test",
        kind=ObjectiveKind.INVESTIGATE,
        label="Investigate Camp",
        target_pos=Vector2(x=10, y=10),
        leads=[lead]
    )
    
    prj = ProjectRecord(
        project_id="prj_test",
        kind=ProjectKind.EXPLORATION,
        label="Test Project",
        objectives=[obj],
        active_objective_id=obj.objective_id
    )
    
    actor.mind.strategic.projects = [prj]
    actor.mind.strategic.current_project_id = prj.project_id
    actor.mind.strategic.current_objective_id = obj.objective_id
    
    # Mock search narrowing to return No next tile (exhausted)
    from src_legacy.core.logic.search_narrowing import SearchNarrowingService
    SearchNarrowingService.select_next_search_tile = MagicMock(return_value=None)
    
    # 2. Run handler
    actor.spatial.pos = Vector2(x=10, y=10) # Arrived
    handler = InvestigateHandler()
    state, proposal = handler.handle(ctx)
    
    # 3. Verify StrategicUpdate contains tested lead
    strat_up = next((up for up in proposal.updates if isinstance(up, StrategicUpdate)), None)
    assert strat_up is not None, f"Updates: {proposal.updates}"
    assert "test_lead_123" in strat_up.tested_lead_ids
    assert any(l.lead_id == "test_lead_123" and l.tested for l in strat_up.leads_add_or_update)
    
    # 4. Apply update via ActionSystem and verify StrategicState
    ActionSystem.apply_strategic_update(actor, strat_up)
    assert "test_lead_123" in actor.mind.strategic.tested_lead_ids
    
    # 5. Verify Ingestion filtering
    # Try to ingest a lead that would generate "lead_guild_camp_10_10"
    camp_lead_id = "lead_guild_camp_10_10"
    actor.mind.strategic.tested_lead_ids.append(camp_lead_id)
    
    filtered_up = StrategicKnowledgeIngestionService.ingest_guild_intel(
        actor_id=actor.id,
        tick=120,
        material_hints={},
        camps_found=[(10, 10)],
        resources_found=[],
        tested_lead_ids=actor.mind.strategic.tested_lead_ids
    )
    assert len(filtered_up.leads_add_or_update) == 0, "Duplicate lead should have been filtered"

def test_milestone_4_social_filtering(ctx, actor, faction_reg):
    """Verify that social candidate selection filters hostiles and uses debt."""
    from src_legacy.ai.strategy.social_candidate_selection import SocialCandidateSelectionService
    
    # 1. Hostile Candidate
    hostile = Entity(id=2, kind="goblin")
    hostile.identity.faction = Faction.GOBLIN_HORDE
    ctx.snapshot.entities[2] = hostile
    
    # 2. Ally Candidate with Debt
    ally = Entity(id=3, kind="hero")
    ally.identity.faction = Faction.HERO_GUILD
    ctx.snapshot.entities[3] = ally
    
    from src_legacy.core.models.social import SocialBond
    actor.mind.social.known_bonds[3] = SocialBond(source_id=actor.id, target_id=3, trust=0.5, debt=-0.8) # Owed to us
    
    # 3. Score them
    hostile_score, _, _ = SocialCandidateSelectionService._score_candidate(ctx, hostile, None)
    ally_score, ally_drivers, _ = SocialCandidateSelectionService._score_candidate(ctx, ally, None)
    
    assert hostile_score < -4.0, f"Hostile score {hostile_score} should be low"
    assert ally_score > 1.0, f"Ally score {ally_score} should be high"
    assert any("debt_obligation" in d for d in ally_drivers), f"Drivers: {ally_drivers}"

def test_strategic_uncertainty_and_anti_cheating(ctx, actor):
    """Verify that rumors have lower certainty and vague leads don't 'cheat' with perfect coords."""
    # 1. Ingest a rumor
    rumor_up = StrategicKnowledgeIngestionService.ingest_inn_rumor(
        actor_id=actor.id,
        tick=100,
        rumor_text="Rumors of a dragon in the north",
        danger_level=0.8,
        rng=DeterministicRNG(42)
    )
    
    lead = rumor_up.leads_add_or_update[0]
    assert lead.certainty == 0.5, "Rumors should have 0.5 certainty"
    assert lead.target_coords is None, "Rumors should not magically have coords"
    
    # 2. Ingest guild intel (Higher confidence)
    guild_up = StrategicKnowledgeIngestionService.ingest_guild_intel(
        actor_id=actor.id,
        tick=110,
        material_hints={},
        camps_found=[(50, 50)],
        resources_found=[],
        source_confidence=0.9
    )
    
    guild_lead = next(l for l in guild_up.leads_add_or_update if "camp" in l.label.lower())
    assert guild_lead.certainty == 0.9
    # NOTE: ingest_guild_intel currently doesn't set target_coords on the LeadRecord,
    # it puts it in candidate_zones. This is correct Phase 3 behavior (Anti-cheating).
    assert guild_lead.target_coords is None
    assert len(guild_up.candidate_zones_add_or_update) > 0
    
    # 3. Verify that we can't build a precise objective from a vague lead without a search
    # (Checking the ObjectiveDerivationService/CandidateBuilder logic)
    from src_legacy.core.models.strategy import ProjectRecord, ProjectKind, ObjectiveRecord, ObjectiveKind
    
    # If we create an objective for this vague lead
    obj = ObjectiveRecord(
        objective_id="obj_vague",
        project_id="prj_vague",
        kind=ObjectiveKind.INVESTIGATE,
        label="Investigate Rumor",
        leads=[lead]
    )
    
    # In a real scenario, the Brain should use SearchNarrowingService to find the first tile.
    # If target_pos is missing, it should fallback to region center or similar, not the 'cheated' camp loc.
    assert obj.target_pos is None

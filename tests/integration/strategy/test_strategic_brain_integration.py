"""Integration tests for Strategic Brain logic and Event consequences.
[CONSOLIDATED FROM test_strategic_reprioritization.py, test_strategic_consequences.py, and test_strategic_event_consequences.py]
"""

import pytest
import uuid
from src.core.models.world_state import WorldState
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.strategy import StrategicStatus, ConcernKind, ProjectKind, DirectiveKind, ProjectRecord, ConcernRecord
from src.ai.brain import AIBrain, AIContext
from src.core.models.snapshot import Snapshot
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.core.models.life_events import InterpretedLifeEvent
from src.core.models.enums import InterpretedLifeEventKind, TurningPointKind, Material, AttachmentKind, OfferStatus, ContractKind
from src.core.aspects.mind import InterpretedEvent
from src.actions.base import StrategicUpdate
from src.core.gameplay.faction import FactionRegistry

@pytest.fixture
def mock_world():
    grid = Grid(100, 100)
    spatial = SpatialHash(cell_size=10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.entities = {}
    return world

@pytest.fixture
def brain():
    config = SimulationConfig()
    return AIBrain(config, DeterministicRNG(0))

# --- Brain Decision Integration Tests ---

def test_strategic_pivot_on_regional_danger(mock_world, brain):
    """Verify that heroes pivot from personal quests to regional stabilization during high-danger events."""
    from src.core.world.regions import Region
    from src.core.models.regions import RegionConsequenceRecord
    
    r1 = Region(region_id="forest", name="The Dark Forest", terrain=Material.FOREST, center=Vector2(25, 25), radius=50, difficulty=1)
    mock_world.regions = [r1]
    mock_world.region_consequence_registry = {
        "forest": RegionConsequenceRecord(region_id="forest", danger_level=0.9, stability=0.2)
    }
    
    hero = Entity(id=1, kind="hero")
    hero.spatial.pos = Vector2(25, 25)
    hero.spatial.region_id = "forest"
    
    default_prj = ProjectRecord(project_id="quest_1", kind=ProjectKind.QUEST, label="Standard Quest", priority=2.0)
    hero.mind.strategic.projects.append(default_prj)
    hero.mind.strategic.current_project_id = "quest_1"
    
    mock_world.add_entity(hero)
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    
    update = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    assert update is not None
    assert update.current_project_id == "project_stabilization"
    assert update.interrupted_project_id == "quest_1"

def test_scar_detection(mock_world, brain):
    """Verify that heroes sense nearby world trauma (scars) and investigate."""
    from src.core.models.local_scars import LocalScarRecord, ScarKind
    
    hero = Entity(id=1, kind="hero")
    hero.spatial.pos = Vector2(20, 20)
    mock_world.add_entity(hero)
    
    mock_world.scar_registry = [
        LocalScarRecord(location_pos=Vector2(22, 22), kind=ScarKind.BATTLE_FIELD, severity=0.5, created_tick=50, source_event_id="evt_123")
    ]
    
    snapshot = Snapshot.from_world(mock_world)
    state, proposal = brain.decide(hero, snapshot)
    update = next((u for u in proposal.updates if isinstance(u, StrategicUpdate)), None)
    
    scar_c = next((c for c in update.concerns_add_or_update if c.concern_id == "concern_nearby_scar"), None)
    assert scar_c is not None
    assert scar_c.source_event_id == "evt_123"

# --- Event Consequence Integration Tests ---

def test_near_death_triggers_survival_consequences(mock_world):
    """Verify that a NEAR_DEATH event generates a concern and suspends the current project via applicator."""
    hero = Entity(id=1, kind="hero")
    hero.spatial.pos = Vector2(25, 25)
    mock_world.entities[1] = hero
    
    current_prj = ProjectRecord(project_id="quest_alpha", kind=ProjectKind.QUEST, label="Exploring Ruins", priority=2.0, status=StrategicStatus.ACTIVE)
    hero.mind.strategic.projects.append(current_prj)
    hero.mind.strategic.current_project_id = "quest_alpha"
    
    event = InterpretedLifeEvent(
        event_id="evt_death_1", kind=InterpretedLifeEventKind.NEAR_DEATH, tick=100, actor_id=1, severity=0.8, turning_point_candidate=True
    )
    
    from src.core.logic.social_state_applicator import SocialStateApplicator
    updates = SocialStateApplicator.apply_interpreted_event(event, mock_world)
    
    strat_up = next((u for u in updates if isinstance(u, StrategicUpdate)), None)
    assert strat_up is not None
    
    survival_c = next((c for c in strat_up.concerns_add_or_update if "Recovery" in c.label), None)
    assert survival_c is not None
    
    suspended_prj = next((p for p in strat_up.projects_add_or_update if p.project_id == "quest_alpha"), None)
    assert suspended_prj is not None
    assert suspended_prj.status == StrategicStatus.SUSPENDED

def test_betrayal_mutates_directives(mock_world):
    """Verify that a salient betrayal turning point adds an 'Avenge' directive."""
    actor = Entity(id=1, kind="hero")
    mock_world.entities[1] = actor
    
    event = InterpretedLifeEvent(
        event_id="evt_betrayal_1", kind=InterpretedLifeEventKind.BETRAYAL, tick=100, actor_id=1, subject_ids=[2], severity=0.9, turning_point_candidate=True
    )
    
    from src.core.logic.social_state_applicator import SocialStateApplicator
    updates = SocialStateApplicator.apply_interpreted_event(event, mock_world)
    
    strat_up = next((u for u in updates if isinstance(u, StrategicUpdate)), None)
    avenge_d = next((d for d in strat_up.directives_add if "Avenge" in d.label), None)
    assert avenge_d is not None

def test_divergent_home_response(mock_world, brain):
    """Verify that only entities with place attachment react strongly to home damage."""
    from src.core.models.lived_structure import PlaceAttachment
    
    attached_hero = Entity(id=1, kind="hero")
    attached_hero.mind.place_attachments.append(PlaceAttachment(location_pos=Vector2(x=5, y=5), building_id=101, importance=0.8))
    
    unattached_hero = Entity(id=2, kind="hero")
    
    mock_world.tick = 100
    mock_world.add_entity(attached_hero)
    mock_world.add_entity(unattached_hero)
    
    home_event = InterpretedEvent(tick=60, type="trauma", impact=4.0, life_event_kind=InterpretedLifeEventKind.HOME_DAMAGED, details={"building_id": 101})
    attached_hero.mind.narrative.memory_log.append(home_event)
    unattached_hero.mind.narrative.memory_log.append(home_event)
    
    _, attached_proposal = brain.decide(attached_hero, Snapshot.from_world(mock_world))
    _, unattached_proposal = brain.decide(unattached_hero, Snapshot.from_world(mock_world))
    
    attached_up = next(u for u in attached_proposal.updates if isinstance(u, StrategicUpdate))
    unattached_up = next(u for u in unattached_proposal.updates if isinstance(u, StrategicUpdate))
    
    assert next(c for c in attached_up.concerns_add_or_update if "Home" in c.label).priority > 5.0
    assert next(c for c in unattached_up.concerns_add_or_update if "Home" in c.label).priority == 1.0

def test_betrayal_trauma_affects_recruitment(mock_world):
    """Verify that a recent betrayal makes entities less willing to accept recruitment offers."""
    from src.ai.strategy.recruitment_negotiation import RecruitmentNegotiationService
    from src.core.models.strategy import RecruitmentOfferRecord, ContractTermRecord
    
    rng = DeterministicRNG(seed=121)
    config = SimulationConfig()
    faction_reg = FactionRegistry()
    
    actor = Entity(id=1, kind="hero")
    recruiter = Entity(id=2, kind="hero")
    mock_world.add_entity(actor)
    mock_world.add_entity(recruiter)
    ctx = AIContext(actor=actor, snapshot=Snapshot.from_world(mock_world), config=config, rng=rng, faction_reg=faction_reg)
    
    offer = RecruitmentOfferRecord(
        offer_id="off_1", recruiter_id=2, candidate_id=1, 
        proposed_terms=[ContractTermRecord(term_type="payout", label="Payout", params={"value": 0.4})],
        contract_kind=ContractKind.EXPEDITION
    )
    
    # Baseline: ACCEPTED
    assert RecruitmentNegotiationService.evaluate_offer(ctx, offer).status == OfferStatus.ACCEPTED
    
    # With Betrayal Concern: DECLINED
    actor.mind.strategic.concerns.append(ConcernRecord(concern_id="c1", kind=ConcernKind.THREAT, label="Betrayal Retribution", priority=4.0))
    assert RecruitmentNegotiationService.evaluate_offer(ctx, offer).status == OfferStatus.DECLINED

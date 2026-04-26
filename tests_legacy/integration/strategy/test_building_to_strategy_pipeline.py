import pytest
from src_legacy.core.logic.strategic_knowledge_ingestion import StrategicKnowledgeIngestionService
from src_legacy.core.models.strategy import StrategicState, ProjectRecord, ProjectKind, StrategicStatus
from src_legacy.core.models.world_state import WorldState
from src_legacy.core.entities.entity import Entity
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.core.world.grid import Grid
from src_legacy.platform.spatial_hash import SpatialHash
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.api.presenters.ai_presenter import AIPresenter
from src_legacy.systems.gameplay.action_system import ActionSystem
from src_legacy.actions.base import ActionProposal
from src_legacy.core.models.enums import ActionType

@pytest.fixture
def test_rng():
    return DeterministicRNG(seed=42)

@pytest.fixture
def base_world():
    grid = Grid(100, 100)
    world = WorldState(seed=42, grid=grid, spatial_index=SpatialHash(cell_size=10))
    return world

@pytest.fixture
def test_entity(base_world, test_rng):
    builder = EntityBuilder(test_rng, entity_id=1)
    entity = builder.kind("hero").with_identity(display_name="Test Hero").build()
    entity.world = base_world
    base_world.entities[1] = entity
    return entity

def test_guild_intel_to_strategy_visible_pipeline(test_entity, base_world, test_rng):
    """Verify that guild intel produces leads/zones that are visible in API schemas."""
    tick = 10
    
    # 1. Ingest guild intel
    update = StrategicKnowledgeIngestionService.ingest_guild_intel(
        actor_id=test_entity.id,
        tick=tick,
        material_hints={"iron_ore": "Found in the northern peaks"},
        camps_found=[(10, 20)],
        resources_found=[]
    )
    
    # 2. Apply update via ActionSystem
    proposal = ActionProposal(actor_id=test_entity.id, verb=ActionType.REST)
    ActionSystem._apply_updates(base_world, test_entity, [update], proposal)
    
    # 3. Verify StrategicState presence
    strat = test_entity.mind.strategic
    assert len(strat.leads) == 2 # 1 for iron_ore, 1 for camp
    assert len(strat.candidate_zones) == 1
    
    lead_mat = next(l for l in strat.leads if l.subject == "iron_ore")
    assert lead_mat.source_type == "guild"
    assert lead_mat.interpreted_meaning == "Found in the northern peaks"
    
    # 4. Verify API Visibility via AIPresenter
    explanation = AIPresenter.get_explanation(test_entity)
    strat_schema = explanation.strategy
    
    assert strat_schema is not None
    assert len(strat_schema.leads) == 2
    assert len(strat_schema.zones) == 1
    
    # Check specific fields that we just expanded
    api_lead = next(l for l in strat_schema.leads if l.subject == "iron_ore")
    assert api_lead.source_type == "guild"
    assert api_lead.discovered_tick == tick
    assert api_lead.certainty == 0.8
    assert api_lead.directness == 1.0

def test_blacksmith_blocker_resolution_pipeline(test_entity, base_world, test_rng):
    """Verify that blacksmith constraints produce blockers that are resolved by acquisition."""
    tick = 15
    
    # 1. Ingest blacksmith constraint (missing iron_ore)
    update = StrategicKnowledgeIngestionService.ingest_blacksmith_constraint(
        actor_id=test_entity.id,
        tick=tick,
        recipe_id="iron_sword",
        missing_materials={"iron_ore": (0, 5)},
        gold_needed=0
    )
    
    proposal = ActionProposal(actor_id=test_entity.id, verb=ActionType.REST)
    ActionSystem._apply_updates(base_world, test_entity, [update], proposal)
    
    # 2. Verify blocker exists
    strat = test_entity.mind.strategic
    blocker = next((b for b in strat.blockers if b.subject_ref == "iron_ore"), None)
    assert blocker is not None
    assert blocker.resolved is False
    assert blocker.severity == 1.0
    
    # 3. Verify API Visibility
    explanation = AIPresenter.get_explanation(test_entity)
    assert any(b.label == "Missing iron_ore" for b in explanation.strategy.blockers)
    
    # 4. Simulate acquisition and resolution
    res_update = StrategicKnowledgeIngestionService.ingest_material_acquisition(
        actor_id=test_entity.id,
        tick=tick + 1,
        item_ids=["iron_ore"]
    )
    ActionSystem._apply_updates(base_world, test_entity, [res_update], proposal)
    
    # 5. Verify blocker is resolved
    blocker = next((b for b in strat.blockers if b.subject_ref == "iron_ore"), None)
    assert blocker is not None
    assert blocker.resolved is True
    
    # 6. Verify API Visibility reflects resolution
    explanation = AIPresenter.get_explanation(test_entity)
    api_blocker = next(b for b in explanation.strategy.blockers if b.label == "Missing iron_ore")
    assert api_blocker.resolved is True

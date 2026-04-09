import pytest
from src.core.world.grid import Grid
from src.systems.spatial_hash import SpatialHash
from src.core.entities.entity_builder import EntityBuilder
from src.platform.rng import DeterministicRNG
from src.systems.social.group_system import GroupSystem
from src.systems.infrastructure.base import SystemContext
from src.api.presenters.entity_presenter import EntityPresenter
from src.core.models.enums import Faction, LifeRole, AIState, GoalType
from src.core.models.lived_structure import PlaceAttachment, AttachmentKind
from src.core.models.vectors import Vector2

class MockWorld:
    def __init__(self):
        self.grid = Grid(50, 50)
        self.spatial_hash = SpatialHash(cell_size=5)
        self.entities = {}
        self.group_registry = {}
        self.rng = DeterministicRNG(42)
        self.tick = 0

    def get_entity(self, eid):
        return self.entities.get(eid)

@pytest.fixture
def inspection_setup():
    world = MockWorld()
    rng = DeterministicRNG(42)
    
    # Create a band of raiders
    raider1 = EntityBuilder(rng, 1).kind("goblin_warrior").faction(Faction.GOBLIN_HORDE).at(Vector2(10, 10)).clique("test_cluster").world_role(LifeRole.RAIDER).build()
    
    raider2 = EntityBuilder(rng, 2).kind("goblin_warrior").faction(Faction.GOBLIN_HORDE).at(Vector2(11, 11)).clique("test_cluster").world_role(LifeRole.RAIDER).build()
    
    world.entities = {raider1.id: raider1, raider2.id: raider2}
    
    # Add a place attachment to raider1
    raider1.mind.place_attachments.append(
        PlaceAttachment(
            location_pos=Vector2(5, 5),
            building_id=101,
            kind=AttachmentKind.HOME,
            importance=0.9
        )
    )
    
    return world, raider1, raider2

def test_entity_inspection_behavior_parity(inspection_setup):
    world, raider1, raider2 = inspection_setup
    
    from src.config import SimulationConfig
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    system = GroupSystem(config=config, rng=rng)
    context = SystemContext(
        config=config, 
        world=world, 
        rng=rng, 
        generator=None,
        faction_reg=None,
        emit=lambda *args, **kwargs: None
    )
    system.on_tick(context, tick=0)
    
    assert raider1.identity.group_id is not None
    assert raider1.identity.group_id == raider2.identity.group_id
    
    # 2. Serialize raider1 and check schema parity
    schema = EntityPresenter.to_full_schema(raider1, world=world)
    
    # Check fields added in Pass 4
    assert schema.world_role == "raider"
    assert schema.cluster_id == "test_cluster"
    assert schema.group_id == raider1.identity.group_id
    
    # Check place attachments
    assert len(schema.place_attachments) >= 1
    # Find our manual attachment
    manual_att = next((a for a in schema.place_attachments if a.place_id == 101), None)
    assert manual_att is not None
    assert manual_att.importance == 0.9
    assert manual_att.attachment_kind == "home"
    
    # Check routine (from Pass 3)
    assert schema.routine is not None
    assert "06:00 - 22:00" in schema.routine.active_hours

def test_ai_explanation_parity(inspection_setup):
    world, raider1, raider2 = inspection_setup
    
    from src.config import SimulationConfig
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    system = GroupSystem(config=config, rng=rng)
    context = SystemContext(
        config=config, 
        world=world, 
        rng=rng, 
        generator=None,
        faction_reg=None,
        emit=lambda *args, **kwargs: None
    )
    system.on_tick(context, tick=0)
    
    # Mock some decision state
    raider1.mind.decision.ai_state = AIState.COMBAT
    raider1.mind.decision.last_goal = GoalType.COMBAT
    raider1.mind.routine.active_routine_id = "raid_routine"
    
    from src.api.presenters.ai_presenter import AIPresenter
    explanation = AIPresenter.get_explanation(raider1)
    
    assert explanation.current_state == "combat"
    assert explanation.group_id == raider1.identity.group_id
    assert explanation.active_routine_id == "raid_routine"

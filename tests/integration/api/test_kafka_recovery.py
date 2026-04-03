from src.utils.serialization import SimulationSerializer
from unittest.mock import MagicMock, patch

from src.core.models.enums import AIState, ActionType, Domain
from src.core.entities.entity import Entity, Vector2
from src.platform.rng import DeterministicRNG
from src.core.world.grid import Grid
from src.config import SimulationConfig
from src.core.models.snapshot import Snapshot
from src.api.engine_manager import EngineManager
from src.actions.base import ActionProposal
from src.platform.spatial_hash import SpatialHash
from src.core.models.world_state import WorldState

@patch("src.api.kafka_client.create_kafka_consumer")
def test_engine_manager_kafka_recovery(mock_create_consumer, monkeypatch):
    """Test that EngineManager can recover from a Kafka snapshot + event stream."""
    
    # 1. Setup a valid Config
    config = SimulationConfig(
        grid_width=50,
        grid_height=50,
        world_seed=42,
    )
    
    # 2. Build a fake WorldState and serialize it
    grid = Grid(config.grid_width, config.grid_height)
    spatial = SpatialHash(config.spatial_cell_size)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.tick = 400
    
    dummy = Entity(id=99, kind="goblin", pos=Vector2(5, 5))
    dummy.mind.ai_state = AIState.COMBAT
    world.add_entity(dummy)
    
    snap = Snapshot.from_world(world)
    serialized_snap = SimulationSerializer.dumps(snap)
    
    # 3. Build fake event payload (tick 401)
    # A MOVE proposal for the dummy entity
    proposal = ActionProposal(
        actor_id=99,
        verb=ActionType.MOVE,
        target=Vector2(6, 6),
        reason="Testing move"
    )
    payload = {
        "tick": 401,
        "proposals": [proposal]
    }
    serialized_event = SimulationSerializer.dumps(payload)
    
    # 4. Mock the Kafka Consumer behavior
    # We need to simulate two reads: one for the Snapshot topic, one for Events.
    # We will track which topic is assigned to return the right data.
    mock_consumer = MagicMock()
    mock_create_consumer.return_value = mock_consumer
    
    # State flags to simulate the queue
    assigned_topics = []
    
    def mock_assign(partitions):
        nonlocal assigned_topics
        assigned_topics.clear()
        for p in partitions:
            assigned_topics.append(p.topic)
            
    mock_consumer.assign = mock_assign
    
    # Keep track of how many times poll is called per topic so we can return EOF (None)
    poll_counts = {"sim.snapshots": 0, "sim.events": 0}
    
    def mock_poll(timeout):
        nonlocal poll_counts
        
        # Determine which topic is currently assigned
        current_topic = assigned_topics[0] if assigned_topics else None
        if not current_topic:
            return None
            
        count = poll_counts.get(current_topic, 0)
        
        if current_topic == "sim.snapshots":
            if count == 0:
                poll_counts[current_topic] += 1
                msg = MagicMock()
                msg.error.return_value = False
                msg.value.return_value = serialized_snap
                return msg
            else:
                return None # EOF timeout
                
        elif current_topic == "sim.events":
            if count == 0:
                poll_counts[current_topic] += 1
                msg = MagicMock()
                msg.error.return_value = False
                msg.value.return_value = serialized_event
                return msg
            else:
                return None # EOF timeout
                
        return None

    mock_consumer.poll = mock_poll
    
    # 5. Run the EngineManager build (this occurs automatically on __init__)
    engine = EngineManager(config)
    recovered_world = engine._loop._world
    
    # 6. Assertions
    assert recovered_world is not None, "World should have been recovered"
    assert recovered_world.tick == 401, "World tick should have advanced from 400 to 401 via event replay"
    
    # Verify the dummy entity is present and has moved
    assert 99 in recovered_world.entities, "Entity 99 should exist"
    recovered_dummy = recovered_world.entities[99]
    assert recovered_dummy.spatial.pos.x == 6, "Entity should have moved to x=6"
    assert recovered_dummy.spatial.pos.y == 6, "Entity should have moved to y=6"
    

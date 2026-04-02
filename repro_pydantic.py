import json
from src.core.entities.entity import Entity
from src.core.models.snapshot import Snapshot
from src.core.models.vectors import Vector2
from src.core.aspects.mind import MemoryRecord, MindAspect
from src.utils.serialization import SimulationSerializer
from src.core.world.grid import Grid
from pydantic import TypeAdapter

# 1. Create a test entity with memory
try:
    e = Entity(id=1, kind="hero")
    # Entity constructor might need more fields if config is strict
    print("Entity created successfully")
except Exception as ex:
    print(f"Entity creation failed: {ex}")
    # Fallback to manual dict if needed, but we want to test Pydantic
    exit(1)

rec = MemoryRecord(entity_id=2, pos=Vector2(10, 20), kind="goblin")
e.mind.perception.entity_memory[2] = rec

# 2. Mock Snapshot fields
grid = Grid(width=10, height=10)
# Use the from_world style or manual init
snap = Snapshot(
    tick=1, seed=42, 
    entities={1: e}, 
    grid=grid, 
    ground_items={}, 
    camps=(), 
    buildings=(), 
    resource_nodes=(), 
    treasure_chests=(), 
    regions=(),
    region_control={},
    war_status={},
    faction_aggression={}
)

# 3. Serialize using the actual tool the worker uses
data_json = SimulationSerializer.dumps(snap)
print(f"Serialized JSON size: {len(data_json)} bytes")

# 4. Deserialize using the actual tool the worker uses
snap2 = SimulationSerializer.loads(data_json, Snapshot)
e2 = snap2.entities[1]
memory = e2.mind.perception.entity_memory

print(f"Memory keys: {list(memory.keys())}")
# JSON keys are always strings, let's see if Pydantic 2 coerced back to int
key = 2
if 2 not in memory and "2" in memory:
    print("Warning: Key remained 'str' instead of 'int'")
    key = "2"

rec2 = memory[key]
print(f"Record type: {type(rec2)}")

if isinstance(rec2, dict):
    print("FAIL: MemoryRecord is a dict")
    # Check if we can manually validate it
    try:
        rec_fixed = MemoryRecord.model_validate(rec2)
        print(f"Manual validation success: pos={rec_fixed.pos}")
    except Exception as ex2:
        print(f"Manual validation failed: {ex2}")
else:
    print(f"SUCCESS: MemoryRecord is {type(rec2)}")
    print(f"Pos type: {type(rec2.pos)}")
    if isinstance(rec2.pos, dict):
        print("FAIL: Vector2 is a dict")
    else:
        print(f"Vector2 success: {rec2.pos}")

import os
import sys
# Ensure we can import from src
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.core.models.base import SimulationModel
from src.core.models.vectors import Vector2
from pydantic import Field
from types import MappingProxyType

class MockModel(SimulationModel):
    pos: Vector2 = Field(default_factory=Vector2)
    path: list[Vector2] = Field(default_factory=list)
    lookup: dict[str, Vector2] = Field(default_factory=dict)

def test_reproduce():
    model = MockModel()
    model.pos = Vector2(10, 20)
    model.path = [Vector2(1, 1), Vector2(2, 2)]
    model.lookup = {"start": Vector2(0, 0)}
    
    print(f"Before freeze: pos type = {type(model.pos)}")
    model.freeze()
    print(f"After freeze: pos type = {type(model.pos)}")
    
    assert isinstance(model.pos, Vector2), f"Expected Vector2, got {type(model.pos)}"
    assert isinstance(model.path[0], Vector2), f"Expected Vector2 in list, got {type(model.path[0])}"
    assert isinstance(model.lookup["start"], Vector2), f"Expected Vector2 in dict, got {type(model.lookup['start'])}"
    
    print("Test passed!")

if __name__ == "__main__":
    try:
        test_reproduce()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

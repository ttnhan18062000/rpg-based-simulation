
import pytest
from src.core.models.base import SimulationModel
from src.core.models.vectors import Vector2
from src.core.aspects.mind import BeliefRecord

def test_vector2_coercion_during_freeze():
    """
    CRITICAL ARCHITECTURAL VERIFICATION:
    Ensures that if a field expecting a SimulationModel subclass (like Vector2) 
    contains a raw dict (e.g. from serialization drift), the freeze() logic 
    authoritatively coerces it back to the proper object before applying proxies.
    """
    # 1. Create a BeliefRecord with a raw dict in 'pos' (simulating drift)
    # Using model_construct to avoid initial validation, or just assigning after init
    b = BeliefRecord(entity_id=32, pos=Vector2(0,0))
    
    # Simulate drift: replace Vector2 object with a raw dict
    drifted_pos = {"x": 100, "y": 200}
    # Bypass Pydantic frozen/validation for the assignment to simulate dirty state
    object.__setattr__(b, "pos", drifted_pos)
    
    assert isinstance(b.pos, dict), "Setup failed: pos should be a dict for this reproduction"
    
    # 2. Trigger the AOA Freeze phase
    # This should find the dict and coerce it back to Vector2
    b.freeze()
    
    # 3. VERIFY: pos must be a Vector2 object and have attributes x,y
    assert not isinstance(b.pos, dict), "Fix failed: pos was NOT coerced back from dict"
    assert isinstance(b.pos, Vector2), f"Fix failed: pos should be Vector2, got {type(b.pos)}"
    assert b.pos.x == 100
    assert b.pos.y == 200
    
    # Ensure it's not a mappingproxy (which lacks .x)
    try:
        _ = b.pos.x
    except AttributeError as e:
        pytest.fail(f"pos still behaves like a mappingproxy: {e}")

if __name__ == "__main__":
    # Allow running directly
    try:
        test_vector2_coercion_during_freeze()
        print("Test PASSED locally")
    except Exception as e:
        print(f"Test FAILED: {e}")
        import traceback
        traceback.print_exc()

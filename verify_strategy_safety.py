import sys
import os
# Add src to path
sys.path.append(os.getcwd())

from src.core.aspects.mind import MindAspect
from src.core.models.strategy import StrategicState, DirectiveRecord, DirectiveKind

def test_snapshot_safety():
    mind = MindAspect()
    mind.strategic.directives.append(DirectiveRecord(
        directive_id="test_1",
        kind=DirectiveKind.PERSONAL,
        label="Test Directive"
    ))
    
    # 1. Test Copy (Snapshot Isolation)
    mind_copy = mind.copy()
    assert mind_copy.strategic is not mind.strategic
    assert mind_copy.strategic.directives[0] is not mind.strategic.directives[0]
    assert mind_copy.strategic.directives[0].directive_id == "test_1"
    
    # Mutate copy
    mind_copy.strategic.directives[0].label = "Mutated"
    assert mind.strategic.directives[0].label == "Test Directive"
    print("Snapshot isolation verified.")

def test_freeze_safety():
    mind = MindAspect()
    mind.strategic.directives.append(DirectiveRecord(
        directive_id="test_1",
        kind=DirectiveKind.PERSONAL,
        label="Test Directive"
    ))
    
    mind.freeze()
    assert mind._frozen is True
    assert mind.strategic._frozen is True
    assert mind.strategic.directives[0]._frozen is True
    
    try:
        mind.strategic.directives[0].label = "Illegal"
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        print(f"Freeze safety verified: {e}")

if __name__ == "__main__":
    test_snapshot_safety()
    test_freeze_safety()

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.apply import ApplyPath

def test_trace_gating():
    state = AuthoritativeState(tick=100, seed=42, transaction_trace=["old_trace"])
    update = StateUpdate(transaction_trace=["new_trace"])
    
    # Test with audit_mode=True
    state_audit = ApplyPath.apply_generation(state, update, audit_mode=True)
    print(f"Trace with audit_mode=True: {state_audit.transaction_trace}")
    assert "new_trace" in state_audit.transaction_trace
    assert "old_trace" in state_audit.transaction_trace
    
    # Test with audit_mode=False
    state_no_audit = ApplyPath.apply_generation(state, update, audit_mode=False)
    print(f"Trace with audit_mode=False: {state_no_audit.transaction_trace}")
    assert len(state_no_audit.transaction_trace) == 0
    
    print("Trace Gating Tests Passed!")

if __name__ == "__main__":
    test_trace_gating()

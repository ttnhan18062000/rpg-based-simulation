import pytest
from src.testing.assertions import assert_cognition_consistency

def test_cognition_assertion_detects_drift():
    """Prove that assert_cognition_consistency fails when replay and graph diverged."""
    
    # 1. Setup a "healthy" state
    replay = {
        "ticks": [
            {
                "tick": 1,
                "entities": [
                    {
                        "id": 101,
                        "strategy": {
                            "last_capacity_profile": {
                                "planning_budget": 100,
                                "active_slice_limit": 50,
                            },
                            "active_slice_used": 5,
                            "is_overloaded": False
                        }
                    }
                ]
            }
        ]
    }
    
    graph = {
        "elements": {
            "nodes": [
                {
                    "data": {
                        "id": "cognition:101:1",
                        "kind": "cognition_profile",
                        "planning_budget": 100,
                        "active_slice_used": 5,
                        "active_slice_limit": 50,
                        "is_overloaded": False
                    }
                }
            ],
            "edges": []
        }
    }
    
    # Should pass initially
    assert_cognition_consistency(replay, {101: graph})
    
    # 2. Induce Drift: Change budget in replay
    replay["ticks"][0]["entities"][0]["strategy"]["last_capacity_profile"]["planning_budget"] = 99
    with pytest.raises(AssertionError) as excinfo:
        assert_cognition_consistency(replay, {101: graph})
    assert "planning_budget mismatch" in str(excinfo.value)
    
    # 3. Induced Drift: Change usage in graph
    replay["ticks"][0]["entities"][0]["strategy"]["last_capacity_profile"]["planning_budget"] = 100
    graph["elements"]["nodes"][0]["data"]["active_slice_used"] = 6
    with pytest.raises(AssertionError) as excinfo:
        assert_cognition_consistency(replay, {101: graph})
    assert "active_slice_used mismatch" in str(excinfo.value)

if __name__ == "__main__":
    pytest.main([__file__])

import pytest
from tests.parity.helpers.oracle_loader import load_oracle

@pytest.mark.differential
@pytest.mark.parametrize("input_data, expected", load_oracle("substrate", "distance"))
def test_manhattan_distance_parity(input_data, expected):
    """
    V2 implementation of Manhattan distance parity test.
    Verifies that the framework can load and compare cases.
    """
    p1 = input_data["p1"]
    p2 = input_data["p2"]
    
    # V2 implementation (should match legacy)
    v2_distance = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    assert v2_distance == expected["distance"]

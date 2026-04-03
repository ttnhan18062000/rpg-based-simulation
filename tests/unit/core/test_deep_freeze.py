import pytest
from src.core.models.base import SimulationModel
from pydantic import Field

class NestedModel(SimulationModel):
    data: list[list[int]] = Field(default_factory=list)
    metadata: dict[str, list[int]] = Field(default_factory=dict)

def test_deep_freeze_nested_collections():
    """Verify that freeze() recursively converts nested collections to immutable types."""
    model = NestedModel()
    model.data = [[1, 2], [3, 4]]
    model.metadata = {"a": [5, 6], "b": [7, 8]}
    
    model.freeze()
    
    # 1. Top-level should be frozen
    with pytest.raises(RuntimeError):
        model.data = [[0]]
        
    # 2. Outer list should be a tuple
    assert isinstance(model.data, tuple)
    
    # 3. Inner lists should also be tuples (RECURSIVE)
    assert isinstance(model.data[0], tuple)
    assert model.data[0] == (1, 2)
    
    # 4. Dictionary should be MappingProxyType
    from types import MappingProxyType
    assert isinstance(model.metadata, MappingProxyType)
    
    # 5. Values within dictionary should be tuples
    assert isinstance(model.metadata["a"], tuple)
    assert model.metadata["a"] == (5, 6)

def test_deep_freeze_idempotency():
    """Verify that calling freeze() multiple times is safe."""
    model = NestedModel(data=[[1]])
    model.freeze()
    model.freeze()
    assert model.data == ((1,),)

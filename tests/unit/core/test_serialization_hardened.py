import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
import json
from types import MappingProxyType
from enum import Enum
from typing import Any
from pydantic import BaseModel
from src.utils.serialization import SimulationSerializer, SimulationJSONEncoder
from src.core.models.vectors import Vector2

class MockEnum(Enum):
    ALPHA = 1
    BETA = 2

class MockNestedModel(BaseModel):
    name: str
    pos: Vector2

class MockComplexModel(BaseModel):
    id: int
    tags: list[str]
    frozen_dict: Any = None # We'll manually put MappingProxy here

def test_json_encoder_mapping_proxy():
    proxy = MappingProxyType({"a": 1, "b": 2})
    encoded = json.dumps(proxy, cls=SimulationJSONEncoder)
    assert json.loads(encoded) == {"a": 1, "b": 2}

def test_json_encoder_enum():
    data = {"status": MockEnum.ALPHA}
    encoded = json.dumps(data, cls=SimulationJSONEncoder)
    assert json.loads(encoded) == {"status": 1}

def test_serialization_pydantic_model():
    model = MockNestedModel(name="test", pos=Vector2(x=10, y=20))
    # SimulationSerializer.dumps(model) uses model_dump_json()
    bytes_data = SimulationSerializer.dumps(model)
    assert b'"name":"test"' in bytes_data
    assert b'"pos":{"x":10,"y":20}' in bytes_data or b'"pos":{"x":10,"y":20}' in bytes_data.replace(b" ", b"")

def test_serialization_frozen_model_with_proxy():
    # This simulates a frozen SimulationModel
    raw_data = {"id": 1, "tags": ["a"], "frozen_dict": MappingProxyType({"val": 42})}
    bytes_data = SimulationSerializer.dumps(raw_data)
    
    decoded = json.loads(bytes_data.decode("utf-8"))
    assert decoded["id"] == 1
    assert decoded["frozen_dict"] == {"val": 42}

def test_serializer_loads():
    data = b'{"name": "test", "pos": {"x": 5, "y": 5}}'
    model = SimulationSerializer.loads(data, MockNestedModel)
    assert isinstance(model, MockNestedModel)
    assert model.name == "test"
    assert model.pos.x == 5

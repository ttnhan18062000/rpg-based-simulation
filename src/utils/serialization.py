from __future__ import annotations
import json
from typing import Any, Type, TypeVar
from pydantic import BaseModel
from dataclasses import is_dataclass, asdict
from enum import Enum
from types import MappingProxyType

T = TypeVar("T")

class SimulationJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles AOA-specific types."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, MappingProxyType):
            return dict(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if is_dataclass(obj):
            return asdict(obj)
        # Handle specialized types if needed (e.g. Vector2 if not Pydantic)
        return super().default(obj)

class SimulationSerializer:
    """Handles serialization of SimulationModels and Dataclasses (UTF-8 JSON)."""
    
    @staticmethod
    def dumps(obj: Any) -> bytes:
        """Serialize an object to bytes (UTF-8 JSON) using CustomJSONEncoder."""
        # For pure Pydantic models, use their optimized JSON method
        if isinstance(obj, BaseModel):
            return obj.model_dump_json().encode("utf-8")
        
        # For containers (list/dict) that might have nested frozen models
        return json.dumps(obj, cls=SimulationJSONEncoder).encode("utf-8")

    @staticmethod
    def loads(data: bytes, target_cls: Type[T] | None = None) -> T | Any:
        """Deserialize bytes to a specific target class or raw dict."""
        decoded = data.decode("utf-8")
        raw_data = json.loads(decoded)
        
        if target_cls and issubclass(target_cls, BaseModel):
            return target_cls.model_validate(raw_data)
        
        return raw_data

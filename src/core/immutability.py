from __future__ import annotations
from typing import Any
from types import MappingProxyType
from dataclasses import is_dataclass, fields, replace

def deep_freeze(obj: Any) -> Any:
    """
    Recursively transform mutable structures into their immutable counterparts.
    Law: Decision logic must only operate on deeply frozen state.
    """
    if isinstance(obj, dict):
        return MappingProxyType({k: deep_freeze(v) for k, v in obj.items()})
    
    if isinstance(obj, list):
        return tuple(deep_freeze(v) for v in obj)
    
    if isinstance(obj, set):
        return frozenset(deep_freeze(v) for v in obj)
    
    if is_dataclass(obj):
        # Create a new instance with frozen fields
        # Note: Dataclass must be frozen=True for this to be effective at the top level
        new_values = {}
        for field in fields(obj):
            val = getattr(obj, field.name)
            new_values[field.name] = deep_freeze(val)
        return replace(obj, **new_values)
    
    # Primitive types (int, float, str, bool, None) are already immutable
    return obj

def shallow_freeze(obj: Any) -> Any:
    """
    Shallow transform mutable structures into their immutable counterparts.
    Used for high-frequency state views where deep_freeze is too expensive.
    """
    if isinstance(obj, dict):
        return MappingProxyType(obj)
    if isinstance(obj, list):
        return tuple(obj)
    if isinstance(obj, set):
        return frozenset(obj)
    return obj

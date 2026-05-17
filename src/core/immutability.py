# Compliance IDs: AUTH-011, AUTH-012, AUTH-014, AUTH-015, AUTH-018, AUTH-019, AUTH-021, AUTH-023, AUTH-024, AUTH-035, AUTH-036, AUTH-037, DATA-020, DATA-060, DATA-061, DATA-062, DATA-066, DATA-067, DATA-075, DATA-078, DATA-093, INFRA-046, INFRA-197, INFRA-198, WORLD-004
from __future__ import annotations
from typing import Any
from types import MappingProxyType
from dataclasses import is_dataclass, fields, replace

# Lazy module-level cache to avoid circular import
_ReadOnlyDict = None

def _get_readonly_dict():
    global _ReadOnlyDict
    if _ReadOnlyDict is None:
        from src.core.state import ReadOnlyDict
        _ReadOnlyDict = ReadOnlyDict
    return _ReadOnlyDict

def deep_freeze(obj: Any) -> Any:
    """
    Recursively transform mutable structures into their immutable counterparts.
    Law: Decision logic must only operate on deeply frozen state.
    """
    ReadOnlyDict = _get_readonly_dict()
    if isinstance(obj, (ReadOnlyDict, MappingProxyType, tuple, frozenset, int, float, str, bool)) or obj is None:
        return obj
    
    if isinstance(obj, dict):
        return ReadOnlyDict({k: deep_freeze(v) for k, v in obj.items()})
    
    if isinstance(obj, list):
        return tuple(deep_freeze(v) for v in obj)
    
    if isinstance(obj, set):
        return frozenset(deep_freeze(v) for v in obj)
    
    if is_dataclass(obj):
        # Optimization: If dataclass is already frozen and has a cache, use it
        if hasattr(obj, "_readonly_cache") and obj._readonly_cache is not None:
            return obj._readonly_cache
        if hasattr(obj, "to_readonly"):
            return obj.to_readonly()
            
        new_values = {}
        changed = False
        for field in fields(obj):
            if field.name == "_readonly_cache":
                continue
            val = getattr(obj, field.name)
            frozen_val = deep_freeze(val)
            if frozen_val is not val:
                changed = True
            new_values[field.name] = frozen_val
            
        if not changed:
            return obj
            
        res = replace(obj, **new_values)
        return res
    
    return obj

def shallow_freeze(obj: Any) -> Any:
    """
    Shallow transform mutable structures into their immutable counterparts.
    Used for high-frequency state views where deep_freeze is too expensive.
    """
    ReadOnlyDict = _get_readonly_dict()
    if isinstance(obj, (ReadOnlyDict, tuple, frozenset)):
        return obj
    if isinstance(obj, dict):
        return ReadOnlyDict(obj)
    if isinstance(obj, list):
        return tuple(obj)
    if isinstance(obj, set):
        return frozenset(obj)
    return obj


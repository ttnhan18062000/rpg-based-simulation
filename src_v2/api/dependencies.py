from __future__ import annotations
from typing import Optional
from src_v2.api.engine_manager import V2EngineManager

_engine_manager: Optional[V2EngineManager] = None

def set_engine_manager(manager: V2EngineManager):
    global _engine_manager
    _engine_manager = manager

def get_engine_manager() -> V2EngineManager:
    if _engine_manager is None:
        raise RuntimeError("V2EngineManager not initialized.")
    return _engine_manager

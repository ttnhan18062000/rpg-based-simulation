"""FastAPI dependency injection — provides the EngineManager singleton."""

from __future__ import annotations

from src.api.engine_manager import EngineManager

_engine_manager: EngineManager | None = None


def set_engine_manager(manager: EngineManager) -> None:
    global _engine_manager
    _engine_manager = manager


def get_engine_manager() -> EngineManager:
    if _engine_manager is None:
        raise RuntimeError("EngineManager not initialized — server not started correctly.")
    return _engine_manager

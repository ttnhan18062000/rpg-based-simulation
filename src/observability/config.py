from __future__ import annotations
import os
import threading
from enum import Enum
from typing import Optional


class ObservabilityMode(str, Enum):
    """
    Observability operational modes for the RPG Simulation Engine.
    """
    OFF = "OFF"
    LIGHT = "LIGHT"
    DEBUG = "DEBUG"
    CERTIFICATION = "CERTIFICATION"
    LONG_RUN = "LONG_RUN"


class ObservabilityConfig:
    """
    Thread-safe global manager for resolving the active simulation observability mode.
    Precedence: Direct override -> Environment variable -> Default (LIGHT)
    """
    _override_mode: Optional[ObservabilityMode] = None
    _lock = threading.Lock()

    @classmethod
    def set_override_mode(cls, mode: Optional[ObservabilityMode]) -> None:
        """Sets a programmatic override mode, e.g. for specific tests."""
        with cls._lock:
            cls._override_mode = mode

    @classmethod
    def get_mode(cls) -> ObservabilityMode:
        """Resolves the current active observability mode with precedence."""
        with cls._lock:
            if cls._override_mode is not None:
                return cls._override_mode

        # Precedence: Env variable -> Default
        env_val = os.environ.get("SIM_OBS_MODE") or os.environ.get("RPG_OBS_MODE")
        if env_val:
            try:
                return ObservabilityMode(env_val.strip().upper())
            except ValueError:
                pass

        return ObservabilityMode.LIGHT

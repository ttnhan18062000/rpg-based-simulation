"""Scratch-only, library-only Codex pilot lifecycle simulation.

This package deliberately has no command-line entry point and never selects a
real pilot, changes Codex configuration, or targets the repository monitoring
corpus.  Callers must provide a disposable scratch root.
"""

from .simulation import simulate_pilot

__all__ = ["simulate_pilot"]

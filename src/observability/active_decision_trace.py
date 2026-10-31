"""
src/observability/active_decision_trace.py
───────────────────────────────────────────────────────────────────────────────
Run-scoped slot for the active decision-trace writer.

Dependency-free on purpose: this module imports nothing from
``src.observability.cognition`` or ``src.observability.queue``. The adventure
scorer reads the slot on every tick of every run, including OFF-mode runs, so
holding the slot in ``decision_trace_writer`` made an OFF-mode process load the
cognition package (and through it the recorder and queue modules).

The Kernel sets the slot at run start and clears it at run end; the scorer only
reads it. ``decision_trace_writer`` re-exports ``set_active_writer`` and
``get_active_writer`` so existing importers keep working.
"""
from __future__ import annotations

from typing import Any, Optional

# Typed loosely (Any) so no import of DecisionTraceWriter is needed; the slot only
# ever holds a DecisionTraceWriter (or None).
_active_writer: Optional[Any] = None


def set_active_writer(writer: Optional[Any]) -> None:
    """Register (or clear) the run-scoped DecisionTraceWriter singleton."""
    global _active_writer
    _active_writer = writer


def get_active_writer() -> Optional[Any]:
    """Return the currently active DecisionTraceWriter, or None."""
    return _active_writer

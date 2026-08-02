"""Immutable input and result models for a synthetic pilot lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class PilotSimulationContext:
    """All caller-supplied inputs, intentionally limited to disposable data."""

    scratch_root: Path
    ticket_id: str
    execution_id: str
    run_id: str
    start_ts: str
    end_ts: str
    post_tool_payload: dict
    adapter_gate: Mapping[str, str]
    enabled_hook_events: frozenset[str] = frozenset({"PostToolUse"})
    enabled_writer_names: frozenset[str] = frozenset({"write_line", "write_lines"})


@dataclass(frozen=True)
class ClaimMarker:
    ticket_id: str
    execution_id: str
    state: str


@dataclass(frozen=True)
class SimulationResult:
    success: bool
    boundary: str
    claim: ClaimMarker | None

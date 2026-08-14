"""Narrow imports of the established validators and shared writer call sites."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, _TOOLS / "agent-monitoring" / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load shared monitoring dependency {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


record_run = _load("agent_codex_pilot_executor_record_run", "record_run.py")
record_events = _load("agent_codex_pilot_executor_record_events", "record_events.py")

write_line = record_run.write_line
write_lines = record_events.write_lines

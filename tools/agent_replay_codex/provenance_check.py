"""Monitoring-record provenance check (TCK-20260721-CODEX-REPLAY-PARITY, Step 9, AC #8).

An always-runnable structural invariant (does not require a real Codex invocation): nothing in
this package ever calls tools/agent-monitoring/writer.py with provider="codex" — the whole
package only reads fixtures and writes to a scratch-dir JSON file — so this check should hold at
any point in time, not merely "after tests ran."
"""
from __future__ import annotations

import json
from pathlib import Path

from .errors import ContainmentViolationError

_MONITORING_FILENAMES = ("runs.jsonl", "events.jsonl", "tools.jsonl")


def assert_no_codex_provider_writes(agent_monitoring_dir: Path, provider_value: str = "codex") -> None:
    """Reads the real runs.jsonl/events.jsonl/tools.jsonl and raises ContainmentViolationError if
    any record's 'provider' field equals provider_value. Read-only — never writes."""
    for filename in _MONITORING_FILENAMES:
        path = agent_monitoring_dir / filename
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict) and record.get("provider") == provider_value:
                    raise ContainmentViolationError(
                        f"{filename}:{line_no}: found a live monitoring record with "
                        f"provider=={provider_value!r} — Codex must never be a live writer"
                    )

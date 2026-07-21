"""Fixture envelope loader/validator for the agent-workflow replay proof.

Built for TCK-20260721-CODEX-REPLAY-PROOF. Defines the versioned envelope shape a
`tests/fixtures/agent_replay/*.yaml` file must satisfy — see docs/ai/replay_fixture_spec.md for
the full spec — and `load_fixture()`, the single validation entry point `tools/agent_replay/runner.py`
and its tests both call.

Fail-closed by design (a deliberate inversion of this repo's dominant fail-open monitoring-write
convention): any missing or null required field raises `FixtureValidationError` naming the exact
field and phase index. There is no default substitution and no log-and-continue path — a malformed
fixture must never silently produce a partial replay.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class FixtureValidationError(Exception):
    """Raised by `load_fixture` when a required envelope field is missing or null."""


_REQUIRED_SOURCE_KEYS = ("ticket_id", "ticket_path", "events_run_id")
_REQUIRED_PHASE_KEYS = ("phase", "agent", "input", "output", "transition")


@dataclass(frozen=True)
class PhaseEntry:
    phase: str
    agent: str
    input: dict[str, Any]
    output: dict[str, Any]
    transition: str


@dataclass(frozen=True)
class FixtureEnvelope:
    version: int
    source: dict[str, Any]
    phases: list[PhaseEntry]


def load_fixture(path: str | Path) -> FixtureEnvelope:
    """Load and validate a replay fixture YAML file, raising on any missing required field."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise FixtureValidationError(f"{path}: fixture root is not a mapping")

    if raw.get("version") is None:
        raise FixtureValidationError(f"{path}: missing required top-level field 'version'")

    source = raw.get("source")
    if not isinstance(source, dict):
        raise FixtureValidationError(f"{path}: missing required top-level field 'source'")
    for key in _REQUIRED_SOURCE_KEYS:
        if not source.get(key):
            raise FixtureValidationError(f"{path}: source is missing required field '{key}'")

    phases_raw = raw.get("phases")
    if not isinstance(phases_raw, list) or len(phases_raw) == 0:
        raise FixtureValidationError(f"{path}: 'phases' must be a non-empty list")

    phases: list[PhaseEntry] = []
    for idx, entry in enumerate(phases_raw):
        if not isinstance(entry, dict):
            raise FixtureValidationError(f"{path}: phases[{idx}] is not a mapping")
        for key in _REQUIRED_PHASE_KEYS:
            if entry.get(key) is None:
                raise FixtureValidationError(
                    f"{path}: phases[{idx}] is missing required field '{key}'"
                )
        phases.append(
            PhaseEntry(
                phase=entry["phase"],
                agent=entry["agent"],
                input=entry["input"],
                output=entry["output"],
                transition=entry["transition"],
            )
        )

    return FixtureEnvelope(version=raw["version"], source=source, phases=phases)

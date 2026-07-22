"""Standalone reader for agent-orchestration/terminal-statuses.yaml.

Mirrors tools/agent_orchestration/loader.py's "only yaml.safe_load + stdlib, no network" reading
philosophy, but deliberately does NOT extend `ContractBundle` or edit `loader.py` itself —
terminal-statuses.yaml is a standalone sibling file, read by this ticket's own package, keeping
`ContractBundle`'s dataclass shape (and every test asserting it) untouched.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_VALID_KINDS = {"literal", "verdict_derived", "bypass"}


class TerminalStatusValidationError(Exception):
    """Raised by validate_terminal_statuses when agent-orchestration/terminal-statuses.yaml is
    missing a required field, malformed, or contains a duplicate `value` entry.

    Mirrors tools/agent_orchestration/errors.py's flat-exception style: a single exception class,
    no subclass hierarchy, raised with a message naming the exact offending entry/field.
    """


def validate_terminal_statuses(data: dict[str, Any]) -> None:
    """Schema/shape validation for terminal-statuses.yaml's parsed content.

    Independent of any live-source comparison — a malformed contract entry surfaces here as a
    named validation error, rather than as an opaque downstream mismatch in a conformance test.
    """
    if not isinstance(data, dict):
        raise TerminalStatusValidationError("terminal-statuses.yaml: YAML root is not a mapping")

    if data.get("terminal_status_schema_version") != 1:
        raise TerminalStatusValidationError(
            "terminal-statuses.yaml: 'terminal_status_schema_version' missing or not 1, "
            f"got {data.get('terminal_status_schema_version')!r}"
        )

    if not data.get("workflow_id"):
        raise TerminalStatusValidationError("terminal-statuses.yaml: missing required field 'workflow_id'")

    statuses = data.get("statuses")
    if not isinstance(statuses, list) or len(statuses) == 0:
        raise TerminalStatusValidationError("terminal-statuses.yaml: 'statuses' must be a non-empty list")

    seen_values: set[str] = set()
    for idx, entry in enumerate(statuses):
        if not isinstance(entry, dict):
            raise TerminalStatusValidationError(f"terminal-statuses.yaml: statuses[{idx}] is not a mapping")

        value = entry.get("value")
        if not value:
            raise TerminalStatusValidationError(f"terminal-statuses.yaml: statuses[{idx}] missing required field 'value'")

        kind = entry.get("kind")
        if not kind:
            raise TerminalStatusValidationError(
                f"terminal-statuses.yaml: statuses[{idx}] (value={value!r}) missing required field 'kind'"
            )
        if kind not in _VALID_KINDS:
            raise TerminalStatusValidationError(
                f"terminal-statuses.yaml: statuses[{idx}] (value={value!r}) has invalid 'kind' "
                f"{kind!r}, expected one of {sorted(_VALID_KINDS)}"
            )

        phases = entry.get("phases")
        if not isinstance(phases, list) or len(phases) == 0:
            raise TerminalStatusValidationError(
                f"terminal-statuses.yaml: statuses[{idx}] (value={value!r}) 'phases' must be a non-empty list"
            )
        if not all(isinstance(p, str) for p in phases):
            raise TerminalStatusValidationError(
                f"terminal-statuses.yaml: statuses[{idx}] (value={value!r}) 'phases' must be a list of strings"
            )

        if value in seen_values:
            raise TerminalStatusValidationError(
                f"terminal-statuses.yaml: duplicate 'value' {value!r} (statuses[{idx}])"
            )
        seen_values.add(value)


def load_terminal_statuses(repo_root: Path) -> list[dict]:
    """Load, validate, and return the `statuses` list from agent-orchestration/terminal-statuses.yaml.

    `repo_root` is the repository root — the file itself is
    `repo_root / "agent-orchestration" / "terminal-statuses.yaml"`.
    """
    path = repo_root / "agent-orchestration" / "terminal-statuses.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_terminal_statuses(data)
    return data["statuses"]

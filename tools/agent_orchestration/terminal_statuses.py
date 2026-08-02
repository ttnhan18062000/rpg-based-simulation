"""Provider-neutral validation for agent-orchestration/terminal-statuses.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_VALID_KINDS = {"literal", "verdict_derived", "bypass"}


class TerminalStatusValidationError(Exception):
    pass


def validate_terminal_statuses(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise TerminalStatusValidationError("terminal-statuses.yaml: YAML root is not a mapping")
    if data.get("terminal_status_schema_version") != 1:
        raise TerminalStatusValidationError("terminal-statuses.yaml: 'terminal_status_schema_version' missing or not 1")
    if not isinstance(data.get("workflow_id"), str) or not data["workflow_id"]:
        raise TerminalStatusValidationError("terminal-statuses.yaml: missing required field 'workflow_id'")
    statuses = data.get("statuses")
    if not isinstance(statuses, list) or not statuses:
        raise TerminalStatusValidationError("terminal-statuses.yaml: 'statuses' must be a non-empty list")
    seen = set()
    for index, entry in enumerate(statuses):
        if not isinstance(entry, dict):
            raise TerminalStatusValidationError(f"terminal-statuses.yaml: statuses[{index}] is not a mapping")
        value, kind, phases = entry.get("value"), entry.get("kind"), entry.get("phases")
        if not isinstance(value, str) or not value:
            raise TerminalStatusValidationError(f"terminal-statuses.yaml: statuses[{index}] missing required field 'value'")
        if kind not in _VALID_KINDS:
            raise TerminalStatusValidationError(f"terminal-statuses.yaml: statuses[{index}] (value={value!r}) has invalid 'kind' {kind!r}")
        if not isinstance(phases, list) or not phases or not all(isinstance(p, str) for p in phases):
            raise TerminalStatusValidationError(f"terminal-statuses.yaml: statuses[{index}] (value={value!r}) 'phases' must be a non-empty list of strings")
        if value in seen:
            raise TerminalStatusValidationError(f"terminal-statuses.yaml: duplicate 'value' {value!r}")
        seen.add(value)


def load_terminal_statuses(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / "agent-orchestration" / "terminal-statuses.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_terminal_statuses(data)
    return data["statuses"]

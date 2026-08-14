"""Standalone schema/shape validation tests for terminal-statuses.yaml
(TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, Review-phase Fix A).

Independent of Step 2's live-extraction comparison tests: exercises
`validate_terminal_statuses` directly against (a) the real committed
agent-orchestration/terminal-statuses.yaml, which must pass cleanly, and (b) a table of synthetic
malformed fixtures, each asserted to raise `TerminalStatusValidationError` naming the specific
field/entry at fault.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from tools.agent_orchestration_claude_adapter.terminal_status_loader import (
    TerminalStatusValidationError,
    load_terminal_statuses,
    validate_terminal_statuses,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_REAL_TERMINAL_STATUSES_PATH = _REPO_ROOT / "agent-orchestration" / "terminal-statuses.yaml"


def _load_real_data() -> dict:
    return yaml.safe_load(_REAL_TERMINAL_STATUSES_PATH.read_text(encoding="utf-8"))


def test_real_committed_terminal_statuses_yaml_passes_validation_cleanly():
    data = _load_real_data()
    validate_terminal_statuses(data)  # must not raise


def test_load_terminal_statuses_returns_15_entries_from_real_repo_root():
    statuses = load_terminal_statuses(_REPO_ROOT)
    assert len(statuses) == 15


def test_missing_schema_version_raises():
    data = _load_real_data()
    del data["terminal_status_schema_version"]
    with pytest.raises(TerminalStatusValidationError, match="terminal_status_schema_version"):
        validate_terminal_statuses(data)


def test_wrong_schema_version_raises():
    data = _load_real_data()
    data["terminal_status_schema_version"] = 2
    with pytest.raises(TerminalStatusValidationError, match="terminal_status_schema_version"):
        validate_terminal_statuses(data)


def test_missing_workflow_id_raises():
    data = _load_real_data()
    del data["workflow_id"]
    with pytest.raises(TerminalStatusValidationError, match="workflow_id"):
        validate_terminal_statuses(data)


def test_empty_statuses_list_raises():
    data = _load_real_data()
    data["statuses"] = []
    with pytest.raises(TerminalStatusValidationError, match="statuses"):
        validate_terminal_statuses(data)


def test_missing_statuses_key_raises():
    data = _load_real_data()
    del data["statuses"]
    with pytest.raises(TerminalStatusValidationError, match="statuses"):
        validate_terminal_statuses(data)


def test_entry_missing_kind_raises():
    data = _load_real_data()
    data["statuses"] = copy.deepcopy(data["statuses"])
    del data["statuses"][0]["kind"]
    with pytest.raises(TerminalStatusValidationError, match="kind"):
        validate_terminal_statuses(data)


def test_entry_invalid_kind_enum_value_raises():
    data = _load_real_data()
    data["statuses"] = copy.deepcopy(data["statuses"])
    data["statuses"][0]["kind"] = "not_a_real_kind"
    with pytest.raises(TerminalStatusValidationError, match="invalid 'kind'"):
        validate_terminal_statuses(data)


def test_entry_missing_value_raises():
    data = _load_real_data()
    data["statuses"] = copy.deepcopy(data["statuses"])
    del data["statuses"][0]["value"]
    with pytest.raises(TerminalStatusValidationError, match="value"):
        validate_terminal_statuses(data)


def test_entry_missing_phases_raises():
    data = _load_real_data()
    data["statuses"] = copy.deepcopy(data["statuses"])
    del data["statuses"][0]["phases"]
    with pytest.raises(TerminalStatusValidationError, match="phases"):
        validate_terminal_statuses(data)


def test_entry_empty_phases_list_raises():
    data = _load_real_data()
    data["statuses"] = copy.deepcopy(data["statuses"])
    data["statuses"][0]["phases"] = []
    with pytest.raises(TerminalStatusValidationError, match="phases"):
        validate_terminal_statuses(data)


def test_duplicate_value_raises():
    data = _load_real_data()
    data["statuses"] = copy.deepcopy(data["statuses"])
    duplicate_entry = copy.deepcopy(data["statuses"][0])
    data["statuses"].append(duplicate_entry)
    with pytest.raises(TerminalStatusValidationError, match="duplicate"):
        validate_terminal_statuses(data)

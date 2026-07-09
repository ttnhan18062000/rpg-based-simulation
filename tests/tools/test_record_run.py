"""Tests for tools/agent-monitoring/record_run.py's non-null required-field
enforcement (TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT).

Covers both the pure `validate_record` function directly and the CLI's exit-code
contract via subprocess, mirroring test_validate_frontmatter.py's Group 7 pattern.
"""
import json
import subprocess
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from record_run import validate_record  # noqa: E402

_RECORD_PATH = _MONITORING_TOOLS_DIR / "record_run.py"

_VALID_RECORD = {
    "run_id": "TCK-FAKE-RUN",
    "start_ts": "2026-07-08T00:00:00Z",
    "workflow": "implement-ticket",
    "tier": "standard",
    "final_status": "DONE",
}


def test_valid_record_has_no_errors():
    assert validate_record(dict(_VALID_RECORD)) == []


def test_missing_key_rejected():
    record = dict(_VALID_RECORD)
    del record["workflow"]
    errors = validate_record(record)
    assert errors == ["Missing required fields: ['workflow']"]


def test_null_required_field_rejected_identically_to_missing_key():
    record = dict(_VALID_RECORD)
    record["workflow"] = None
    errors = validate_record(record)
    assert errors == ["Missing required fields: ['workflow']"]


def test_multiple_null_fields_all_reported():
    record = dict(_VALID_RECORD)
    record["workflow"] = None
    record["tier"] = None
    errors = validate_record(record)
    assert errors == ["Missing required fields: ['tier', 'workflow']"]


def test_falsy_but_non_null_value_still_passes():
    # is-None check, not a truthiness check — an empty-string final_status is
    # a schema-shape question outside this ticket's scope, not a null-check failure.
    record = dict(_VALID_RECORD)
    record["final_status"] = ""
    assert validate_record(record) == []


class TestExitCodeContract:
    def _run(self, data: dict):
        return subprocess.run(
            [sys.executable, str(_RECORD_PATH), "--data", json.dumps(data)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

    def test_exit_1_on_null_required_field(self, tmp_path, monkeypatch):
        result = self._run({**_VALID_RECORD, "workflow": None})
        assert result.returncode == 1
        assert "Missing required fields" in result.stderr
        assert "workflow" in result.stderr

    def test_exit_1_matches_missing_key_exit_code(self):
        record = dict(_VALID_RECORD)
        del record["workflow"]
        missing_key_result = self._run(record)
        null_result = self._run({**_VALID_RECORD, "workflow": None})
        assert missing_key_result.returncode == null_result.returncode == 1

"""Tests for tools/agent-monitoring/record_run.py's non-null required-field
enforcement (TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT) and write-time
duration_s computation (TCK-20260709-AGENT-MONITORING-DURATION).

Covers both the pure `validate_record`/`compute_duration_s` functions directly
and the CLI's exit-code contract via subprocess, mirroring
test_validate_frontmatter.py's Group 7 pattern.
"""
import json
import subprocess
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import record_run  # noqa: E402
from record_run import compute_duration_s, validate_record  # noqa: E402

_RECORD_PATH = _MONITORING_TOOLS_DIR / "record_run.py"

_VALID_RECORD = {
    "run_id": "TCK-FAKE-RUN",
    "start_ts": "2026-07-08T00:00:00Z",
    "workflow": "implement-ticket",
    "tier": "standard",
    "final_status": "DONE",
    "agent_count": 1,
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


def test_missing_agent_count_rejected():
    # TCK-... (2026-07-20 orchestration audit): docs/agent-monitoring/schema.md documents
    # agent_count as Nullable: No, but record_run.py's REQUIRED set previously omitted it —
    # not manifesting in production (all 4 real callers pass it) but a real contract mismatch.
    record = dict(_VALID_RECORD)
    del record["agent_count"]
    errors = validate_record(record)
    assert errors == ["Missing required fields: ['agent_count']"]


def test_null_agent_count_rejected():
    record = dict(_VALID_RECORD)
    record["agent_count"] = None
    errors = validate_record(record)
    assert errors == ["Missing required fields: ['agent_count']"]


def test_agent_count_zero_is_falsy_but_valid():
    # 0 is a legitimate agent_count (e.g. a crashed run with no agent calls yet) — must not be
    # treated as missing, mirroring test_falsy_but_non_null_value_still_passes's is-None check.
    record = dict(_VALID_RECORD)
    record["agent_count"] = 0
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


# ---------------------------------------------------------------------------
# TCK-20260709-AGENT-MONITORING-DURATION — write-time duration_s computation
# ---------------------------------------------------------------------------

def test_compute_duration_s_from_valid_start_and_end():
    record = {**_VALID_RECORD, "start_ts": "2026-07-08T10:00:00Z", "end_ts": "2026-07-08T10:48:30Z"}
    assert compute_duration_s(record) == 2910


def test_compute_duration_s_none_when_end_ts_missing():
    record = dict(_VALID_RECORD)
    assert "end_ts" not in record
    assert compute_duration_s(record) is None


def test_compute_duration_s_none_when_end_ts_null():
    record = {**_VALID_RECORD, "end_ts": None}
    assert compute_duration_s(record) is None


class TestDurationWrittenToRecord:
    def _run_and_read(self, data: dict, tmp_path):
        result = subprocess.run(
            [sys.executable, str(_RECORD_PATH), "--data", json.dumps(data)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        written = json.loads((tmp_path / "agent-monitoring" / "runs.jsonl").read_text().strip())
        return written

    def test_duration_s_computed_and_written(self, tmp_path):
        record = {
            **_VALID_RECORD,
            "start_ts": "2026-07-08T10:00:00Z",
            "end_ts": "2026-07-08T10:48:30Z",
        }
        written = self._run_and_read(record, tmp_path)
        assert written["duration_s"] == 2910

    def test_duration_s_null_when_end_ts_absent(self, tmp_path):
        record = dict(_VALID_RECORD)
        written = self._run_and_read(record, tmp_path)
        assert written["duration_s"] is None

    def test_computed_duration_s_overrides_caller_supplied_value(self, tmp_path):
        record = {
            **_VALID_RECORD,
            "start_ts": "2026-07-08T10:00:00Z",
            "end_ts": "2026-07-08T10:48:30Z",
            "duration_s": 99999,
        }
        written = self._run_and_read(record, tmp_path)
        assert written["duration_s"] == 2910


# ---------------------------------------------------------------------------
# TCK-20260721-MONITORING-WRITER-UNIFICATION — shared writer migration
# ---------------------------------------------------------------------------


def test_execution_identity_fields_pass_through_unchanged(tmp_path):
    record = {
        **_VALID_RECORD,
        "execution_id": "claude-TCK-FAKE-RUN-1234567890-abcd1234",
        "provider": "claude",
        "ticket_id": "TCK-FAKE-RUN",
    }
    result = subprocess.run(
        [sys.executable, str(_RECORD_PATH), "--data", json.dumps(record)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    written = json.loads((tmp_path / "agent-monitoring" / "runs.jsonl").read_text().strip())
    assert written["execution_id"] == "claude-TCK-FAKE-RUN-1234567890-abcd1234"
    assert written["provider"] == "claude"
    assert written["ticket_id"] == "TCK-FAKE-RUN"


def test_append_failure_is_non_blocking(tmp_path, monkeypatch, capsys):
    # An append-layer failure (post-validation) must not sys.exit(1) — that
    # code path is reserved for validation failures, which happen before
    # write_line is ever called. This distinguishes WARNING+exit-0 (append
    # failure) from ERROR+exit-1 (validation failure).
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(record_run, "write_line", lambda *a, **kw: False)
    monkeypatch.setattr(sys, "argv", ["record_run.py", "--data", json.dumps(dict(_VALID_RECORD))])

    record_run.main()  # must not raise SystemExit

    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "DONE:" in captured.out

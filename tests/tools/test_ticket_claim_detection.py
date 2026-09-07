"""Tests for TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING.

`tools/agent-monitoring/ticket_claim_detection.py` is a read-only, log-only, always-on check
wired into `implement-ticket.js`'s Scope phase (immediately after `const tid =
ticketInfo.ticket_id`). It enumerates other sessions' `.claude/current_run.*` sidecar files
(reusing `post_tool_hook.py`'s own glob pattern, not its function) and flags a detection — never
a block/refusal — when another session's scoped sidecar has both `run_id == tid` AND an mtime
within `CLAIM_DETECTION_WINDOW_SECONDS` (900s) of now.

Imports the module directly (it is a plain function module, unlike post_tool_hook.py which
executes on import) and drives it against `tmp_path` fixtures — never the real `.claude/` or
`agent-monitoring/data/` directories. `claude_dir`/`data_dir`/`window_seconds`/`own_session_id`
are all injectable parameters for exactly this reason.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import ticket_claim_detection  # noqa: E402
from ticket_claim_detection import check_and_log, _find_concurrent_claimants  # noqa: E402

_TID = "TCK-20260907-EXAMPLE-TICKET"


def _write_sidecar(claude_dir: Path, session_id: str, run_id, age_seconds: float = 0.0) -> Path:
    claude_dir.mkdir(parents=True, exist_ok=True)
    path = claude_dir / f"current_run.{session_id}"
    path.write_text(json.dumps({
        "run_id": run_id, "seq": 1, "phase": "Implement", "agent": "implementer",
        "execution_id": f"claude-{run_id}-abc", "provider": "claude",
    }))
    if age_seconds:
        now = time.time()
        import os
        os.utime(path, (now - age_seconds, now - age_seconds))
    return path


def _iso_week_dir(data_dir: Path) -> Path:
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    return data_dir / iso_week


def test_two_concurrent_session_sidecars_for_same_ticket_produce_one_detection(tmp_path):
    claude_dir = tmp_path / ".claude"
    data_dir = tmp_path / "agent-monitoring" / "data"
    _write_sidecar(claude_dir, "sess-other", _TID)

    record = check_and_log(
        _TID, claude_dir=claude_dir, data_dir=data_dir,
        own_session_id="sess-self",
    )

    assert record is not None
    assert record["ticket_id"] == _TID
    assert record["other_session_ids"] == ["sess-other"]

    lines = (_iso_week_dir(data_dir) / "claim_detections.jsonl").read_text().splitlines()
    assert len(lines) == 1
    written = json.loads(lines[0])
    assert written["ticket_id"] == _TID
    assert written["other_session_ids"] == ["sess-other"]


def test_single_session_sidecar_produces_zero_detections(tmp_path):
    claude_dir = tmp_path / ".claude"
    data_dir = tmp_path / "agent-monitoring" / "data"
    _write_sidecar(claude_dir, "sess-self", _TID)

    record = check_and_log(
        _TID, claude_dir=claude_dir, data_dir=data_dir,
        own_session_id="sess-self",
    )

    assert record is None
    assert not (_iso_week_dir(data_dir) / "claim_detections.jsonl").exists()


def test_instrumentation_never_raises_on_malformed_sidecar(tmp_path):
    claude_dir = tmp_path / ".claude"
    data_dir = tmp_path / "agent-monitoring" / "data"
    claude_dir.mkdir(parents=True, exist_ok=True)

    (claude_dir / "current_run.sess-bad-json").write_text("{not valid json")
    (claude_dir / "current_run.sess-no-run-id").write_text(json.dumps({"seq": 1}))

    record = check_and_log(
        _TID, claude_dir=claude_dir, data_dir=data_dir,
        own_session_id="sess-self",
    )

    assert record is None  # no exception propagated, no false detection either


def test_instrumentation_never_blocks_or_raises_regardless_of_detection_outcome():
    source = (_MONITORING_TOOLS_DIR / "ticket_claim_detection.py").read_text(encoding="utf-8")
    assert "ClaimRefusedError" not in source
    # No actual `raise` statement anywhere in the module's real code — only doc/comment mentions
    # of "raises"/"Never raises" survive this check (they don't start with "raise ").
    code_lines = [line for line in source.splitlines() if not line.strip().startswith(("#", '"""'))]
    assert not any(line.strip().startswith("raise ") or line.strip() == "raise" for line in code_lines)

    workflow_source = _WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        'await bash(`python3 tools/agent-monitoring/ticket_claim_detection.py "${tid}" 2>/dev/null || true`)'
        in workflow_source
    )


def test_stale_sidecar_outside_short_window_does_not_false_positive(tmp_path):
    claude_dir = tmp_path / ".claude"
    data_dir = tmp_path / "agent-monitoring" / "data"
    # 30 minutes stale — well past the 15-minute detection window, well short of the unrelated
    # 24-hour post_tool_hook.py prune threshold, so this test is unambiguous about which
    # mechanism it exercises.
    _write_sidecar(claude_dir, "sess-stale", _TID, age_seconds=30 * 60)

    record = check_and_log(
        _TID, claude_dir=claude_dir, data_dir=data_dir,
        own_session_id="sess-self",
    )

    assert record is None


def test_own_session_sidecar_excluded_from_detection(tmp_path):
    claude_dir = tmp_path / ".claude"
    data_dir = tmp_path / "agent-monitoring" / "data"
    _write_sidecar(claude_dir, "sess-self", _TID)

    record = check_and_log(
        _TID, claude_dir=claude_dir, data_dir=data_dir,
        own_session_id="sess-self",
    )

    assert record is None


def test_ad_hoc_null_sentinel_sidecar_never_counted_as_a_claim(tmp_path):
    claude_dir = tmp_path / ".claude"
    data_dir = tmp_path / "agent-monitoring" / "data"
    # TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION sentinel shape.
    _write_sidecar(claude_dir, "sess-sentinel", None)

    record = check_and_log(
        _TID, claude_dir=claude_dir, data_dir=data_dir,
        own_session_id="sess-self",
    )

    assert record is None


def test_detection_record_written_to_dedicated_jsonl_not_runs_or_events(tmp_path):
    claude_dir = tmp_path / ".claude"
    data_dir = tmp_path / "agent-monitoring" / "data"
    _write_sidecar(claude_dir, "sess-other", _TID)

    check_and_log(_TID, claude_dir=claude_dir, data_dir=data_dir, own_session_id="sess-self")

    week_dir = _iso_week_dir(data_dir)
    assert (week_dir / "claim_detections.jsonl").exists()
    assert not (week_dir / "runs.jsonl").exists()
    assert not (week_dir / "events.jsonl").exists()


def test_find_concurrent_claimants_requires_both_run_id_and_window_match(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    # Fresh but unrelated ticket -> excluded by run_id check alone.
    _write_sidecar(claude_dir, "sess-unrelated", "TCK-OTHER-TICKET")
    # Matching run_id but stale -> excluded by window check alone.
    _write_sidecar(claude_dir, "sess-stale-match", _TID, age_seconds=30 * 60)
    # Matching run_id and fresh -> the only real match.
    _write_sidecar(claude_dir, "sess-real-match", _TID)

    matches = _find_concurrent_claimants(
        _TID, claude_dir=claude_dir, own_session_id="sess-self",
        window_seconds=ticket_claim_detection.CLAIM_DETECTION_WINDOW_SECONDS, now=time.time(),
    )

    assert [m["session_id"] for m in matches] == ["sess-real-match"]


def test_empty_tid_produces_no_detection_and_no_write(tmp_path):
    claude_dir = tmp_path / ".claude"
    data_dir = tmp_path / "agent-monitoring" / "data"
    _write_sidecar(claude_dir, "sess-other", "")

    record = check_and_log("", claude_dir=claude_dir, data_dir=data_dir, own_session_id="sess-self")

    assert record is None
    assert not data_dir.exists() or not any(data_dir.rglob("claim_detections.jsonl"))

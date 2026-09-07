"""tools/agent-monitoring/ticket_claim_detection.py — log-only ticket-claim detection
(TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING).

Read-only over .claude/current_run.* sidecars; never writes/deletes a sidecar. Never raises.
No blocking/refusal of any kind — see
docs/plans/agent_infrastructure/ai_first_hardening_epics/ticket_claim_detection_experiment.md
for the full rationale, including the documented false-negative gap in the 900-second window
(measured against the other session's last phase-transition sidecar write, not its continuous
activity — not fixed by widening this constant, see that doc's Known Limitations).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_MONITORING_DIR = Path(__file__).resolve().parent
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))

from writer import write_line  # noqa: E402

CLAIM_DETECTION_WINDOW_SECONDS = 900  # 15 minutes — see experiment doc for rationale/tradeoff


def _iso_week(now: datetime) -> str:
    return now.strftime("%G-W%V")


def _own_sidecar_name(own_session_id: str) -> str:
    return f"current_run.{own_session_id}"


def _find_concurrent_claimants(
    tid: str,
    *,
    claude_dir: Path,
    own_session_id: str,
    window_seconds: int,
    now: float,
) -> list[dict]:
    """Returns a list of {"session_id": ..., "path": ...} for every OTHER scoped sidecar whose
    run_id == tid and whose mtime is within window_seconds of `now`. Never raises — any per-file
    read/parse/stat error is skipped, not propagated (matches post_tool_hook.py's own
    try/except-per-file convention)."""
    matches: list[dict] = []
    own_name = _own_sidecar_name(own_session_id) if own_session_id else None
    try:
        candidates = list(claude_dir.glob("current_run.*"))
    except Exception:
        return matches
    for path in candidates:
        try:
            if own_name and path.name == own_name:
                continue
            if path.name == "current_run":
                continue  # legacy unscoped file carries no reliable single-session identity
            if now - path.stat().st_mtime > window_seconds:
                continue
            data = json.loads(path.read_text())
            run_id = data.get("run_id")
            if run_id != tid:
                continue
            session_id = path.name[len("current_run."):]
            matches.append({"session_id": session_id, "path": str(path)})
        except Exception:
            continue
    return matches


def check_and_log(
    tid: str,
    *,
    claude_dir: Path = Path(".claude"),
    data_dir: Path = Path("agent-monitoring/data"),
    window_seconds: int = CLAIM_DETECTION_WINDOW_SECONDS,
    own_session_id: str | None = None,
) -> dict | None:
    """Checks for other concurrent sessions on the same ticket ID; writes exactly one detection
    record (if any match found) to agent-monitoring/data/<iso-week>/claim_detections.jsonl. Never
    raises. Returns the written record dict for tests, or None if nothing was detected/written."""
    try:
        if not tid:
            return None
        sid = own_session_id if own_session_id is not None else os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        now_epoch = time.time()
        matches = _find_concurrent_claimants(
            tid, claude_dir=claude_dir, own_session_id=sid,
            window_seconds=window_seconds, now=now_epoch,
        )
        if not matches:
            return None
        now_dt = datetime.now(timezone.utc)
        record = {
            "ticket_id": tid,
            "ts": now_dt.isoformat().replace("+00:00", "Z"),
            "detecting_session_id": sid or None,
            "other_session_ids": [m["session_id"] for m in matches],
            "window_seconds": window_seconds,
            "sidecar_files": [m["path"] for m in matches],
        }
        target = data_dir / _iso_week(now_dt) / "claim_detections.jsonl"
        # write_line()'s own lock-acquire step runs before its internal mkdir, so the parent
        # directory must already exist (matches record_run.py/post_tool_hook.py's identical
        # pre-mkdir convention before calling write_line()).
        target.parent.mkdir(parents=True, exist_ok=True)
        write_line(target, json.dumps(record, separators=(",", ":")))
        return record
    except Exception:
        return None


if __name__ == "__main__":
    try:
        _tid = sys.argv[1] if len(sys.argv) > 1 else ""
        check_and_log(_tid)
    except Exception:
        pass

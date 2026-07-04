#!/usr/bin/env python3
"""PostToolUse hook: nudges to run /agent-monitoring-retro once enough
implement-ticket runs have completed DONE since the last dated retro report.

Advisory only — never raises, never blocks the tool call. Fires at most once
per session (tracked via a small state file keyed by session_id from the hook
payload, matching the pattern in pre_tool_hook.py / post_tool_hook.py).
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

THRESHOLD = 5
RUNS_FILE = Path("agent-monitoring/runs.jsonl")
RETRO_DIR = Path("agent-monitoring/retro")
STATE_FILE = Path(".claude/.retro_nudge_state.json")
COOLDOWN_S = 3600  # fallback only, used if no session_id is available


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _last_dated_retro_mtime() -> float:
    dated = [p for p in RETRO_DIR.glob("RETRO-*.md") if p.name != "RETRO-ALL.md"]
    if not dated:
        return 0.0  # no dated report has ever existed -> threshold already crossed
    return max(p.stat().st_mtime for p in dated)


def _count_done_since(cutoff: float) -> int:
    if not RUNS_FILE.exists():
        return 0
    count = 0
    for line in RUNS_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except Exception:
            continue
        workflow = record.get("workflow") or record.get("agent")
        status = record.get("final_status") or record.get("status")
        start_ts = record.get("start_ts") or record.get("started_at")
        if workflow != "implement-ticket" or status != "DONE" or not start_ts:
            continue
        try:
            ts = datetime.fromisoformat(str(start_ts).replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        if ts > cutoff:
            count += 1
    return count


try:
    payload = json.load(sys.stdin)
    session_id = payload.get("session_id", "")

    state = _load_state()
    now = time.time()
    if session_id and state.get("session_id") == session_id:
        sys.exit(0)
    if not session_id and now - state.get("ts", 0) < COOLDOWN_S:
        sys.exit(0)

    cutoff = _last_dated_retro_mtime()
    count = _count_done_since(cutoff)

    if count >= THRESHOLD:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"session_id": session_id, "ts": now}))
        message = (
            f"agent-monitoring-retro: {count} implement-ticket runs have completed "
            f"DONE since the last dated retro report (threshold {THRESHOLD}). "
            "Run /agent-monitoring-retro to review the accumulated data."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": message,
            }
        }))
except Exception:
    pass

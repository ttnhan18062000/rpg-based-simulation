"""Measures `agent-monitoring/data/*/tools.jsonl` run_id attribution coverage
(TCK-20260915-SIDECAR-ATTRIBUTION-GAP, child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).

**This module used to also gate on the rate (a floor ratchet); that gate was removed by
TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE (2026-09-16). Do not rebuild it.**

The rate is a rolling-14-day corpus-wide percentage. It tracks the *mix* of hand-orchestrated vs.
pipeline-driven work in that window, not defect presence: hand-orchestrated closures never open a
`run_id` at all (by design -- see `record_hand_orchestrated_closure.py`), so any batch of
sanctioned hand-orchestration drags the rate down exactly as hard as a real regression would, and
recovers only as old pipeline-heavy days age out of the window. Six successive re-pins (74.7 ->
73.7 -> 73.6 -> 73.5 -> 73.4 -> 72.7 -> 72.6) never converged, the absolute-count variant swung
0 -> 1,492 -> 2,044 -> 595 day to day tracking the same working-style mix, and one re-pin attempt
required editing this module's own guard test to accept a lowered floor -- the exact anti-pattern
that test existed to prevent. No threshold over this number can distinguish "attribution is
breaking" from "hand-orchestration is sanctioned and happening" -- they produce the same signal.

The measurement itself stays, since the rate is genuinely informative in `RETRO-*.md`. If a real
detector is wanted, scope it to a population where attribution is *expected* to hold: pipeline
runs that opened a `run_id` whose own tool rows lack one (expected zero, so nonzero is a true
defect) -- not this corpus-wide rate. That is a different, narrower check and belongs in its own
ticket with its own measured baseline.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
for _dir in (str(_TOOLS_DIR), str(_MONITORING_TOOLS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from generate_retro import _load_source, DEFAULT_TOOLS_FILE  # noqa: E402

WINDOW_DAYS = 14


def compute_attribution_rate(tools: List[dict] = None, window_days: int = WINDOW_DAYS):
    """Returns (rate_pct, attributed_count, total_count) over the last `window_days` days of
    real tool rows. `tools` defaults to the real corpus when not supplied -- tests inject a
    synthetic list instead of touching the real `agent-monitoring/data/` shards."""
    if tools is None:
        tools = _load_source(DEFAULT_TOOLS_FILE, "tools")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    recent = [t for t in tools if t.get("ts") and t["ts"] >= cutoff]
    total = len(recent)
    if total == 0:
        return (None, 0, 0)
    attributed = sum(1 for t in recent if t.get("run_id"))
    return (round(100 * attributed / total, 1), attributed, total)


if __name__ == "__main__":
    rate, attributed, total = compute_attribution_rate()
    if rate is None:
        evidence = "no tool rows in the last 14 days -- nothing to measure"
    else:
        evidence = f"attribution rate {rate}% ({attributed}/{total} tool rows over the last {WINDOW_DAYS} days)"
    result = [{"status": "PASS", "evidence": evidence}]
    print("MARKER:" + json.dumps(result))

#!/usr/bin/env python3
"""Pure, read-time active/idle duration split for a single run (TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT).

Never mutates runs.jsonl/events.jsonl — a run's naive `duration_s` (end_ts - start_ts) doesn't
distinguish real working time from idle gaps between phase transitions (session pauses, long
human-review waits, etc.), which distorts what "slow" means in generate_retro.py's Slow Runs /
Duration outliers reporting and retrieval_baseline_metrics.py's one-off snapshot.

Two judgment calls (real decisions, not derived law — see staging_artifacts/
TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT/investigation.md for the full evidence):

1. Pause threshold: 1800s (30 min), reusing generate_retro.py's own existing "Slow Runs" absolute
   threshold (`duration_s > 1800`) for conceptual consistency, and falling inside this ticket's own
   real gap-distribution data (p90=19min, p95=43.5min across 5960 real gaps).
2. start_ts/end_ts ARE included as timeline boundaries, not just strict inter-event gaps: a gap
   between start_ts and the first logged event (or the last event and end_ts) is measured and
   classified by the same threshold as any mid-run gap. This is required by this module's own
   invariant (active_duration_s + idle_gap_s == total_duration_s) -- excluding boundary gaps would
   silently omit them from both totals. Real corpus rows exist where the dominant gap is a
   run-start-to-first-event gap, not a mid-run transition.

`active_duration_s` is defined as `total_duration_s - idle_gap_s` (the complement of idle time
within the run's own known span), not independently re-summed from the "active" gaps -- so the
sum invariant holds by construction regardless of out-of-order or boundary-adjacent event data.
"""
from __future__ import annotations

from datetime import datetime

PAUSE_THRESHOLD_SECONDS = 1800  # 30 min; see module docstring, decision 1.


def _parse_ts(ts_str):
    """Returns a timezone-aware datetime, or None if ts_str is missing/non-string/unparseable.

    Matches the datetime.fromisoformat(ts_str.replace("Z", "+00:00")) pattern already used
    throughout tools/agent-monitoring/*.py (generate_retro.py, post_tool_hook.py, record_run.py,
    epic_staleness_check.py, retro_nudge_hook.py) -- never raises.
    """
    if not isinstance(ts_str, str):
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def compute_active_idle_split(
    start_ts, end_ts, events, pause_threshold_s: float = PAUSE_THRESHOLD_SECONDS
) -> dict | None:
    """Computes the active/idle duration split for one run.

    Args:
        start_ts: the run's runs.jsonl start_ts (ISO 8601 string).
        end_ts: the run's runs.jsonl end_ts (ISO 8601 string).
        events: that run's events.jsonl rows (any order -- sorted here strictly by `ts`, never
            `seq`, since seq resets across pause/resume sessions and cannot be trusted for
            ordering). Rows with missing/non-string/unparseable `ts` are skipped, not crashed on.
        pause_threshold_s: a gap at or above this many seconds counts as idle_gap_s; below it,
            the gap counts toward active_duration_s. Defaults to PAUSE_THRESHOLD_SECONDS.

    Returns:
        None if start_ts or end_ts itself is missing/unparseable (caller should fall back to raw
        duration_s only). Otherwise a dict:
            total_duration_s: end_ts - start_ts, in seconds (>= 0).
            active_duration_s: total_duration_s - idle_gap_s (the complement; invariant holds by
                construction).
            idle_gap_s: sum of all gaps (including the start-to-first-event and
                last-event-to-end boundary gaps) at or above pause_threshold_s.
            largest_gap_s: the single largest gap found, in seconds.
            largest_gap_from / largest_gap_to: labels for the two boundary points of that gap --
                "start"/"end" for the run's own timeline edges, or "<phase>:<agent>" for a real
                event -- letting a caller report e.g. "Investigate:investigator -> Plan:planner".
            pause_threshold_s: the threshold actually used, echoed back for transparency.
    """
    start_dt = _parse_ts(start_ts)
    end_dt = _parse_ts(end_ts)
    if start_dt is None or end_dt is None:
        return None

    points = [(start_dt, "start")]
    for e in events:
        dt = _parse_ts(e.get("ts"))
        if dt is None:
            continue
        label = f"{e.get('phase', '?')}:{e.get('agent', '?')}"
        points.append((dt, label))
    points.append((end_dt, "end"))
    points.sort(key=lambda p: p[0])  # strictly by ts -- never seq (may collide across pause/resume)

    total_duration_s = max((end_dt - start_dt).total_seconds(), 0.0)

    idle_gap_s = 0.0
    largest_gap_s = 0.0
    largest_gap_from = None
    largest_gap_to = None
    for (t1, l1), (t2, l2) in zip(points, points[1:]):
        gap = (t2 - t1).total_seconds()
        if gap <= 0:
            continue  # defensive: out-of-order/duplicate ts contributes nothing, never negative
        if gap >= pause_threshold_s:
            idle_gap_s += gap
        if gap > largest_gap_s:
            largest_gap_s = gap
            largest_gap_from, largest_gap_to = l1, l2

    active_duration_s = max(total_duration_s - idle_gap_s, 0.0)

    return {
        "total_duration_s": total_duration_s,
        "active_duration_s": active_duration_s,
        "idle_gap_s": idle_gap_s,
        "largest_gap_s": largest_gap_s,
        "largest_gap_from": largest_gap_from,
        "largest_gap_to": largest_gap_to,
        "pause_threshold_s": pause_threshold_s,
    }

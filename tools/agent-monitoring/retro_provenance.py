"""tools/agent-monitoring/retro_provenance.py: how the retro treats a run's duration and cost provenance
(TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE; fields from TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS and
-COST-ATTRIBUTION; owner decision 2026-10-06 recorded in TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN).

The rules, all report-only:
- the headline average duration uses measured and declared durations only: a run with `duration_source: tool_activity`
  is DERIVED and is averaged beside it, labelled, with its n; it is excluded from Slow Runs and duration outliers;
- a run with `duration_source: unknown` has a null duration, is COUNTED wherever an average is shown, and never averaged;
- a row with no `duration_source` is unlabelled (it predates the field) and keeps its old treatment;
- a `cost_source: session_window` event is one ticket-level total, not phase-resolved: it stays out of the spend tables and is
  reported on its own line.
Everything here is inert when no run carries `duration_source`, so reports for earlier weeks render unchanged.
"""
from __future__ import annotations

from datetime import datetime

SOURCES = ("declared", "tool_activity", "unknown")
LABELS = {"declared": "Declared", "tool_activity": "Derived (tool activity)", "unknown": "Unknown (not averaged)", "unlabelled": "Unlabelled (pre-field)"}


def source_of(run: dict) -> str:
    value = run.get("duration_source")
    return value if value in SOURCES else "unlabelled"


def is_derived(run: dict) -> bool:
    return run.get("duration_source") == "tool_activity"


def is_session_window(event: dict) -> bool:
    return event.get("cost_source") == "session_window"


def avg_minutes(runs: list[dict]) -> int | None:
    durations = [r["duration_s"] for r in runs if r.get("duration_s")]
    return int(sum(durations) / len(durations)) // 60 if durations else None


def _iso_week(run: dict) -> str | None:
    try:
        return datetime.fromisoformat(str(run.get("end_ts") or run.get("start_ts")).replace("Z", "+00:00")).strftime("%G-W%V")
    except ValueError:
        return None


def summary(runs: list[dict], events: list[dict]) -> dict | None:
    """The provenance block of the retro metrics, or None when no run in the window carries `duration_source`."""
    if not any(r.get("duration_source") for r in runs):
        return None
    hand = [r for r in runs if r.get("execution_mode") == "hand"]
    by_source = {s: [r for r in hand if source_of(r) == s] for s in (*SOURCES, "unlabelled")}  # hand closures only
    headline = [r for r in runs if not is_derived(r)]
    scored_runs = {e.get("run_id") for e in events if e.get("cost_proxy_score") is not None}
    weeks = sorted(w for w in (_iso_week(r) for r in runs if r.get("duration_source")) if w)
    return {
        "first_week": weeks[0] if weeks else None,
        "headline": {"n": len([r for r in headline if r.get("duration_s")]), "avg_min": avg_minutes(headline),
                     "unknown": len([r for r in runs if r.get("duration_source") == "unknown"])},
        "derived": {"n": len([r for r in runs if is_derived(r) and r.get("duration_s")]), "avg_min": avg_minutes([r for r in runs if is_derived(r)])},
        "by_source": {s: {"count": len(rs), "with_duration": len([r for r in rs if r.get("duration_s")]),
                          "avg_min": None if s == "unknown" else avg_minutes(rs)} for s, rs in by_source.items()},
        "hand_coverage": {"hand_runs": len(hand), "duration_known": len([r for r in hand if r.get("duration_s")]),
                          "cost_known": len([r for r in hand if r.get("run_id") in scored_runs])},
        "session_window": {"events": len([e for e in events if is_session_window(e)]),
                          "total": round(sum(e["cost_proxy_score"] for e in events if is_session_window(e) and e.get("cost_proxy_score") is not None), 1)},
    }


def _pct(n: int, total: int) -> str:
    return f"{round(100 * n / total)}%" if total else "n/a"


def top_note(p: dict) -> list[str]:
    return [f"_Duration provenance: from {p['first_week']} this report separates measured/declared durations from derived "
            "(tool-activity) ones and counts unknown ones without averaging them; averages in earlier reports are not comparable. "
            "Derived runs are excluded from Slow Runs and Duration outliers; `session_window` cost is one ticket-level total and is "
            "excluded from the Spend Proxy tables._", ""]


def run_summary_rows(p: dict) -> list[str]:
    h, d = p["headline"], p["derived"]
    avg = f"{h['avg_min']} min" if h["avg_min"] is not None else "n/a"
    d_avg = f"{d['avg_min']} min" if d["avg_min"] is not None else "n/a"
    return [f"| Avg duration (measured/declared, n={h['n']}) | {avg} (unknown, not averaged: {h['unknown']}) |",
            f"| Avg duration, derived from tool activity (n={d['n']}) | {d_avg} |"]


def by_source_lines(p: dict) -> list[str]:
    lines = ["**Hand-closed runs by duration source**", "", "| Source | Runs | With a duration | Avg duration |", "|---|---|---|---|"]
    for s in (*SOURCES, "unlabelled"):
        row = p["by_source"][s]
        avg = "not averaged" if s == "unknown" else (f"{row['avg_min']} min" if row["avg_min"] is not None else "n/a")
        lines.append(f"| {LABELS[s]} | {row['count']} | {row['with_duration']} | {avg} |")
    cov = p["hand_coverage"]
    lines += ["", f"_Hand-closed coverage: duration known for {cov['duration_known']} of {cov['hand_runs']} "
                  f"({_pct(cov['duration_known'], cov['hand_runs'])}); a cost value for {cov['cost_known']} of {cov['hand_runs']} "
                  f"({_pct(cov['cost_known'], cov['hand_runs'])})._", ""]
    return lines


def session_window_line(p: dict) -> list[str]:
    sw = p["session_window"]
    if not sw["events"]:
        return []
    return [f"_Derived ticket-level cost (`session_window`): {sw['events']} hand closure(s), total score {sw['total']}; not phase-resolved, "
            "not in the tables above._", ""]

#!/usr/bin/env python3
"""
Generate a weekly agent monitoring retro report.

Usage:
  python3 tools/agent-monitoring/generate_retro.py          # current ISO week
  python3 tools/agent-monitoring/generate_retro.py --days 30
  python3 tools/agent-monitoring/generate_retro.py --all
  python3 tools/agent-monitoring/generate_retro.py --week 2026-W23
"""
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

RUNS_FILE = Path("agent-monitoring/runs.jsonl")
EVENTS_FILE = Path("agent-monitoring/events.jsonl")
RETRO_DIR = Path("agent-monitoring/retro")


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def iso_week(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%G-W%V")
    except Exception:
        return "unknown"


def week_range(week_str):
    year, w = week_str.split("-W")
    monday = datetime.strptime(f"{year}-W{w}-1", "%G-W%V-%u").replace(tzinfo=timezone.utc)
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def current_week():
    return datetime.now(timezone.utc).strftime("%G-W%V")


def fmt_pct(n, total):
    if total == 0:
        return "0%"
    return f"{100 * n // total}%"


def generate(runs, events, label, week_str=None):
    events_by_run = defaultdict(list)
    for e in events:
        events_by_run[e.get("run_id", "")].append(e)

    total = len(runs)
    done_count = sum(1 for r in runs if r.get("final_status") == "DONE")
    gate_fails = [r for r in runs if r.get("final_status") not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS")]

    durations = [r["duration_s"] for r in runs if r.get("duration_s")]
    avg_dur = int(sum(durations) / len(durations)) if durations else 0
    avg_dur_min = avg_dur // 60

    agent_counts = [r.get("agent_count", 0) for r in runs if r.get("agent_count")]
    avg_agents = round(sum(agent_counts) / len(agent_counts), 1) if agent_counts else 0

    # Gate failure breakdown
    gate_counter = Counter(r.get("final_status") for r in gate_fails)

    # Tier distribution
    tier_counts = Counter(r.get("tier", "unknown") for r in runs)
    tier_done = defaultdict(int)
    for r in runs:
        if r.get("final_status") == "DONE":
            tier_done[r.get("tier", "unknown")] += 1

    # Agent status distribution
    agent_stats = defaultdict(lambda: Counter())
    for e in events:
        agent_stats[e.get("agent", "?")][e.get("status", "?")] += 1

    # Summary quality
    empty_summaries = sum(1 for e in events if not e.get("summary", "").strip())
    long_summaries = sum(1 for e in events if len(e.get("summary", "")) > 200)

    # Slow runs (> 30 min = 1800s)
    slow_runs = [r for r in runs if (r.get("duration_s") or 0) > 1800]

    # Build report
    lines = []
    lines.append(f"# Agent Monitoring Retro — {label}")
    if week_str:
        try:
            start, end = week_range(week_str)
            lines.append(f"\n_{start} → {end}_")
        except Exception:
            pass
    lines.append("")
    lines.append("---")
    lines.append("")

    # Run summary
    lines.append("## Run Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Total runs | {total} |")
    lines.append(f"| Completed (DONE) | {done_count} ({fmt_pct(done_count, total)}) |")
    lines.append(f"| Gate failures | {len(gate_fails)} |")
    lines.append(f"| Avg duration | {avg_dur_min} min |")
    lines.append(f"| Avg agents per run | {avg_agents} |")
    lines.append(f"| Total agent calls | {len(events)} |")
    lines.append("")

    # Gate failures
    lines.append("## Gate Failure Breakdown")
    lines.append("")
    if gate_counter:
        lines.append("| Gate | Count | % of runs |")
        lines.append("|---|---|---|")
        for gate, count in gate_counter.most_common():
            lines.append(f"| {gate} | {count} | {fmt_pct(count, total)} |")
    else:
        lines.append("_No gate failures this period._")
    lines.append("")

    # Tier distribution
    lines.append("## Tier Distribution")
    lines.append("")
    lines.append("| Tier | Count | DONE count | DONE rate |")
    lines.append("|---|---|---|---|")
    for tier in sorted(tier_counts):
        n = tier_counts[tier]
        d = tier_done[tier]
        lines.append(f"| {tier} | {n} | {d} | {fmt_pct(d, n)} |")
    lines.append("")

    # Agent status distribution
    lines.append("## Agent Status Distribution")
    lines.append("")
    if agent_stats:
        lines.append("| Agent | Calls | ok | failed | blocked | skipped |")
        lines.append("|---|---|---|---|---|---|")
        for agent in sorted(agent_stats):
            c = agent_stats[agent]
            total_calls = sum(c.values())
            lines.append(
                f"| {agent} | {total_calls} | {c.get('ok',0)} | "
                f"{c.get('failed',0)} | {c.get('blocked',0)} | {c.get('skipped',0)} |"
            )
    else:
        lines.append("_No events recorded._")
    lines.append("")

    # Summary quality
    lines.append("## Summary Quality")
    lines.append("")
    lines.append("| Issue | Count |")
    lines.append("|---|---|")
    lines.append(f"| Empty summary | {empty_summaries} |")
    lines.append(f"| Truncated (>200 chars) | {long_summaries} |")
    if empty_summaries > 0:
        lines.append("")
        lines.append(f"_⚠ {empty_summaries} empty summaries — check agent prompts for `summary` field._")
    lines.append("")

    # Slow runs
    lines.append("## Slow Runs (> 30 min)")
    lines.append("")
    if slow_runs:
        lines.append("| run_id | duration | final_status |")
        lines.append("|---|---|---|")
        for r in sorted(slow_runs, key=lambda x: x.get("duration_s", 0), reverse=True):
            dur_min = (r.get("duration_s", 0) or 0) // 60
            lines.append(f"| {r.get('run_id','')} | {dur_min} min | {r.get('final_status','')} |")
    else:
        lines.append("_No slow runs this period._")
    lines.append("")

    # Notes (human-written)
    lines.append("## Notes")
    lines.append("")
    lines.append("_Fill in after reviewing the report above. What patterns stand out? What to improve?_")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate agent monitoring retro report")
    parser.add_argument("--days", type=int, help="Include runs from the last N days")
    parser.add_argument("--all", action="store_true", help="Include all runs")
    parser.add_argument("--week", help="Specific ISO week (e.g. 2026-W23); default = current week")
    args = parser.parse_args()

    all_runs = load_jsonl(RUNS_FILE)
    all_events = load_jsonl(EVENTS_FILE)

    if args.all:
        runs = all_runs
        events = all_events
        label = "All Time"
        week_str = None
        out_name = "RETRO-ALL.md"
    elif args.days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()
        runs = [r for r in all_runs if (r.get("start_ts") or "") >= cutoff]
        run_ids = {r["run_id"] for r in runs}
        events = [e for e in all_events if e.get("run_id") in run_ids]
        label = f"Last {args.days} Days"
        week_str = None
        out_name = f"RETRO-LAST{args.days}D.md"
    else:
        week_str = args.week or current_week()
        runs = [r for r in all_runs if iso_week(r.get("start_ts", "")) == week_str]
        run_ids = {r["run_id"] for r in runs}
        events = [e for e in all_events if e.get("run_id") in run_ids]
        label = week_str
        out_name = f"RETRO-{week_str}.md"

    report = generate(runs, events, label, week_str)

    RETRO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RETRO_DIR / out_name
    out_path.write_text(report)
    print(f"Written: {out_path}")
    print(f"Runs: {len(runs)}, Events: {len(events)}")

    # Update index
    _update_index()


def _update_index():
    retro_files = sorted(RETRO_DIR.glob("RETRO-*.md"), reverse=True)
    retro_files = [f for f in retro_files if f.name != "index.md"]

    lines = ["# Agent Monitoring Retro Index", ""]
    lines.append("| Report | Runs | DONE | Gate failures |")
    lines.append("|---|---|---|---|")

    all_runs = load_jsonl(RUNS_FILE)
    runs_by_week = defaultdict(list)
    for r in all_runs:
        runs_by_week[iso_week(r.get("start_ts", ""))].append(r)

    for f in retro_files:
        name = f.stem.replace("RETRO-", "")
        week_runs = runs_by_week.get(name, [])
        n = len(week_runs)
        done = sum(1 for r in week_runs if r.get("final_status") == "DONE")
        fails = sum(1 for r in week_runs if r.get("final_status") not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS"))
        lines.append(f"| [{name}]({f.name}) | {n} | {done} | {fails} |")

    (RETRO_DIR / "index.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

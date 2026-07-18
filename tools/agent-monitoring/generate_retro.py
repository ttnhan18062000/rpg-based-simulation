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
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

# tools/agent-monitoring/generate_retro.py's parent is tools/agent-monitoring/, so parent.parent
# is tools/ — same sys.path wiring pattern tag_report.py uses for its own imports, one directory
# further up. Read-only reuse: this module only calls load_registry/categorize_tag/
# collect_completed_tickets/extract_frontmatter/_ticket_id_effective_date, never modifies them.
_TOOLS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_TOOLS_DIR))
from tag_registry import load_registry  # noqa: E402
from tag_report import categorize_tag, collect_completed_tickets  # noqa: E402
from validate_frontmatter import (  # noqa: E402
    TAG_TAXONOMY_EFFECTIVE_DATE,
    _ticket_id_effective_date,
    extract_frontmatter,
)

RUNS_FILE = Path("agent-monitoring/runs.jsonl")
EVENTS_FILE = Path("agent-monitoring/events.jsonl")
RETRO_DIR = Path("agent-monitoring/retro")

# Repo root — two levels above tools/agent-monitoring/, matching this file's actual depth.
_DEFAULT_TICKETS_ROOT = Path(__file__).resolve().parent.parent.parent


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


def _resolve_status(r):
    """Fallback-aware run status for runs.jsonl. Current schema writes
    final_status; legacy (pre-normalization) records write only status.
    Mirrors the precedented pattern in retro_nudge_hook.py:49 and
    validate.py (post TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP).
    Only bridges the field-presence gap — does NOT normalize legacy
    status-string spellings (e.g. "success", "done", "complete") to
    "DONE"; those remain distinct, literal values by design."""
    return r.get("final_status") or r.get("status")


def _is_legacy_event(e):
    """events.jsonl legacy-schema discriminator: agent is None on
    pre-normalization records (free-text `event` field, no `summary`).
    Distinct from _resolve_status's runs.jsonl discriminator — different
    field, different file. Do not merge these two predicates."""
    return e.get("agent") is None


def _is_gate_fail(r):
    """Single source of truth for "this run did not reach a terminal
    success/scoped/in-progress state" — mirrors the gate_fails filter below.
    Extracted so per-tag gate-failure counts share one definition instead of
    a second copy of the same status tuple."""
    return _resolve_status(r) not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS")


def _collect_inprogress_tagged_tickets(root):
    """Walk tickets/inprogress/ (rglob, future-proofed against subfolders even
    though it is flat today) applying the same three skip rules
    collect_completed_tickets applies to tickets/done/: unparseable/missing
    frontmatter, pre-taxonomy or unparseable ticket_id date, empty/missing
    tags. Returns a list of (ticket_id, tags, rel_path) tuples in the same
    shape collect_completed_tickets returns.

    tickets/inprogress/ is outside collect_completed_tickets's contract
    (hardcoded to tickets/done/), so this is a small parallel implementation
    built from the same reusable primitives, not a duplicate of that function.
    """
    inprogress_dir = root / "tickets" / "inprogress"
    included = []

    if not inprogress_dir.is_dir():
        return included

    for md_file in sorted(inprogress_dir.rglob("*.md")):
        rel_path = str(md_file.relative_to(root))
        text = md_file.read_text(encoding="utf-8")
        try:
            fm = extract_frontmatter(text)
        except ValueError:
            continue
        if fm is None:
            continue

        ticket_id = fm.get("ticket_id") or md_file.stem
        embedded_date = _ticket_id_effective_date(ticket_id)
        if embedded_date is None or embedded_date < TAG_TAXONOMY_EFFECTIVE_DATE:
            continue

        tags = fm.get("tags")
        if not tags or not isinstance(tags, list):
            continue

        included.append((ticket_id, tags, rel_path))

    return included


def _collect_tagged_tickets(root):
    """Return {ticket_id: tags} merged across tickets/done/ (recursive, via
    collect_completed_tickets — unmodified) and tickets/inprogress/ (recursive,
    via _collect_inprogress_tagged_tickets). Later write wins on a collision —
    a ticket_id should only exist under one directory at a time in practice."""
    ticket_tag_map = {}
    done_included, _skip_reasons, _skipped_paths = collect_completed_tickets(root)
    for ticket_id, tags, _rel_path in done_included:
        ticket_tag_map[ticket_id] = tags
    for ticket_id, tags, _rel_path in _collect_inprogress_tagged_tickets(root):
        ticket_tag_map[ticket_id] = tags
    return ticket_tag_map


# Tag -> gate phase / final_status this Process/Skill-signal tag can be cross-referenced against.
# `security` is the only Process/Skill-signal tag with a real gate today: mirrors
# phase('Security-Review') in .claude/workflows/implement-ticket.js (built by
# TCK-20260705-WORKFLOW-SECURITY-GATE). Grepping that file confirmed zero phase(...) calls exist
# for `api-design`/`debugging`/`performance` — those three tags only ever drive an advisory
# suggested_skills log line, never a gate, so they deliberately have no entry here rather than a
# fabricated one. This is the fourth conceptual place a tag->phase mapping exists in the repo
# (ticket-scoper.md, ticket_tagging.md, implement-ticket.js are the other three) — keep this dict
# as the single local source of truth for the retro report rather than re-deriving it inline.
_TAG_GATE_PHASE = {"security": "Security-Review"}
_TAG_GATE_FINAL_STATUS = {"security": "SECURITY_BLOCKED"}
_NO_GATE_IMPLEMENTED = "N/A — no gate implemented"


def compute_retro_metrics(runs, events, tickets_root=None) -> dict:
    """Pure computation over `runs`/`events` — the same metrics `generate()` has always rendered
    to Markdown, extracted (TCK-20260718-RETRO-STATS-REFACTOR) so a JSON API
    (TCK-20260718-AGENTOPS-STATS-API) can consume them without duplicating this logic. Returns a
    plain dict — mirrors `tools/tag_report.py::build_json_report()`'s precedent (this module has
    no existing dataclass/TypedDict convention to introduce instead). Deliberately free of any
    string-formatting/Markdown concern (`fmt_pct`, table syntax) — that stays in `generate()`,
    the sole rendering consumer. Never writes a file or prints — read-only over its `runs`/
    `events`/`tickets_root` inputs, matching every other function in this module.
    """
    tickets_root = tickets_root if tickets_root is not None else _DEFAULT_TICKETS_ROOT
    ticket_tag_map = _collect_tagged_tickets(tickets_root)
    registry = load_registry(tickets_root)

    events_by_run = defaultdict(list)
    for e in events:
        events_by_run[e.get("run_id", "")].append(e)

    total = len(runs)
    done_count = sum(1 for r in runs if _resolve_status(r) == "DONE")
    gate_fails = [r for r in runs if _is_gate_fail(r)]

    durations = [r["duration_s"] for r in runs if r.get("duration_s")]
    avg_dur = int(sum(durations) / len(durations)) if durations else 0
    avg_dur_min = avg_dur // 60

    agent_counts = [r.get("agent_count", 0) for r in runs if r.get("agent_count")]
    avg_agents = round(sum(agent_counts) / len(agent_counts), 1) if agent_counts else 0

    # Gate failure breakdown
    gate_counter = Counter(_resolve_status(r) for r in gate_fails)

    # Reason-code breakdown (TCK-20260706-MONITORING-REASON-CODE, extended by
    # TCK-20260706-SCOPE-TAG-REGISTRY-CHECK and TCK-20260706-CREATE-TICKETS-TAG-CHECK) —
    # reason_code disambiguates gate statuses that collapse multiple distinct causes into one
    # value (DOD_BLOCKED at Verify; Scope's 'failed'/'blocked' across both workflows). Workflow-
    # agnostic: iterates every event regardless of which workflow (implement-ticket or
    # create-tickets) wrote it (docs/agent-monitoring/schema.md).
    reason_counter = Counter(e.get("reason_code") for e in events if e.get("reason_code"))

    # Tag breakdown — run_id resolved live against ticket_tag_map (built above from
    # tickets/done/ + tickets/inprogress/ frontmatter). A run_id with no matching entry
    # (EPIC-*/FOLDER-*/CREATE-TICKETS-*/ad-hoc/legacy/missing-file/pre-taxonomy/no-tags) is
    # simply not in the dict and falls through here — no prefix-based special-casing, the dict
    # lookup itself is the universal "unresolvable" fallback.
    subsystem_tag_runs = defaultdict(list)
    skill_tag_runs = defaultdict(list)
    for r in runs:
        tags = ticket_tag_map.get(r.get("run_id"))
        if not tags:
            continue
        for tag in tags:
            category = categorize_tag(tag, registry)
            if category == "subsystem-topic":
                subsystem_tag_runs[tag].append(r)
            elif category == "process-skill-signal":
                skill_tag_runs[tag].append(r)

    # Deliberately does NOT apply Tier Distribution's EPIC_SCOPED-exclusion-from-denominator
    # logic: EPIC_SCOPED only ever occurs on EPIC-*/FOLDER-* run_ids (implement-epic runs), which
    # never resolve to a single ticket's tags and are therefore never present in
    # subsystem_tag_runs in the first place — importing that logic here would be "fixing" a bug
    # that cannot occur.
    tag_breakdown_subsystem = {}
    for tag, tag_runs in subsystem_tag_runs.items():
        n = len(tag_runs)
        d = sum(1 for r in tag_runs if _resolve_status(r) == "DONE")
        gf = sum(1 for r in tag_runs if _is_gate_fail(r))
        tag_breakdown_subsystem[tag] = {"runs": n, "done": d, "gate_fails": gf}

    # Asymmetric by design (see _TAG_GATE_PHASE's comment above): only `security` has a real gate
    # to cross-reference today, so every other Process/Skill-signal tag's gate_hits is None
    # (rendered as an explicit "N/A — no gate implemented" marker, not a fabricated 0) — that
    # marker is itself useful retro signal (visible evidence those tags remain advisory-only).
    tag_breakdown_skill = {}
    for tag, tag_runs in skill_tag_runs.items():
        n = len(tag_runs)
        if tag in _TAG_GATE_PHASE:
            gate_phase = _TAG_GATE_PHASE[tag].casefold()
            final_status = _TAG_GATE_FINAL_STATUS.get(tag)
            hits = sum(
                1
                for r in tag_runs
                if any(
                    e.get("phase", "").casefold() == gate_phase
                    for e in events_by_run[r.get("run_id", "")]
                )
                or _resolve_status(r) == final_status
            )
        else:
            hits = None
        tag_breakdown_skill[tag] = {"runs": n, "gate_hits": hits}

    # Tier distribution
    tier_counts = Counter(r.get("tier", "unknown") for r in runs)
    tier_done = defaultdict(int)
    tier_scoped = defaultdict(int)
    for r in runs:
        if _resolve_status(r) == "DONE":
            tier_done[r.get("tier", "unknown")] += 1
        if _resolve_status(r) == "EPIC_SCOPED":
            tier_scoped[r.get("tier", "unknown")] += 1
    tier_distribution = {
        tier: {"count": n, "scoped": tier_scoped[tier], "done": tier_done[tier]}
        for tier, n in tier_counts.items()
    }

    # Agent status distribution
    agent_stats = defaultdict(lambda: Counter())
    for e in events:
        agent_stats[e.get("agent", "?")][e.get("status", "?")] += 1
    agent_status_distribution = {agent: dict(counts) for agent, counts in agent_stats.items()}

    # Spend proxy — by phase and by agent. Filter-then-aggregate: events lacking cost_proxy_score
    # (pre-TCK-20260708-AGENT-COST-OBSERVABILITY historical records, no backfill) are excluded from
    # both sum and count, never coerced to 0 (would silently deflate older phases' averages).
    scored_events = [e for e in events if e.get("cost_proxy_score") is not None]
    phase_scores = defaultdict(list)
    agent_scores = defaultdict(list)
    for e in scored_events:
        phase_scores[e.get("phase", "?")].append(e["cost_proxy_score"])
        agent_scores[e.get("agent", "?")].append(e["cost_proxy_score"])
    spend_proxy_by_phase = {
        phase: {
            "events_scored": len(scores),
            "total": round(sum(scores), 1),
            "avg": round(sum(scores) / len(scores), 1),
        }
        for phase, scores in phase_scores.items()
    }
    spend_proxy_by_agent = {
        agent: {
            "events_scored": len(scores),
            "total": round(sum(scores), 1),
            "avg": round(sum(scores) / len(scores), 1),
        }
        for agent, scores in agent_scores.items()
    }

    # Summary quality
    legacy_events = [e for e in events if _is_legacy_event(e)]
    current_events = [e for e in events if not _is_legacy_event(e)]
    empty_summaries_current = sum(1 for e in current_events if not e.get("summary", "").strip())
    legacy_event_count = len(legacy_events)
    long_summaries = sum(1 for e in events if len(e.get("summary", "")) > 200)

    # Slow runs (> 30 min = 1800s) — sorted here (a data concern), not left to the renderer.
    slow_runs = sorted(
        (r for r in runs if (r.get("duration_s") or 0) > 1800),
        key=lambda x: x.get("duration_s", 0),
        reverse=True,
    )
    slow_runs_list = [
        {
            "run_id": r.get("run_id", ""),
            "duration_s": r.get("duration_s", 0),
            "final_status": r.get("final_status", ""),
        }
        for r in slow_runs
    ]

    return {
        "run_summary": {
            "total": total,
            "done_count": done_count,
            "gate_fail_count": len(gate_fails),
            "avg_duration_min": avg_dur_min,
            "avg_agents": avg_agents,
            "total_agent_calls": len(events),
        },
        "gate_failure_breakdown": dict(gate_counter),
        "reason_code_breakdown": dict(reason_counter),
        "tag_breakdown_subsystem": tag_breakdown_subsystem,
        "tag_breakdown_skill": tag_breakdown_skill,
        "tier_distribution": tier_distribution,
        "agent_status_distribution": agent_status_distribution,
        "spend_proxy_by_phase": spend_proxy_by_phase,
        "spend_proxy_by_agent": spend_proxy_by_agent,
        "summary_quality": {
            "empty_summaries_current": empty_summaries_current,
            "legacy_event_count": legacy_event_count,
            "long_summaries": long_summaries,
        },
        "slow_runs": slow_runs_list,
    }


def generate(runs, events, label, week_str=None, tickets_root=None):
    """Render `compute_retro_metrics()`'s result to the retro report's Markdown text — the sole
    rendering consumer of that function. Signature/behavior unchanged by the
    TCK-20260718-RETRO-STATS-REFACTOR extraction; see that ticket's plan.md Step 3 for the
    byte-identical-output proof this relies on.
    """
    metrics = compute_retro_metrics(runs, events, tickets_root)
    rs = metrics["run_summary"]
    gate_counter = Counter(metrics["gate_failure_breakdown"])
    reason_counter = Counter(metrics["reason_code_breakdown"])

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
    lines.append(f"| Total runs | {rs['total']} |")
    lines.append(f"| Completed (DONE) | {rs['done_count']} ({fmt_pct(rs['done_count'], rs['total'])}) |")
    lines.append(f"| Gate failures | {rs['gate_fail_count']} |")
    lines.append(f"| Avg duration | {rs['avg_duration_min']} min |")
    lines.append(f"| Avg agents per run | {rs['avg_agents']} |")
    lines.append(f"| Total agent calls | {rs['total_agent_calls']} |")
    lines.append("")

    # Gate failures
    lines.append("## Gate Failure Breakdown")
    lines.append("")
    if gate_counter:
        lines.append("| Gate | Count | % of runs |")
        lines.append("|---|---|---|")
        for gate, count in gate_counter.most_common():
            lines.append(f"| {gate} | {count} | {fmt_pct(count, rs['total'])} |")
    else:
        lines.append("_No gate failures this period._")
    lines.append("")

    # Reason-code breakdown — only rendered when at least one event carries one, so weeks with
    # no reason_code data (or runs predating this field) don't get an empty/zero-value section.
    if reason_counter:
        lines.append("## Reason Codes")
        lines.append("")
        lines.append("| Reason | Count |")
        lines.append("|---|---|")
        for reason, count in reason_counter.most_common():
            lines.append(f"| {reason} | {count} |")
        lines.append("")

    # Tag Breakdown — Subsystem/Topic: per-tag run count, DONE rate, gate-failure count. Only
    # rendered when at least one run resolves to a registered subsystem-topic tag, mirroring the
    # Reason Codes conditional-render pattern above.
    if metrics["tag_breakdown_subsystem"]:
        lines.append("## Tag Breakdown — Subsystem/Topic")
        lines.append("")
        lines.append("| Tag | Runs | DONE rate | Gate failures |")
        lines.append("|---|---|---|---|")
        for tag in sorted(metrics["tag_breakdown_subsystem"]):
            row = metrics["tag_breakdown_subsystem"][tag]
            lines.append(f"| {tag} | {row['runs']} | {fmt_pct(row['done'], row['runs'])} | {row['gate_fails']} |")
        lines.append("")

    # Tag Breakdown — Process/Skill-signal: per-tag run count plus a gate-hit cross-reference.
    if metrics["tag_breakdown_skill"]:
        lines.append("## Tag Breakdown — Process/Skill-signal")
        lines.append("")
        lines.append("| Tag | Runs | Gate Hits |")
        lines.append("|---|---|---|")
        for tag in sorted(metrics["tag_breakdown_skill"]):
            row = metrics["tag_breakdown_skill"][tag]
            hits_cell = str(row["gate_hits"]) if row["gate_hits"] is not None else _NO_GATE_IMPLEMENTED
            lines.append(f"| {tag} | {row['runs']} | {hits_cell} |")
        lines.append("")

    # Tier distribution
    lines.append("## Tier Distribution")
    lines.append("")
    lines.append("| Tier | Count | Scoped | DONE count | DONE rate |")
    lines.append("|---|---|---|---|---|")
    for tier in sorted(metrics["tier_distribution"]):
        row = metrics["tier_distribution"][tier]
        denom = row["count"] - row["scoped"]
        lines.append(f"| {tier} | {row['count']} | {row['scoped']} | {row['done']} | {fmt_pct(row['done'], denom)} |")
    lines.append("")

    # Agent status distribution
    lines.append("## Agent Status Distribution")
    lines.append("")
    if metrics["agent_status_distribution"]:
        lines.append("| Agent | Calls | ok | failed | blocked | skipped |")
        lines.append("|---|---|---|---|---|---|")
        for agent in sorted(metrics["agent_status_distribution"]):
            c = metrics["agent_status_distribution"][agent]
            total_calls = sum(c.values())
            lines.append(
                f"| {agent} | {total_calls} | {c.get('ok',0)} | "
                f"{c.get('failed',0)} | {c.get('blocked',0)} | {c.get('skipped',0)} |"
            )
    else:
        lines.append("_No events recorded._")
    lines.append("")

    # Spend proxy — by phase and by agent.
    if metrics["spend_proxy_by_phase"]:
        lines.append("## Spend Proxy — By Phase")
        lines.append("")
        lines.append("| Phase | Events scored | Total | Avg |")
        lines.append("|---|---|---|---|")
        for phase in sorted(metrics["spend_proxy_by_phase"]):
            row = metrics["spend_proxy_by_phase"][phase]
            lines.append(f"| {phase} | {row['events_scored']} | {row['total']} | {row['avg']} |")
        lines.append("")

        lines.append("## Spend Proxy — By Agent")
        lines.append("")
        lines.append("| Agent | Events scored | Total | Avg |")
        lines.append("|---|---|---|---|")
        for agent in sorted(metrics["spend_proxy_by_agent"]):
            row = metrics["spend_proxy_by_agent"][agent]
            lines.append(f"| {agent} | {row['events_scored']} | {row['total']} | {row['avg']} |")
        lines.append("")

    # Summary quality
    sq = metrics["summary_quality"]
    lines.append("## Summary Quality")
    lines.append("")
    lines.append("| Issue | Count |")
    lines.append("|---|---|")
    lines.append(f"| Empty summary (current schema) | {sq['empty_summaries_current']} |")
    lines.append(f"| Legacy-format records (summary field not applicable) | {sq['legacy_event_count']} |")
    lines.append(f"| Truncated (>200 chars) | {sq['long_summaries']} |")
    if sq['empty_summaries_current'] > 0:
        lines.append("")
        lines.append(f"_⚠ {sq['empty_summaries_current']} empty summaries (current schema) — check agent prompts for `summary` field._")
    lines.append("")

    # Slow runs
    lines.append("## Slow Runs (> 30 min)")
    lines.append("")
    if metrics["slow_runs"]:
        lines.append("| run_id | duration | final_status |")
        lines.append("|---|---|---|")
        for r in metrics["slow_runs"]:
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
        # "ALL" is never a real ISO week (RETRO-ALL.md is the all-time snapshot,
        # not a dated weekly report) — the runs_by_week lookup would always miss.
        week_runs = all_runs if name == "ALL" else runs_by_week.get(name, [])
        n = len(week_runs)
        done = sum(1 for r in week_runs if _resolve_status(r) == "DONE")
        fails = sum(1 for r in week_runs if _resolve_status(r) not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS"))
        lines.append(f"| [{name}]({f.name}) | {n} | {done} | {fails} |")

    (RETRO_DIR / "index.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

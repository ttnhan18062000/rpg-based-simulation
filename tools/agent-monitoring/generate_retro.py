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
import sqlite3
import statistics
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocabulary import WORKFLOW_AGENTS, WORKFLOW_PHASES, infer_workflow  # noqa: E402

# Read-only reference imports for TCK-20260729-RETRIEVAL-RETRO-VIEWS's retrieval-quality views —
# anti-drift: compute_retrieval_metrics() must never re-literal these values (see
# test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants).
from hybrid_retrieval import UNRATED  # noqa: E402
from retrieval_cache import (  # noqa: E402
    HIT,
    MISS,
    STALE_REJECTED,
    INDEX_CACHE_CATEGORY,
    QUERY_CACHE_CATEGORY,
    PACKET_CACHE_CATEGORY,
)

RUNS_FILE = Path("agent-monitoring/runs.jsonl")
EVENTS_FILE = Path("agent-monitoring/events.jsonl")
RETRO_DIR = Path("agent-monitoring/retro")
DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")
DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")

# Repo root — two levels above tools/agent-monitoring/, matching this file's actual depth.
_DEFAULT_TICKETS_ROOT = Path(__file__).resolve().parent.parent.parent


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def _load_runs_and_events():
    """Return (all_runs, all_events) sourced from the derived SQLite index when available,
    building it on demand if missing. The index must never become a hard gating dependency for
    a retro report (unlike query.py/validate.py's open_index(), which sys.exit(1)s) — any failure
    along this path (missing index, on-demand build failure) degrades to the original direct
    load_jsonl(RUNS_FILE)/load_jsonl(EVENTS_FILE) scan rather than raising.
    """
    try:
        if not DEFAULT_DB_PATH.exists():
            import build_index
            from types import SimpleNamespace

            build_index.build(
                SimpleNamespace(
                    runs_file=str(RUNS_FILE),
                    events_file=str(EVENTS_FILE),
                    tools_file=str(DEFAULT_TOOLS_FILE),
                    db_path=str(DEFAULT_DB_PATH),
                )
            )

        conn = sqlite3.connect(str(DEFAULT_DB_PATH))
        try:
            runs = [json.loads(row[0]) for row in conn.execute("SELECT raw_json FROM runs ORDER BY id")]
            events = [json.loads(row[0]) for row in conn.execute("SELECT raw_json FROM events ORDER BY id")]
        finally:
            conn.close()
        return runs, events
    except Exception as exc:
        print(
            f"WARNING: agent-monitoring index unavailable ({exc}); falling back to direct JSONL "
            f"scan of {RUNS_FILE}/{EVENTS_FILE}",
            file=sys.stderr,
        )
        return load_jsonl(RUNS_FILE), load_jsonl(EVENTS_FILE)


def iso_week(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%G-W%V")
    except Exception:
        return "unknown"


def _record_since_cutoff(start_ts, cutoff):
    """True if start_ts (expected ISO 8601 string) is at/after cutoff (ISO 8601 string).

    Legacy records may store start_ts as a non-string, missing, or non-ISO8601 value (see this
    module's "Known Limitations" — docs/agent-monitoring/schema.md documents 5+ legacy schema
    generations). Such records are excluded from a --days window rather than crashing the `>=`
    comparison, mirroring iso_week()'s existing fail-to-"unknown" pattern for the --week path.
    """
    if not isinstance(start_ts, str) or not start_ts:
        return False
    return start_ts >= cutoff


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


def _canonicalize(value, canonical_set):
    """Return the member of `canonical_set` matching `value` case-insensitively, or
    `value` unchanged if no member matches. Never invents a canonical spelling for a
    value outside the known vocabulary — a genuinely unrecognized phase/agent (a future
    workflow, a typo, a prefix-family agent like `investigate:C1`) passes through as-is,
    exactly the graceful-degradation default `record_events.py`'s own warn-only
    vocabulary check already uses for the same class of value."""
    if value is None:
        return value
    for canonical in canonical_set:
        if canonical.casefold() == value.casefold():
            return canonical
    return value


def _normalize_phase(e):
    """Fold a phase casing variant (e.g. 'verify'/'VERIFY') to its canonical spelling
    ('Verify') for the event's own inferred workflow, per `vocabulary.py`'s
    WORKFLOW_PHASES — the single source of truth `record_events.py`'s warn-only check
    and `validate.py`'s drift report both already import from. Read-time merge only:
    does not write back to events.jsonl, does not affect validate.py's drift-visibility
    output (which deliberately keeps reporting casing variants as distinct entries)."""
    workflow = infer_workflow(e.get("run_id") or "")
    phase = e.get("phase")
    if workflow is None:
        return phase
    return _canonicalize(phase, WORKFLOW_PHASES.get(workflow, set()))


def _normalize_agent(e):
    """Same as `_normalize_phase`, for the `agent` field against WORKFLOW_AGENTS. A
    prefix-family agent (e.g. create-tickets' `investigate:C1`) never exact-matches a
    literal in the canonical set, so it correctly passes through unchanged rather than
    being merged into something it isn't."""
    workflow = infer_workflow(e.get("run_id") or "")
    agent = e.get("agent")
    if workflow is None:
        return agent
    return _canonicalize(agent, WORKFLOW_AGENTS.get(workflow, set()))


def _is_search_or_graphify_call(tool_row):
    """True if this tools.jsonl row satisfies the CLAUDE.md search-before-grep hard rule:
    mcp__knowledge-search__search_docs, or a Bash call invoking graphify. Deliberately
    independent of retrieval_baseline_metrics.py's SEARCH_TOOL_NAMES (a different vocabulary
    for a different metric) — do not import or reuse that constant here."""
    tool = tool_row.get("tool")
    if tool == "mcp__knowledge-search__search_docs":
        return True
    if tool == "Bash":
        summary = tool_row.get("input_summary") or ""
        return summary.startswith("graphify")
    return False


def _is_grep_call(tool_row):
    """True if this tools.jsonl row is a Grep tool call or a Bash call whose input_summary
    contains 'grep'."""
    tool = tool_row.get("tool")
    if tool == "Grep":
        return True
    if tool == "Bash":
        summary = tool_row.get("input_summary") or ""
        return "grep" in summary
    return False


def _is_parity_ledger_yaml_write(tool_row):
    if tool_row.get("tool") not in ("Edit", "Write"):
        return False
    summary = tool_row.get("input_summary") or ""
    return "docs/parity_ledger/" in summary and ".yaml" in summary


def _is_unsafe_parity_build_call(tool_row):
    if tool_row.get("tool") != "Bash":
        return False
    summary = tool_row.get("input_summary") or ""
    if "parity_index.py" not in summary or "build" not in summary:
        return False
    if "--db-path" not in summary:
        return True  # no override -> defaults to the real repo parity-index/parity.db path
    return "parity-index/parity.db" in summary


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

# Outlier-flag threshold (TCK-20260719-RETRO-OUTLIER-FLAGS): calibratable, not precision-load-
# bearing — mirrors cost_proxy.py's own "weights are calibratable" convention. A run/event is
# flagged when its value exceeds OUTLIER_MEDIAN_MULTIPLIER times its group's median. Purely a
# visibility signal ("this sits far from its peers"), never a claim about *why* — matches the
# ticket's own explicit framing ("does not need to explain why an outlier occurred, just make it
# visible").
OUTLIER_MEDIAN_MULTIPLIER = 3
# A median computed from too few points is not a meaningful comparison baseline — a group with
# fewer than this many non-null values is skipped entirely (no outliers flagged for it), rather
# than flagging against a near-arbitrary 1- or 2-point "median."
_OUTLIER_MIN_GROUP_SIZE = 3


def _flag_outliers(items, group_key_fn, value_fn, multiplier=OUTLIER_MEDIAN_MULTIPLIER):
    """Group `items` by `group_key_fn`, compute each group's median of `value_fn`, and return
    every item whose value exceeds `multiplier` times its group's median — sorted by ratio
    descending (worst outliers first). Items are only ever compared within their own group (e.g.
    each tier's own duration_s median, each phase's own cost_proxy_score median), never against a
    single global median that would conflate unlike things (a hotfix's typical duration is not
    comparable to an epic's). Groups with fewer than _OUTLIER_MIN_GROUP_SIZE values are skipped —
    a median from 1-2 points is not a meaningful baseline. Items with a None value_fn result are
    excluded from both the candidate set and the median basis (never coerced to 0)."""
    by_group = defaultdict(list)
    for item in items:
        value = value_fn(item)
        if value is None:
            continue
        by_group[group_key_fn(item)].append((item, value))

    flagged = []
    for group_key, pairs in by_group.items():
        if len(pairs) < _OUTLIER_MIN_GROUP_SIZE:
            continue
        median = statistics.median(v for _, v in pairs)
        if median <= 0:
            continue
        for item, value in pairs:
            if value > multiplier * median:
                flagged.append((item, value, median, group_key))

    flagged.sort(key=lambda t: t[1] / t[2], reverse=True)
    return flagged


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

    # Agent status distribution + phase status distribution (TCK-20260719-PHASE-AGENT-CASE-FOLD:
    # both keyed on the *normalized* phase/agent, so casing variants of the same logical
    # phase/agent — e.g. 'Verify'/'verify'/'VERIFY' — merge into one row instead of silently
    # fragmenting counts (and, for gate-adjacent phases like Review, undercounting the real
    # failure rate). phase_status_distribution is new — nothing previously exposed a per-phase
    # ok/failed/blocked/skipped breakdown, so a phase's true gate-failure rate (the ticket's own
    # motivating example: Review's real 18.2%) was not computable from this function's output at
    # all before this, regardless of casing.
    agent_stats = defaultdict(lambda: Counter())
    phase_stats = defaultdict(lambda: Counter())
    for e in events:
        agent_stats[_normalize_agent(e) or "?"][e.get("status", "?")] += 1
        phase_stats[_normalize_phase(e) or "?"][e.get("status", "?")] += 1
    agent_status_distribution = {agent: dict(counts) for agent, counts in agent_stats.items()}
    phase_status_distribution = {phase: dict(counts) for phase, counts in phase_stats.items()}

    # Spend proxy — by phase and by agent. Filter-then-aggregate: events lacking cost_proxy_score
    # (pre-TCK-20260708-AGENT-COST-OBSERVABILITY historical records, no backfill) are excluded from
    # both sum and count, never coerced to 0 (would silently deflate older phases' averages).
    # Keyed on normalized phase/agent for the same reason as agent_status_distribution above.
    scored_events = [e for e in events if e.get("cost_proxy_score") is not None]
    phase_scores = defaultdict(list)
    agent_scores = defaultdict(list)
    for e in scored_events:
        phase_scores[_normalize_phase(e) or "?"].append(e["cost_proxy_score"])
        agent_scores[_normalize_agent(e) or "?"].append(e["cost_proxy_score"])
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

    # Outliers (TCK-20260719-RETRO-OUTLIER-FLAGS): a *relative* signal — "this sits far from its
    # peers" — distinct from slow_runs' fixed 30-min absolute threshold above. The two can overlap
    # on the same run (both are computed independently, neither excludes the other) but answer
    # different questions: slow_runs = "was this literally a long time," outliers = "was this way
    # more than similar runs typically take." Both are surfaced, not merged, so a reader isn't
    # misled into thinking they're the same signal.
    #
    # duration_s outliers are grouped by tier (runs.jsonl has no phase field, only tier) — a
    # hotfix's typical duration is not a meaningful baseline for an epic's, so comparing against
    # a single global median would flag nearly every epic as "an outlier" for no real reason.
    duration_outliers = _flag_outliers(
        runs,
        group_key_fn=lambda r: r.get("tier", "unknown"),
        value_fn=lambda r: r.get("duration_s"),
    )
    outliers_duration_s = [
        {
            "run_id": item.get("run_id", ""),
            "tier": group_key,
            "duration_s": value,
            "median": round(median, 1),
            "ratio": round(value / median, 1),
        }
        for item, value, median, group_key in duration_outliers
    ]

    # cost_proxy_score outliers are grouped by *normalized* phase (reusing _normalize_phase from
    # TCK-20260719-PHASE-AGENT-CASE-FOLD, landed immediately before this ticket in the same batch —
    # a casing-fragmented phase would otherwise silently split one real group into several
    # too-small-to-median groups). Matches D25's own finding shape (">10x spread within the same
    # phase/agent pair").
    cost_outliers = _flag_outliers(
        scored_events,
        group_key_fn=lambda e: _normalize_phase(e) or "?",
        value_fn=lambda e: e.get("cost_proxy_score"),
    )
    outliers_cost_proxy_score = [
        {
            "run_id": item.get("run_id", ""),
            "seq": item.get("seq"),
            "phase": group_key,
            "agent": _normalize_agent(item) or item.get("agent", "?"),
            "cost_proxy_score": value,
            "median": round(median, 1),
            "ratio": round(value / median, 1),
        }
        for item, value, median, group_key in cost_outliers
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
        "phase_status_distribution": phase_status_distribution,
        "spend_proxy_by_phase": spend_proxy_by_phase,
        "spend_proxy_by_agent": spend_proxy_by_agent,
        "summary_quality": {
            "empty_summaries_current": empty_summaries_current,
            "legacy_event_count": legacy_event_count,
            "long_summaries": long_summaries,
        },
        "slow_runs": slow_runs_list,
        "outliers": {
            "duration_s": outliers_duration_s,
            "cost_proxy_score": outliers_cost_proxy_score,
        },
    }


def compute_retrieval_metrics(events: list[dict]) -> dict:
    """Pure, read-only computation over `events` covering TCK-20260729-RETRIEVAL-EVENT-SCHEMA-
    EMIT's original AC7 proof-of-queryability (cache rates, per-event candidate/selected and
    selected/cited ratios) plus TCK-20260729-RETRIEVAL-RETRO-VIEWS's four dashboard signals:
    aggregated noise-indicator ratios, freshness/authority distribution (UNRATED-inclusive), and
    an unconditional follow-up/expansion rate. Never calls write_lines/write_line or opens any
    file; operates entirely on its `events` argument (a fixture list in tests, or the real
    events.jsonl-derived list in `_load_runs_and_events()`'s callers).

    Ordinary workflow events (no `retrieval_event_schema_version` key) are skipped, not crashed
    on — the same graceful-skip discipline `_is_legacy_event`/`_resolve_status` already use for
    other events.jsonl schema variance.
    """
    retrieval_events = [e for e in events if "retrieval_event_schema_version" in e]

    cache_status_counts_by_level = defaultdict(Counter)
    for e in retrieval_events:
        cache_level = e.get("cache_level")
        cache_status = e.get("cache_status")
        if cache_level is not None and cache_status is not None:
            cache_status_counts_by_level[cache_level][cache_status] += 1

    cache_rates = {}
    for cache_level, counts in cache_status_counts_by_level.items():
        total = sum(counts.values())
        cache_rates[cache_level] = {
            "counts": dict(counts),
            "total": total,
            # Zero-division-guarded: total is always >0 here since a Counter only gains an entry
            # in this loop when it observes at least one (cache_level, cache_status) pair, but the
            # guard is kept explicit rather than relying on that invariant silently.
            "rates": {status: count / total for status, count in counts.items()} if total else {},
        }

    candidate_to_selected_ratios = []
    selected_to_cited_ratios = []
    total_candidates = 0
    total_selected_for_candidates = 0
    total_selected = 0
    total_cited = 0
    authority_distribution = Counter()
    freshness_distribution = Counter()
    for e in retrieval_events:
        candidate_count = e.get("candidate_count")
        selected_count = e.get("selected_count")
        if candidate_count is not None and selected_count is not None:
            ratio = (selected_count / candidate_count) if candidate_count else None
            candidate_to_selected_ratios.append(
                {"run_id": e.get("run_id"), "seq": e.get("seq"), "ratio": ratio}
            )
            total_candidates += candidate_count
            total_selected_for_candidates += selected_count

        cited_source_hashes = e.get("cited_source_hashes")
        if selected_count is not None and cited_source_hashes is not None:
            ratio = (len(cited_source_hashes) / selected_count) if selected_count else None
            selected_to_cited_ratios.append(
                {"run_id": e.get("run_id"), "seq": e.get("seq"), "ratio": ratio}
            )
            total_selected += selected_count
            total_cited += len(cited_source_hashes)

        authority_counts = e.get("authority_counts")
        if authority_counts:
            authority_distribution.update(authority_counts)

        freshness_counts = e.get("freshness_counts")
        if freshness_counts:
            freshness_distribution.update(freshness_counts)

    candidate_to_selected_aggregate = {
        "total_candidates": total_candidates,
        "total_selected": total_selected_for_candidates,
        "ratio": (total_selected_for_candidates / total_candidates) if total_candidates else None,
    }
    selected_to_cited_aggregate = {
        "total_selected": total_selected,
        "total_cited": total_cited,
        "ratio": (total_cited / total_selected) if total_selected else None,
    }

    # UNCONDITIONAL formula (Resolved Decision 1, plan.md): fraction of retrieval events carrying
    # expansion_reason/expansion_count at all, not conditioned on adequacy_verdict. Rejected the
    # conditional-on-adequacy_verdict alternative because none of the 3 shipped wrap_*() functions
    # ever emit expansion_reason/expansion_count today, making that reading untestable against real
    # behavior.
    expansion_count_events = sum(
        1
        for e in retrieval_events
        if e.get("expansion_reason") is not None or e.get("expansion_count") is not None
    )
    expansion_rate = (
        (expansion_count_events / len(retrieval_events)) if retrieval_events else 0.0
    )

    return {
        "retrieval_event_count": len(retrieval_events),
        "cache_rates": cache_rates,
        "candidate_to_selected_ratios": candidate_to_selected_ratios,
        "selected_to_cited_ratios": selected_to_cited_ratios,
        "candidate_to_selected_aggregate": candidate_to_selected_aggregate,
        "selected_to_cited_aggregate": selected_to_cited_aggregate,
        "authority_distribution": dict(authority_distribution),
        "freshness_distribution": dict(freshness_distribution),
        "expansion_rate": expansion_rate,
    }


def compute_shadow_baseline_comparison(events: list[dict]) -> dict:
    """Partitions events by real (TCK-...) vs. synthetic (RETRIEVAL-EVENT-...) run_id
    provenance, using vocabulary.infer_workflow(run_id) is not None as the sole partition test —
    the same non-None-vs-None idiom _normalize_phase()/_normalize_agent() already use. Does NOT
    pre-filter to retrieval-shaped events itself: compute_retrieval_metrics() already applies its
    own "retrieval_event_schema_version" in e discriminator internally, so passing the full
    per-cohort event list (including ordinary workflow events) is correct and avoids a second,
    redundant filter.
    """
    shadow_events = [e for e in events if infer_workflow(e.get("run_id") or "") is not None]
    baseline_events = [e for e in events if infer_workflow(e.get("run_id") or "") is None]
    return {
        "shadow": compute_retrieval_metrics(shadow_events),
        "baseline": compute_retrieval_metrics(baseline_events),
    }


def compute_tool_safety_metrics(events: list[dict], tools: list[dict]) -> dict:
    """Pure, read-only computation over `events`/`tools` auditing (1) search-before-grep
    hard-rule compliance (CLAUDE.md) for tools.jsonl rows within real Investigate-phase
    (run_id, seq) pairs, identified via events.jsonl's `phase` field (the authoritative
    phase-transition record — never tools.jsonl's own, less-authoritative `phase` field, which
    is null for records predating TCK-20260719-LIVE-PHASE-AGENT-LABEL), and (2)
    parity_index.py write-safety across the whole `tools` argument as passed in (not scoped to
    Investigate-phase pairs) — a zero-tolerance count of Edit/Write calls into
    docs/parity_ledger/*.yaml and of `parity_index.py build` invocations targeting the real
    repo parity-index/parity.db path instead of a scratch path. Never calls write_lines/
    write_line or opens any file; operates entirely on its `events`/`tools` arguments.

    tools.jsonl rows with seq: null or seq <= 0 (shadow-packet rows) are structurally excluded
    by never matching an Investigate-phase key derived from events.jsonl (whose seq is
    non-nullable and >= 1 for real phase events) — no explicit skip branch is needed.
    """
    investigate_pairs = {
        (e.get("run_id"), e.get("seq"))
        for e in events
        if _normalize_phase(e) == "Investigate"
        and e.get("run_id") is not None
        and e.get("seq") is not None
    }

    pair_tool_rows = defaultdict(list)
    for row in tools:
        key = (row.get("run_id"), row.get("seq"))
        if key in investigate_pairs:
            pair_tool_rows[key].append(row)

    per_pair_compliance = {}
    for key, rows in pair_tool_rows.items():
        first_search_idx = next(
            (i for i, r in enumerate(rows) if _is_search_or_graphify_call(r)), None
        )
        first_grep_idx = next((i for i, r in enumerate(rows) if _is_grep_call(r)), None)
        if first_grep_idx is None:
            per_pair_compliance[key] = True
        elif first_search_idx is None:
            per_pair_compliance[key] = False
        else:
            per_pair_compliance[key] = first_search_idx < first_grep_idx

    investigate_pair_count = len(per_pair_compliance)
    compliant_count = sum(1 for v in per_pair_compliance.values() if v)

    parity_yaml_writes = [r for r in tools if _is_parity_ledger_yaml_write(r)]
    unsafe_parity_builds = [r for r in tools if _is_unsafe_parity_build_call(r)]

    return {
        "search_before_grep": {
            "investigate_pair_count": investigate_pair_count,
            "compliant_count": compliant_count,
            "compliance_rate": (
                compliant_count / investigate_pair_count if investigate_pair_count else None
            ),
            "per_pair_compliance": {
                f"{run_id}::{seq}": compliant
                for (run_id, seq), compliant in per_pair_compliance.items()
            },
        },
        "parity_write_safety": {
            "parity_ledger_yaml_write_count": len(parity_yaml_writes),
            "unsafe_parity_build_count": len(unsafe_parity_builds),
            "parity_ledger_yaml_write_examples": parity_yaml_writes[:5],
            "unsafe_parity_build_examples": unsafe_parity_builds[:5],
        },
    }


def generate(runs, events, label, week_str=None, tickets_root=None, tools=None):
    """Render `compute_retro_metrics()`'s result to the retro report's Markdown text — the sole
    rendering consumer of that function. Signature/behavior unchanged by the
    TCK-20260718-RETRO-STATS-REFACTOR extraction; see that ticket's plan.md Step 3 for the
    byte-identical-output proof this relies on.
    """
    metrics = compute_retro_metrics(runs, events, tickets_root)
    retrieval_metrics = compute_retrieval_metrics(events)
    shadow_comparison = compute_shadow_baseline_comparison(events)
    tool_safety = compute_tool_safety_metrics(events, tools or [])
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

    # Phase status distribution — same shape as Agent Status Distribution above, keyed by phase
    # instead of agent. Surfaces a phase's real gate-failure rate (e.g. "Review: 41 failed / 225
    # total") that was not visible from any other section of this report.
    lines.append("## Phase Status Distribution")
    lines.append("")
    if metrics["phase_status_distribution"]:
        lines.append("| Phase | Calls | ok | failed | blocked | skipped |")
        lines.append("|---|---|---|---|---|---|")
        for phase in sorted(metrics["phase_status_distribution"]):
            c = metrics["phase_status_distribution"][phase]
            total_calls = sum(c.values())
            lines.append(
                f"| {phase} | {total_calls} | {c.get('ok',0)} | "
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

    # Outliers — relative signal (Nx group median), distinct from Slow Runs' fixed 30-min
    # threshold above. Conditionally rendered: only appears when at least one outlier was flagged
    # in either category, mirroring the Reason Codes/Tag Breakdown conditional-render pattern.
    outliers = metrics["outliers"]
    if outliers["duration_s"] or outliers["cost_proxy_score"]:
        lines.append("## Outliers")
        lines.append("")
        lines.append(
            f"_Flags a value more than {OUTLIER_MEDIAN_MULTIPLIER}x its group's median — a "
            "relative visibility signal, not an absolute threshold like Slow Runs above, and not "
            "a claim about *why* the value is high._"
        )
        lines.append("")
        if outliers["duration_s"]:
            lines.append("### Duration outliers (by tier)")
            lines.append("")
            lines.append("| run_id | tier | duration_s | tier median | ratio |")
            lines.append("|---|---|---|---|---|")
            for o in outliers["duration_s"]:
                lines.append(
                    f"| {o['run_id']} | {o['tier']} | {o['duration_s']} | {o['median']} | {o['ratio']}x |"
                )
            lines.append("")
        if outliers["cost_proxy_score"]:
            lines.append("### Cost-proxy-score outliers (by phase)")
            lines.append("")
            lines.append("| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |")
            lines.append("|---|---|---|---|---|---|---|")
            for o in outliers["cost_proxy_score"]:
                lines.append(
                    f"| {o['run_id']} | {o['seq']} | {o['phase']} | {o['agent']} | "
                    f"{o['cost_proxy_score']} | {o['median']} | {o['ratio']}x |"
                )
            lines.append("")

    # Retrieval Quality (TCK-20260729-RETRIEVAL-RETRO-VIEWS): conditionally rendered, mirroring
    # the Reason Codes/Tag Breakdown/Outliers gating pattern above. Omitted entirely (not rendered
    # empty) when zero retrieval events are present — the realistic majority case today, since no
    # Phase 3 module is wired into a real agent run yet.
    if retrieval_metrics["retrieval_event_count"]:
        lines.append("## Retrieval Quality")
        lines.append("")
        lines.append(
            "_Retrieval-event volume reflects test/manual invocations only; visible under "
            "`--all`, not `--days`/`--week`, since these run_ids are deliberately unlinked from "
            "any `runs.jsonl` row._"
        )
        lines.append("")

        lines.append("### Cache Rates by Level")
        lines.append("")
        cache_rates = retrieval_metrics["cache_rates"]
        if cache_rates:
            lines.append(f"| Cache Level | {HIT} | {MISS} | {STALE_REJECTED} | Total |")
            lines.append("|---|---|---|---|---|")
            for cache_level in sorted(cache_rates):
                row = cache_rates[cache_level]
                counts = row["counts"]
                lines.append(
                    f"| {cache_level} | {counts.get(HIT, 0)} | {counts.get(MISS, 0)} | "
                    f"{counts.get(STALE_REJECTED, 0)} | {row['total']} |"
                )
        else:
            lines.append("_No cache-level data this period._")
        lines.append("")

        lines.append("### Noise Indicators")
        lines.append("")
        cts_agg = retrieval_metrics["candidate_to_selected_aggregate"]
        stc_agg = retrieval_metrics["selected_to_cited_aggregate"]
        cts_ratio = "n/a" if cts_agg["ratio"] is None else f"{cts_agg['ratio']:.2f}"
        stc_ratio = "n/a" if stc_agg["ratio"] is None else f"{stc_agg['ratio']:.2f}"
        lines.append("| Signal | Numerator | Denominator | Ratio |")
        lines.append("|---|---|---|---|")
        lines.append(
            f"| Candidate → Selected | {cts_agg['total_selected']} | {cts_agg['total_candidates']} | {cts_ratio} |"
        )
        lines.append(
            f"| Selected → Cited | {stc_agg['total_cited']} | {stc_agg['total_selected']} | {stc_ratio} |"
        )
        lines.append("")

        lines.append("### Freshness / Authority Distribution")
        lines.append("")
        authority_distribution = retrieval_metrics["authority_distribution"]
        lines.append("**Authority**")
        lines.append("")
        if authority_distribution:
            lines.append("| Bucket | Count |")
            lines.append("|---|---|")
            for bucket in sorted(authority_distribution):
                lines.append(f"| {bucket} | {authority_distribution[bucket]} |")
        else:
            lines.append("_No authority data this period._")
        lines.append("")
        freshness_distribution = retrieval_metrics["freshness_distribution"]
        lines.append("**Freshness**")
        lines.append("")
        if freshness_distribution:
            lines.append("| Bucket | Count |")
            lines.append("|---|---|")
            for bucket in sorted(freshness_distribution):
                lines.append(f"| {bucket} | {freshness_distribution[bucket]} |")
        else:
            lines.append("_No freshness data this period._")
        lines.append("")

        lines.append("### Expansion Rate")
        lines.append("")
        lines.append(f"**Expansion rate:** {retrieval_metrics['expansion_rate'] * 100:.1f}%")
        lines.append("")

    # Shadow vs. Baseline Retrieval Comparison (TCK-20260729-SHADOW-BASELINE-COMPARISON):
    # additive, separately-gated section — never rendered empty, omitted entirely when the
    # shadow (real-run-id) cohort has zero retrieval events, independent of whether the
    # synthetic/baseline cohort is nonzero.
    if shadow_comparison["shadow"]["retrieval_event_count"]:
        lines.append("## Shadow vs. Baseline Retrieval Comparison")
        lines.append("")
        lines.append(
            "_Compares shadow-packet-covered (real TCK-... run_id) retrieval events against the "
            "synthetic/manual-invocation baseline, using the same cache-rate/noise-ratio/"
            "freshness-authority/expansion-rate measurement domain as `## Retrieval Quality` "
            "above. Comparison data only._"
        )
        lines.append("")

        shadow_m = shadow_comparison["shadow"]
        baseline_m = shadow_comparison["baseline"]

        lines.append("| Metric | Shadow | Baseline |")
        lines.append("|---|---|---|")
        lines.append(
            f"| Retrieval event count | {shadow_m['retrieval_event_count']} | "
            f"{baseline_m['retrieval_event_count']} |"
        )

        def _fmt_ratio(agg):
            return "n/a" if agg["ratio"] is None else f"{agg['ratio']:.2f}"

        lines.append(
            f"| Candidate → Selected ratio | "
            f"{_fmt_ratio(shadow_m['candidate_to_selected_aggregate'])} | "
            f"{_fmt_ratio(baseline_m['candidate_to_selected_aggregate'])} |"
        )
        lines.append(
            f"| Selected → Cited ratio | "
            f"{_fmt_ratio(shadow_m['selected_to_cited_aggregate'])} | "
            f"{_fmt_ratio(baseline_m['selected_to_cited_aggregate'])} |"
        )
        lines.append(
            f"| Expansion rate | {shadow_m['expansion_rate'] * 100:.1f}% | "
            f"{baseline_m['expansion_rate'] * 100:.1f}% |"
        )
        lines.append("")

        lines.append("**Cache Rates by Level — Shadow**")
        lines.append("")
        if shadow_m["cache_rates"]:
            lines.append(f"| Cache Level | {HIT} | {MISS} | {STALE_REJECTED} | Total |")
            lines.append("|---|---|---|---|---|")
            for cache_level in sorted(shadow_m["cache_rates"]):
                row = shadow_m["cache_rates"][cache_level]
                counts = row["counts"]
                lines.append(
                    f"| {cache_level} | {counts.get(HIT, 0)} | {counts.get(MISS, 0)} | "
                    f"{counts.get(STALE_REJECTED, 0)} | {row['total']} |"
                )
        else:
            lines.append("_No cache-level data this period._")
        lines.append("")

        lines.append("**Cache Rates by Level — Baseline**")
        lines.append("")
        if baseline_m["cache_rates"]:
            lines.append(f"| Cache Level | {HIT} | {MISS} | {STALE_REJECTED} | Total |")
            lines.append("|---|---|---|---|---|")
            for cache_level in sorted(baseline_m["cache_rates"]):
                row = baseline_m["cache_rates"][cache_level]
                counts = row["counts"]
                lines.append(
                    f"| {cache_level} | {counts.get(HIT, 0)} | {counts.get(MISS, 0)} | "
                    f"{counts.get(STALE_REJECTED, 0)} | {row['total']} |"
                )
        else:
            lines.append("_No cache-level data this period._")
        lines.append("")

        lines.append("**Freshness / Authority — Shadow**")
        lines.append("")
        lines.append(f"Authority: {dict(shadow_m['authority_distribution']) or '_none_'}")
        lines.append(f"Freshness: {dict(shadow_m['freshness_distribution']) or '_none_'}")
        lines.append("")
        lines.append("**Freshness / Authority — Baseline**")
        lines.append("")
        lines.append(f"Authority: {dict(baseline_m['authority_distribution']) or '_none_'}")
        lines.append(f"Freshness: {dict(baseline_m['freshness_distribution']) or '_none_'}")
        lines.append("")

    # Tool Safety Audit (TCK-20260803-RETRO-TOOL-SAFETY-AUDIT): audits search-before-grep hard-rule
    # compliance (CLAUDE.md) during real Investigate phases, and parity_index.py write-safety
    # (zero-tolerance docs/parity_ledger/*.yaml write / real-path build invocation count).
    # Additive, separately-gated section — omitted entirely (not rendered empty) when the period
    # has zero real Investigate-phase tool-call data, matching the Shadow vs. Baseline section's
    # own gate.
    sbg = tool_safety["search_before_grep"]
    if sbg["investigate_pair_count"]:
        lines.append("## Tool Safety Audit")
        lines.append("")

        lines.append("### Search-Before-Grep Compliance (Investigate Phase)")
        lines.append("")
        rate = sbg["compliance_rate"]
        rate_str = "n/a" if rate is None else f"{rate * 100:.1f}%"
        lines.append(
            f"**Compliance rate:** {rate_str} "
            f"({sbg['compliant_count']}/{sbg['investigate_pair_count']} Investigate-phase calls)"
        )
        lines.append("")

        pws = tool_safety["parity_write_safety"]
        lines.append("### Parity Ledger Write-Safety")
        lines.append("")
        lines.append(
            f"**`docs/parity_ledger/*.yaml` write violations:** "
            f"{pws['parity_ledger_yaml_write_count']}"
        )
        lines.append(
            f"**Unsafe `parity_index.py build` invocations (real repo path):** "
            f"{pws['unsafe_parity_build_count']}"
        )
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

    all_runs, all_events = _load_runs_and_events()
    all_tools = load_jsonl(DEFAULT_TOOLS_FILE)

    if args.all:
        runs = all_runs
        events = all_events
        tools = all_tools
        label = "All Time"
        week_str = None
        out_name = "RETRO-ALL.md"
    elif args.days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()
        runs = [r for r in all_runs if _record_since_cutoff(r.get("start_ts"), cutoff)]
        run_ids = {r["run_id"] for r in runs}
        events = [e for e in all_events if e.get("run_id") in run_ids]
        tools = [t for t in all_tools if t.get("run_id") in run_ids]
        label = f"Last {args.days} Days"
        week_str = None
        out_name = f"RETRO-LAST{args.days}D.md"
    else:
        week_str = args.week or current_week()
        runs = [r for r in all_runs if iso_week(r.get("start_ts", "")) == week_str]
        run_ids = {r["run_id"] for r in runs}
        events = [e for e in all_events if e.get("run_id") in run_ids]
        tools = [t for t in all_tools if t.get("run_id") in run_ids]
        label = week_str
        out_name = f"RETRO-{week_str}.md"

    report = generate(runs, events, label, week_str, tools=tools)

    RETRO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RETRO_DIR / out_name
    out_path.write_text(report)
    print(f"Written: {out_path}")
    print(f"Runs: {len(runs)}, Events: {len(events)}")

    # Update index
    _update_index(all_runs)


def _update_index(all_runs):
    retro_files = sorted(RETRO_DIR.glob("RETRO-*.md"), reverse=True)
    retro_files = [f for f in retro_files if f.name != "index.md"]

    lines = ["# Agent Monitoring Retro Index", ""]
    lines.append("| Report | Runs | DONE | Gate failures |")
    lines.append("|---|---|---|---|")

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

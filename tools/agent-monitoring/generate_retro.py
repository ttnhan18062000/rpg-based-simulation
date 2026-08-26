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
import re
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone, timedelta
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
from duration_utils import compute_active_idle_split  # noqa: E402

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
    read_cache_access_log,
)

RUNS_FILE = Path("agent-monitoring/runs.jsonl")
EVENTS_FILE = Path("agent-monitoring/events.jsonl")
RETRO_DIR = Path("agent-monitoring/retro")
DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")
DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")

# Repo root — two levels above tools/agent-monitoring/, matching this file's actual depth.
_DEFAULT_TICKETS_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_SKILLS_DIR = _DEFAULT_TICKETS_ROOT / ".claude" / "skills"


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def _index_is_stale(db_path):
    """True if db_path is missing, or any source JSONL (runs/events/tools) has a newer mtime
    than the index — the index is a point-in-time snapshot (TCK-20260713-MONITORING-SQLITE-INDEX),
    so any write to a source file after the index was last built makes it stale, not just absent.
    """
    if not db_path.exists():
        return True
    db_mtime = db_path.stat().st_mtime
    for source in (RUNS_FILE, EVENTS_FILE, DEFAULT_TOOLS_FILE):
        if source.exists() and source.stat().st_mtime > db_mtime:
            return True
    return False


def _load_runs_and_events():
    """Return (all_runs, all_events) sourced from the derived SQLite index when available,
    (re)building it on demand if missing OR stale (TCK-20260811-AGENT-MONITORING-INDEX-SILENT-
    STALENESS — a present-but-outdated index previously read silently, under-reporting retro
    numbers with no warning). The index must never become a hard gating dependency for a retro
    report (unlike query.py/validate.py's open_index(), which sys.exit(1)s) — any failure along
    this path (missing/stale index, on-demand build failure) degrades to the original direct
    load_jsonl(RUNS_FILE)/load_jsonl(EVENTS_FILE) scan rather than raising.
    """
    try:
        if _index_is_stale(DEFAULT_DB_PATH):
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


def _is_parity_index_build_call(tool_row):
    """True if this row invokes parity_index.py's build path — the shared, broader precondition
    both _is_unsafe_parity_build_call (is THIS call unsafe) and the parity_write_safety
    co-occurrence check (did this RUN touch parity_index.py's build path at all) need. A safe
    scratch-path build still establishes real risk-adjacent behavior in that run for the
    co-occurrence check's purposes, even though it isn't itself "unsafe"."""
    if tool_row.get("tool") != "Bash":
        return False
    summary = tool_row.get("input_summary") or ""
    return "parity_index.py" in summary and "build" in summary


def _is_unsafe_parity_build_call(tool_row):
    if not _is_parity_index_build_call(tool_row):
        return False
    summary = tool_row.get("input_summary") or ""
    if "--db-path" not in summary:
        return True  # no override -> defaults to the real repo parity-index/parity.db path
    return "parity-index/parity.db" in summary


# Path-anchored so a bare filename match (e.g. tests/tools/test_parity_index.py, whose character
# immediately preceding "parity_index.py" is "_", not "/") never matches, and requiring one of
# entry/impact/health as the very next token excludes --help, `git log -- ... parity_index.py`,
# and `sed -n '1,60p' tools/parity_index.py` — all real corpus-observed shapes that merely mention
# the filename without invoking its read path (TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING).
_PARITY_INDEX_READPATH_RE = re.compile(r'(?:^|/)parity_index\.py\s+(entry|impact|health)\b')


def _is_parity_index_readpath_call(tool_row):
    """True if this row invokes parity_index.py's entry/impact/health read path — a separate
    detector from _is_parity_index_build_call above (read-path usage vs. build-path write-safety);
    the two are never merged."""
    if tool_row.get("tool") != "Bash":
        return False
    return bool(_PARITY_INDEX_READPATH_RE.search(tool_row.get("input_summary") or ""))


def compute_parity_index_readpath_call_count(tools: list[dict]) -> dict:
    """Pure, read-only count of parity_index.py entry/impact/health invocations observed in
    `tools`. Confirmed 0 today (TCK-20260731-PARITY-READPATH-GATE's Gate A review found the read
    path reviewed GO but not yet wired into any real call site) — this function counts live
    against whatever `tools` it is given, so a future real call site needs zero code change here
    to start reporting a nonzero number."""
    bash_rows = [r for r in tools if r.get("tool") == "Bash"]
    matches = [r for r in tools if _is_parity_index_readpath_call(r)]
    return {
        "count": len(matches),
        "bash_rows_scanned": len(bash_rows),
        "examples": matches[:5],
        "derivation": (
            "Counts tools.jsonl rows where tool == \"Bash\" and input_summary matches "
            "parity_index.py followed immediately by entry, impact, or health (path-anchored, "
            "so a filename mention alone — e.g. test_parity_index.py, --help, `git log -- ... "
            "parity_index.py`, `sed -n '1,60p' tools/parity_index.py` — never counts). "
            "bash_rows_scanned is the total Bash-tool row population this detector ran against "
            "(the section's own 'N' denominator). Confirmed 0 real call sites as of "
            "TCK-20260731-PARITY-READPATH-GATE's Gate A review (reviewed GO, not yet wired into "
            "any real workflow call site) — this is the expected, correct value until a future "
            "ticket adds a real entry/impact/health call site, not a bug."
        ),
    }


# The literal `tool` values confirmed present in the real corpus (investigation.md's direct scan)
# that represent a follow-up search action. mcp__knowledge-search__search_health is deliberately
# excluded — it is a health-check call, not a follow-up search. Bash is excluded even though some
# Bash calls have search-flavored input_summary text, since that is not distinguishable by tool
# name alone and this metric must stay precise, not inflated.
#
# Relocated here from retrieval_baseline_metrics.py (TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-
# TRACKING) to resolve a real circular-import constraint: retrieval_baseline_metrics.py already
# imports FROM generate_retro.py, so generate_retro.py importing this constant back from
# retrieval_baseline_metrics.py would create a two-file import cycle. retrieval_baseline_metrics.py
# now re-imports this name from generate_retro.py's existing import statement instead of defining
# it — semantics and membership are unchanged, only the file of definition moved.
SEARCH_TOOL_NAMES = frozenset({
    "mcp__knowledge-search__search_docs",
    "ToolSearch",
    "WebSearch",
})

# 14 days: the 6 domain skills authored by TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC
# (date_added: "2026-08-05") are 10 days old as of this ticket's investigation — still inside a
# 14-day window, matching the requirement that they not be flagged on day 1.
# TCK-20260705-SIX-SKILLS-INVESTIGATION's pre-existing zero-invocation skills stayed at zero past
# 30+ days regardless of grace length, so grace-period length mainly protects genuinely-new
# skills, not a cure for structurally-redundant ones (TCK-20260810-SKILL-USAGE-RETRO-TRACKING).
SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS = 14


def build_search_count_section(tools: list) -> dict:
    per_run: dict = defaultdict(int)
    total = 0
    for record in tools:
        if record.get("tool") in SEARCH_TOOL_NAMES:
            # tools.jsonl records issued outside any workflow run carry run_id=None
            # (legacy_reader.py's "interactive_null" shape) — grouped under a literal
            # "unattributed" key rather than None, since a None dict key breaks
            # json.dumps(sort_keys=True)'s key comparison against the str keys of real runs.
            run_id = record.get("run_id") or "unattributed"
            per_run[run_id] += 1
            total += 1
    return {
        "derivation": "Derived from tools.jsonl's literal `tool` field, filtered to "
                      "SEARCH_TOOL_NAMES = {mcp__knowledge-search__search_docs, ToolSearch, "
                      "WebSearch}. This is a finer-grained derivation than the ticket AC's literal "
                      "'tool_call_count' wording — tool_call_count is a coarse per-event total-tool"
                      "-activity aggregate on events.jsonl records, and does not distinguish a search "
                      "call from any other tool call. This report uses the more precise, still-100%"
                      "-existing-data derivation because it actually answers 'how many follow-up "
                      "searches happened', per this ticket's plan.md Step 3.",
        "per_run": dict(per_run),
        "total": total,
    }


def build_raw_investigation_count_section(tools: list) -> dict:
    per_run: dict = defaultdict(int)
    total = 0
    for record in tools:
        if record.get("tool") == "Read":
            # Same run_id=None -> "unattributed" convention as build_search_count_section
            # (see that function's inline comment) — reused verbatim, not reinvented.
            run_id = record.get("run_id") or "unattributed"
            per_run[run_id] += 1
            total += 1

    search_total = build_search_count_section(tools)["total"]
    if search_total > 0:
        ratio = round(total / search_total, 4)
    else:
        ratio = (
            "undefined: zero search_count.total in corpus, cannot compute a ratio "
            "without a fabricated denominator"
        )

    return {
        "derivation": (
            "Derived from tools.jsonl's literal `tool` field, filtered to `tool == \"Read\"` "
            "(the single most common non-Bash tool in this corpus). `Grep` is not counted "
            "because no distinct `Grep` tool name is ever recorded in this environment; "
            "grep-equivalent work runs through the catch-all `Bash` tool, which is excluded "
            "here for the same non-distinguishability rationale documented on "
            "SEARCH_TOOL_NAMES above (some Bash calls are search/grep-flavored by content, "
            "but that is not distinguishable by tool name alone). This section is therefore "
            "a proxy for raw investigation effort (how often the agent had to open a file "
            "directly to look), not a literal grep-call count. read_to_search_ratio is "
            "computed corpus-wide only (this section's total Read count divided by "
            "search_count's total, both derived from this same tools list), never per-run, "
            "because search_count.per_run and this section's per_run do not share an "
            "identical run_id key set in general; if search_count.total is 0 the ratio is "
            "the literal string above instead of a divided-by-zero or fabricated value."
        ),
        "per_run": dict(per_run),
        "total": total,
        "read_to_search_ratio": ratio,
    }


# Relocated here from skill_usage_metric.py (TCK-20260810-SKILL-USAGE-RETRO-TRACKING) to resolve
# the identical circular-import constraint SEARCH_TOOL_NAMES/build_search_count_section faced
# above: skill_usage_metric.py already imports DEFAULT_TOOLS_FILE/load_jsonl FROM
# generate_retro.py, so generate_retro.py importing build_skill_usage_section back FROM
# skill_usage_metric.py would create a two-file import cycle. skill_usage_metric.py now
# re-imports this name from generate_retro.py's existing import statement instead of defining it
# — semantics, regex, and output shape are unchanged, only the file of definition moved.
#
# tools.jsonl's `input_summary` field is a Python-dict-repr string (e.g. "{'skill': 'graphify', ...}"),
# not JSON — confirmed by direct inspection. json.loads() on this field raises
# json.JSONDecodeError; regex extraction is the only correct approach.
_SKILL_NAME_RE = re.compile(r"'skill':\s*'([^']*)'")


def build_skill_usage_section(tools: list) -> dict:
    per_skill: dict = defaultdict(int)
    per_skill_per_run: dict = defaultdict(lambda: defaultdict(int))
    total = 0
    unparseable = 0

    for record in tools:
        if record.get("tool") != "Skill":
            continue
        total += 1
        # tools.jsonl records issued outside any workflow run carry run_id=None (legacy_reader.py's
        # "interactive_null" shape) — grouped under a literal "unattributed" key rather than None,
        # since a None dict key breaks json.dumps(sort_keys=True)'s key comparison against the str
        # keys of real runs (same convention as build_search_count_section's own run_id handling).
        run_id = record.get("run_id") or "unattributed"
        match = _SKILL_NAME_RE.search(record.get("input_summary", ""))
        if match:
            skill_name = match.group(1)
            per_skill[skill_name] += 1
            per_skill_per_run[skill_name][run_id] += 1
        else:
            unparseable += 1

    return {
        "total_skill_invocations": total,
        "unparseable": unparseable,
        "per_skill": dict(per_skill),
        "per_skill_per_run": {k: dict(v) for k, v in per_skill_per_run.items()},
        "derivation": (
            "Derived from tools.jsonl's literal `tool` field, filtered to `tool == 'Skill'`, "
            "with the skill name extracted from `input_summary` via regex "
            r"(r\"'skill':\s*'([^']*)'\") — never json.loads(), since input_summary is a Python "
            "dict-repr string, not JSON. Records where the regex finds no match are counted under "
            "`unparseable`, never silently dropped. `unattributed` covers Skill invocations with "
            "no run_id (interactive, outside any workflow run). Distinct from generate_retro.py's "
            "tag_breakdown_skill aggregate — this is a raw per-skill invocation count, not a "
            "tag-driven gate-hit count."
        ),
    }


def compute_zero_invocation_skill_flags(
    tools: list, skills_dir: Path | None = None, today: date | None = None
) -> dict:
    """All-time (never period-scoped) cross-reference of the real `.claude/skills/*/SKILL.md`
    catalog against `build_skill_usage_section(tools)`'s per_skill counts — flags any skill with
    zero invocations, split into two non-conflated buckets rather than one undifferentiated list:

    - `flagged_stale`: a real, parseable `date_added` older than the grace period, zero
      invocations. A confirmed-age signal.
    - `flagged_unknown_age`: no `date_added` (missing, unparseable frontmatter, or unparseable
      date string), zero invocations. A fail-open, lower-certainty signal — cannot prove the
      skill is genuinely stale, but there is no recorded authorship date and no invocation either.
      This fail-open choice is what makes `backend-testing`'s real pre-TCK-20260805-COMMUNITY-
      SKILL-SWAP-UNDISCLOSED state (no `date_added` at all) correctly flaggable.

    `skills_dir`/`today` default to the real on-disk catalog / real wall-clock date only when the
    caller omits them — accepting both as parameters (rather than reading them internally by
    default) keeps this function's own unit tests deterministic. This function's real-filesystem
    default is safe only because `generate()` (see Step 4) never reaches this function unless the
    caller explicitly supplied `all_tools` — callers that have not opted in never trigger a real
    `.claude/skills/` scan as a side effect.

    Read-only: only ever calls `skills_dir.iterdir()` and `skill_md.read_text()`. Never writes
    to `.claude/skills/` or anywhere else.
    """
    skills_dir = skills_dir or _DEFAULT_SKILLS_DIR
    today = today or datetime.now(timezone.utc).date()

    per_skill = build_skill_usage_section(tools)["per_skill"]

    flagged_stale = []
    flagged_unknown_age = []
    catalog_parse_errors = []

    for skill_path in sorted(skills_dir.iterdir()):
        skill_md = skill_path / "SKILL.md"
        if not skill_md.is_file():
            continue
        name = skill_path.name
        if per_skill.get(name, 0) > 0:
            continue

        try:
            fm = extract_frontmatter(skill_md.read_text())
        except ValueError:
            catalog_parse_errors.append(name)
            flagged_unknown_age.append(name)
            continue

        date_added = fm.get("date_added") if fm else None
        if not date_added:
            flagged_unknown_age.append(name)
            continue

        try:
            added_date = datetime.strptime(date_added, "%Y-%m-%d").date()
        except ValueError:
            flagged_unknown_age.append(name)
            continue

        if (today - added_date).days >= SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS:
            flagged_stale.append(name)

    return {
        "grace_period_days": SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS,
        "flagged_stale": sorted(flagged_stale),
        "flagged_unknown_age": sorted(flagged_unknown_age),
        "catalog_parse_errors": sorted(catalog_parse_errors),
        "derivation": (
            "All-time (never period-scoped) cross-reference of the real .claude/skills/*/SKILL.md "
            "catalog against build_skill_usage_section(tools)'s per_skill counts. A skill with "
            "any nonzero invocation count is never flagged, regardless of age. Of the remaining "
            "zero-invocation skills: `flagged_stale` requires a real, parseable `date_added` "
            f"older than the {SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS}-day grace period — a "
            "confirmed-age signal. `flagged_unknown_age` covers skills with no (or unparseable) "
            "`date_added` and zero invocations — an honest, lower-certainty signal, not proof of "
            "staleness, since no authorship date can be established. This fail-open policy on "
            "missing date_added is deliberate: it is what makes backend-testing's real pre-"
            "TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED state (no date_added field at all) "
            "correctly flaggable, per TCK-20260810-SKILL-USAGE-RETRO-TRACKING's AC2."
        ),
    }


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



# KGMCP cache-access-log grouping window (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-
# USAGE-DASHBOARD): a "write" event for the same real cache row (same cache_level + query_hash/
# repo_branch_scope, or same cache_level + packet_id) following ANY prior event for that same row
# within this many seconds is flagged as a repeated refetch — content that a HIT should have
# served instead of a fresh provider round-trip / packet assembly. 300s (5 min) is a deliberate,
# generous window: shorter windows would flag ordinary independent re-queries across unrelated
# phases of the same run as "repeated," which is not the wasted-refetch signal this is meant to
# surface.
KGMCP_REFETCH_WINDOW_SECONDS = 300


def _kgmcp_access_log_group_key(row: dict):
    if row.get("cache_level") == "level2_context_packet":
        return ("level2_context_packet", row.get("packet_id"))
    return ("level1_provider_result", row.get("query_hash"), row.get("repo_branch_scope"))


def _kgmcp_verdict(
    total_hits: int,
    total_writes: int,
    dead_write_count: int,
    repeated_refetch_count: int,
    search_calls_total: int,
    coverage_rate: float | None,
) -> tuple[str, str]:
    """Turns the raw counters below into a single glanceable verdict + explanation — the actual
    headline ask behind this section ("is the knowledge gateway cache good, is it inefficient"),
    not just a table of numbers a reader has to interpret themselves. Every clause here is a
    direct, literal readout of an already-computed number — no fabricated score, no LLM judgment
    call, just a rule-based label over real counts. Returns (verdict_label, explanation_text).

    A low `coverage_rate` is architectural, not a fixable cache inefficiency: this cache
    (`retrieval_cache.py::log_cache_access()`) is wired only into `knowledge_gateway_mcp.py`'s
    `knowledge_context`/`knowledge_status` tools, while the hard-rule-mandated
    `mcp__knowledge-search__search_docs` is served by a completely separate, uninstrumented
    implementation (`knowledge_search.py`) that never touches this cache path at all. The
    low-coverage clause appended below says so explicitly rather than implying the cache itself
    is underperforming (TCK-20260824-RETRO-METRIC-CAVEATS).
    """
    total_events = total_hits + total_writes

    if total_events == 0:
        if search_calls_total > 0:
            return (
                "NOT IN USE",
                f"Zero KGMCP cache hit/write events recorded against {search_calls_total} real "
                "search_docs/graphify/ToolSearch calls in this corpus — retrieval work is not "
                "touching the cache path at all. This is a bypass, not merely low reuse: the "
                "cache cannot be judged efficient or inefficient because it is not being "
                "exercised."
            )
        return (
            "NO DATA",
            "No KGMCP cache activity and no search/graphify tool calls recorded in this corpus — "
            "nothing to evaluate yet.",
        )

    reuse_rate = total_hits / total_events
    parts = []
    if reuse_rate >= 0.5:
        verdict = "EFFECTIVE"
        parts.append(
            f"{reuse_rate * 100:.0f}% of cache access events were hits (reuse) rather than fresh "
            "writes — the cache is meaningfully saving repeated retrieval work."
        )
    elif reuse_rate >= 0.2:
        verdict = "MODERATE"
        parts.append(
            f"Only {reuse_rate * 100:.0f}% of cache access events were hits — the cache is reused "
            "sometimes but still does a lot of write-once work."
        )
    else:
        verdict = "LOW VALUE"
        parts.append(
            f"Only {reuse_rate * 100:.0f}% of cache access events were hits — the cache is mostly "
            "write-once, rarely reused."
        )

    if dead_write_count:
        parts.append(
            f"{dead_write_count} write(s) were never hit before being superseded (or before the "
            "end of the observed log) — wasted writes with no payoff so far."
        )

    if repeated_refetch_count:
        parts.append(
            f"{repeated_refetch_count} repeated refetch(es) detected within "
            f"{KGMCP_REFETCH_WINDOW_SECONDS}s of a prior access to the same row — duplicated work "
            "the cache should have caught but didn't."
        )

    if search_calls_total > 0:
        if coverage_rate is not None and coverage_rate < 0.5:
            parts.append(
                f"Coverage is low: {total_events} cache event(s) against {search_calls_total} "
                f"real search/graphify calls ({coverage_rate * 100:.0f}% coverage) — much "
                "retrieval activity bypasses the cache path entirely, so even a high reuse rate "
                "on the events that DO reach the cache understates the real gap. This reflects "
                "two independently-implemented tools (only knowledge_context/knowledge_status "
                "are cache-instrumented; search_docs is served by a separate, uninstrumented "
                "implementation), not a fixable inefficiency in the cache itself."
            )
            if verdict == "EFFECTIVE":
                verdict = "MODERATE"

    return verdict, " ".join(parts)


def compute_kgmcp_cache_efficiency_metrics(
    access_log_rows: list[dict], tools: list[dict] | None = None,
    all_tools: list[dict] | None = None,
) -> dict:
    """Pure, read-only computation over `access_log_rows` — tools/retrieval_cache.py::
    read_cache_access_log()'s real output, or a fixture list in the same row shape in tests —
    plus `tools` (tools.jsonl rows, same shape build_search_count_section() already consumes)
    for the coverage-vs-usage signal below. Mirrors compute_retrieval_metrics()'s own shape (a
    pure function over already-loaded data, never opens retrieval_cache.db itself) so this stays
    independently testable and so the CLI Markdown report (generate()) and the JSON API
    (DashboardCache.get_agent_monitoring_stats()) compute from the exact same call, never two
    independently-drifting implementations.

    This is deliberately more than a raw hit/write counter — the real ask behind this section is
    "can a human glance at this and judge whether the knowledge gateway cache is working well or
    not," so four distinct efficiency signals are computed, each answering a different question a
    raw count alone cannot:
    - `overall_reuse_rate`/per-ticket/per-agent reuse_rate — hit / (hit + write): is the cache
      mostly reused (high value) or mostly write-once (low value)?
    - `repeated_refetches` — same real cache row written again within
      KGMCP_REFETCH_WINDOW_SECONDS of a prior access: duplicated work the cache should have
      caught but didn't.
    - `dead_writes`/`dead_write_count` — a write never hit before the next write to that same row
      (or before the end of the observed log): wasted writes with no payoff so far.
    - `coverage` — real search_docs/graphify/ToolSearch call volume (from `tools`, via
      build_search_count_section()) compared against total cache access events: how much real
      retrieval activity even touches the cache path at all, vs. bypasses it entirely. A period
      with substantial search/graphify activity but zero cache events is a real, notable finding
      (cache not being used at all) — surfaced explicitly by `verdict`, never hidden by only
      reporting rates that are undefined/zero without an accompanying "coverage: 0" flag.
    `verdict`/`verdict_explanation` (see _kgmcp_verdict()) fold all four signals into one
    glanceable label + 1-3 sentence explanation, so a reader is never left to eyeball a table of
    numbers to answer "is this good or bad."

    A low `coverage_rate` (`coverage["coverage_rate"]`) is an architectural fact, not a fixable
    cache inefficiency: this cache (`retrieval_cache.py::log_cache_access()`) is wired only into
    `tools/knowledge_gateway_mcp.py`'s `knowledge_context`/`knowledge_status` tools, while the
    hard-rule-mandated `mcp__knowledge-search__search_docs` — the actual bulk of real search
    volume feeding `search_calls_total` above — is served by a completely separate,
    uninstrumented implementation (`tools/knowledge_search.py`, confirmed zero references to
    `retrieval_cache`/`knowledge_gateway_cache`) that never touches this cache path at all. A
    near-zero coverage number therefore reflects two independently-implemented tools, only one
    of which is cache-instrumented, not evidence the cache is being underused where it applies
    (TCK-20260824-RETRO-METRIC-CAVEATS).

    `search_calls_total` (the coverage denominator) is deliberately computed from `all_tools`
    when the caller supplies it, not the period-scoped `tools` (TCK-20260826-KGMCP-COVERAGE-RATE-
    OVERFLOW). `access_log_rows` (the numerator's source) is always the all-time corpus — main()
    never period-slices `kgmcp_access_log` (see generate()'s own docstring) — so pairing that
    all-time numerator against a period-scoped `tools` denominator produced values like 1059.3%
    on a one-week report: not a real coverage signal, just a time-window mismatch. Falls back to
    `tools` when `all_tools` is not supplied (e.g. a direct unit-test call with only `tools` set),
    preserving prior behavior exactly for those callers.

    `ticket_id`/`agent` absent on a row (ad-hoc, non-workflow calls, or a stale/unmigrated sidecar
    — see tools/retrieval_cache.py::read_current_run_sidecar()) are grouped under the literal
    "unattributed" key, matching build_search_count_section()'s own established run_id=None ->
    "unattributed" convention, reused here rather than reinvented.
    """
    total_hits = sum(1 for r in access_log_rows if r.get("event_type") == "hit")
    total_writes = sum(1 for r in access_log_rows if r.get("event_type") == "write")
    stale_attributed = sum(1 for r in access_log_rows if r.get("sidecar_stale"))

    def _reuse_rate(hit: int, write: int):
        denom = hit + write
        return round(hit / denom, 4) if denom else None

    per_ticket = defaultdict(lambda: {"hit": 0, "write": 0})
    per_agent = defaultdict(lambda: {"hit": 0, "write": 0})
    for r in access_log_rows:
        event_type = r.get("event_type")
        if event_type not in ("hit", "write"):
            continue
        ticket_id = r.get("ticket_id") or "unattributed"
        agent = r.get("agent") or "unattributed"
        per_ticket[ticket_id][event_type] += 1
        per_agent[agent][event_type] += 1

    per_ticket_out = {
        t: {"hit": c["hit"], "write": c["write"], "reuse_rate": _reuse_rate(c["hit"], c["write"])}
        for t, c in per_ticket.items()
    }
    per_agent_out = {
        a: {"hit": c["hit"], "write": c["write"], "reuse_rate": _reuse_rate(c["hit"], c["write"])}
        for a, c in per_agent.items()
    }

    grouped = defaultdict(list)
    for r in access_log_rows:
        if r.get("ts") is None:
            continue
        grouped[_kgmcp_access_log_group_key(r)].append(r)

    repeated_refetches = []
    dead_writes = []
    for rows in grouped.values():
        rows_sorted = sorted(rows, key=lambda r: r["ts"])

        # Repeated-refetch detection: any 'write' following ANY prior event (hit or write) for
        # this same real cache row within the window.
        for i in range(1, len(rows_sorted)):
            cur = rows_sorted[i]
            if cur.get("event_type") != "write":
                continue
            prev = rows_sorted[i - 1]
            gap = cur["ts"] - prev["ts"]
            if gap <= KGMCP_REFETCH_WINDOW_SECONDS:
                repeated_refetches.append(
                    {
                        "cache_level": cur.get("cache_level"),
                        "run_id": cur.get("run_id"),
                        "ticket_id": cur.get("ticket_id") or "unattributed",
                        "agent": cur.get("agent") or "unattributed",
                        "gap_s": round(gap, 1),
                        "prior_run_id": prev.get("run_id"),
                        "prior_event_type": prev.get("event_type"),
                    }
                )

        # Dead-write detection: a 'write' with no 'hit' between it and the next 'write' for the
        # same row (or the end of the observed log, if it is the row's most recent write) never
        # paid off within the data this function can see.
        write_positions = [i for i, r in enumerate(rows_sorted) if r.get("event_type") == "write"]
        for pos, i in enumerate(write_positions):
            next_write_i = (
                write_positions[pos + 1] if pos + 1 < len(write_positions) else len(rows_sorted)
            )
            window = rows_sorted[i + 1:next_write_i]
            if not any(r.get("event_type") == "hit" for r in window):
                w = rows_sorted[i]
                dead_writes.append(
                    {
                        "cache_level": w.get("cache_level"),
                        "run_id": w.get("run_id"),
                        "ticket_id": w.get("ticket_id") or "unattributed",
                        "agent": w.get("agent") or "unattributed",
                        "ts": w.get("ts"),
                    }
                )

    # TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW: access_log_rows (the numerator's source) is
    # always the all-time corpus (see generate()'s own docstring on kgmcp_access_log never being
    # period-sliced) — so the denominator must also be all-time, or coverage_rate compares two
    # different time windows and can exceed 100% for a reason that has nothing to do with real
    # cache coverage (e.g. 1059.3% on a --week report: all-time cache events over one week's
    # worth of search calls). `all_tools` (already loaded once, unfiltered, in main() for the
    # Zero-Invocation Skill Flags section) is preferred when the caller explicitly supplies it;
    # `tools` remains the fallback so every pre-existing direct call/test with only `tools` set
    # keeps its exact prior behavior.
    search_calls_total = build_search_count_section(
        all_tools if all_tools is not None else (tools or [])
    )["total"]
    total_events = total_hits + total_writes
    coverage_rate = (total_events / search_calls_total) if search_calls_total else None

    verdict, verdict_explanation = _kgmcp_verdict(
        total_hits, total_writes, len(dead_writes), len(repeated_refetches),
        search_calls_total, coverage_rate,
    )

    return {
        "total_hits": total_hits,
        "total_writes": total_writes,
        "overall_reuse_rate": _reuse_rate(total_hits, total_writes),
        "per_ticket": per_ticket_out,
        "per_agent": per_agent_out,
        "repeated_refetch_window_seconds": KGMCP_REFETCH_WINDOW_SECONDS,
        "repeated_refetches": repeated_refetches,
        "dead_writes": dead_writes,
        "dead_write_count": len(dead_writes),
        "coverage": {
            "search_calls_total": search_calls_total,
            "cache_events_total": total_events,
            "coverage_rate": coverage_rate,
        },
        "verdict": verdict,
        "verdict_explanation": verdict_explanation,
        "stale_attribution_count": stale_attributed,
        "derivation": (
            "Derived from tools/retrieval_cache.py::read_cache_access_log()'s real "
            "retrieval_cache_access_log rows (Level 1 provider-result + Level 2 context-packet "
            "cache hit/write events only — 'invalidate' is a schema-supported but never-emitted "
            "event_type today) plus tools.jsonl's real search_docs/graphify/ToolSearch call "
            "volume (via build_search_count_section(), for `coverage` only). reuse_rate = hit / "
            "(hit + write) per ticket/agent/overall — the fraction of real access events served "
            "from cache rather than re-fetched. repeated_refetches flags a 'write' event for the "
            "same real cache row (same cache_level + query_hash/repo_branch_scope, or same "
            f"cache_level + packet_id) following any prior event for that row within "
            f"{KGMCP_REFETCH_WINDOW_SECONDS}s — content re-fetched instead of reused. "
            "dead_writes flags a 'write' never followed by a 'hit' before the next write to that "
            "same row (or the end of the observed log) — a wasted write, as of what this function "
            "can currently see (a row that is still live may yet be hit later; this is not a "
            "permanent-deadness claim past the observed data). coverage compares total cache "
            "events against real search/graphify tool-call volume — a period with substantial "
            "search activity but few/zero cache events means retrieval work is bypassing the "
            "cache path, a real, distinct finding from a low reuse_rate. `ticket_id`/`agent` "
            "absent on a row (ad-hoc calls or a stale sidecar) are grouped under the literal "
            "'unattributed' key, mirroring build_search_count_section()'s run_id=None convention. "
            "`stale_attribution_count` counts rows whose `.claude/current_run` sidecar pointed at "
            "an already-closed ticket at log time (tools/retrieval_cache.py::"
            "_sidecar_run_is_stale()) — a real, disclosed known limitation of sidecar-based "
            "attribution (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD "
            "Scope item 6), not a fixed one; these rows are still counted in hit/write/reuse-rate "
            "totals above, just flagged rather than silently trusted or dropped. `verdict`/"
            "`verdict_explanation` are a rule-based summary of the four signals above (reuse rate, "
            "repeated refetches, dead writes, coverage) — every clause is a literal readout of an "
            "already-computed number, never a fabricated score."
        ),
    }


def compute_retro_metrics(
    runs, events, tickets_root=None, tools=None, kgmcp_access_log=None, all_tools=None,
) -> dict:
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

    # Active/idle duration split (TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT): a run's raw duration_s
    # (end_ts - start_ts) doesn't distinguish real working time from idle gaps between phase
    # transitions, which distorts what "slow" means below. duration_utils.compute_active_idle_split
    # is the single shared, pure computation (never reimplemented here) — indexed once by run_id
    # since it needs that run's own events.jsonl rows, ordered strictly by ts (not seq).
    events_by_run_id = defaultdict(list)
    for e in events:
        rid = e.get("run_id")
        if rid:
            events_by_run_id[rid].append(e)

    def _duration_split_fields(run_row: dict) -> dict:
        split = compute_active_idle_split(
            run_row.get("start_ts"),
            run_row.get("end_ts"),
            events_by_run_id.get(run_row.get("run_id", ""), []),
        )
        if split is None:
            return {}
        return {"active_duration_s": split["active_duration_s"], "idle_gap_s": split["idle_gap_s"]}

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
            **_duration_split_fields(r),
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
            **_duration_split_fields(item),
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
        # Additive (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD):
        # `tools`/`kgmcp_access_log` default to None, so every pre-existing caller that omits them
        # (the CLI's own historical positional-args call pattern, and every pre-existing test
        # constructed before this ticket) gets these two keys computed over an empty list — real,
        # not fabricated, values (build_skill_usage_section([])/compute_kgmcp_cache_efficiency_
        # metrics([])'s own genuine zero/empty-input output), never omitted from the dict. This
        # keeps the "CLI Markdown report and JSON API stay logically consistent" property
        # TCK-20260718-RETRO-STATS-REFACTOR established: both consumers read these same two keys
        # from this one function, rather than generate() computing skill_usage separately (as it
        # did before this ticket) and the JSON API never seeing it at all.
        "skill_usage": build_skill_usage_section(tools or []),
        "kgmcp_cache_efficiency": compute_kgmcp_cache_efficiency_metrics(
            kgmcp_access_log or [], tools=tools or [], all_tools=all_tools
        ),
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


def compute_search_investigation_trend(tools: list[dict]) -> dict:
    """Thin wrapper over the two relocated section functions above — adds no filtering logic of
    its own, so the trended report-over-report numbers this feeds stay identical to
    retrieval_baseline_metrics.py's one-off snapshot numbers (TCK-20260810-CONTEXT-TOOLING-
    EFFECTIVENESS-TRACKING)."""
    return {
        "search_count": build_search_count_section(tools),
        "raw_investigation_count": build_raw_investigation_count_section(tools),
    }


def compute_tool_safety_metrics(events: list[dict], tools: list[dict]) -> dict:
    """Pure, read-only computation over `events`/`tools` auditing (1) search-before-grep
    hard-rule compliance (CLAUDE.md) for tools.jsonl rows within real Investigate-phase
    (run_id, seq) pairs, identified via events.jsonl's `phase` field (the authoritative
    phase-transition record — never tools.jsonl's own, less-authoritative `phase` field, which
    is null for records predating TCK-20260719-LIVE-PHASE-AGENT-LABEL), and (2)
    parity_index.py write-safety across the whole `tools` argument as passed in (not scoped to
    Investigate-phase pairs) — a count of Edit/Write calls into docs/parity_ledger/*.yaml made in
    a run that ALSO invokes parity_index.py's build path (same run_id, anywhere in that run's own
    tool history — a normal parity-ledger edit alone, with no co-occurring build call in the same
    run, is not flagged; TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE), and of
    `parity_index.py build` invocations targeting the real repo parity-index/parity.db path
    instead of a scratch path. Never calls write_lines/write_line or opens any file; operates
    entirely on its `events`/`tools` arguments.

    tools.jsonl rows with seq: null or seq <= 0 (shadow-packet rows) are structurally excluded
    by never matching an Investigate-phase key derived from events.jsonl (whose seq is
    non-nullable and >= 1 for real phase events) — no explicit skip branch is needed.

    `search_before_grep.compliance_rate` only sees the orchestrating run's own direct tools.jsonl
    rows for each (run_id, seq) pair — it has no visibility into a dispatched sub-agent's (e.g.
    `investigator`) own tool calls, which are logged, if at all, outside this pair's key. When
    Investigate is properly delegated to a real sub-agent (the standard, correct pattern), that
    sub-agent's own search_docs/grep sequence is invisible here; a pair marked non-compliant may
    reflect an orchestrator-level incidental call rather than the real investigation's own
    behavior. The true compliance rate for delegated investigation work is unknown and plausibly
    higher than this number (TCK-20260824-RETRO-METRIC-CAVEATS).
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

    # Read-count correlation (TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING): reuses
    # pair_tool_rows/per_pair_compliance above, already built per Investigate-phase pair — not a
    # second scan of `tools`. Real evidence for or against "does search-before-grep compliance
    # reduce raw investigation effort", not an assumed causal story.
    pair_read_counts = {
        key: sum(1 for r in rows if r.get("tool") == "Read") for key, rows in pair_tool_rows.items()
    }
    compliant_reads = [
        count for key, count in pair_read_counts.items() if per_pair_compliance[key]
    ]
    non_compliant_reads = [
        count for key, count in pair_read_counts.items() if not per_pair_compliance[key]
    ]

    def _group_stats(counts):
        return {
            "count": len(counts),
            "median": statistics.median(counts) if counts else None,
            "average": (sum(counts) / len(counts)) if counts else None,
        }

    read_count_correlation = {
        "compliant_group": _group_stats(compliant_reads),
        "non_compliant_group": _group_stats(non_compliant_reads),
        "derivation": (
            "Per-Investigate-pair Read-tool-call count, split by that pair's own "
            "search-before-grep compliance (per_pair_compliance above) — reuses pair_tool_rows, "
            "never a second scan of tools. median/average are computed independently for the "
            "compliant and non-compliant groups; an empty group reports None for both rather than "
            "a fabricated 0 or a statistics.median([]) crash. A real evidence signal for whether "
            "compliance correlates with lower raw-investigation effort — not a causal claim."
        ),
    }

    run_ids_with_build_calls = {
        r.get("run_id") for r in tools if _is_parity_index_build_call(r) and r.get("run_id")
    }
    parity_yaml_writes = [
        r
        for r in tools
        if _is_parity_ledger_yaml_write(r) and r.get("run_id") in run_ids_with_build_calls
    ]
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
        "read_count_correlation": read_count_correlation,
    }


def generate(
    runs, events, label, week_str=None, tickets_root=None, tools=None, all_tools=None,
    kgmcp_access_log=None,
):
    """Render `compute_retro_metrics()`'s result to the retro report's Markdown text — the sole
    rendering consumer of that function. Signature/behavior unchanged by the
    TCK-20260718-RETRO-STATS-REFACTOR extraction; see that ticket's plan.md Step 3 for the
    byte-identical-output proof this relies on.

    `all_tools` (TCK-20260810-SKILL-USAGE-RETRO-TRACKING) is deliberately NOT defaulted from
    `tools` — `tools` is period-scoped (sliced to the reporting window by main()), but the
    zero-invocation-skill flag is an all-time question ("has this skill ever been invoked"), so
    conflating the two would make the flag silently wrong on every --week/--days report. The
    Zero-Invocation Flags subsection — and compute_zero_invocation_skill_flags itself, whose own
    skills_dir default reaches the real .claude/skills/ catalog on disk — is computed and
    rendered ONLY when the caller's own argument is explicitly non-None (see `zif` below). Never
    substitute `tools` (or any other implicit default) for a missing `all_tools` here: doing so
    was a confirmed architecture-review violation (2026-08-15) that silently coupled 121+
    pre-existing tests' synthetic fixtures to the real, unmocked skills catalog.

    `kgmcp_access_log` (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD)
    is, like `all_tools`, deliberately never period-sliced by the caller — main() always passes
    the full corpus regardless of --days/--week/--all, mirroring the existing `## Retrieval
    Quality` section's own precedent ("visible under --all, not --days/--week, since these run_ids
    are deliberately unlinked from any runs.jsonl row") for the same reason: retrieval_cache.db's
    access-log rows are attributed via the `.claude/current_run` sidecar at call time, not via any
    runs.jsonl timestamp this function's period filters already operate on.
    """
    metrics = compute_retro_metrics(
        runs, events, tickets_root, tools=tools, kgmcp_access_log=kgmcp_access_log,
        all_tools=all_tools,
    )
    retrieval_metrics = compute_retrieval_metrics(events)
    shadow_comparison = compute_shadow_baseline_comparison(events)
    tool_safety = compute_tool_safety_metrics(events, tools or [])
    sit = compute_search_investigation_trend(tools or [])
    pircc = compute_parity_index_readpath_call_count(tools or [])
    # su/kce are read from `metrics` (compute_retro_metrics()'s own output), not recomputed via a
    # second, separate call — guarantees this Markdown renderer and the JSON API
    # (DashboardCache.get_agent_monitoring_stats()) always report identical numbers for both
    # sections, since both now source from the exact same compute_retro_metrics() call.
    su = metrics["skill_usage"]
    kce = metrics["kgmcp_cache_efficiency"]
    zif = compute_zero_invocation_skill_flags(all_tools) if all_tools is not None else None
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
        lines.append("| run_id | duration | active | idle | final_status |")
        lines.append("|---|---|---|---|---|")
        idle_dominated_count = 0
        for r in metrics["slow_runs"]:
            dur_s = r.get("duration_s", 0) or 0
            dur_min = dur_s // 60
            active_s, idle_s = r.get("active_duration_s"), r.get("idle_gap_s")
            if active_s is None or idle_s is None:
                active_str, idle_str = "—", "—"
            else:
                active_str, idle_str = f"{active_s // 60:g} min", f"{idle_s // 60:g} min"
                if dur_s > 0 and idle_s >= dur_s / 2:
                    idle_dominated_count += 1
            lines.append(
                f"| {r.get('run_id','')} | {dur_min} min | {active_str} | {idle_str} | "
                f"{r.get('final_status','')} |"
            )
        if idle_dominated_count:
            lines.append("")
            lines.append(
                f"_{idle_dominated_count} of the runs above spend at least half their reported "
                "duration idle (gaps ≥ 30 min between phase transitions, e.g. waiting on human "
                "review) rather than in active work — see `active`/`idle` columns; \"slow\" here "
                "does not mean \"took a long time to actively work on.\"_"
            )
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
            lines.append("| run_id | tier | duration_s | tier median | ratio | active | idle |")
            lines.append("|---|---|---|---|---|---|---|")
            duration_outlier_idle_dominated = 0
            for o in outliers["duration_s"]:
                active_s, idle_s = o.get("active_duration_s"), o.get("idle_gap_s")
                if active_s is None or idle_s is None:
                    active_str, idle_str = "—", "—"
                else:
                    active_str, idle_str = f"{active_s // 60:g} min", f"{idle_s // 60:g} min"
                    if o["duration_s"] > 0 and idle_s >= o["duration_s"] / 2:
                        duration_outlier_idle_dominated += 1
                lines.append(
                    f"| {o['run_id']} | {o['tier']} | {o['duration_s']} | {o['median']} | "
                    f"{o['ratio']}x | {active_str} | {idle_str} |"
                )
            if duration_outlier_idle_dominated:
                lines.append("")
                lines.append(
                    f"_{duration_outlier_idle_dominated} of the duration outliers above spend at "
                    "least half their reported duration idle rather than in active work — see "
                    "`active`/`idle` columns; a large ratio here does not mean \"took unusually "
                    "long to actively work on.\"_"
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

    # Search & Investigation Effort (TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING): trends
    # retrieval_baseline_metrics.py's search_count/raw_investigation_count/read_to_search_ratio
    # numbers (relocated into this module to resolve a circular-import constraint, see
    # compute_search_investigation_trend) report-over-report. Additive, separately-gated section —
    # omitted entirely (not rendered empty) when the period has zero search or Read tool calls.
    sc = sit["search_count"]
    ric = sit["raw_investigation_count"]
    if sc["total"] + ric["total"] > 0:
        lines.append("## Search & Investigation Effort")
        lines.append("")

        lines.append("### Search Calls (Follow-Up Search Tooling)")
        lines.append("")
        lines.append(f"**Total:** {sc['total']}")
        lines.append("")

        lines.append("### Raw Investigation (Read) Calls")
        lines.append("")
        ratio = ric["read_to_search_ratio"]
        ratio_str = ratio if isinstance(ratio, str) else f"{ratio}"
        lines.append(f"**Total:** {ric['total']}")
        lines.append(f"**Read-to-search ratio:** {ratio_str}")
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
        lines.append(
            "_Only the orchestrating run's own direct tools.jsonl rows are visible to this "
            "detector — a dispatched sub-agent's (e.g. `investigator`) own search/grep calls are "
            "not attributed back to this pair, so a 'non-compliant' pair may reflect an "
            "orchestrator-level incidental call rather than the real investigation's own "
            "behavior. The true compliance rate for delegated investigation work is unknown and "
            "plausibly higher than the rate below._"
        )
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
            f"**`docs/parity_ledger/*.yaml` edits co-occurring with a same-run "
            f"`parity_index.py build` call:** "
            f"{pws['parity_ledger_yaml_write_count']}"
        )
        lines.append(
            f"**Unsafe `parity_index.py build` invocations (real repo path):** "
            f"{pws['unsafe_parity_build_count']}"
        )
        lines.append("")

        rcc = tool_safety["read_count_correlation"]
        lines.append("### Read-Count Correlation (Search-Before-Grep Compliance)")
        lines.append("")

        def _fmt_stat(value):
            return "n/a" if value is None else f"{value:.1f}"

        compliant_group = rcc["compliant_group"]
        non_compliant_group = rcc["non_compliant_group"]
        lines.append("| Group | Pairs | Median Read count | Avg Read count |")
        lines.append("|---|---|---|---|")
        lines.append(
            f"| Compliant | {compliant_group['count']} | "
            f"{_fmt_stat(compliant_group['median'])} | {_fmt_stat(compliant_group['average'])} |"
        )
        lines.append(
            f"| Non-compliant | {non_compliant_group['count']} | "
            f"{_fmt_stat(non_compliant_group['median'])} | {_fmt_stat(non_compliant_group['average'])} |"
        )
        lines.append("")

    # Parity Index Read-Path Usage (TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING): unlike
    # every other section in this file, this one always renders — "0 today" is itself the
    # reportable finding (parity_index.py's entry/impact/health read path was reviewed GO by
    # TCK-20260731-PARITY-READPATH-GATE's Gate A but has zero real call sites yet), not an empty
    # period this section should stay silent about.
    lines.append("## Parity Index Read-Path Usage")
    lines.append("")
    lines.append(
        f"**`entry`/`impact`/`health` call count:** {pircc['count']}/{pircc['bash_rows_scanned']} "
        f"Bash rows scanned"
    )
    lines.append("")
    lines.append(f"_{pircc['derivation']}_")
    lines.append("")

    # KGMCP Cache Efficiency (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-
    # DASHBOARD): unlike most sections in this file, this one ALWAYS renders, mirroring Parity
    # Index Read-Path Usage's own precedent immediately above — "zero cache activity" is itself
    # the reportable finding (a real, documented failure mode: substantial search_docs/graphify
    # investigation activity with zero corresponding cache-DB events means the cache path is being
    # bypassed entirely, not merely underused), never a period this section should stay silent
    # about. Always reflects the FULL retrieval_cache_access_log corpus regardless of the report's
    # own --days/--week/--all period selection — see generate()'s own docstring for why (mirrors
    # `## Retrieval Quality`'s established "visible under --all only, in spirit" precedent for
    # KGMCP-adjacent data unlinked from runs.jsonl periods).
    lines.append("## KGMCP Cache Efficiency")
    lines.append("")
    lines.append(
        "_Reflects the full retrieval_cache_access_log corpus regardless of this report's "
        "--days/--week/--all period selection — these rows are logged against "
        "`.claude/current_run` sidecar attribution at call time, not `runs.jsonl` timestamps._"
    )
    lines.append("")
    lines.append(
        "_A low coverage rate is architectural, not a fixable cache inefficiency: only "
        "`knowledge_gateway_mcp.py`'s `knowledge_context`/`knowledge_status` tools are wired "
        "into this cache; the hard-rule-mandated `mcp__knowledge-search__search_docs` is served "
        "by a completely separate, uninstrumented implementation (`knowledge_search.py`) that "
        "never touches this cache path at all._"
    )
    lines.append("")
    lines.append(f"**Cache Efficiency: {kce['verdict']}** — {kce['verdict_explanation']}")
    lines.append("")

    reuse_str = "n/a" if kce["overall_reuse_rate"] is None else f"{kce['overall_reuse_rate'] * 100:.1f}%"
    coverage = kce["coverage"]
    coverage_str = "n/a" if coverage["coverage_rate"] is None else f"{coverage['coverage_rate'] * 100:.1f}%"
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Total hits | {kce['total_hits']} |")
    lines.append(f"| Total writes | {kce['total_writes']} |")
    lines.append(f"| Overall reuse rate | {reuse_str} |")
    lines.append(f"| Dead writes (never hit) | {kce['dead_write_count']} |")
    lines.append(f"| Repeated refetches (within {kce['repeated_refetch_window_seconds']}s) | {len(kce['repeated_refetches'])} |")
    lines.append(f"| Real search/graphify calls (coverage denominator) | {coverage['search_calls_total']} |")
    lines.append(f"| Coverage rate (cache events / search calls) | {coverage_str} |")
    if kce["stale_attribution_count"]:
        lines.append(f"| Stale-sidecar-attributed rows | {kce['stale_attribution_count']} |")
    lines.append("")

    if kce["per_ticket"]:
        lines.append("### Per-Ticket")
        lines.append("")
        lines.append("| Ticket | Hits | Writes | Reuse rate |")
        lines.append("|---|---|---|---|")
        for ticket in sorted(kce["per_ticket"]):
            row = kce["per_ticket"][ticket]
            rr = "n/a" if row["reuse_rate"] is None else f"{row['reuse_rate'] * 100:.1f}%"
            lines.append(f"| {ticket} | {row['hit']} | {row['write']} | {rr} |")
        lines.append("")

    if kce["per_agent"]:
        lines.append("### Per-Agent")
        lines.append("")
        lines.append("| Agent | Hits | Writes | Reuse rate |")
        lines.append("|---|---|---|---|")
        for agent in sorted(kce["per_agent"]):
            row = kce["per_agent"][agent]
            rr = "n/a" if row["reuse_rate"] is None else f"{row['reuse_rate'] * 100:.1f}%"
            lines.append(f"| {agent} | {row['hit']} | {row['write']} | {rr} |")
        lines.append("")

    if kce["repeated_refetches"]:
        lines.append(
            f"### Repeated Refetches (within {kce['repeated_refetch_window_seconds']}s of a prior access)"
        )
        lines.append("")
        lines.append("| Cache Level | Run | Ticket | Agent | Gap (s) | Prior Run |")
        lines.append("|---|---|---|---|---|---|")
        for rf in kce["repeated_refetches"]:
            lines.append(
                f"| {rf['cache_level']} | {rf['run_id']} | {rf['ticket_id']} | {rf['agent']} | "
                f"{rf['gap_s']} | {rf['prior_run_id']} |"
            )
        lines.append("")

    if kce["dead_writes"]:
        lines.append("### Dead Writes (never hit)")
        lines.append("")
        lines.append("| Cache Level | Run | Ticket | Agent |")
        lines.append("|---|---|---|---|")
        for dw in kce["dead_writes"]:
            lines.append(
                f"| {dw['cache_level']} | {dw['run_id']} | {dw['ticket_id']} | {dw['agent']} |"
            )
        lines.append("")

    lines.append(f"_{kce['derivation']}_")
    lines.append("")

    # Skill Usage (TCK-20260810-SKILL-USAGE-RETRO-TRACKING): two subsections of genuinely
    # different scope under one heading — a period-scoped per-skill invocation count (trended
    # report-over-report via index.md's Skill Invocations column, gated like Search & Investigation
    # Effort above) and an all-time zero-invocation flag (gated separately, only computed/rendered
    # when the caller explicitly supplied all_tools — see `zif` above). The whole heading is
    # omitted (not rendered empty) when neither subsection has anything to show.
    if su["total_skill_invocations"] > 0 or (
        zif is not None and (zif["flagged_stale"] or zif["flagged_unknown_age"])
    ):
        lines.append("## Skill Usage")
        lines.append("")

        if su["total_skill_invocations"] > 0:
            lines.append("### Per-Skill Invocation Counts (This Period)")
            lines.append("")
            lines.append("| Skill | Invocations |")
            lines.append("|---|---|")
            for skill in sorted(su["per_skill"]):
                lines.append(f"| {skill} | {su['per_skill'][skill]} |")
            lines.append("")
            lines.append(f"**Total:** {su['total_skill_invocations']}")
            lines.append("")
            lines.append(f"_{su['derivation']}_")
            lines.append("")

        if zif is not None and (zif["flagged_stale"] or zif["flagged_unknown_age"]):
            lines.append(
                f"### Zero-Invocation Flags (All-Time, {zif['grace_period_days']}-Day Grace Period)"
            )
            lines.append("")
            if zif["flagged_stale"]:
                lines.append("**Flagged (confirmed age past grace period):** " + ", ".join(zif["flagged_stale"]))
            else:
                lines.append("**Flagged (confirmed age past grace period):** _none_")
            if zif["flagged_unknown_age"]:
                lines.append("**Flagged (unknown age, no `date_added`):** " + ", ".join(zif["flagged_unknown_age"]))
            else:
                lines.append("**Flagged (unknown age, no `date_added`):** _none_")
            lines.append("")
            lines.append(f"_{zif['derivation']}_")
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
    # Never period-sliced (see generate()'s own docstring) — read_cache_access_log() never raises
    # (returns [] on a fresh/never-migrated retrieval_cache.db), so no try/except is needed here.
    all_kgmcp_access_log = read_cache_access_log()

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

    report = generate(
        runs, events, label, week_str, tools=tools, all_tools=all_tools,
        kgmcp_access_log=all_kgmcp_access_log,
    )

    RETRO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RETRO_DIR / out_name
    out_path.write_text(report)
    print(f"Written: {out_path}")
    print(f"Runs: {len(runs)}, Events: {len(events)}")

    # Update index
    _update_index(all_runs, all_tools)


def _update_index(all_runs, all_tools=None):
    all_tools = all_tools or []

    retro_files = sorted(RETRO_DIR.glob("RETRO-*.md"), reverse=True)
    retro_files = [f for f in retro_files if f.name != "index.md"]

    lines = ["# Agent Monitoring Retro Index", ""]
    lines.append("| Report | Runs | DONE | Gate failures | Search Calls | Read Calls | Skill Invocations |")
    lines.append("|---|---|---|---|---|---|---|")

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

        # Mirrors main()'s own per-period run_id filter of all_tools (:1536/:1545) — reused here,
        # not a new mechanism, threaded through the same run-id-to-week association runs_by_week
        # already computed above.
        if name == "ALL":
            week_tools = all_tools
        else:
            week_run_ids = {r.get("run_id") for r in week_runs}
            week_tools = [t for t in all_tools if t.get("run_id") in week_run_ids]
        search_calls = build_search_count_section(week_tools)["total"]
        read_calls = build_raw_investigation_count_section(week_tools)["total"]
        skill_invocations = build_skill_usage_section(week_tools)["total_skill_invocations"]

        lines.append(
            f"| [{name}]({f.name}) | {n} | {done} | {fails} | {search_calls} | {read_calls} | "
            f"{skill_invocations} |"
        )

    (RETRO_DIR / "index.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

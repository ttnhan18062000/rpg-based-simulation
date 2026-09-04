"""File-reading, parsing, join, and in-memory cache layer for the Agent Ops
Dashboard backend.

Read-only: this module never writes to tickets/**, agent-monitoring/*.jsonl,
or any other durable source — it only reads them into an in-memory cache
rebuilt on source mtime change.

Reuses (never reimplements):
- tools/validate_frontmatter.py::extract_frontmatter for ticket frontmatter
- tools/generate_registry.py::parse_body_section/_strip_frontmatter for ticket
  body-section fields (title, tier, ticket_type, priority, workflow_status) —
  title comes from the ## Title body section, not the H1 heading, since the
  H1 is mandated to equal the ticket_id and would otherwise mask the title
- tools/agent-monitoring/validate.py::load_jsonl (the tolerant loader — catches
  JSONDecodeError per line, warns, continues) and its legacy status allowlists
"""
from __future__ import annotations

import re
import sys
import threading
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TOOLS_DIR = _REPO_ROOT / "tools"
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
for _p in (_TOOLS_DIR, _MONITORING_TOOLS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from validate_frontmatter import extract_frontmatter  # noqa: E402
from generate_registry import parse_body_section, _strip_frontmatter  # noqa: E402
from ticket_field_values import (  # noqa: E402
    LAYER_VALUES,
    PRIORITY_VALUES,
    TIER_VALUES,
    WORKFLOW_STATUS_VALUES,
)
import validate  # noqa: E402  (tools/agent-monitoring/validate.py)
from generate_retro import compute_retro_metrics, current_week, iso_week  # noqa: E402
from retrieval_cache import read_cache_access_log  # noqa: E402
from ticket_stats_report import (  # noqa: E402
    collect_done_tickets,
    compute_artifact_completeness,
    compute_distribution,
    compute_velocity,
)
from glossary_registry import load_registry as load_glossary_registry  # noqa: E402
import layer_registry  # noqa: E402  (load_registry() for layer note-field reuse — see get_glossary())
import tag_registry  # noqa: E402  (load_registry() for the tags facet — see get_tickets())

from src.api.agent_ops_dashboard.models import (
    AgentMonitoringStats,
    ArtifactCompletenessStats,
    BulkRunTimeline,
    CostProxyOutlierEntry,
    DurationOutlierEntry,
    FileTouch,
    GlossaryEntry,
    GlossaryResponse,
    HealthStatus,
    IncompleteArtifactEntry,
    KgmcpCacheEfficiencyStats,
    KgmcpCacheTicketStats,
    KgmcpCoverageStats,
    KgmcpDeadWriteEntry,
    KgmcpRepeatedRefetchEntry,
    OutlierStats,
    RawToolCall,
    RunDetail,
    RunMatchSummary,
    RunSummary,
    RunSummaryStats,
    RunTimeline,
    SkillTagStats,
    SkillUsageSection,
    SlowRunEntry,
    SpendProxyStats,
    SubsystemTagStats,
    SummaryQualityStats,
    TicketCorpusStats,
    TicketDistributionStats,
    VelocityStats,
    TicketSummary,
    TierDistributionStats,
    TimelineEntry,
)

ACTIVE_WINDOW_MINUTES = 10
_EDIT_TOOLS = {"Read", "Edit", "Write", "MultiEdit"}
_TICKET_ID_RE = re.compile(r"^TCK-\d{8}-")
# A ticket can transiently exist under both tickets/todos/{folder}/ and
# tickets/inprogress/ (the todos source file is only deleted at ticket close,
# per CLAUDE.md's Workflow Rule) — lower number wins when the same ticket_id
# is found under more than one lifecycle directory in the same rebuild.
_LIFECYCLE_PRIORITY = {"inprogress": 0, "done": 1, "todos": 2}

# Reused directly — not reimplemented. AC #3 asserts these are the same function
# objects as their source modules, not behaviorally-similar reimplementations.
load_jsonl = validate.load_jsonl


# ---------------------------------------------------------------------------
# Step 3 — tolerant JSONL loading with an unparsed-line count for /api/health
# ---------------------------------------------------------------------------


def load_jsonl_counted(path: Path) -> tuple[list[dict], int]:
    """Load path via validate.load_jsonl, also returning the count of skipped lines.

    validate.load_jsonl itself does the tolerant per-line JSON parsing (catches
    json.JSONDecodeError, warns, continues) — this wrapper only adds the count,
    derived by comparing valid-record count against total non-blank lines, so
    the parsing behavior itself is never duplicated.
    """
    if not path.exists():
        return [], 0
    total_lines = sum(1 for line in path.read_text().splitlines() if line.strip())
    records = load_jsonl(path)
    return records, total_lines - len(records)


def _week_shard_paths(data_root: Path, filename: str) -> list[Path]:
    """Every agent-monitoring/data/<week>/{filename} shard under data_root, sorted for
    determinism — mirrors record_events.py::compute_tool_stats()'s
    `sorted(Path(".").glob("agent-monitoring/data/*/tools.jsonl"))` precedent. A
    data_root with no matching week folders yields an empty list (not an error).

    Falls back to a single flat data_root.parent/{filename} file (e.g.
    <repo_root>/agent-monitoring/runs.jsonl directly, no data/ subfolder) when data_root itself
    doesn't exist — the scratch/legacy shape this subsystem's own synthetic test fixtures still
    build directly. Mirrors tools/agent_replay_codex/monitoring_shards.py::source_paths and
    tools/agent-monitoring/manifest.py::_source_paths, the landed precedents for this exact
    dual-mode resolution (TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK)."""
    if data_root.is_dir():
        return sorted(data_root.glob(f"*/{filename}"))
    single = data_root.parent / filename
    return [single] if single.exists() else []


def _max_mtime(paths: list[Path]) -> float:
    """max() mtime across paths, defaulting to 0.0 for an empty list — guards the
    empty-glob ValueError footgun (max() over an empty sequence raises without
    `default=`), matching the old single-file "doesn't exist -> 0.0" precedent."""
    return max((p.stat().st_mtime for p in paths if p.exists()), default=0.0)


def _load_jsonl_counted_multi(data_root: Path, filename: str) -> tuple[list[dict], int]:
    """Read + concatenate every agent-monitoring/data/<week>/{filename} shard (sorted,
    ISO-week order) via load_jsonl_counted per file, summing unparsed-line counts
    across all shards. Safe against double-counting: (run_id, seq) is globally unique
    across weeks (see record_events.py::compute_tool_stats's docstring) and each shard
    is read exactly once here."""
    all_records: list[dict] = []
    total_unparsed = 0
    for path in _week_shard_paths(data_root, filename):
        records, unparsed = load_jsonl_counted(path)
        all_records.extend(records)
        total_unparsed += unparsed
    return all_records, total_unparsed


# ---------------------------------------------------------------------------
# Step 2 — ticket frontmatter + body-section parsing
# ---------------------------------------------------------------------------


def parse_ticket_file(path: Path, lifecycle_state: str) -> Optional[dict]:
    """Parse one ticket markdown file into an internal record dict, or None if
    it has no frontmatter block (not a ticket file)."""
    text = path.read_text(encoding="utf-8")
    fm = extract_frontmatter(text)
    if fm is None:
        return None

    body = _strip_frontmatter(text)
    title = parse_body_section(body, "Title")
    tier = parse_body_section(body, "Tier") or None
    ticket_type = parse_body_section(body, "Type") or None
    priority = parse_body_section(body, "Priority") or None
    workflow_status = parse_body_section(body, "Status") or None

    raw_tags = fm.get("tags", [])
    tags = raw_tags if isinstance(raw_tags, list) else []

    return {
        "ticket_id": fm.get("ticket_id") or path.stem,
        "title": title,
        "tier": tier,
        "ticket_type": ticket_type,
        "priority": priority,
        "layer": fm.get("layer", ""),
        "status": fm.get("status", ""),
        "workflow_status": workflow_status,
        "tags": tags,
        "date": fm.get("date", ""),
        "lifecycle_state": lifecycle_state,
        "matching_runs": [],
    }


def walk_ticket_dirs(tickets_root: Path) -> list[Path]:
    """Return every TCK-*.md file under tickets/{inprogress,done,todos}/.

    done/ and todos/ are walked recursively (epics/sequences live in
    subfolders); non-ticket files (SEQUENCE.md, etc.) are filtered out by
    filename pattern before any frontmatter parsing is attempted.
    """
    candidates: list[Path] = []
    inprogress = tickets_root / "inprogress"
    done = tickets_root / "done"
    todos = tickets_root / "todos"
    if inprogress.is_dir():
        candidates.extend(inprogress.glob("*.md"))
    if done.is_dir():
        candidates.extend(done.rglob("*.md"))
    if todos.is_dir():
        candidates.extend(todos.rglob("*.md"))
    return [p for p in candidates if _TICKET_ID_RE.match(p.stem)]


def lifecycle_state_for_path(path: Path, tickets_root: Path) -> str:
    """inprogress/done/todos, derived from which directory a ticket file lives under."""
    rel = path.relative_to(tickets_root)
    return rel.parts[0]


# ---------------------------------------------------------------------------
# Step 4 — ticket-to-run join: all matching runs.jsonl rows, sorted desc
# ---------------------------------------------------------------------------


def _resolve_final_status(rec: dict) -> str:
    """Prefer final_status, fall back to status (FOLDER-*/EPIC-* legacy shape),
    mirroring validate.py's own _record_is_complete two-field check. For the
    older legacy generations that carry neither field (started_at/finished_at,
    ts_start/ts_end/result), validate._record_is_complete's own completion-field
    allowlist still resolves a reasonable DONE/CRASHED/IN_PROGRESS value."""
    status = rec.get("final_status") or rec.get("status")
    if status:
        return status
    if validate._record_is_complete(rec):
        return "DONE"
    if rec.get("start_ts"):
        return "CRASHED"
    return "IN_PROGRESS"


def _resolve_identity_provenance(rec: dict) -> str:
    """'native' if the record carries the new execution-identity fields (this
    migration or later); 'legacy' for any pre-migration record — mirrors
    _resolve_final_status's fallback-without-raising shape, but for identity
    rather than completion status."""
    return "native" if rec.get("execution_id") is not None else "legacy"


def _coerce_ts(value) -> Optional[str]:
    """A handful of legacy runs.jsonl/events.jsonl/tools.jsonl rows carry raw
    unix-epoch numbers (int/float) instead of ISO strings for timestamp
    fields — every model field they feed is typed str, so normalize here
    rather than let a type mismatch raise at the Pydantic boundary."""
    if value is None:
        return None
    return str(value)


def build_matching_runs(ticket_id: str, runs_all: list[dict]) -> list[RunMatchSummary]:
    """Every runs.jsonl row whose run_id == ticket_id, sorted start_ts descending.

    Never collapses to a single match — a ticket_id can legitimately have
    multiple runs.jsonl rows (retries/re-runs). Rows without a start_ts sort
    last, never first, and never raise.
    """
    matches = [r for r in runs_all if r.get("run_id") == ticket_id]
    normalized = [
        {
            "run_id": r.get("run_id"),
            "start_ts": _coerce_ts(r.get("start_ts")),
            "end_ts": _coerce_ts(r.get("end_ts")),
            "final_status": _resolve_final_status(r),
        }
        for r in matches
    ]
    with_ts = [r for r in normalized if r["start_ts"]]
    without_ts = [r for r in normalized if not r["start_ts"]]
    with_ts.sort(key=lambda r: r["start_ts"], reverse=True)
    ordered = with_ts + without_ts
    return [RunMatchSummary(**r) for r in ordered]


def _group_runs_by_id(runs_all: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in runs_all:
        run_id = r.get("run_id")
        if run_id:
            grouped[run_id].append(r)
    return grouped


def _primary_run_record(records: list[dict]) -> dict:
    """The single canonical row for a run_id with 2+ rows: the most recent by
    start_ts (consistent with matching_runs' own descending-by-start_ts order)."""
    with_ts = [r for r in records if r.get("start_ts")]
    if with_ts:
        return max(with_ts, key=lambda r: str(r["start_ts"]))
    return records[0]


# ---------------------------------------------------------------------------
# Step 5 — inferred-active computation
# ---------------------------------------------------------------------------


def _parse_iso(ts) -> Optional[datetime]:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_inferred_active(
    tools_by_run_recent: dict, runs_by_id: dict, now: datetime
) -> dict[str, dict]:
    """run_id -> {"inferred_start_ts": ...} for every run visible in tools.jsonl
    but absent from runs_by_id, whose most recent tool-call ts is within
    ACTIVE_WINDOW_MINUTES of now. Recomputed fresh from runs_by_id's current
    contents every call — never carried over from a previous snapshot, so a
    run that completes falls out of this set on the very next rebuild.
    """
    window = timedelta(minutes=ACTIVE_WINDOW_MINUTES)
    inferred: dict[str, dict] = {}
    for run_id, rows in tools_by_run_recent.items():
        if run_id in runs_by_id:
            continue
        timestamps = [(row.get("ts"), _parse_iso(row.get("ts"))) for row in rows]
        parsed = [(raw, dt) for raw, dt in timestamps if dt is not None]
        if not parsed:
            continue
        _, max_dt = max(parsed, key=lambda pair: pair[1])
        min_ts_raw, _ = min(parsed, key=lambda pair: pair[1])
        if now - max_dt <= window:
            inferred[run_id] = {"inferred_start_ts": min_ts_raw}
    return inferred


# ---------------------------------------------------------------------------
# Step 6 — files_touched derivation
# ---------------------------------------------------------------------------


def extract_files_touched(entries: list[dict], live_tail: list[dict]) -> list[FileTouch]:
    """Deduplicated-by-path FileTouch list from every tool_calls[] item across
    entries (each an internal record with a "tool_calls" list) and live_tail
    (raw tool rows directly), restricted to Read/Edit/Write/MultiEdit, keeping
    the first ts+tool seen per path.
    """
    seen: dict[str, FileTouch] = {}
    all_calls: list[dict] = []
    for entry in entries:
        all_calls.extend(entry.get("tool_calls", []))
    all_calls.extend(live_tail)

    for call in all_calls:
        tool = call.get("tool")
        if tool not in _EDIT_TOOLS:
            continue
        path = (call.get("input_summary") or "").strip()
        if not path or path in seen:
            continue
        seen[path] = FileTouch(path=path, tool=tool, ts=_coerce_ts(call.get("ts")) or "")
    return list(seen.values())


def _tool_call_to_model(t: dict) -> RawToolCall:
    return RawToolCall(
        tool=t.get("tool", ""),
        input_summary=t.get("input_summary", ""),
        status=t.get("status", ""),
        duration_ms=t.get("duration_ms"),
        ts=_coerce_ts(t.get("ts")) or "",
    )


def _build_run_summary(run_id: str, record: Optional[dict], inferred: Optional[dict]) -> RunSummary:
    if record is not None:
        return RunSummary(
            run_id=run_id,
            workflow=record.get("workflow") or "",
            tier=record.get("tier") or "",
            final_status=_resolve_final_status(record),
            start_ts=_coerce_ts(record.get("start_ts")),
            end_ts=_coerce_ts(record.get("end_ts")),
            duration_s=record.get("duration_s"),
            agent_count=record.get("agent_count") or 0,
            is_inferred_active=False,
            inferred_start_ts=None,
            provider=record.get("provider"),
            execution_id=record.get("execution_id"),
            ticket_id=record.get("ticket_id"),
            identity_provenance=_resolve_identity_provenance(record),
        )
    info = inferred or {}
    return RunSummary(
        run_id=run_id,
        workflow="unknown",
        tier="unknown",
        final_status="IN_PROGRESS",
        start_ts=None,
        end_ts=None,
        duration_s=None,
        agent_count=0,
        is_inferred_active=True,
        inferred_start_ts=info.get("inferred_start_ts"),
        provider=None,
        execution_id=None,
        ticket_id=None,
        identity_provenance="legacy",
    )


def _ticket_record_to_summary(record: dict) -> TicketSummary:
    return TicketSummary(
        ticket_id=record["ticket_id"],
        title=record["title"],
        tier=record["tier"],
        ticket_type=record["ticket_type"],
        priority=record["priority"],
        layer=record["layer"],
        status=record["status"],
        workflow_status=record["workflow_status"],
        tags=record["tags"],
        date=record["date"],
        lifecycle_state=record["lifecycle_state"],
        matching_runs=record["matching_runs"],
    )


class TicketsQueryResult(list):
    """The requested page of TicketSummary, plus total_count/facets computed
    over the full filtered-but-unpaginated result. Subclasses list (rather
    than wrapping items in a dict/namedtuple) so that the pre-existing
    direct-call get_tickets tests — which iterate the return value and read
    .ticket_id off each element — keep passing unmodified: with the default
    limit=None, the page equals the full filtered set, so iterating this
    object is indistinguishable from iterating the old bare list.
    """

    def __init__(self, items: list[TicketSummary], total_count: int, facets: dict[str, list[str]]):
        super().__init__(items)
        self.total_count = total_count
        self.facets = facets


# WORKFLOW_STATUS_VALUES itself now lives in tools/ticket_field_values.py (imported above) —
# TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM relocated it there so it is the single shared source
# for all four canonical ticket-field enums (Tier/Layer/Status/Priority), not a dashboard-local
# definition. See that module's docstring for the full "why" (frontmatter-vs-body-section
# validation split, the anti-duplication rationale). All five ticket facets (tiers/layers/
# statuses/priorities/tags) are now fixed canonical lists, independent of active filters or
# current corpus content — see TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL for the first four
# and TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY for tags joining them.


def _load_agent_role_descriptions(repo_root: Path) -> dict[str, str]:
    """Read every `.claude/agents/*.md` role file's own frontmatter and return {name: description}
    for each file that has both a non-empty `name:` and `description:` field.

    Reuses extract_frontmatter (never a second frontmatter parser) — see get_glossary()'s
    docstring for why this reads the files directly instead of copying their descriptions into
    glossary_registry.jsonl. Tolerant by design: a missing .claude/agents/ directory (e.g. a
    trimmed-down tmp_path fixture in tests) or a file with unparseable/absent frontmatter simply
    contributes nothing — never raises, since one malformed role file must not break the whole
    glossary endpoint.
    """
    agents_dir = repo_root / ".claude" / "agents"
    if not agents_dir.is_dir():
        return {}

    descriptions: dict[str, str] = {}
    for path in sorted(agents_dir.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
            fm = extract_frontmatter(text)
        except (OSError, ValueError):
            continue
        if not fm:
            continue
        name = fm.get("name", "")
        description = fm.get("description", "")
        if name and description:
            descriptions[name] = description
    return descriptions


# ---------------------------------------------------------------------------
# Step 7 — RLock-per-method cache, matching ReadModelCache's exact pattern
# ---------------------------------------------------------------------------


class DashboardCache:
    """In-memory cache over tickets/** + agent-monitoring/*.jsonl, rebuilt on
    source mtime change. Every public method opens `with self._lock:` as its
    first statement (single threading.RLock() guarding every read and write —
    src/api/read_model_cache.py::ReadModelCache's exact pattern, not the
    swap-based build-outside-lock alternative)."""

    def __init__(self, repo_root: Path = _REPO_ROOT):
        self._repo_root = repo_root
        self._data_root = repo_root / "agent-monitoring" / "data"
        self._tickets_root = repo_root / "tickets"
        self._lock = threading.RLock()

        self._runs_all: list[dict] = []
        self._events_all: list[dict] = []
        # Retained (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD) so
        # get_agent_monitoring_stats() can pass the real tools.jsonl corpus into
        # compute_retro_metrics()'s `tools` parameter (Skill Usage) — previously _rebuild() below
        # discarded `tools_all` after building _tools_by_seq/_tools_by_run_recent from it.
        self._tools_all: list[dict] = []
        self._runs_by_id: dict[str, dict] = {}
        self._tickets_by_id: dict[str, dict] = {}
        self._tools_by_seq: dict = {}
        self._tools_by_run_recent: dict = {}
        self._events_by_run: dict = {}
        self._inferred_active: dict[str, dict] = {}
        self._last_rebuilt_ts: Optional[str] = None
        self._unparsed_lines: dict[str, int] = {}
        self._source_mtimes: dict[str, float] = {}

    def _current_source_state(self) -> dict[str, float]:
        def _mtime(p: Path) -> float:
            return p.stat().st_mtime if p.exists() else 0.0

        ticket_files = walk_ticket_dirs(self._tickets_root)
        tickets_state = float(len(ticket_files)) + sum(_mtime(p) for p in ticket_files)
        return {
            "runs.jsonl": _max_mtime(_week_shard_paths(self._data_root, "runs.jsonl")),
            "events.jsonl": _max_mtime(_week_shard_paths(self._data_root, "events.jsonl")),
            "tools.jsonl": _max_mtime(_week_shard_paths(self._data_root, "tools.jsonl")),
            "tickets": tickets_state,
        }

    def _maybe_rebuild(self, now: Optional[datetime] = None) -> None:
        with self._lock:
            current_state = self._current_source_state()
            if self._last_rebuilt_ts is not None and current_state == self._source_mtimes:
                return
            self._rebuild(current_state, now or datetime.now(timezone.utc))

    def _rebuild(self, source_state: dict[str, float], now: datetime) -> None:
        with self._lock:
            runs_all, runs_unparsed = _load_jsonl_counted_multi(self._data_root, "runs.jsonl")
            events_all, events_unparsed = _load_jsonl_counted_multi(self._data_root, "events.jsonl")
            tools_all, tools_unparsed = _load_jsonl_counted_multi(self._data_root, "tools.jsonl")

            grouped_runs = _group_runs_by_id(runs_all)
            runs_by_id = {rid: _primary_run_record(rows) for rid, rows in grouped_runs.items()}

            events_by_run: dict = defaultdict(list)
            for e in events_all:
                run_id = e.get("run_id")
                if run_id:
                    events_by_run[run_id].append(e)

            tools_by_seq: dict = defaultdict(list)
            tools_by_run_recent: dict = defaultdict(list)
            for t in tools_all:
                run_id = t.get("run_id")
                if run_id is None:
                    continue
                tools_by_run_recent[run_id].append(t)
                seq = t.get("seq")
                if seq is not None:
                    tools_by_seq[(run_id, seq)].append(t)

            tickets_by_id: dict[str, dict] = {}
            for path in walk_ticket_dirs(self._tickets_root):
                lifecycle_state = lifecycle_state_for_path(path, self._tickets_root)
                record = parse_ticket_file(path, lifecycle_state)
                if record is None:
                    continue
                record["matching_runs"] = build_matching_runs(record["ticket_id"], runs_all)
                existing = tickets_by_id.get(record["ticket_id"])
                if existing is None or _LIFECYCLE_PRIORITY.get(
                    lifecycle_state, 99
                ) < _LIFECYCLE_PRIORITY.get(existing["lifecycle_state"], 99):
                    tickets_by_id[record["ticket_id"]] = record

            inferred_active = compute_inferred_active(tools_by_run_recent, runs_by_id, now)

            self._runs_all = runs_all
            self._events_all = events_all
            self._tools_all = tools_all
            self._runs_by_id = runs_by_id
            self._tickets_by_id = tickets_by_id
            self._tools_by_seq = tools_by_seq
            self._tools_by_run_recent = tools_by_run_recent
            self._events_by_run = events_by_run
            self._inferred_active = inferred_active
            self._last_rebuilt_ts = now.isoformat().replace("+00:00", "Z")
            self._unparsed_lines = {
                "runs.jsonl": runs_unparsed,
                "events.jsonl": events_unparsed,
                "tools.jsonl": tools_unparsed,
            }
            self._source_mtimes = source_state

    def get_tickets(
        self,
        *,
        tier: Optional[str] = None,
        layer: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[list[str]] = None,
        lifecycle: Optional[str] = None,
        q: Optional[str] = None,
        sort: str = "date_desc",
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> TicketsQueryResult:
        with self._lock:
            self._maybe_rebuild()
            records = list(self._tickets_by_id.values())

            filtered = []
            for r in records:
                if tier is not None and r["tier"] != tier:
                    continue
                if layer is not None and r["layer"] != layer:
                    continue
                if status is not None and r["workflow_status"] != status:
                    continue
                if priority is not None and r["priority"] != priority:
                    continue
                if lifecycle is not None and lifecycle != "all" and r["lifecycle_state"] != lifecycle:
                    continue
                if tags and not (set(tags) & set(r["tags"])):
                    continue
                if q:
                    haystack = f"{r['title']} {r['ticket_id']}".lower()
                    if q.lower() not in haystack:
                        continue
                filtered.append(r)

            filtered.sort(key=lambda r: r["date"] or "", reverse=(sort != "date_asc"))

            total_count = len(filtered)
            # tiers/layers/statuses/priorities/tags are all fixed canonical lists, independent of
            # active filters, pagination, and current corpus content, so a legitimate value with
            # zero matching tickets right now (e.g. a rarely-used Tier, or a registered tag nobody
            # has used yet) is still a selectable filter option rather than silently absent. `tags`
            # joined this canonical-facet model in TCK-20260720-DASHBOARD-TAG-FACET-REGISTRY,
            # reading registries/tag_registry.jsonl directly (mirroring get_glossary()'s existing
            # layer_registry.load_registry() pattern) instead of TCK-20260718-DASHBOARD-FACETS-
            # FULLY-CANONICAL's original "tags is genuinely open-vocabulary, not a small closed
            # enum" reasoning — true before the tag registry existed as a real governed list,
            # no longer true after. Deliberate, accepted consequence: a legacy/pre-taxonomy
            # free-text tag present on real tickets but absent from the registry no longer appears
            # in this facet, and open-ended phase-N tags (exempt from registration entirely) never
            # appear here either — both are intentional, not a regression. All five sets are
            # frozensets/dicts (unordered) — sort explicitly rather than relying on
            # set/dict-iteration order, which is not guaranteed stable.
            facets = {
                "tiers": sorted(TIER_VALUES),
                "layers": sorted(LAYER_VALUES),
                "statuses": sorted(WORKFLOW_STATUS_VALUES),
                "priorities": sorted(PRIORITY_VALUES),
                "tags": sorted(tag_registry.load_registry(self._repo_root).keys()),
            }

            paged = filtered[offset : offset + limit] if limit is not None else filtered
            return TicketsQueryResult(
                items=[_ticket_record_to_summary(r) for r in paged],
                total_count=total_count,
                facets=facets,
            )

    def get_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        workflow: Optional[str] = None,
        since: Optional[str] = None,
        provider: Optional[str] = None,
        execution_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
    ) -> list[RunSummary]:
        with self._lock:
            self._maybe_rebuild()
            all_run_ids = set(self._runs_by_id) | set(self._inferred_active)
            summaries = []
            for run_id in all_run_ids:
                summary = _build_run_summary(
                    run_id, self._runs_by_id.get(run_id), self._inferred_active.get(run_id)
                )
                if status is not None and summary.final_status != status:
                    continue
                if workflow is not None and summary.workflow != workflow:
                    continue
                if since is not None and (summary.start_ts is None or summary.start_ts < since):
                    continue
                if provider is not None and summary.provider != provider:
                    continue
                if execution_id is not None and summary.execution_id != execution_id:
                    continue
                if ticket_id is not None and summary.ticket_id != ticket_id:
                    continue
                summaries.append(summary)

            summaries.sort(key=lambda s: s.start_ts or "", reverse=True)
            return summaries[offset : offset + limit]

    def get_run(self, run_id: str) -> Optional[RunDetail]:
        with self._lock:
            self._maybe_rebuild()
            record = self._runs_by_id.get(run_id)
            inferred = self._inferred_active.get(run_id)
            if record is None and inferred is None:
                return None
            summary = _build_run_summary(run_id, record, inferred)
            ticket = self._tickets_by_id.get(run_id)
            return RunDetail(
                **summary.model_dump(),
                ticket_title=ticket["title"] if ticket else None,
                ticket_lifecycle_state=ticket["lifecycle_state"] if ticket else None,
            )

    def _build_timeline_entries(self, run_id: str) -> tuple[list[TimelineEntry], list[dict]]:
        """Pure extraction of get_timeline()'s entries-building loop. Caller must already hold
        self._lock and have already called self._maybe_rebuild() — this method does neither
        itself, since both get_timeline() and get_bulk_timeline() call it once per already-locked,
        already-rebuilt request, not once per run inside their own loops."""
        raw_events = sorted(
            self._events_by_run.get(run_id, []), key=lambda e: e.get("seq") or 0
        )
        entries = []
        entry_dicts = []
        for e in raw_events:
            raw_tool_calls = self._tools_by_seq.get((run_id, e.get("seq")), [])
            entries.append(
                TimelineEntry(
                    seq=e.get("seq"),
                    phase=e.get("phase"),
                    agent=e.get("agent"),
                    status=e.get("status", ""),
                    summary=e.get("summary", ""),
                    ts=_coerce_ts(e.get("ts")) or "",
                    tool_call_count=e.get("tool_call_count"),
                    cost_proxy_score=e.get("cost_proxy_score"),
                    reason_code=e.get("reason_code"),
                    tool_calls=[_tool_call_to_model(t) for t in raw_tool_calls],
                )
            )
            entry_dicts.append({"tool_calls": raw_tool_calls})
        return entries, entry_dicts

    def get_timeline(self, run_id: str) -> Optional[RunTimeline]:
        with self._lock:
            self._maybe_rebuild()
            if run_id not in self._runs_by_id and run_id not in self._inferred_active:
                return None

            entries, entry_dicts = self._build_timeline_entries(run_id)

            is_live = run_id in self._inferred_active
            live_tail_raw: list[dict] = []
            if is_live:
                known_seqs = {ent.seq for ent in entries}
                for t in self._tools_by_run_recent.get(run_id, []):
                    if t.get("seq") is None or t.get("seq") not in known_seqs:
                        live_tail_raw.append(t)

            files_touched = extract_files_touched(entry_dicts, live_tail_raw)

            return RunTimeline(
                run_id=run_id,
                is_live=is_live,
                entries=entries,
                live_tail=[_tool_call_to_model(t) for t in live_tail_raw],
                files_touched=files_touched,
            )

    def get_bulk_timeline(
        self,
        *,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> BulkRunTimeline:
        """Deliberately duplicates get_runs()'s since/sort/slice selection logic (with `until`
        added in the same per-run-id filter loop, before sort+slice) rather than calling
        get_runs() and post-filtering — get_runs()'s own [offset:offset+limit] slice happens
        before any `until` bound could be applied, which would silently return the wrong page."""
        with self._lock:
            self._maybe_rebuild()
            all_run_ids = set(self._runs_by_id) | set(self._inferred_active)
            summaries = []
            for run_id in all_run_ids:
                summary = _build_run_summary(
                    run_id, self._runs_by_id.get(run_id), self._inferred_active.get(run_id)
                )
                if since is not None and (summary.start_ts is None or summary.start_ts < since):
                    continue
                if until is not None and (summary.start_ts is None or summary.start_ts > until):
                    continue
                summaries.append(summary)

            summaries.sort(key=lambda s: s.start_ts or "", reverse=True)
            page = summaries[offset : offset + limit]

            entries_by_run: dict[str, list[TimelineEntry]] = {}
            for s in page:
                entries, _entry_dicts = self._build_timeline_entries(s.run_id)
                entries_by_run[s.run_id] = entries
            return BulkRunTimeline(entries_by_run=entries_by_run)

    def get_agent_monitoring_stats(
        self,
        *,
        days: Optional[int] = None,
        all_time: bool = False,
        week: Optional[str] = None,
    ) -> AgentMonitoringStats:
        """Same period-selection semantics as generate_retro.py's CLI (--days/--all/--week,
        default current week) — replicated here rather than imported since main() mixes
        argparse/file-I/O concerns with the filter logic; only the filter logic itself is
        duplicated (a handful of lines), never compute_retro_metrics()'s actual computation."""
        with self._lock:
            self._maybe_rebuild()

            if all_time:
                runs = self._runs_all
                events = self._events_all
            elif days:
                # generate_retro.py's own CLI (main()) does the bare `(r.get("start_ts") or "")
                # >= cutoff` comparison with no type guard, which crashes on the legacy runs.jsonl
                # records confirmed to carry a raw Unix-timestamp number (float/int) instead of an
                # ISO8601 string for start_ts — reproduced live: `generate_retro.py --days 7`
                # crashes the same way against real data. Out of scope to fix main() itself
                # (untouched, per this ticket's scope guard); guard it here instead, consistent
                # with iso_week()'s own existing try/except-based tolerance for the same class of
                # malformed legacy data (used by the week-selection branch below).
                cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
                runs = [
                    r for r in self._runs_all
                    if isinstance(r.get("start_ts"), str) and r["start_ts"] >= cutoff
                ]
                run_ids = {r["run_id"] for r in runs}
                events = [e for e in self._events_all if e.get("run_id") in run_ids]
            else:
                week_str = week or current_week()
                runs = [r for r in self._runs_all if iso_week(r.get("start_ts", "")) == week_str]
                run_ids = {r["run_id"] for r in runs}
                events = [e for e in self._events_all if e.get("run_id") in run_ids]

            # tools/kgmcp_access_log (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-
            # USAGE-DASHBOARD): passed as the FULL corpus, never period-sliced to `runs`/`events`
            # above — mirrors generate_retro.py's own CLI precedent for both `all_tools` (Skill
            # Usage zero-invocation flags are an all-time question) and `kgmcp_access_log`
            # (retrieval_cache_access_log rows are attributed via the `.claude/current_run`
            # sidecar at call time, not any runs.jsonl timestamp this period filter operates on).
            # read_cache_access_log() never raises (returns [] on a fresh/never-migrated
            # retrieval_cache.db), so no try/except is needed here, consistent with every other
            # read in this method.
            metrics = compute_retro_metrics(
                runs,
                events,
                tickets_root=self._tickets_root,
                tools=self._tools_all,
                kgmcp_access_log=read_cache_access_log(),
            )

            # compute_retro_metrics()'s gate_failure_breakdown can carry a literal `None` key
            # (a runs.jsonl record with neither final_status nor status set — _resolve_status()
            # returns None, and gate_counter has no `.get(..., "unknown")` fallback the way
            # tier_counts does). The Markdown renderer tolerates this fine (f"| {gate} | ..."
            # prints the literal text "None"), but a JSON object cannot have a None key — sanitize
            # only at this typed API boundary, never inside compute_retro_metrics() itself, so the
            # CLI/Markdown report's own byte-identical behavior (TCK-20260718-RETRO-STATS-REFACTOR)
            # stays completely untouched.
            gate_failure_breakdown = {
                (gate if gate is not None else "unknown"): count
                for gate, count in metrics["gate_failure_breakdown"].items()
            }

            return AgentMonitoringStats(
                run_summary=RunSummaryStats(**metrics["run_summary"]),
                gate_failure_breakdown=gate_failure_breakdown,
                reason_code_breakdown=metrics["reason_code_breakdown"],
                tag_breakdown_subsystem={
                    tag: SubsystemTagStats(**row)
                    for tag, row in metrics["tag_breakdown_subsystem"].items()
                },
                tag_breakdown_skill={
                    tag: SkillTagStats(**row) for tag, row in metrics["tag_breakdown_skill"].items()
                },
                tier_distribution={
                    tier: TierDistributionStats(**row)
                    for tier, row in metrics["tier_distribution"].items()
                },
                agent_status_distribution=metrics["agent_status_distribution"],
                phase_status_distribution=metrics["phase_status_distribution"],
                spend_proxy_by_phase={
                    phase: SpendProxyStats(**row)
                    for phase, row in metrics["spend_proxy_by_phase"].items()
                },
                spend_proxy_by_agent={
                    agent: SpendProxyStats(**row)
                    for agent, row in metrics["spend_proxy_by_agent"].items()
                },
                summary_quality=SummaryQualityStats(**metrics["summary_quality"]),
                slow_runs=[SlowRunEntry(**r) for r in metrics["slow_runs"]],
                outliers=OutlierStats(
                    duration_s=[
                        DurationOutlierEntry(**d) for d in metrics["outliers"]["duration_s"]
                    ],
                    cost_proxy_score=[
                        CostProxyOutlierEntry(**d) for d in metrics["outliers"]["cost_proxy_score"]
                    ],
                ),
                skill_usage=SkillUsageSection(**metrics["skill_usage"]),
                kgmcp_cache_efficiency=KgmcpCacheEfficiencyStats(
                    total_hits=metrics["kgmcp_cache_efficiency"]["total_hits"],
                    total_writes=metrics["kgmcp_cache_efficiency"]["total_writes"],
                    overall_reuse_rate=metrics["kgmcp_cache_efficiency"]["overall_reuse_rate"],
                    per_ticket={
                        t: KgmcpCacheTicketStats(**row)
                        for t, row in metrics["kgmcp_cache_efficiency"]["per_ticket"].items()
                    },
                    per_agent={
                        a: KgmcpCacheTicketStats(**row)
                        for a, row in metrics["kgmcp_cache_efficiency"]["per_agent"].items()
                    },
                    repeated_refetch_window_seconds=metrics["kgmcp_cache_efficiency"][
                        "repeated_refetch_window_seconds"
                    ],
                    repeated_refetches=[
                        KgmcpRepeatedRefetchEntry(**r)
                        for r in metrics["kgmcp_cache_efficiency"]["repeated_refetches"]
                    ],
                    dead_writes=[
                        KgmcpDeadWriteEntry(**d)
                        for d in metrics["kgmcp_cache_efficiency"]["dead_writes"]
                    ],
                    dead_write_count=metrics["kgmcp_cache_efficiency"]["dead_write_count"],
                    coverage=KgmcpCoverageStats(**metrics["kgmcp_cache_efficiency"]["coverage"]),
                    verdict=metrics["kgmcp_cache_efficiency"]["verdict"],
                    verdict_explanation=metrics["kgmcp_cache_efficiency"]["verdict_explanation"],
                    stale_attribution_count=metrics["kgmcp_cache_efficiency"][
                        "stale_attribution_count"
                    ],
                    derivation=metrics["kgmcp_cache_efficiency"]["derivation"],
                ),
            )

    def get_ticket_corpus_stats(self) -> TicketCorpusStats:
        """Ticket-corpus statistics (velocity, tier/type/priority/layer distribution, artifact
        completeness) via tools/ticket_stats_report.py's computation functions — imported and
        called directly, never reimplemented. Unlike every other DashboardCache method, this one
        does its own fresh file walk each call rather than reading from the mtime-cached
        _tickets_by_id/_runs_all state: tools/ticket_stats_report.py is a standalone tool
        following tools/tag_report.py's own precedent (a script that walks tickets/done/ itself),
        and its output shape (layer/tier/priority per ticket) isn't a subset of what
        DashboardCache's own parse_ticket_file() already extracts and caches — folding it into
        the mtime-rebuild cycle would require restructuring _rebuild() for a stats view that
        changes far less often than ticket/run browsing does. self._maybe_rebuild() is still
        called first for interface consistency with every other method, even though this
        computation reads its own file set independent of what that rebuild refreshes.
        """
        with self._lock:
            self._maybe_rebuild()

            included, skip_reasons = collect_done_tickets(self._repo_root)
            velocity = compute_velocity(self._repo_root)
            distribution = compute_distribution(included)
            artifact_completeness = compute_artifact_completeness(included, self._repo_root)

            return TicketCorpusStats(
                scanned_files=len(included) + sum(skip_reasons.values()),
                included_tickets=len(included),
                skipped=dict(skip_reasons),
                velocity=VelocityStats(**velocity),
                distribution=TicketDistributionStats(**distribution),
                artifact_completeness=ArtifactCompletenessStats(
                    complete_count=artifact_completeness["complete_count"],
                    incomplete_count=artifact_completeness["incomplete_count"],
                    total_checked=artifact_completeness["total_checked"],
                    incomplete=[
                        IncompleteArtifactEntry(**entry)
                        for entry in artifact_completeness["incomplete"]
                    ],
                ),
            )

    def get_glossary(self) -> GlossaryResponse:
        """Backend-owned tooltip descriptions, keyed by term. Three sources merged at read time,
        never duplicated into one file: `tools/glossary_registry.py`'s own registry (ticket-status/
        tier/priority/type/run-status/reason-code/event-status terms), every entry in
        `tools/layer_registry.py`'s registry re-exposed here under category="layer" (reusing each
        layer's existing `note` field as its description), and every `.claude/agents/*.md` role
        file re-exposed here under category="agent" (reusing each file's own frontmatter
        `description:` field — see `_load_agent_role_descriptions()`). None of the three is copied
        into a second file — this dashboard is read-only, so it reads each source directly instead
        (see docs/plans/archive/agent_ops_dashboard/proposal_glossary_tooltips.md and
        docs/plans/archive/agent_ops_dashboard/proposal_agent_glossary.md's investigations for why).

        Like get_ticket_corpus_stats(), this does its own fresh file read rather than participating
        in the mtime-cached _rebuild() cycle — all three sources are small and change far less
        often than tickets/runs, so a fresh read per call is simpler than restructuring
        _rebuild() for three more source files/dirs. self._maybe_rebuild() is still called first
        for interface consistency with every other method.
        """
        with self._lock:
            self._maybe_rebuild()

            terms: dict[str, GlossaryEntry] = {}
            for term, entry in load_glossary_registry(self._repo_root).items():
                terms[term] = GlossaryEntry(
                    term=entry["term"],
                    category=entry["category"],
                    description=entry["description"],
                )
            for layer, entry in layer_registry.load_registry(self._repo_root).items():
                if layer in terms:
                    # No current collision (verified: no layer name matches a glossary_registry
                    # term), but never let one registry silently shadow the other if a future
                    # addition to either ever collides — first-registered (glossary_registry) wins.
                    continue
                note = entry.get("note", "")
                if not note:
                    continue
                terms[layer] = GlossaryEntry(term=layer, category="layer", description=note)
            for agent_name, description in _load_agent_role_descriptions(self._repo_root).items():
                if agent_name in terms:
                    # Same shadow-protection precedent as the layer merge above — no current
                    # collision (verified: no .claude/agents/*.md `name:` matches any
                    # glossary_registry/layer term), first-registered source wins if one ever
                    # arises.
                    continue
                terms[agent_name] = GlossaryEntry(
                    term=agent_name, category="agent", description=description
                )

            return GlossaryResponse(terms=terms)

    def get_health(self) -> HealthStatus:
        with self._lock:
            self._maybe_rebuild()
            return HealthStatus(
                status="ok",
                cache_last_rebuilt_ts=self._last_rebuilt_ts,
                cache_source_mtimes=dict(self._source_mtimes),
                unparsed_lines=dict(self._unparsed_lines),
            )

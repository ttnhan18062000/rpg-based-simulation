"""File-reading, parsing, join, and in-memory cache layer for the Agent Ops
Dashboard backend.

Read-only: this module never writes to tickets/**, agent-monitoring/*.jsonl,
or any other durable source — it only reads them into an in-memory cache
rebuilt on source mtime change.

Reuses (never reimplements):
- tools/validate_frontmatter.py::extract_frontmatter for ticket frontmatter
- tools/generate_registry.py::parse_body_section/parse_h1_title/_strip_frontmatter
  for ticket body-section fields (title, tier, ticket_type, priority, workflow_status)
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
from generate_registry import parse_body_section, parse_h1_title, _strip_frontmatter  # noqa: E402
import validate  # noqa: E402  (tools/agent-monitoring/validate.py)

from src.api.agent_ops_dashboard.models import (
    FileTouch,
    HealthStatus,
    RawToolCall,
    RunDetail,
    RunMatchSummary,
    RunSummary,
    RunTimeline,
    TicketSummary,
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
    title = parse_h1_title(body)
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
        self._runs_file = repo_root / "agent-monitoring" / "runs.jsonl"
        self._events_file = repo_root / "agent-monitoring" / "events.jsonl"
        self._tools_file = repo_root / "agent-monitoring" / "tools.jsonl"
        self._tickets_root = repo_root / "tickets"
        self._lock = threading.RLock()

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
            "runs.jsonl": _mtime(self._runs_file),
            "events.jsonl": _mtime(self._events_file),
            "tools.jsonl": _mtime(self._tools_file),
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
            runs_all, runs_unparsed = load_jsonl_counted(self._runs_file)
            events_all, events_unparsed = load_jsonl_counted(self._events_file)
            tools_all, tools_unparsed = load_jsonl_counted(self._tools_file)

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
    ) -> list[TicketSummary]:
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
            return [_ticket_record_to_summary(r) for r in filtered]

    def get_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        workflow: Optional[str] = None,
        since: Optional[str] = None,
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

    def get_timeline(self, run_id: str) -> Optional[RunTimeline]:
        with self._lock:
            self._maybe_rebuild()
            if run_id not in self._runs_by_id and run_id not in self._inferred_active:
                return None

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

            is_live = run_id in self._inferred_active
            live_tail_raw: list[dict] = []
            if is_live:
                known_seqs = {e.get("seq") for e in raw_events}
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

    def get_health(self) -> HealthStatus:
        with self._lock:
            self._maybe_rebuild()
            return HealthStatus(
                status="ok",
                cache_last_rebuilt_ts=self._last_rebuilt_ts,
                cache_source_mtimes=dict(self._source_mtimes),
                unparsed_lines=dict(self._unparsed_lines),
            )

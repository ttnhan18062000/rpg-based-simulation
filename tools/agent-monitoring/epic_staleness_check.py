#!/usr/bin/env python3
"""Read-only check: flags open epic-tier tickets whose children showed real
activity evidence that has since gone idle past a staleness window.

Discovers candidate epics the same way `.claude/workflows/implement-epic.js`
discovers them — `epic_id` mode (a single `## Tier` -> `epic` ticket file in
`tickets/inprogress/`, children parsed from its `## Related Tickets` section)
and `folder` mode (`tickets/todos/{folder}/` containing a `SEQUENCE.md` and/or
an epic-tier ticket file, children parsed from `SEQUENCE.md` or sibling
`TCK-*.md` files) — then cross-references `tickets/working_log.csv` and
`agent-monitoring/runs.jsonl` for the most recent child-ticket activity.

An epic whose children have shown zero activity ever (no working_log.csv row,
no runs.jsonl record, for any child, ever) is NEVER flagged stale here — that
shape is a scoped-and-sequenced epic deliberately queued behind other work, a
normal planning state, not evidence of abandonment. It is instead surfaced,
separately, in a lower-priority "never started" informational list that only
the human-invoked report includes — never the hook nudge. Only an epic with
at least one child showing real activity evidence, followed by silence past
the window, is flagged stale. See
staging_artifacts/TCK-20260710-EPIC-STALENESS-CHECK/plan.md Decision 5.

An epic ticket whose own body `## Status` field reads `BLOCKED` is a
deliberately governed pause, not neglect — e.g. TCK-20260730-CODEX-RUNTIME-
ACTIVATION-EPIC, parked pending an explicit owner decision, with a dated
rationale in its own body. Such a candidate is NEVER flagged stale here
regardless of how idle its children have gone, and never lands in the
never-started bucket either — it is classified into a third, "blocked"
bucket instead. `find_stale_epics` (the hook fire-trigger) never returns a
blocked candidate. `compute_stale_epics_report` still surfaces blocked
candidates, separately, in an "Informational: BLOCKED epics" section, so
genuinely parked work stays visible without re-triggering the idle-activity
nudge. See docs/plans/archive/epic_staleness_status_aware_epic.md and
TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC.

Advisory only — mirrors retro_nudge_hook.py's shape (session-scoped state
file, bare try/except:pass hook wrapper, additionalContext only). Never
mutates a ticket file, never raises past its own entry points, never blocks
a tool call.
"""
import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_STALENESS_WINDOW_DAYS = 5

CHILD_ID_PATTERN = re.compile(r"TCK-\d{8}-[A-Z0-9-]+")

STATE_FILE = Path(".claude/.epic_staleness_state.json")
COOLDOWN_S = 3600  # fallback only, used if no session_id is available


@dataclass
class EpicCandidate:
    epic_id: str
    source_path: Path
    mode: str  # "epic_id" or "folder"
    child_ids: list
    epic_date: Optional[date] = None
    status: Optional[str] = None  # ticket body "## Status" value, upper-cased; None if unknown


# ---------------------------------------------------------------------------
# Ticket-file parsing helpers
# ---------------------------------------------------------------------------

def _dedupe_preserve_order(items: Iterable[str]) -> list:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _dedupe_candidates_by_epic_id(candidates: list) -> list:
    seen = set()
    result = []
    for candidate in candidates:
        if candidate.epic_id not in seen:
            seen.add(candidate.epic_id)
            result.append(candidate)
    return result


def _frontmatter_block(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return ""


def _frontmatter_field(text: str, field_name: str) -> Optional[str]:
    match = re.search(rf"^{field_name}:\s*(.+)$", _frontmatter_block(text), re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def _section_body(text: str, heading: str) -> str:
    heading_line = f"## {heading}"
    body_lines = []
    in_section = False
    for line in text.splitlines():
        if line.strip() == heading_line:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            body_lines.append(line)
    return "\n".join(body_lines).strip()


def _parse_epic_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def _child_ids_from_text(text: str, exclude_id: str) -> list:
    found = [tid for tid in CHILD_ID_PATTERN.findall(text) if tid != exclude_id]
    return _dedupe_preserve_order(found)


def _find_governing_epic_status(inprogress_dir: Path, child_ids: list) -> Optional[str]:
    """Cross-references tickets/inprogress/ for an epic-tier ticket whose own
    '## Related Tickets' body references at least one of a todos_dir
    subfolder's child ticket IDs. Used when the subfolder itself has no
    epic-tier ticket file (e.g. tickets/todos/codex-runtime-activation/,
    whose real governing epic TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC
    lives in tickets/inprogress/ instead), so the folder candidate's status
    (e.g. BLOCKED) is still discoverable instead of falling through to None.
    Cross-referencing by child-ID overlap is used rather than a folder-name-
    to-epic-id string convention because it is anchored on data the two
    tickets already carry (parent/child references) and survives folder or
    epic-ticket renames that a name-matching heuristic would not."""
    if not child_ids or not inprogress_dir.exists():
        return None
    child_id_set = set(child_ids)
    for ticket_file in sorted(inprogress_dir.glob("*.md")):
        try:
            text = ticket_file.read_text()
        except Exception:
            continue
        if _section_body(text, "Tier").strip().lower() != "epic":
            continue
        related_ids = set(CHILD_ID_PATTERN.findall(_section_body(text, "Related Tickets")))
        if related_ids & child_id_set:
            status_body = _section_body(text, "Status").strip()
            return status_body.upper() if status_body else None
    return None


# ---------------------------------------------------------------------------
# Step 1 — discovery
# ---------------------------------------------------------------------------

def discover_candidate_epics(inprogress_dir: Path, todos_dir: Path) -> list:
    candidates = []

    if inprogress_dir.exists():
        for ticket_file in sorted(inprogress_dir.glob("*.md")):
            try:
                text = ticket_file.read_text()
            except Exception:
                continue
            if _section_body(text, "Tier").strip().lower() != "epic":
                continue
            epic_id = _frontmatter_field(text, "ticket_id") or ticket_file.stem
            epic_date = _parse_epic_date(_frontmatter_field(text, "date"))
            child_ids = _child_ids_from_text(_section_body(text, "Related Tickets"), epic_id)
            status_body = _section_body(text, "Status").strip()
            candidates.append(EpicCandidate(
                epic_id=epic_id,
                source_path=ticket_file,
                mode="epic_id",
                child_ids=child_ids,
                epic_date=epic_date,
                status=status_body.upper() if status_body else None,
            ))

    if todos_dir.exists():
        for subdir in sorted(p for p in todos_dir.iterdir() if p.is_dir()):
            sequence_path = subdir / "SEQUENCE.md"
            has_sequence = sequence_path.exists()

            epic_ticket_file = None
            epic_text = None
            for ticket_file in sorted(subdir.glob("TCK-*.md")):
                try:
                    ticket_text = ticket_file.read_text()
                except Exception:
                    continue
                if _section_body(ticket_text, "Tier").strip().lower() == "epic":
                    epic_ticket_file = ticket_file
                    epic_text = ticket_text
                    break

            if not has_sequence and epic_ticket_file is None:
                continue

            if epic_text is not None:
                epic_id = _frontmatter_field(epic_text, "ticket_id") or epic_ticket_file.stem
                epic_date = _parse_epic_date(_frontmatter_field(epic_text, "date"))
                status_body = _section_body(epic_text, "Status").strip()
                status = status_body.upper() if status_body else None
            else:
                epic_id = f"FOLDER-tickets-todos-{subdir.name}"
                epic_date = None
                status = None

            child_ids = []
            if has_sequence:
                try:
                    child_ids = _child_ids_from_text(sequence_path.read_text(), epic_id)
                except Exception:
                    child_ids = []
            if not child_ids:
                sibling_files = sorted(p for p in subdir.glob("TCK-*.md") if p != epic_ticket_file)
                child_ids = _dedupe_preserve_order(
                    p.stem for p in sibling_files if p.stem != epic_id
                )

            if epic_text is None:
                cross_referenced_status = _find_governing_epic_status(inprogress_dir, child_ids)
                if cross_referenced_status is not None:
                    status = cross_referenced_status

            candidates.append(EpicCandidate(
                epic_id=epic_id,
                source_path=subdir,
                mode="folder",
                child_ids=child_ids,
                epic_date=epic_date,
                status=status,
            ))

    return _dedupe_candidates_by_epic_id(candidates)


# ---------------------------------------------------------------------------
# Step 2 — activity resolution
# ---------------------------------------------------------------------------

def resolve_child_activity(
    child_ids: Iterable[str],
    working_log_rows: Iterable[dict],
    runs_records: Iterable[dict],
) -> Optional[datetime]:
    child_id_set = set(child_ids)
    if not child_id_set:
        return None

    latest = None

    for row in working_log_rows:
        tid = str(row.get("ticket_id", "")).strip()
        if tid not in child_id_set:
            continue
        ts_raw = str(row.get("timestamp", "")).strip()
        if not ts_raw:
            continue
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except Exception:
            continue
        if latest is None or ts > latest:
            latest = ts

    for record in runs_records:
        rid = str(record.get("run_id") or record.get("ticket_id") or "").strip()
        if rid not in child_id_set:
            continue
        ts_raw = record.get("start_ts") or record.get("started_at")
        if not ts_raw:
            continue
        try:
            ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        except Exception:
            continue
        if latest is None or ts > latest:
            latest = ts

    return latest


# ---------------------------------------------------------------------------
# Step 3 — staleness decision (no epic_date fallback, per Decision 5)
# ---------------------------------------------------------------------------

def is_epic_blocked(candidate: EpicCandidate) -> bool:
    return (candidate.status or "").strip().upper() == "BLOCKED"


def is_epic_stale(
    candidate: EpicCandidate,
    most_recent_activity: Optional[datetime],
    now: datetime,
    window_days: int = DEFAULT_STALENESS_WINDOW_DAYS,
) -> bool:
    if is_epic_blocked(candidate):
        return False
    if not candidate.child_ids:
        return False
    if most_recent_activity is None:
        return False
    return (now - most_recent_activity) > timedelta(days=window_days)


def is_epic_never_started(
    candidate: EpicCandidate,
    most_recent_activity: Optional[datetime],
) -> bool:
    return bool(candidate.child_ids) and most_recent_activity is None


# ---------------------------------------------------------------------------
# Step 4 — top-level report / hook-decision functions
# ---------------------------------------------------------------------------

def _read_working_log_rows(working_log_path: Path) -> list:
    try:
        with open(working_log_path, newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _read_runs_records(runs_jsonl_path: Path) -> list:
    try:
        text = runs_jsonl_path.read_text()
    except Exception:
        return []
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            continue
    return records


def _classify_candidates(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now, window_days):
    candidates = discover_candidate_epics(inprogress_dir, todos_dir)
    working_log_rows = _read_working_log_rows(working_log_path)
    runs_records = _read_runs_records(runs_jsonl_path)

    stale = []
    never_started = []
    blocked = []
    for candidate in candidates:
        most_recent = resolve_child_activity(candidate.child_ids, working_log_rows, runs_records)
        if is_epic_blocked(candidate):
            blocked.append((candidate, most_recent))
        elif is_epic_stale(candidate, most_recent, now, window_days):
            stale.append((candidate, most_recent))
        elif is_epic_never_started(candidate, most_recent):
            never_started.append(candidate)
    return stale, never_started, blocked


def find_stale_epics(
    inprogress_dir: Path,
    todos_dir: Path,
    working_log_path: Path,
    runs_jsonl_path: Path,
    now: Optional[datetime] = None,
    window_days: int = DEFAULT_STALENESS_WINDOW_DAYS,
) -> list:
    """The sole function the hook wrapper consults to decide fire/no-fire —
    never the never-started/blocked/informational lists, never a string-parse
    of compute_stale_epics_report's output. A BLOCKED candidate never appears
    here regardless of idle time (see is_epic_blocked/is_epic_stale)."""
    try:
        now = now or datetime.now(timezone.utc)
        stale, _, _ = _classify_candidates(inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now, window_days)
        return [candidate for candidate, _ in stale]
    except Exception:
        return []


def _format_epic_line(candidate: EpicCandidate) -> str:
    return f"{candidate.epic_id} ({candidate.source_path})"


def compute_stale_epics_report(
    inprogress_dir: Path,
    todos_dir: Path,
    working_log_path: Path,
    runs_jsonl_path: Path,
    now: Optional[datetime] = None,
    window_days: int = DEFAULT_STALENESS_WINDOW_DAYS,
) -> str:
    try:
        now = now or datetime.now(timezone.utc)
        stale, never_started, blocked = _classify_candidates(
            inprogress_dir, todos_dir, working_log_path, runs_jsonl_path, now, window_days
        )

        lines = ["--- Epic Staleness Report ---", "", "Stale epics:"]
        if stale:
            for candidate, most_recent in stale:
                days_idle = (now - most_recent).days
                lines.append(f"  {_format_epic_line(candidate)} — {days_idle} days idle")
        else:
            lines.append("  none")

        lines.append("")
        lines.append("Informational: never-started epics (not stale — no child activity recorded yet):")
        if never_started:
            for candidate in never_started:
                if candidate.epic_date is not None:
                    since_str = f"{(now.date() - candidate.epic_date).days} days since scoped"
                else:
                    since_str = "date unknown"
                lines.append(f"  {_format_epic_line(candidate)} — {since_str}")
        else:
            lines.append("  none")

        lines.append("")
        lines.append("Informational: BLOCKED epics (not stale — deliberately parked):")
        if blocked:
            for candidate, most_recent in blocked:
                if most_recent is not None:
                    days_idle = (now - most_recent).days
                    since_str = f"{days_idle} days idle"
                else:
                    since_str = "no child activity recorded"
                lines.append(f"  {_format_epic_line(candidate)} — {since_str}")
        else:
            lines.append("  none")

        return "\n".join(lines)
    except Exception as exc:
        return f"--- Epic Staleness Report ---\n\ncould not complete: {exc}"


# ---------------------------------------------------------------------------
# Step 6 — thin hook wrapper (invoked with --hook, reads stdin JSON)
# ---------------------------------------------------------------------------

def _load_hook_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


if __name__ == "__main__":
    if "--hook" in sys.argv:
        try:
            payload = json.load(sys.stdin)
            session_id = payload.get("session_id", "")

            state = _load_hook_state()
            now_epoch = time.time()
            if session_id and state.get("session_id") == session_id:
                sys.exit(0)
            if not session_id and now_epoch - state.get("ts", 0) < COOLDOWN_S:
                sys.exit(0)

            stale = find_stale_epics(
                Path("tickets/inprogress"),
                Path("tickets/todos"),
                Path("tickets/working_log.csv"),
                Path("agent-monitoring/runs.jsonl"),
            )

            if stale:
                STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
                STATE_FILE.write_text(json.dumps({"session_id": session_id, "ts": now_epoch}))
                names = ", ".join(_format_epic_line(c) for c in stale)
                message = (
                    f"epic-staleness: {len(stale)} open epic(s) have gone idle past the "
                    f"{DEFAULT_STALENESS_WINDOW_DAYS}-day staleness window: {names}. "
                    "Run `make agent-monitoring-epic-staleness` to review."
                )
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": message,
                    }
                }))
        except Exception:
            pass
    else:
        print(compute_stale_epics_report(
            Path("tickets/inprogress"),
            Path("tickets/todos"),
            Path("tickets/working_log.csv"),
            Path("agent-monitoring/runs.jsonl"),
        ))

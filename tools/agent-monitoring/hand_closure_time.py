"""tools/agent-monitoring/hand_closure_time.py: the real start, end and provenance of a hand-closed ticket
(TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS; design in
agent-working/stored_artifacts/TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN/design.md).

`record_hand_orchestrated_closure.py` used to write `start_ts = end_ts = now`, so `duration_s` came out 0 and was read as a
measurement. This module resolves one of three sources, in this precedence:

    declared       the closer passed `--start-ts` (measured by the closer)
    tool_activity  the closing session's own `tools.jsonl` rows (matching `session_id`, `run_id` null) since the later of
                   (a) the end of its previous hand closure and (b) the start of the current activity block
                   (a gap above `PAUSE_THRESHOLD_SECONDS` ends a block); at least `MIN_CLAIMED_ROWS` rows
    unknown        otherwise: `start_ts == end_ts` (the field is required) and `duration_s` is null, never 0

Each closure claims only the rows after the previous closure's end, so a row is claimed by at most one closure. The
claimed rows are also the cost join (TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION): `Resolution.claimed`. Pure functions over lists of dicts plus two thin readers; never raises.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from duration_utils import PAUSE_THRESHOLD_SECONDS

MIN_CLAIMED_ROWS = 3
DECLARED, TOOL_ACTIVITY, UNKNOWN = "declared", "tool_activity", "unknown"
DURATION_SOURCES = (DECLARED, TOOL_ACTIVITY, UNKNOWN)
_WEEKS_READ = 2  # the current and the previous ISO-week folder: a closure's own activity is never older


def _parse(ts) -> datetime | None:
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True)
class Resolution:
    duration_source: str
    start_ts: str
    end_ts: str
    claim_peers: int | None = None  # only with tool_activity
    claimed: tuple[dict, ...] = field(default=(), compare=False)


def _read_jsonl(path: Path) -> list[dict]:
    out = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _week_dirs(data_dir: Path) -> list[Path]:
    return sorted(p for p in Path(data_dir).glob("*") if p.is_dir())[-_WEEKS_READ:]


def session_tool_rows(session_id: str, data_dir: Path) -> list[dict]:
    """The session's unattributed tool rows (`run_id` null: a row with a sidecar `run_id` keeps that attribution), oldest first."""
    if not session_id:
        return []
    rows = [r for week in _week_dirs(data_dir) for path in sorted(week.glob("*tools.jsonl")) for r in _read_jsonl(path)
            if r.get("session_id") == session_id and r.get("run_id") is None and _parse(r.get("ts"))]
    return sorted(rows, key=lambda r: r["ts"])


def prior_closure_ends(session_id: str, data_dir: Path, before: str) -> list[str]:
    """End timestamps of this session's earlier hand closures (runs carrying `session_id`), oldest first."""
    if not session_id:
        return []
    limit = _parse(before)
    ends = [r["end_ts"] for week in _week_dirs(data_dir) for path in sorted(week.glob("*runs.jsonl")) for r in _read_jsonl(path)
            if r.get("execution_mode") == "hand" and r.get("session_id") == session_id
            and _parse(r.get("end_ts")) and limit and _parse(r["end_ts"]) < limit]
    return sorted(ends, key=_parse)


def activity_block(rows: list[dict], end_ts: str, gap_s: float = PAUSE_THRESHOLD_SECONDS) -> list[dict]:
    """The contiguous run of rows ending at `end_ts`: walk back until a gap above `gap_s`. Oldest first."""
    end = _parse(end_ts)
    block: list[dict] = []
    last = end
    for row in reversed([r for r in rows if end and _parse(r["ts"]) <= end]):
        t = _parse(row["ts"])
        if (last - t).total_seconds() > gap_s:
            break
        block.append(row)
        last = t
    return block[::-1]


def claim_rows(rows: list[dict], end_ts: str, prior_ends: list[str], gap_s: float = PAUSE_THRESHOLD_SECONDS) -> tuple[list[dict], int]:
    """(claimed rows, claim_peers): the rows of the activity block after the latest prior closure's end, and how many
    prior closures of this session ended inside that block."""
    block = activity_block(rows, end_ts, gap_s)
    if not block:
        return [], 0
    first = _parse(block[0]["ts"])
    peers = [e for e in prior_ends if _parse(e) >= first]
    lower = _parse(max(peers, key=_parse)) if peers else None
    claimed = [r for r in block if lower is None or _parse(r["ts"]) > lower]
    return claimed, len(peers)


def _declared_claim(rows: list[dict], start: str, end: str, prior_ends: list[str]) -> list[dict]:
    """With a declared start the closer names the window: the session's rows in [start, end] after its previous closure."""
    lo, hi = _parse(start), _parse(end)
    lower = _parse(max(prior_ends, key=_parse)) if prior_ends else None
    if lo is None or hi is None:
        return []
    return [r for r in rows if lo <= _parse(r["ts"]) <= hi and (lower is None or _parse(r["ts"]) > lower)]


def resolve(now: str, declared_start: str | None, declared_end: str | None, session_id: str | None,
            rows: list[dict], prior_ends: list[str]) -> Resolution:
    """The closure's start/end/provenance. `now` is the closure time; `declared_end` replaces it when given."""
    end = declared_end or now
    if declared_start:
        return Resolution(DECLARED, declared_start, end, None, tuple(_declared_claim(rows, declared_start, end, prior_ends)))
    claimed, peers = claim_rows(rows, end, prior_ends)
    if len(claimed) >= MIN_CLAIMED_ROWS:
        return Resolution(TOOL_ACTIVITY, claimed[0]["ts"], end, peers, tuple(claimed))
    return Resolution(UNKNOWN, end, end)


def resolve_for_session(now: str, declared_start: str | None, declared_end: str | None, session_id: str | None,
                        data_dir: Path) -> Resolution:
    """`resolve` with the session's rows and prior closures read from `data_dir`; a read failure is `unknown`, never an error."""
    try:
        end = declared_end or now
        sid = session_id or ""
        rows = session_tool_rows(sid, data_dir)
        prior = prior_closure_ends(sid, data_dir, end)
        return resolve(now, declared_start, declared_end, session_id, rows, prior)
    except Exception:  # noqa: BLE001 - monitoring must never fail a closure
        return Resolution(UNKNOWN, declared_end or now, declared_end or now)

#!/usr/bin/env python3
"""Durable record of reset-boundary declarations (TCK-20261015-SESSION-LAYER-MEASURES-SEAT-SUFFIX-RESET-RECORD-NOTE-CAP).

A session says at a stopping point whether a `/clear` is safe (HARD: clear now; SOFT: only with a note; NEVER: do not).
Until now that was said in chat only, so whether a `/clear` happened at a HARD boundary could not be audited. The
declaration is run as a command and appended, one row per call, to this week's
`agent-working/agent-monitoring/data/<week>/reset_boundary.jsonl` (the bare weekly file, written through the shared locked
writer, like `role_boundary.jsonl`; this is not a `manual_actions` row, that metric counts owner-typed repeats).

    python3 tools/sessions/reset_boundary.py declare --kind HARD --row "<process row of the boundary map>"

Row: `{ts, session_id, session_role, kind, row, handover_rel, handover_sha256}`. Never fails the caller: any error prints one
warning line and exits 0. `advisory_for_clear()` is what SessionStart calls on `source == clear`; it never raises.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

KINDS = ("HARD", "SOFT", "NEVER")
FILENAME = "reset_boundary.jsonl"


def _data_dir(root: Path) -> Path:
    from tools.agent_working_paths import AGENT_MONITORING

    return Path(root) / AGENT_MONITORING / "data"


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def handover_path(root: Path, role_id: str, instance_id: str | None = None) -> tuple[str | None, Path | None]:
    """(role-relative handover path, absolute path) of an instance, or (None, None) when the role is unknown."""
    from tools.sessions.roster import handover_rel, load_roster
    from tools.handover_home import handover_base

    role = load_roster(root).role(role_id)
    if role is None:
        return None, None
    rel = handover_rel(role, instance_id)
    return rel, handover_base(root) / rel


def build_row(kind: str, row_text: str, session_id: str, instance: str | None, root: Path, now: datetime | None = None) -> dict:
    """The record to append. `session_role` is the instance id when known (`rpg-implementer-2`), else the role."""
    from tools.sessions.roster import load_roster

    roster = load_roster(root)
    role = roster.role(instance) if instance else None
    base = role
    if base is None and instance:
        head, _, tail = instance.rpartition("-")
        base = roster.role(head) if tail.isdigit() else None
    rel, path = handover_path(root, base.role, instance if instance != base.role else None) if base else (None, None)
    now = now or datetime.now(timezone.utc)
    return {"ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "session_id": session_id, "session_role": instance,
            "kind": kind, "row": row_text, "handover_rel": rel, "handover_sha256": _sha256(path) if path else None}


def append_row(record: dict, root: Path, data_dir: Path | None = None) -> bool:
    """Append `record` to this week's `reset_boundary.jsonl`. Never raises; True when written."""
    try:
        sys.path.insert(0, str(_REPO_ROOT / "tools" / "agent-monitoring"))
        from writer import write_line

        week = datetime.strptime(record["ts"], "%Y-%m-%dT%H:%M:%SZ").strftime("%G-W%V")
        target = (Path(data_dir) if data_dir is not None else _data_dir(root)) / week / FILENAME
        target.parent.mkdir(parents=True, exist_ok=True)
        return bool(write_line(target, json.dumps(record, separators=(",", ":"))))
    except Exception:  # noqa: BLE001
        return False


def read_rows(root: Path, data_dir: Path | None = None) -> list[dict]:
    """Every declaration of every week, file order. Bad lines are skipped; never raises."""
    rows: list[dict] = []
    base = Path(data_dir) if data_dir is not None else _data_dir(root)
    try:
        for path in sorted(base.glob(f"*/{FILENAME}")):
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except OSError:
        pass
    return rows


def advisory_for_clear(rows: list[dict], previous_session_id: str, current_sha256: str | None, instance: str) -> str | None:
    """One advisory line for a `/clear`, or None. Pure.

    - the previous session declared no HARD boundary: say so;
    - it did, but the handover note changed after the declaration (the sha differs): say so, the clear may have dropped
      the later edits' context. A missing note on either side compares as unchanged-unknown and says nothing."""
    mine = [r for r in rows if r.get("session_id") == previous_session_id]
    hard = [r for r in mine if r.get("kind") == "HARD"]
    if not hard:
        return (f"reset-boundary: the previous session of `{instance}` declared no HARD boundary before this /clear "
                "(declare it with `python3 tools/sessions/reset_boundary.py declare --kind HARD --row \"<boundary-map row>\"`; "
                "advisory only).")
    declared = hard[-1].get("handover_sha256")
    if declared and current_sha256 and declared != current_sha256:
        return (f"reset-boundary: the handover note of `{instance}` changed after the previous session's HARD declaration "
                f"({hard[-1].get('ts')}); check it still says what the next session needs (advisory only).")
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("declare", help="record a reset-boundary declaration for this session")
    d.add_argument("--kind", required=True, choices=KINDS)
    d.add_argument("--row", required=True, help="the boundary-map process row this declaration is about")
    d.add_argument("--data-dir", default=None, help="testing: override agent-working/agent-monitoring/data")
    args = ap.parse_args(argv)
    try:
        root = _REPO_ROOT
        session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        instance = os.environ.get("SESSION_ROLE") or None
        if not instance and session_id:
            from tools.sessions import guard, state

            instance = guard.find_session_instance(state.state_root(str(root)), session_id)
        record = build_row(args.kind, args.row, session_id, instance, root)
        ok = append_row(record, root, Path(args.data_dir) if args.data_dir else None)
        print(("recorded: " if ok else "WARNING: could not write; would have recorded: ") + json.dumps(record, sort_keys=True))
    except Exception as exc:  # noqa: BLE001 - never fails the caller
        print(f"WARNING: reset-boundary declaration not recorded ({type(exc).__name__}: {exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

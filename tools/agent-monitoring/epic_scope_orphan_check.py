#!/usr/bin/env python3
"""Standalone, repo-wide sweep detecting the epic-scope-orphan defect fixed by
TCK-20260711-EPIC-SCOPE-ORPHAN-FIX: an epic-tier ticket present in both `tickets/inprogress/`
and `tickets/todos/**` simultaneously (a permanent duplicate, since epic tier never reaches
Finalize's cleanup `rm` step).

This is the *actual* orphan signature — dual presence — not merely "an epic ticket resting in
`tickets/inprogress/`", which is the normal, documented resting place for `epic_id`-mode epics
per `docs/ai/ticket-lifecycle.md:440` and must never be flagged on its own. It also must not flag
non-epic (hotfix/standard) dual presence, which is the normal, expected mid-workflow state pending
Finalize reconciliation.

Mirrors `tools/gate_checks/workflow_meta_conformance.py`'s shape: a single aggregate function
returning `list[dict]`, plus a standalone `MARKER:`-prefixed JSON CLI entrypoint, not wired into
any workflow phase or into `done_checker_static.py`'s aggregates — this check has no natural
in-pipeline call site for epic tier (epic returns before Verify/Finalize ever run), so it ships
standalone, ready for a future ticket to wire in without an interface change.

Reuses `epic_staleness_check.py`'s `_section_body()` for `## Tier` parsing rather than
reimplementing the section-scan a third time.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from epic_staleness_check import _section_body  # noqa: E402

DEFAULT_INPROGRESS_DIR = Path("tickets/inprogress")
DEFAULT_TODOS_DIR = Path("tickets/todos")


def check_single_epic_orphan(
    ticket_id: str,
    inprogress_path: Path,
    todos_dir: Path = DEFAULT_TODOS_DIR,
) -> tuple[str, str]:
    """(status, evidence) shape mirroring `done_checker_static.py::check_ticket_location`.

    `"FAIL"` only when a `tickets/todos/**/{ticket_id}.md` original still exists alongside the
    epic-tier copy at `inprogress_path` — dual presence, the actual orphan signature. `"PASS"`
    otherwise (including when `inprogress_path` itself doesn't exist, or the ticket is simply
    resting in `tickets/inprogress/` with no todos original).
    """
    todos_matches = sorted(todos_dir.rglob(f"{ticket_id}.md")) if todos_dir.exists() else []
    if not todos_matches:
        return ("PASS", f"No tickets/todos/ original found for {ticket_id}")

    todos_path = todos_matches[0]
    return (
        "FAIL",
        f"{ticket_id} exists in both {inprogress_path} and {todos_path} simultaneously "
        "(epic-tier ticket never reaches Finalize's cleanup step)",
    )


def scan_epic_scope_orphans(
    inprogress_dir: Path = DEFAULT_INPROGRESS_DIR,
    todos_dir: Path = DEFAULT_TODOS_DIR,
) -> list:
    """Aggregate repo-wide sweep: one `{"ticket_id", "status", "evidence"}` dict per epic-tier
    file found in `inprogress_dir`. Non-epic tickets resting in `inprogress_dir` are never
    candidates — they are excluded from the result entirely, not merely marked `"PASS"` — since
    the orphan signature this check exists for is epic-tier-specific.
    """
    results = []
    if not inprogress_dir.exists():
        return results

    for ticket_file in sorted(inprogress_dir.glob("*.md")):
        try:
            text = ticket_file.read_text()
        except Exception:
            continue
        if _section_body(text, "Tier").strip().lower() != "epic":
            continue
        ticket_id = ticket_file.stem
        status, evidence = check_single_epic_orphan(ticket_id, ticket_file, todos_dir)
        results.append({"ticket_id": ticket_id, "status": status, "evidence": evidence})

    return results


if __name__ == "__main__":
    print("MARKER:" + json.dumps(scan_epic_scope_orphans()))

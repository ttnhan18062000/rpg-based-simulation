#!/usr/bin/env python3
"""Deterministic ticket-location resolution for the Scope phase's ticketId-provided branch
of `.claude/workflows/implement-ticket.js`.

Built for TCK-20260711-EPIC-SCOPE-ORPHAN-FIX: the Scope phase used to have the ticket-scoper
agent locate a ticket file (checking `tickets/inprogress/`, then `tickets/done/`, then
`tickets/todos/**`) and unconditionally *copy* a todos-originated file to
`tickets/inprogress/{id}.md` inside its own LLM-interpreted prompt text, before the tier was
known. For epic-tier tickets — which return immediately after Scope and never reach Finalize's
`rm` cleanup step — that copy became a permanent duplicate. This module moves the same
file-location + tier-read + relocate decision out of agent-prompt text into orchestrator-side
`bash()`: copy-then-delete (a move) when `## Tier` is `epic`, copy-only otherwise, preserving the
existing Finalize-reconciliation behavior for hotfix/standard tickets.

Reuses `epic_staleness_check.py`'s `_section_body()` for `## Tier` parsing rather than
reimplementing the section-scan a third time (the agent-prompt's own ad hoc extraction was the
second instance; this replaces that instance, not adds a fourth parser).
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from epic_staleness_check import _section_body  # noqa: E402

DEFAULT_INPROGRESS_DIR = Path("tickets/inprogress")
DEFAULT_TODOS_DIR = Path("tickets/todos")
DEFAULT_DONE_DIR = Path("tickets/done")

DEFAULT_TIER = "standard"


def resolve_and_relocate_ticket(
    ticket_id: str,
    inprogress_dir: Path = DEFAULT_INPROGRESS_DIR,
    todos_dir: Path = DEFAULT_TODOS_DIR,
    done_dir: Path = DEFAULT_DONE_DIR,
) -> dict:
    """Locate `ticket_id`'s file (inprogress -> done -> todos, first hit wins) and, if found
    under `todos_dir`, relocate it to `inprogress_dir` — moving (deleting the todos original)
    when the ticket's `## Tier` is `epic`, copying (leaving the todos original in place) otherwise.

    Returns a dict with a fixed small `action` enum: "already_in_inprogress",
    "already_in_done", "not_found", "moved_from_todos", "copied_from_todos".
    """
    inprogress_path = inprogress_dir / f"{ticket_id}.md"
    if inprogress_path.exists():
        text = inprogress_path.read_text()
        return {
            "ticket_path": str(inprogress_path),
            "tier": _section_body(text, "Tier").strip().lower() or DEFAULT_TIER,
            "todos_source_path": "",
            "action": "already_in_inprogress",
        }

    done_path = done_dir / f"{ticket_id}.md"
    if done_path.exists():
        text = done_path.read_text()
        return {
            "ticket_path": str(done_path),
            "tier": _section_body(text, "Tier").strip().lower() or DEFAULT_TIER,
            "todos_source_path": "",
            "action": "already_in_done",
        }

    todos_matches = sorted(todos_dir.rglob(f"{ticket_id}.md")) if todos_dir.exists() else []
    if not todos_matches:
        return {
            "ticket_path": "",
            "tier": "",
            "todos_source_path": "",
            "action": "not_found",
        }

    todos_path = todos_matches[0]
    text = todos_path.read_text()
    tier = _section_body(text, "Tier").strip().lower() or DEFAULT_TIER

    inprogress_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(todos_path, inprogress_path)

    if tier == "epic":
        todos_path.unlink()
        action = "moved_from_todos"
    else:
        action = "copied_from_todos"

    return {
        "ticket_path": str(inprogress_path),
        "tier": tier,
        "todos_source_path": str(todos_path),
        "action": action,
    }


if __name__ == "__main__":
    print("MARKER:" + json.dumps(resolve_and_relocate_ticket(sys.argv[1])))

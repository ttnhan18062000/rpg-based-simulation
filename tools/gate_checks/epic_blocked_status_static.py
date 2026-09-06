"""Deterministic BLOCKED-status backstop for implement-epic.js's folder-mode and epic_id-mode
Discover phases.

Built for TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS: implement-epic.js's Discover phase determined
"already done" purely by checking `tickets/done/` for a matching file, with no equivalent read of
a candidate ticket's own `## Status` body field -- a `BLOCKED` ticket left in a batch would be
attempted in normal sequence instead of being excluded and reported separately. This repo already
shipped the identical fix for a sibling tool
(`tools/agent-monitoring/epic_staleness_check.py::is_epic_blocked()`/`_section_body()`) -- this
module gives `implement-epic.js`'s own Discover phase the equivalent real, testable mechanism
instead of leaving the logic as opaque agent-prompt English, mirroring
`tools/gate_checks/epic_tracking_doc_static.py`'s own "give Discover a real mechanism instead of a
raw agent-prompt English read" precedent for the sibling `tracking_doc` gap.

One function, called from Discover (via the orchestrator's own `bash()`) once the candidate
`ticket_ids` list for a batch is already known (after SEQUENCE.md ordering / `## Related Tickets`
parsing, before the `already_done` filter) -- mirrors `parse_tracking_doc_from_sequence`'s own
"give Discover a real mechanism, called once, over already-known inputs" shape.
"""
from __future__ import annotations

from pathlib import Path


def read_ticket_status(ticket_path: str | Path) -> str:
    """Returns the ticket's body `## Status` value, upper-cased and stripped -- "" if the file
    doesn't exist or has no `## Status` section. Mirrors
    `epic_staleness_check.py`'s own `_section_body()`/`is_epic_blocked()` reading convention (a
    ticket *body* field, not YAML frontmatter -- CLAUDE.md's own documented reason `## Status` is
    parsed this way, not via `validate_frontmatter.py`)."""
    resolved = Path(ticket_path)
    if not resolved.exists():
        return ""
    text = resolved.read_text()
    heading_line = "## Status"
    body_lines: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.strip() == heading_line:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            body_lines.append(line)
    return "\n".join(body_lines).strip().upper()


def find_ticket_path(ticket_id: str, search_roots: list[str]) -> str | None:
    """Resolves a ticket_id to its real file path, checking each root directly
    (`{root}/{ticket_id}.md`) and one level of subdirectories (`{root}/*/{ticket_id}.md}`, for
    folder-batch subfolders like `tickets/todos/some-batch/`). Returns None if not found under any
    root -- the caller treats an unresolved ticket_id as not-blocked (status "") rather than
    erroring, since a missing file is a separate, pre-existing concern this module doesn't own."""
    for root in search_roots:
        root_path = Path(root)
        direct = root_path / f"{ticket_id}.md"
        if direct.exists():
            return str(direct)
        for candidate in root_path.glob(f"*/{ticket_id}.md"):
            return str(candidate)
    return None


def find_blocked_ticket_ids(ticket_ids: list[str], search_roots: list[str]) -> list[str]:
    """Given a candidate `ticket_ids` list and the directories to search for each one's real file
    (folder mode: just that one folder; epic_id mode: `tickets/inprogress`, `tickets/todos`,
    `tickets/done`, matching Discover's own existing epic-ticket search precedent), returns the
    subset whose `## Status` reads `BLOCKED`. Order matches `ticket_ids`' own order."""
    blocked = []
    for ticket_id in ticket_ids:
        path = find_ticket_path(ticket_id, search_roots)
        if path is not None and read_ticket_status(path) == "BLOCKED":
            blocked.append(ticket_id)
    return blocked

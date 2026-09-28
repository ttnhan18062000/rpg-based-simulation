#!/usr/bin/env python3
"""
Report a tickets/todos/<folder>/'s epic-tier parent (if any) and which non-epic children are
still open, for TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT.

Both `.claude/workflows/implement-epic.js`'s folder-cleanup block and
`.claude/workflows/implement-ticket.js`'s Finalize step 3 need the same answer ("is this folder's
epic parent the only thing left, and which file is it?") and previously had no shared, committed
way to get it — the alternative was an inline `python3 -c "..."` in each prompt, which
`tests/tools/test_finalize_working_log_uses_helper_pin.py`'s own blanket "no inline Python source
in the Finalize prompt" guard correctly rejects (TCK-20260912-WORKING-LOG-APPEND-HELPER's own
precedent: a committed helper with a real CLI, never inline source, for exactly this reason).

The epic parent is identified structurally, via the canonical body-section parser
(`tools/generate_registry.py::parse_body_section`, the same parser `tools/ticket_field_values.py`
uses for `## Tier`/`## Priority`) — `## Tier: epic` or `## Status: EPIC_SCOPED` — never by a
filename convention like `-EPIC-`, which both a real epic ticket and a coincidentally-named
non-epic ticket could defeat.

Usage:
  python3 tools/epic_folder_status.py <folder>
  python3 tools/epic_folder_status.py <folder> --done-dir <path>   # test override

Prints one JSON object to stdout and always exits 0 — this is a status report, not a pass/fail
gate (the calling workflow prompt decides what the status means).
"""
import argparse
import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from generate_registry import parse_body_section, _strip_frontmatter  # noqa: E402
from validate_frontmatter import extract_frontmatter  # noqa: E402


def get_epic_folder_status(folder: Path, done_dir: Path) -> dict:
    """Return `{"folder", "epic_parent", "epic_parent_ticket_id", "open_children",
    "stale_child_copies", "all_children_done"}` for the `TCK-*.md` files directly under `folder`.

    `epic_parent`/`epic_parent_ticket_id` are the path/frontmatter `ticket_id` of the one file
    whose `## Tier` reads "epic" or `## Status` reads "EPIC_SCOPED" (`None`/`None` if no such file
    exists in this folder). `open_children` lists the frontmatter `ticket_id` of every OTHER
    (non-epic) `TCK-*.md` file not yet found as `<done_dir>/<ticket_id>.md`.

    `stale_child_copies` (TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT, agent-working-
    design review) lists the frontmatter `ticket_id` of every non-epic `TCK-*.md` file that is
    BOTH still physically present in `folder` AND already found as `<done_dir>/<ticket_id>.md` —
    a resurrected pre-close copy (the exact shape this ticket's own batch started with:
    `tickets/todos/mechanism-registry/`'s 5 child files re-added by an unrelated PR after #209
    had already archived the real ones flat into `tickets/done/`). Every archived folder on this
    branch holds at most one `TCK-*.md` (the epic parent) — a physically-present non-epic child
    is always anomalous, never a legitimate "child closed in place" state, so this is reported
    separately from `open_children` rather than folded into it: an `open_children` entry means
    "not done yet, don't move"; a `stale_child_copies` entry means "already done elsewhere, this
    copy needs deleting before the move" — different fixes, so callers must not conflate them.

    `all_children_done` is `len(open_children) == 0`, independent of `stale_child_copies` and of
    the epic parent's own state — a folder with an open epic parent but all real children done is
    exactly the case this ticket exists to unblock. Callers that move the folder must additionally
    require `stale_child_copies` to be empty (this function does not enforce that itself, since a
    caller may want to report the anomaly without also deciding the move policy).
    """
    epic_parent = None
    epic_parent_ticket_id = None
    open_children = []
    stale_child_copies = []

    for md_file in sorted(folder.glob("TCK-*.md")):
        text = md_file.read_text(encoding="utf-8")
        fm = extract_frontmatter(text)
        ticket_id = (fm or {}).get("ticket_id") or md_file.stem
        body = _strip_frontmatter(text)
        tier = parse_body_section(body, "Tier")
        status = parse_body_section(body, "Status")

        if tier == "epic" or status == "EPIC_SCOPED":
            if epic_parent is None:
                epic_parent = str(md_file)
                epic_parent_ticket_id = ticket_id
            # A second epic-tier file in the same folder is a real data anomaly, not something
            # this status report should silently resolve by picking one — it is surfaced via
            # open_children below (since it isn't the recorded epic_parent) so a caller sees the
            # folder as not-yet-closeable rather than guessing.
            else:
                open_children.append(ticket_id)
            continue

        if (done_dir / f"{ticket_id}.md").exists():
            stale_child_copies.append(ticket_id)
        else:
            open_children.append(ticket_id)

    return {
        "folder": str(folder),
        "epic_parent": epic_parent,
        "epic_parent_ticket_id": epic_parent_ticket_id,
        "open_children": open_children,
        "stale_child_copies": stale_child_copies,
        "all_children_done": len(open_children) == 0,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Report a tickets/todos/<folder>/'s epic-tier parent and open non-epic "
        "children as one JSON object. Always exits 0 — this is a status report, not a gate."
    )
    parser.add_argument("folder", type=Path, help="Path to the tickets/todos/<folder>/ directory.")
    parser.add_argument(
        "--done-dir", type=Path, default=None,
        help="Override the tickets/done/ directory to check children against (default: "
        "<folder>/../../done, i.e. tickets/done/ as a sibling of tickets/todos/). Tests use this "
        "to avoid touching the real tickets/done/ corpus.",
    )
    args = parser.parse_args(argv)

    done_dir = args.done_dir if args.done_dir is not None else (args.folder.parent.parent / "done")
    status = get_epic_folder_status(args.folder, done_dir)
    print(json.dumps(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())

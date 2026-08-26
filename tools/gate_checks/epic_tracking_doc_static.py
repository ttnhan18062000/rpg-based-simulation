"""Deterministic backstop for implement-epic.js `folder` mode's optional tracking-doc status block.

Built for TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP: nothing in `implement-epic.js`
kept a batch's own source-of-truth roadmap doc (e.g. `docs/plans/rpg_design_roadmap/
rpg_design_roadmap.md`) in sync as child tickets completed — the staleness was only caught by a
direct user prompt, not by any gate. This module gives `folder` mode's Discover/Report phases a
real, testable mechanism instead of leaving the logic as opaque agent-prompt English.

Two functions, mirroring the Discover/Report split:

- `parse_tracking_doc_from_sequence` — called from Discover (via the orchestrator's own `bash()`)
  against an already-read `SEQUENCE.md`'s text, to find an optional `tracking_doc: <path>` line.
  Returns `None` when absent — the caller's own guard (`discovery.tracking_doc` truthy) is what
  makes the whole mechanism a true no-op when undeclared, not a call that happens to do nothing.
- `update_tracking_doc_status_block` — called from Report (also via `bash()`) once real
  done/total/remaining counts are known. Never guesses where to place a status block: it requires
  two literal HTML-comment markers (`MARKER_BEGIN`/`MARKER_END`) to already exist in the doc,
  placed manually once by whoever authors the tracking doc wherever they want the block to render.
  Replaces only the content strictly between them — never free-form prose rewriting. Reports
  `markers_missing` (not a silent no-op) when a `tracking_doc:` is declared but the doc has no
  markers yet, so the gap stays visible instead of invisible.

`epic_id` mode is explicitly out of scope (this ticket's own Out of Scope: that mode already has a
natural home — the epic ticket itself — for a status field if one is ever wanted).
"""
from __future__ import annotations

from pathlib import Path

MARKER_BEGIN = "<!-- IMPLEMENT-EPIC-STATUS:BEGIN -->"
MARKER_END = "<!-- IMPLEMENT-EPIC-STATUS:END -->"


def parse_tracking_doc_from_sequence(sequence_text: str) -> str | None:
    """Scans `SEQUENCE.md`'s own text for a `tracking_doc: <path>` line -- plain text, not YAML
    frontmatter (matches SEQUENCE.md's existing plain-markdown style; no new file, no new Discover
    read step since SEQUENCE.md is already read there). First match wins; the path is trimmed of
    surrounding whitespace. Returns None if no such line exists (the common case today).

    Confirmed safe against tools/agent-monitoring/epic_staleness_check.py's own SEQUENCE.md scan
    (CHILD_ID_PATTERN = re.compile(r"TCK-\\d{8}-[A-Z0-9-]+")): a `tracking_doc:` line contains no
    such pattern, so it can never be misparsed as a child ticket ID by that script.
    """
    for line in sequence_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("tracking_doc:"):
            path = stripped[len("tracking_doc:"):].strip()
            return path or None
    return None


def render_status_line(
    done_count: int, total_count: int, remaining_count: int, description: str, ts: str
) -> str:
    """The exact one-paragraph status text written between the markers -- a single bounded line,
    never free-form prose rewriting of the surrounding doc."""
    return (
        f"**Live progress** (auto-updated by implement-epic, last run: {ts}): "
        f"{done_count}/{total_count} tickets done, {remaining_count} remaining. "
        f"Tracking: {description}."
    )


def update_tracking_doc_status_block(
    doc_path: str | Path,
    *,
    done_count: int,
    total_count: int,
    remaining_count: int,
    description: str,
    ts: str,
) -> dict:
    """Replaces the content strictly between MARKER_BEGIN/MARKER_END in `doc_path` with a fresh
    status line -- never guesses a placement when the markers are absent.

    Returns one of:
      - {"status": "doc_not_found", "doc_path": <str>} -- doc_path does not exist, no write attempted.
      - {"status": "markers_missing", "doc_path": <str>} -- doc exists but does not contain both
        markers (or contains them in the wrong order) -- declared as tracking_doc but never given a
        status-block location; no write attempted, so the gap stays visible rather than invisible.
      - {"status": "updated", "doc_path": <str>, "line": <str>} -- the block between the markers
        was replaced with the new status line and the file was written.
    """
    resolved = Path(doc_path)
    if not resolved.exists():
        return {"status": "doc_not_found", "doc_path": str(resolved)}

    text = resolved.read_text()
    begin_idx = text.find(MARKER_BEGIN)
    end_idx = text.find(MARKER_END)
    if begin_idx == -1 or end_idx == -1 or end_idx < begin_idx:
        return {"status": "markers_missing", "doc_path": str(resolved)}

    line = render_status_line(done_count, total_count, remaining_count, description, ts)
    prefix = text[: begin_idx + len(MARKER_BEGIN)]
    suffix = text[end_idx:]
    new_text = f"{prefix}\n{line}\n{suffix}"
    resolved.write_text(new_text)
    return {"status": "updated", "doc_path": str(resolved), "line": line}

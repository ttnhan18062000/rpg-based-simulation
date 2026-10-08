#!/usr/bin/env python3
"""The retro `## Notes` convention (TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE).

Hand-authored Notes accumulate: every regeneration's addendum stayed, so RETRO-2026-W40 grew to hundreds of
lines whose older addenda (written at 18, 38 and 61 runs) contradicted the final tables. This module gives
the Notes an explicit, parsable shape instead of inferring one from prose:

    <!-- retro-note runs=N -->          an addendum written when the report covered N runs
    <!-- retro-note runs=N final -->    the current statement; kept byte-for-byte
    <!-- retro-note-collapsed runs=N --> - headline (full text: <archive>)    what an old addendum becomes

An entry runs from its marker to the next marker (or the end of the file). Text before the first marker, and
any text under a marker that does not parse, is **unmarked** and is always preserved verbatim, never collapsed.
Stamped non-final entries followed by a later `final` entry are collapsed to one history line, and their full
text is first appended to an archive file and read back; if that fails nothing is collapsed. A generated status
line right under `## Notes` says when the final note is older than the data. Regeneration is idempotent.
"""

from __future__ import annotations

import re
from pathlib import Path

MARKER_RE = re.compile(r"^<!--\s*retro-note\s+runs=(\d+)(\s+final)?\s*-->\s*$")
COLLAPSED_PREFIX = "<!-- retro-note-collapsed runs="
STATUS_PREFIX = "<!-- retro-notes-status -->"
HEADLINE_CAP = 120


def _segments(body: list) -> list:
    """[('text', lines) | ('entry', runs, final, lines) | ('collapsed', [line])] covering `body` exactly."""
    segs, current = [], ("text", [])
    for line in body:
        m = MARKER_RE.match(line)
        if m:
            segs.append(current)
            current = ("entry", int(m.group(1)), bool(m.group(2)), [line])
        elif line.startswith(COLLAPSED_PREFIX):
            segs.append(current)
            segs.append(("collapsed", [line]))
            current = ("text", [])
        else:
            current[-1].append(line)
    segs.append(current)
    return [s for s in segs if s[-1]]


def _strip_trailing_blanks(lines: list) -> tuple:
    n = 0
    while lines and not lines[-1].strip():
        lines = lines[:-1]
        n += 1
    return lines, n


def _headline(entry_lines: list) -> str:
    for line in entry_lines[1:]:
        text = re.sub(r"^[\s>*#_-]+|\*\*|`", "", line).strip()
        if text:
            return text if len(text) <= HEADLINE_CAP else text[: HEADLINE_CAP - 1].rstrip() + "…"
    return "(empty entry)"


def _split_status(lines: list) -> list:
    """Drop a previously generated status line (and the one blank line after it)."""
    out, skip_blank = [], False
    for line in lines:
        if line.startswith(STATUS_PREFIX):
            skip_blank = True
            continue
        if skip_blank and not line.strip():
            skip_blank = False
            continue
        skip_blank = False
        out.append(line)
    return out


def _archive(archive_path: Path, label: str, entries: list) -> None:
    """Append each entry's full text (skipping any already there), then read the file back and verify."""
    existing = archive_path.read_text(encoding="utf-8") if archive_path.exists() else ""
    addition = ""
    for runs, text in entries:
        if text in existing + addition:
            continue
        addition += f"\n## {label}: note stamped at {runs} runs\n\n{text}\n"
    if addition:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.write_text(existing + addition, encoding="utf-8")
    written = archive_path.read_text(encoding="utf-8") if archive_path.exists() else ""
    for _runs, text in entries:
        if text not in written:
            raise OSError(f"archive {archive_path} did not read back with the collapsed text; nothing was collapsed")


def process_notes(notes_text: str, run_count, archive_path: Path, label: str, archive_ref: str) -> tuple:
    """(new notes text, [info lines]). `notes_text` runs from the `## Notes` heading to the end of file."""
    had_trailing_newline = notes_text.endswith("\n")
    lines = notes_text.split("\n")
    if had_trailing_newline:
        lines = lines[:-1]
    heading, body = lines[0], _split_status(lines[1:])
    segs = _segments(body)
    entries = [s for s in segs if s[0] == "entry"]
    finals = [s for s in entries if s[2]]
    info = []

    to_collapse = []
    if finals:
        last_final_pos = max(i for i, seg in enumerate(segs) if seg[0] == "entry" and seg[2])
        to_collapse = [seg for i, seg in enumerate(segs) if seg[0] == "entry" and i < last_final_pos]
    collapsing = [(s[1], "\n".join(_strip_trailing_blanks(s[3])[0])) for s in to_collapse]
    if collapsing:
        try:
            _archive(archive_path, label, collapsing)
        except OSError as exc:
            info.append(f"WARNING: notes not collapsed: {exc}")
            to_collapse = []

    out = []
    for seg in segs:
        if any(seg is c for c in to_collapse):
            kept, blanks = _strip_trailing_blanks(seg[3])
            out.append(f"{COLLAPSED_PREFIX}{seg[1]} --> - {_headline(kept)} (full text: {archive_ref})")
            out.extend([""] * blanks)
            info.append(f"collapsed the note stamped at {seg[1]} runs")
        else:
            out.extend(seg[-1])

    stamped = [s[1] for s in segs if s[0] == "entry"]
    reference = finals[-1][1] if finals else (max(stamped) if stamped else None)
    status = []
    if run_count is not None and reference is not None and run_count > reference:
        kind = "final note" if finals else "newest stamped note"
        status = [f"{STATUS_PREFIX}_Notes may be stale: the {kind} was written at {reference} runs; this report covers "
                  f"{run_count} runs. Refresh it or add a new `final` note._", ""]
        info.append(f"final note older than the data ({reference} vs {run_count} runs)")

    if status:
        result = [heading, ""] + status + (out[1:] if out[:1] == [""] else out)
    else:
        result = [heading] + out
    text = "\n".join(result)
    return (text + "\n" if had_trailing_newline else text), info

#!/usr/bin/env python3
"""List the real `bash(` call sites in a `.claude/workflows/*.js` script (TCK-20260930-IMPLEMENT-
TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION).

`grep -c 'bash('` over-counts: it also matches comments that talk about `bash()`. For
implement-ticket.js that is 50 matches against 38 real call sites. A site is a line whose code part
(before any `//` comment, outside comment-only lines) contains `bash(`. Read-only; used by the
classification test to keep the stored classification table in step with the file.

Usage: python3 tools/workflow_bash_sites.py .claude/workflows/implement-ticket.js
"""
import sys
from pathlib import Path


def find_bash_call_sites(path) -> list:
    """Return [(line_number, stripped_line)] for each line with a code-position `bash(`."""
    sites = []
    in_block_comment = False
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/*"):
            in_block_comment = "*/" not in stripped
            continue
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        code = line.split("//", 1)[0] if "//" in line and "bash(" not in line.split("//", 1)[1] else line
        if "bash(" in code:
            sites.append((number, stripped))
    return sites


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: workflow_bash_sites.py <script.js>")
        return 2
    sites = find_bash_call_sites(argv[0])
    for number, text in sites:
        print(f"{number}: {text[:140]}")
    print(f"{len(sites)} bash( call site(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

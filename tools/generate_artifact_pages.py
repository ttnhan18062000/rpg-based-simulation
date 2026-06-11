#!/usr/bin/env python3
"""
Generate stored_artifacts/{ticket_id}/index.md landing pages for Docusaurus.

For each subdirectory in stored_artifacts/ that contains at least one of:
  investigation.md, plan.md, test_plan.md
— writes an index.md with frontmatter and links to the available artifact files.

Idempotent: skips a directory if index.md already exists and is newer than all
artifact files present.

Usage:
    python3 tools/generate_artifact_pages.py [--dry-run]
"""

import argparse
import os
import sys
from pathlib import Path

ARTIFACT_FILES = ["investigation.md", "plan.md", "test_plan.md"]

REPO_ROOT = Path(__file__).parent.parent
STORED_ARTIFACTS = REPO_ROOT / "stored_artifacts"

INDEX_TEMPLATE = """\
---
title: "{ticket_id}"
description: "Artifact landing page for {ticket_id}"
artifact_type: index
layer: misc
tags: []
---

# {ticket_id}

Artifact files for this ticket:

{links}
"""


def build_index(ticket_id: str, present_files: list[str]) -> str:
    links = "\n".join(f"- [{f}](./{f})" for f in present_files)
    return INDEX_TEMPLATE.format(ticket_id=ticket_id, links=links)


def should_regenerate(index_path: Path, artifact_paths: list[Path]) -> bool:
    """Return True if index.md is absent or older than any artifact file."""
    if not index_path.exists():
        return True
    index_mtime = index_path.stat().st_mtime
    for ap in artifact_paths:
        if ap.exists() and ap.stat().st_mtime > index_mtime:
            return True
    return False


def run(dry_run: bool = False) -> int:
    if not STORED_ARTIFACTS.exists():
        print(f"ERROR: stored_artifacts/ not found at {STORED_ARTIFACTS}", file=sys.stderr)
        return 1

    generated = 0
    skipped = 0

    for entry in sorted(STORED_ARTIFACTS.iterdir()):
        if not entry.is_dir():
            continue

        ticket_id = entry.name
        present = [f for f in ARTIFACT_FILES if (entry / f).exists()]

        if not present:
            skipped += 1
            continue

        index_path = entry / "index.md"
        artifact_paths = [entry / f for f in present]

        if not should_regenerate(index_path, artifact_paths):
            skipped += 1
            continue

        content = build_index(ticket_id, present)

        if dry_run:
            try:
                display = index_path.relative_to(REPO_ROOT)
            except ValueError:
                display = index_path
            print(f"[dry-run] Would write {display}")
        else:
            index_path.write_text(content, encoding="utf-8")

        generated += 1

    label = "Would generate" if dry_run else "Generated/updated"
    print(f"{label} {generated} index pages ({skipped} skipped).")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print what would be written without writing")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()

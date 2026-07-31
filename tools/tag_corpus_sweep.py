#!/usr/bin/env python3
"""
Report-only tag/category violation sweep across the full ticket/artifact corpus.

Built for TCK-20260720-TAG-CORPUS-REPAIR-SWEEP. `tools/tag_report.py`'s `main()` only ever
reports on `tickets/done/`, and only on tickets whose `ticket_id` embeds a date on or after the
tag taxonomy's effective date (`TAG_TAXONOMY_EFFECTIVE_DATE`, 2026-07-04) — enforcement there is
deliberately forward-only, per the taxonomy's own "no backfill of history" decision. That leaves
the entire pre-cutoff corpus, plus `tickets/inprogress/`, `tickets/todos/`, and
`stored_artifacts/`, never checked by anything.

This module is a separate, report-only sweep over all four corpus roots with no date cutoff at
all — it walks every file `tag_report.py`'s narrower pass would skip as "too old," and flags every
tag issue (`unregistered`, `invalid_category`, `non_canonical_form`) it finds. It emits
`(file, tag, issue)` rows; deciding what to do with a finding (retag, re-register, etc.) is left
to a human or a follow-up ticket — there is no `--fix` flag, and this module never writes to any
file under `tickets/` or `stored_artifacts/`.

The corpus-walk and per-file classification live in `tools/tag_report.py`
(`collect_sweep_files`, `tag_issues`, `sweep_file_rows`) so they can reuse `extract_frontmatter()`
and the `SEQUENCE.md`-skip convention already established there. This module is only the
orchestration and CLI layer — it does not import, call, or modify `tag_report.py`'s own `main()`,
`print_report()`, `build_json_report()`, or CLI wiring, which stay scoped to their original
`tickets/done/`-only report.

Usage:
  python3 tools/tag_corpus_sweep.py
  python3 tools/tag_corpus_sweep.py --root . --json reports/tag_corpus_sweep.json
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(_TOOLS_DIR))
from tag_report import collect_sweep_files, sweep_file_rows  # noqa: E402
from tag_registry import category_values, load_registry  # noqa: E402

# ---------------------------------------------------------------------------
# Sweep orchestration
# ---------------------------------------------------------------------------


def run_sweep(root: Path) -> dict:
    """Run the full-corpus sweep and return its result as a plain dict.

    Reads `registries/tag_registry.jsonl` and `registries/tag_category_registry.jsonl` (via
    `load_registry`/`category_values`), walks all four corpus roots (`collect_sweep_files`), and
    computes violation rows for every file (`sweep_file_rows`) — no filesystem writes anywhere in
    this call.
    """
    registry = load_registry(root)
    valid_categories = category_values(root)
    relative_paths, skip_reasons, _skipped_paths = collect_sweep_files(root)

    rows = []
    for rel_path in relative_paths:
        text = (root / rel_path).read_text(encoding="utf-8")
        rows.extend(sweep_file_rows(rel_path, text, registry, valid_categories))

    scanned_files = len(relative_paths) + sum(skip_reasons.values())
    issue_counts = Counter(row["issue"] for row in rows)

    return {
        "rows": rows,
        "scanned_files": scanned_files,
        "skipped": dict(sorted(skip_reasons.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def print_report(result: dict) -> None:
    scanned = result["scanned_files"]
    skipped_total = sum(result["skipped"].values())
    print(f"Tag corpus sweep: {scanned} file(s) scanned across all 4 corpus roots")
    print(f"  skipped: {skipped_total}")
    for reason, count in result["skipped"].items():
        print(f"    {reason}: {count}")

    print(f"\n{len(result['rows'])} violation row(s) found:")
    for issue, count in result["issue_counts"].items():
        print(f"  {issue}: {count}")

    print(f"\n{'FILE':<70} {'TAG':<28} ISSUE")
    for row in result["rows"]:
        print(f"  {row['file']}\t{row['tag']}\t{row['issue']}")


def build_json_report(result: dict) -> dict:
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scanned_files": result["scanned_files"],
        "skipped": result["skipped"],
        "issue_counts": result["issue_counts"],
        "rows": result["rows"],
    }


# ---------------------------------------------------------------------------
# CLI (report-only — no --fix, no write-capable flag beyond the explicit --json output path)
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report-only tag/category violation sweep across the full ticket/artifact "
        "corpus (no date cutoff, no --fix, no writes)."
    )
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--json", default=None, help="Optional path to write a structured JSON report")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = run_sweep(root)

    print_report(result)

    if args.json:
        json_path = Path(args.json)
        if not json_path.is_absolute():
            json_path = root / json_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        report = build_json_report(result)
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote JSON report to {json_path}")


if __name__ == "__main__":
    main()

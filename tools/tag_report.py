#!/usr/bin/env python3
"""
Export a tag-usage report over completed tickets (tickets/done/).

Built for TCK-20260706-TAG-REPORT-TOOL, updated for TCK-20260706-TAG-REGISTRY-DATA. Counts how many
times each `tags` value appears across `tickets/done/` (recursing into the small number of
`tickets/done/{folder}/` subfolders), skipping tickets that predate the tag taxonomy or carry no
tags at all — so the count reflects the current controlled vocabulary
(docs/guidelines/tag_taxonomy.md), not the ~1273-distinct-tag pre-taxonomy corpus that document
describes.

Tag categorization is now a direct lookup against `registries/tag_registry.jsonl` (via
`tools/tag_registry.py`) rather than a heuristic guess against a handful of hardcoded example
tags — the registry is the authoritative source for "which category is this tag," so a tag is
only ever "unclassified" here if it somehow isn't registered (which `validate_frontmatter.py`'s
hard-allowlist check should prevent from happening for any ticket created after the registry
existed).

Usage:
  python3 tools/tag_report.py
  python3 tools/tag_report.py --root . --json reports/tag_report.json
  python3 tools/tag_report.py --list-skipped
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Reuse frontmatter parsing from validate_frontmatter.py, and tag rules/registry lookup from
# tag_registry.py (same package, same import pattern as tools/generate_registry.py).
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(_TOOLS_DIR))
from validate_frontmatter import (  # noqa: E402
    TAG_TAXONOMY_EFFECTIVE_DATE,
    _ticket_id_effective_date,
    extract_frontmatter,
)
from tag_registry import (  # noqa: E402,F401
    canonical_form_violation,
    category_values,
    is_phase_milestone_tag,
    is_tag_registered,
    load_registry,
)

# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------


def categorize_tag(tag: str, registry: dict) -> str:
    """Look up `tag`'s category from the registry.

    Canonical `phase-N` tags are classified as "phase-milestone" without a registry lookup — see
    tag_registry.py's module docstring for why phase tags aren't individually registered.
    Returns "unclassified" if the tag is registered nowhere and isn't a phase tag — should be rare
    for any ticket created after the registry existed, since validate_frontmatter.py's hard
    allowlist rejects unregistered tags at commit time.
    """
    if is_phase_milestone_tag(tag):
        return "phase-milestone"
    entry = registry.get(tag)
    if entry:
        return entry["category"]
    return "unclassified"


# ---------------------------------------------------------------------------
# Sweep violation classification (TCK-20260720-TAG-CORPUS-REPAIR-SWEEP)
#
# A different question from categorize_tag() above: categorize_tag() answers "what display
# category does this tag have," tag_issues() answers "which rule(s) does this tag violate."
# Every check here calls straight into tag_registry.py's existing functions — no rule is
# re-derived.
# ---------------------------------------------------------------------------


def tag_issues(tag: str, registry: dict, valid_categories: frozenset) -> list[str]:
    """Return the violation issue strings for `tag`: zero, one, two, or all three of
    'unregistered', 'invalid_category', 'non_canonical_form' may apply.

    'unregistered' and 'invalid_category' are mutually exclusive by construction:
    'invalid_category' only fires for a tag with a literal registry entry (`tag in registry`), a
    strictly narrower condition than `is_tag_registered` (which also allows phase-N tags that have
    no registry entry and thus no category to check). 'non_canonical_form' is independent of both.
    """
    issues = []
    if not is_tag_registered(tag, registry):
        issues.append("unregistered")
    elif tag in registry:
        recorded_category = registry[tag].get("category")  # defensive: missing category -> invalid
        if recorded_category not in valid_categories:
            issues.append("invalid_category")
    if canonical_form_violation(tag) is not None:
        issues.append("non_canonical_form")
    return issues


def sweep_file_rows(rel_path: str, text: str, registry: dict, valid_categories: frozenset) -> list[dict]:
    """Return one `{"file", "tag", "issue"}` row per (tag, issue) violation found in `text`'s
    frontmatter `tags:` list — zero rows, never a crash, for no-frontmatter, no-tags-key, or
    unparseable-frontmatter input. Deliberately does not read `ticket_id` or apply the
    TAG_TAXONOMY_EFFECTIVE_DATE cutoff `collect_completed_tickets()` applies — this sweep exists
    specifically to cover the pre-cutoff corpus that check skips.
    """
    try:
        fm = extract_frontmatter(text)
    except ValueError:
        return []

    if fm is None:
        return []

    tags = fm.get("tags")
    if not tags or not isinstance(tags, list):
        return []

    rows = []
    for tag in tags:
        for issue in tag_issues(tag, registry, valid_categories):
            rows.append({"file": rel_path, "tag": tag, "issue": issue})
    return rows


# ---------------------------------------------------------------------------
# Ticket collection
# ---------------------------------------------------------------------------


def collect_completed_tickets(root: Path):
    """Walk tickets/done/ recursively for ticket markdown files.

    Returns (included, skip_reasons) where:
      - included is a list of (ticket_id, tags, relative_path) tuples for tickets that pass all
        skip rules (parseable frontmatter, ticket_id date on/after the taxonomy cutoff, non-empty
        tags).
      - skip_reasons is a Counter keyed by skip reason.
    """
    done_dir = root / "tickets" / "done"
    included = []
    skip_reasons: Counter = Counter()
    skipped_paths = defaultdict(list)

    if not done_dir.is_dir():
        return included, skip_reasons, skipped_paths

    for md_file in sorted(done_dir.rglob("*.md")):
        rel_path = str(md_file.relative_to(root))

        if md_file.name == "SEQUENCE.md":
            skip_reasons["sequence_index_file"] += 1
            skipped_paths["sequence_index_file"].append(rel_path)
            continue

        text = md_file.read_text(encoding="utf-8")
        try:
            fm = extract_frontmatter(text)
        except ValueError:
            skip_reasons["unparseable_frontmatter"] += 1
            skipped_paths["unparseable_frontmatter"].append(rel_path)
            continue

        if fm is None:
            skip_reasons["no_frontmatter_legacy_format"] += 1
            skipped_paths["no_frontmatter_legacy_format"].append(rel_path)
            continue

        ticket_id = fm.get("ticket_id") or md_file.stem
        embedded_date = _ticket_id_effective_date(ticket_id)
        if embedded_date is None or embedded_date < TAG_TAXONOMY_EFFECTIVE_DATE:
            skip_reasons["pre_taxonomy_or_legacy_ticket_id"] += 1
            skipped_paths["pre_taxonomy_or_legacy_ticket_id"].append(rel_path)
            continue

        tags = fm.get("tags")
        if not tags or not isinstance(tags, list):
            skip_reasons["no_tags"] += 1
            skipped_paths["no_tags"].append(rel_path)
            continue

        included.append((ticket_id, tags, rel_path))

    return included, skip_reasons, skipped_paths


def collect_sweep_files(root: Path):
    """Walk all four corpus roots (`tickets/done`, `tickets/inprogress`, `tickets/todos`,
    `stored_artifacts`) recursively for markdown files, for the full-corpus repair sweep
    (TCK-20260720-TAG-CORPUS-REPAIR-SWEEP).

    Unlike `collect_completed_tickets()`, this applies only the `sequence_index_file` skip rule —
    no frontmatter parsing, no tags check, and critically no `TAG_TAXONOMY_EFFECTIVE_DATE` date-
    cutoff skip happens here; those checks are the sweep's whole point of existing, and belong to
    `sweep_file_rows()` instead, applied unconditionally to every file this function returns.

    Returns (relative_paths, skip_reasons, skipped_paths) — `relative_paths` is the sorted list of
    files to sweep, `skip_reasons` is a Counter keyed by skip reason (currently only
    `sequence_index_file`), and `skipped_paths` maps each reason to its list of relative paths.
    """
    roots = [
        root / "tickets" / "done",
        root / "tickets" / "inprogress",
        root / "tickets" / "todos",
        root / "stored_artifacts",
    ]
    skip_reasons: Counter = Counter()
    skipped_paths = defaultdict(list)

    all_files = []
    for corpus_root in roots:
        if not corpus_root.is_dir():
            continue
        all_files.extend(corpus_root.rglob("*.md"))

    relative_paths = []
    for md_file in sorted(all_files):
        rel_path = str(md_file.relative_to(root))

        if md_file.name == "SEQUENCE.md":
            skip_reasons["sequence_index_file"] += 1
            skipped_paths["sequence_index_file"].append(rel_path)
            continue

        relative_paths.append(rel_path)

    return relative_paths, skip_reasons, skipped_paths


# ---------------------------------------------------------------------------
# Report building
# ---------------------------------------------------------------------------


def build_tag_rows(included, registry: dict):
    """Return (rows, non_canonical_hits) from a list of (ticket_id, tags, path) tuples.

    rows is sorted by count desc, then tag asc. Each row carries the tag, its count, its
    registry-derived category, and the sorted list of ticket IDs that use it.
    """
    tag_counter: Counter = Counter()
    tag_tickets = defaultdict(list)
    non_canonical_hits = []

    for ticket_id, tags, _path in included:
        for tag in tags:
            tag_counter[tag] += 1
            tag_tickets[tag].append(ticket_id)
            if canonical_form_violation(tag) is not None:
                non_canonical_hits.append({"ticket_id": ticket_id, "tag": tag})

    rows = [
        {
            "tag": tag,
            "count": count,
            "category": categorize_tag(tag, registry),
            "tickets": sorted(set(tag_tickets[tag])),
        }
        for tag, count in sorted(tag_counter.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    return rows, non_canonical_hits


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def print_report(included, skip_reasons, rows, non_canonical_hits, show_tickets: bool) -> None:
    scanned = len(included) + sum(skip_reasons.values())
    print(f"Tag report: {scanned} ticket file(s) scanned under tickets/done/")
    print(f"  included (tagged, post-taxonomy): {len(included)}")
    if skip_reasons:
        print("  skipped:")
        for reason, count in sorted(skip_reasons.items()):
            print(f"    {reason}: {count}")
    else:
        print("  skipped: 0")

    print(f"\n{len(rows)} unique tag(s) across {len(included)} included ticket(s):\n")
    print(f"  {'TAG':<28} {'COUNT':>5}  CATEGORY")
    for row in rows:
        print(f"  {row['tag']:<28} {row['count']:>5}  {row['category']}")
        if show_tickets:
            for tid in row["tickets"]:
                print(f"      - {tid}")

    if non_canonical_hits:
        print(f"\nWARNING: {len(non_canonical_hits)} non-canonical tag usage(s) found "
              f"among included (post-taxonomy) tickets:")
        for hit in non_canonical_hits:
            print(f"    {hit['ticket_id']}: {hit['tag']!r}")


def build_json_report(included, skip_reasons, rows, non_canonical_hits) -> dict:
    scanned = len(included) + sum(skip_reasons.values())
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scanned_files": scanned,
        "included_tickets": len(included),
        "skipped": dict(sorted(skip_reasons.items())),
        "tags": rows,
        "non_canonical_hits": non_canonical_hits,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a tag-usage report over completed tickets (tickets/done/)."
    )
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--json", default=None, help="Optional path to write a structured JSON report")
    parser.add_argument(
        "--show-tickets",
        action="store_true",
        help="Also print the list of ticket IDs using each tag in the stdout table",
    )
    parser.add_argument(
        "--list-skipped",
        action="store_true",
        help="Print the file paths skipped under each skip reason",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    registry = load_registry(root)
    included, skip_reasons, skipped_paths = collect_completed_tickets(root)
    rows, non_canonical_hits = build_tag_rows(included, registry)

    print_report(included, skip_reasons, rows, non_canonical_hits, args.show_tickets)

    if args.list_skipped and skipped_paths:
        print("\nSkipped files by reason:")
        for reason, paths in sorted(skipped_paths.items()):
            print(f"  {reason}:")
            for p in paths:
                print(f"    {p}")

    if args.json:
        json_path = Path(args.json)
        if not json_path.is_absolute():
            json_path = root / json_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        report = build_json_report(included, skip_reasons, rows, non_canonical_hits)
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote JSON report to {json_path}")


if __name__ == "__main__":
    main()

"""
catalog_list.py — List available catalog IDs by type.

Usage:
    python3 tools/catalog_list.py
    python3 tools/catalog_list.py --types biomes ecologies factions
    make catalog-list

Reads data/content/ and prints all registered catalog IDs grouped by type.
No world assembly is required — this reads the static catalog only.
"""
from __future__ import annotations

import argparse
import sys
from typing import List

# Ensure project root is on the path when run as a script.
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.content.repository import CatalogRepository

# Ordered list of (display_label, type_key) pairs shown by default.
DEFAULT_TYPES: List[tuple[str, str]] = [
    ("biomes", "biome"),
    ("ecologies", "ecology"),
    ("populations", "population"),
    ("factions", "faction"),
    ("regions", "region"),
]

# All supported type keys (superset of DEFAULT_TYPES).
ALL_TYPES: List[tuple[str, str]] = DEFAULT_TYPES + [
    ("terrain", "terrain"),
    ("buildings", "building"),
    ("resources", "resource"),
    ("items", "item"),
    ("races", "race"),
    ("roles", "role"),
    ("traits", "trait"),
    ("materials", "material"),
    ("recipes", "recipe"),
    ("services", "service_profile"),
    ("perspectives", "perspective"),
]

ALL_TYPE_KEYS = {label: key for label, key in ALL_TYPES}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List registered catalog IDs by type (reads data/content/, no assembly needed)."
    )
    parser.add_argument(
        "--types",
        nargs="+",
        metavar="TYPE",
        default=None,
        help=(
            "Catalog types to display. "
            f"Defaults: {', '.join(label for label, _ in DEFAULT_TYPES)}. "
            f"All available: {', '.join(label for label, _ in ALL_TYPES)}"
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="show_all",
        help="Show all catalog types, not just the author-relevant defaults.",
    )
    args = parser.parse_args(argv)

    # Determine which types to show.
    if args.show_all:
        types_to_show = ALL_TYPES
    elif args.types:
        types_to_show = []
        for label in args.types:
            key = ALL_TYPE_KEYS.get(label)
            if key is None:
                print(
                    f"Unknown type: {label!r}. "
                    f"Available: {', '.join(ALL_TYPE_KEYS.keys())}",
                    file=sys.stderr,
                )
                return 1
            types_to_show.append((label, key))
    else:
        types_to_show = DEFAULT_TYPES

    # Load catalog.
    repo = CatalogRepository()
    report = repo.load_all(strict=False)

    if report.missing_required_files:
        print(
            f"Warning: missing required catalog files: {report.missing_required_files}",
            file=sys.stderr,
        )

    # Print results.
    print()
    any_ids = False
    for label, type_key in types_to_show:
        ids = sorted(repo.get_all_ids_by_type(type_key))
        print(f"=== {label} ({len(ids)}) ===")
        if ids:
            any_ids = True
            for item_id in ids:
                print(f"  {item_id}")
        else:
            print("  (none loaded)")
        print()

    if not any_ids:
        print(
            "No catalog IDs found. Verify data/content/ is present and populated.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

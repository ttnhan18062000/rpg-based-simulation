"""Check ``docs/performance/gate_conformance.yaml`` against the live perf-check call sites (TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE).

Every ``assert_perf_threshold`` / ``perf_check`` call site found by :mod:`tools.perf.perf_threshold_inventory` must have a map entry that names a
clause ID from the clause inventory or the literal ``none``. The problems reported, each naming the file and function:

* **unmapped**: a call site with no entry;
* **stale**: an entry whose site no longer exists;
* **unknown clause**: a ``clause`` or ``related`` ID that is not a row of ``performance_clause_inventory.md``;
* **duplicate**: two entries for one site;
* **missing path**: an ``other_checks`` path that does not exist.

A site key is ``file::function#N``: N is the 1-based position of the call among the helper calls of that function in source order. It carries no
line number, so moving code does not break the map; adding or removing a check in the same function does (the ordinals move), which is the point.

    python3 -m tools.perf.gate_conformance        # exit 1 when the map and the call sites disagree
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

import yaml

from tools.perf.perf_threshold_inventory import build_report

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = "docs/performance/gate_conformance.yaml"
INVENTORY_PATH = "docs/performance/performance_clause_inventory.md"
NONE = "none"
_CLAUSE_ROW = re.compile(r"^\| ([A-Z]{2,4}-\d+) \|", re.MULTILINE)


def site_keys(report: Mapping[str, Any]) -> List[str]:
    """The ``file::function#N`` key of every call site in ``report``, in report order."""
    seen: Counter = Counter()
    keys = []
    for row in report["call_sites"]:
        base = (row["file"], row["function"])
        seen[base] += 1
        keys.append(f"{row['file']}::{row['function']}#{seen[base]}")
    return keys


def clause_ids(inventory_text: str) -> Set[str]:
    """Every clause ID that heads a row of the clause inventory."""
    return set(_CLAUSE_ROW.findall(inventory_text))


def _readable(key: str) -> str:
    file, _, rest = key.partition("::")
    function = rest.rsplit("#", 1)[0]
    return f"{file} in {function}"


def _clause_problems(entry: Mapping[str, Any], label: str, known: Set[str]) -> List[str]:
    problems = []
    clauses = entry.get("clause")
    for clause in clauses if isinstance(clauses, list) else [clauses]:
        if clause != NONE and clause not in known:
            problems.append(f"unknown clause {clause!r} for {label}: not a row of {INVENTORY_PATH} (use {NONE!r} when the check enforces none)")
    for related in entry.get("related") or []:
        if related not in known:
            problems.append(f"unknown related clause {related!r} for {label}")
    return problems


def problems(report: Mapping[str, Any], conformance: Mapping[str, Any], known: Set[str], root: Optional[Path] = None) -> List[str]:
    """Every disagreement between the call sites in ``report`` and the ``conformance`` map. Empty means they agree."""
    found: List[str] = []
    live = site_keys(report)
    mapped: Dict[str, Mapping[str, Any]] = {}
    for entry in conformance.get("sites") or []:
        key = entry.get("site", "")
        if key in mapped:
            found.append(f"duplicate entry for {_readable(key)} ({key})")
        mapped[key] = entry
        found.extend(_clause_problems(entry, f"{_readable(key)} ({key})", known))
    found.extend(f"unmapped call site: {_readable(key)} ({key}) has no entry in {MAP_PATH}" for key in live if key not in mapped)
    found.extend(f"stale entry: {_readable(key)} ({key}) names a call site that no longer exists" for key in mapped if key not in set(live))
    for entry in conformance.get("other_checks") or []:
        found.extend(_clause_problems(entry, f"other check {entry.get('path')!r}", known))
        if root is not None and not (root / str(entry.get("path", ""))).exists():
            found.append(f"missing path: other check {entry.get('path')!r} does not exist")
    return found


def check_repo(root: Path = REPO_ROOT) -> List[str]:
    """:func:`problems` for the working tree at ``root``."""
    conformance = yaml.safe_load((root / MAP_PATH).read_text(encoding="utf-8")) or {}
    known = clause_ids((root / INVENTORY_PATH).read_text(encoding="utf-8"))
    return problems(build_report(root), conformance, known, root)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Print every problem; exit 1 when there is one."""
    parser = argparse.ArgumentParser(description="Check docs/performance/gate_conformance.yaml against the perf-check call sites.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root to check (default: this checkout)")
    args = parser.parse_args(argv)
    found = check_repo(args.root.resolve())
    for line in found:
        print(f"GATE-CONFORMANCE: {line}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Rule ID corpus scanner for the Simulation Semantic Control Plane
(TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION).

Rule IDs live only as Markdown headings across `docs/world_rules/**/*.md`
(`## <ID> -- <one-line restatement>`, e.g. `## TERR-01 -- Territorial claim, de facto control,
...`, `docs/world_rules/places-culture/territory-control.md:27`). There is no separate
machine-readable Rule index -- the corpus itself is the source of truth, so `rule_id` resolution
for the new edge/classification schemas must scan it live rather than trust a hardcoded or cached
list.

`docs/world_rules/review-exports/` is excluded: those files are prose *about* Rules (batch
reports, candidate findings) using a different heading vocabulary ("## Rule Inventory",
"## Repository Findings", ...) and must never contribute a false Rule ID match or a double-count
of a real one.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Set

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_WORLD_RULES_PATH = _REPO_ROOT / "docs" / "world_rules"

_RULE_ID_HEADING_RE = re.compile(r"^## ([A-Z]{2,8}-[0-9]{2})\b")


def scan_rule_ids(base_path: Path = DEFAULT_WORLD_RULES_PATH) -> Set[str]:
    """Every Rule ID declared as a `## <ID> -- ...` heading under `base_path`, excluding any path
    with a `review-exports` directory component. Confirmed by direct sweep (investigation.md,
    TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION) to match exactly 172 unique ids across the real
    corpus today."""
    ids: Set[str] = set()
    for path in base_path.rglob("*.md"):
        if "review-exports" in path.parts:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _RULE_ID_HEADING_RE.match(line)
            if match:
                ids.add(match.group(1))
    return ids

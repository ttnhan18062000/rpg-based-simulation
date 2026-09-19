#!/usr/bin/env python3
"""
Report-only scan for status vocabulary embedded in hand-written description/label prose across
`rpg_feature_atlas.html`, `simulation_capabilities.html`, and `rpg_simulation_wiring_map.html`'s
own Entity Operating Loop node labels.

TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION. The rule this enforces: prose describes *what a
mechanism does*; it never states *whether it currently works* — that's the registry's job, derived
and checked. What went stale on `motivation_doctrine` (this epic, 2026-09-16) was never the
description of what doctrine-based route bias did — that fairly described the code. It was the
sentence "confirmed live via the always-on Adventure route scoring path", a status claim, written
in prose, in three separately hand-authored documents, checked by nothing, that all three writers
got wrong the same way once the code was deleted.

Scans only the genuinely duplicated surface (free-text `desc` fields in the atlas/capabilities
JSON, and the wiring map's own node label strings) -- never the atlas's `badges`/capabilities'
`tier`/`tierLabel` fields, which ARE the registry's own intentional, already-checked status surface
(`mechanism_atlas_regenerate.py`/`mechanism_capabilities_regenerate.py` keep those converged with
`mechanisms.yaml` directly; duplicating that check here would be redundant, not additive).

Report-only, same convention as every other detector in this corpus
(`mechanism_registry_graphify_check.py`, `mechanism_registry_completeness_check.py`) -- never fails
the build by itself. A detector that fires on legitimate prose teaches people to ignore it
(`docs/plans/mechanism_claims_as_tests_initiative.md` §4.1's own report-first rule); this scan is
meant to surface candidates for human review, not to gate anything.

Usage:
  python3 tools/mechanism_registry/mechanism_status_language_check.py
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ATLAS_PATH = _REPO_ROOT / "docs" / "brainstorm" / "rpg_feature_atlas.html"
_CAPABILITIES_PATH = _REPO_ROOT / "docs" / "brainstorm" / "simulation_capabilities.html"
_WIRING_MAP_PATH = _REPO_ROOT / "docs" / "brainstorm" / "rpg_simulation_wiring_map.html"

_ATLAS_BLOCK_RE = re.compile(
    r'<script type="application/json" id="card-sections-data">\n(.*?)\n</script>', re.S
)
_CAPABILITIES_BLOCK_RE = re.compile(
    r'<script type="application/json" id="sections-data">\n(.*?)\n</script>', re.S
)
# Entity Operating Loop diagram node labels only (scope item 3's own target) -- e.g.
# `TRM["Trauma<br/>Wound -> Scar"]`. Deliberately does not match the wiring map's other two
# diagrams (Layer Model, Entity Lifecycle Arc), same scoping precedent as
# `mechanism_wiring_map_classdef.py`'s own docstring.
_NODE_LABEL_RE = re.compile(r'(\w+)\["([^"]*)"\]')

# Status vocabulary -- whether a mechanism currently works, not what it does. Seeded from the
# ticket's own known examples plus a real corpus scan (2026-09-19) that confirmed each of these
# actually occurs, not guessed in advance (this ticket's own Assumptions/Open Questions note).
STATUS_PHRASES: List[str] = [
    "confirmed live",
    "still confirmed",
    "always-on",
    "always on",
    "never fires",
    "never actually triggers",
    "never once actually completed",
    "now works",
    "gated off",
    "no longer",
    "actually fires",
    "actually triggers",
    "actually completed",
    "no write path",
    "zero callers",
    "currently",
]


@dataclass(frozen=True)
class Hit:
    artifact: str
    location: str
    phrase: str
    snippet: str


def _find_phrases(text: str) -> List[str]:
    lowered = text.lower()
    return [p for p in STATUS_PHRASES if p in lowered]


def _snippet(text: str, phrase: str, radius: int = 40) -> str:
    idx = text.lower().find(phrase.lower())
    start = max(0, idx - radius)
    end = min(len(text), idx + len(phrase) + radius)
    return text[start:end].replace("\n", " ")


def scan_atlas(html: str) -> List[Hit]:
    m = _ATLAS_BLOCK_RE.search(html)
    if not m:
        return []
    data = json.loads(m.group(1))
    hits: List[Hit] = []
    for section_id, cards in data.items():
        for i, card in enumerate(cards):
            desc = card.get("desc", "")
            for phrase in _find_phrases(desc):
                hits.append(Hit(
                    artifact="atlas", location=f"{section_id}#{i} ({card.get('title', '?')})",
                    phrase=phrase, snippet=_snippet(desc, phrase),
                ))
    return hits


def scan_capabilities(html: str) -> List[Hit]:
    m = _CAPABILITIES_BLOCK_RE.search(html)
    if not m:
        return []
    data = json.loads(m.group(1))
    hits: List[Hit] = []
    for section in data:
        for i, card in enumerate(section.get("cards", [])):
            desc = card.get("desc", "")
            for phrase in _find_phrases(desc):
                hits.append(Hit(
                    artifact="capabilities",
                    location=f"{section.get('id', '?')}#{i} ({card.get('title', '?')})",
                    phrase=phrase, snippet=_snippet(desc, phrase),
                ))
    return hits


def scan_wiring_map_labels(html: str) -> List[Hit]:
    hits: List[Hit] = []
    for match in _NODE_LABEL_RE.finditer(html):
        node_id, label = match.group(1), match.group(2)
        for phrase in _find_phrases(label):
            hits.append(Hit(
                artifact="wiring_map", location=f"node {node_id}",
                phrase=phrase, snippet=_snippet(label, phrase),
            ))
    return hits


def check() -> List[Hit]:
    hits: List[Hit] = []
    hits.extend(scan_atlas(_ATLAS_PATH.read_text(encoding="utf-8")))
    hits.extend(scan_capabilities(_CAPABILITIES_PATH.read_text(encoding="utf-8")))
    hits.extend(scan_wiring_map_labels(_WIRING_MAP_PATH.read_text(encoding="utf-8")))
    return hits


def main() -> int:
    hits = check()
    by_artifact: dict = {}
    for h in hits:
        by_artifact.setdefault(h.artifact, []).append(h)

    print(f"Status-language scan (report-only, never fails): {len(hits)} hit(s) across "
          f"{len(by_artifact)} artifact(s)")
    for artifact in ("atlas", "capabilities", "wiring_map"):
        artifact_hits = by_artifact.get(artifact, [])
        print(f"\n{artifact}: {len(artifact_hits)} hit(s)")
        for h in artifact_hits:
            print(f"  [{h.phrase}] {h.location}: ...{h.snippet}...")
    return 0  # Always 0 -- this check never fails the build.


if __name__ == "__main__":
    sys.exit(main())

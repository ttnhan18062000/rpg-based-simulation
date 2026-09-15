#!/usr/bin/env python3
"""
Surgically sync docs/brainstorm/rpg_feature_atlas.html's mapped card badge `cls` values to
mechanisms.yaml's own `state` -- and nothing else.

TCK-20260915-ARTIFACT-STATE-CONVERGENCE (scope item 1). The atlas is a 3000+ line artifact the user
reads directly; its value is concentrated in hand-written card descriptions accumulated across many
revisions. `camp` was itself found in a description, not a badge, and
TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT exists specifically to re-read those
descriptions -- a regenerator that emitted whole cards from a template would silently destroy the
input to that audit before it runs. So this tool touches exactly one leaf value per mapped
badge (`badges[i]["cls"]`), via mechanism_atlas_card_mapping.py's own citation-derived positions,
and nothing else. Proven safe by an exact round-trip check: parsing the real file's JSON block and
re-serializing it unmodified with `json.dumps(indent=2, ensure_ascii=False)` reproduces it
byte-for-byte (verified interactively before writing this tool) -- so any diff this tool produces is
attributable entirely to the `cls` values it intentionally changed, never to reformatting.

Idea-level cards (not present in mechanism_atlas_card_mapping.all_mechanism_card_badge_positions())
are never visited at all, let alone touched.

Usage:
  python3 tools/mechanism_atlas_regenerate.py               # writes the real file
  python3 tools/mechanism_atlas_regenerate.py --check        # exit 1 if drift exists, writes nothing
  python3 tools/mechanism_atlas_regenerate.py --path PATH    # target a different atlas file (tests)
  python3 tools/mechanism_atlas_regenerate.py --registry PATH  # target a different registry (tests)
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ATLAS_PATH = _REPO_ROOT / "docs" / "brainstorm" / "rpg_feature_atlas.html"
_DEFAULT_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"

sys.path.insert(0, str(_REPO_ROOT / "tools"))
from mechanism_atlas_card_mapping import all_mechanism_card_badge_positions  # noqa: E402

_BLOCK_RE = re.compile(
    r'(<script type="application/json" id="card-sections-data">\n)(.*?)(\n</script>)',
    re.S,
)


def load_registry_states(registry_path: Path) -> Dict[str, str]:
    data = yaml.safe_load(registry_path.read_text())
    return {mech["id"]: mech["state"] for mech in data["mechanisms"]}


def extract_json_block(html: str) -> Tuple[str, int, int]:
    m = _BLOCK_RE.search(html)
    if not m:
        raise ValueError("card-sections-data script block not found in atlas HTML")
    return m.group(2), m.start(2), m.end(2)


def compute_diffs(atlas_data: dict, states: Dict[str, str]) -> List[dict]:
    """Returns a list of {mechanism_id, section, index, badge_index, old_cls, new_cls} for every
    mapped badge whose current cls disagrees with the registry. Never mutates atlas_data."""
    diffs = []
    positions = all_mechanism_card_badge_positions()
    for mech_id, entries in positions.items():
        if mech_id not in states:
            raise KeyError(
                f"mechanism_atlas_card_mapping references unknown mechanism id {mech_id!r} "
                "-- mapping table is stale against mechanisms.yaml"
            )
        expected = states[mech_id]
        for section, index, badge_index in entries:
            card = atlas_data[section][index]
            badge = card["badges"][badge_index]
            if badge["cls"] != expected:
                diffs.append(
                    {
                        "mechanism_id": mech_id,
                        "section": section,
                        "index": index,
                        "badge_index": badge_index,
                        "title": card.get("title", ""),
                        "old_cls": badge["cls"],
                        "new_cls": expected,
                    }
                )
    return diffs


def apply_diffs(atlas_data: dict, diffs: List[dict]) -> dict:
    """Returns a NEW deep-copied structure with only the diffed cls values changed -- every other
    field (title/text/fromNote/desc/src, and every non-diffed badge) is untouched."""
    mutated = copy.deepcopy(atlas_data)
    for d in diffs:
        mutated[d["section"]][d["index"]]["badges"][d["badge_index"]]["cls"] = d["new_cls"]
    return mutated


def render(check: bool, atlas_path: Path, registry_path: Path) -> int:
    states = load_registry_states(registry_path)
    html = atlas_path.read_text()
    raw_json, start, end = extract_json_block(html)
    atlas_data = json.loads(raw_json)

    diffs = compute_diffs(atlas_data, states)

    if not diffs:
        print("OK: atlas badge cls values match the registry (0 mapped cards drifted).")
        return 0

    print(f"{'DRIFT' if check else 'FIXING'}: {len(diffs)} mapped badge(s) disagree with the registry:")
    for d in diffs:
        print(
            f"  {d['section']}#{d['index']} badge[{d['badge_index']}] ({d['title']!r}) "
            f"-> {d['mechanism_id']}: atlas={d['old_cls']!r}, registry={d['new_cls']!r}"
        )

    if check:
        return 1

    mutated = apply_diffs(atlas_data, diffs)
    new_json = json.dumps(mutated, indent=2, ensure_ascii=False)
    new_html = html[:start] + new_json + html[end:]
    atlas_path.write_text(new_html)
    print(f"Wrote {len(diffs)} cls fix(es) to {atlas_path}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift, write nothing, exit 1 if any.")
    parser.add_argument("--path", type=Path, default=_DEFAULT_ATLAS_PATH, help="Atlas HTML path.")
    parser.add_argument("--registry", type=Path, default=_DEFAULT_REGISTRY_PATH, help="Registry YAML path.")
    args = parser.parse_args()
    return render(check=args.check, atlas_path=args.path, registry_path=args.registry)


if __name__ == "__main__":
    raise SystemExit(main())

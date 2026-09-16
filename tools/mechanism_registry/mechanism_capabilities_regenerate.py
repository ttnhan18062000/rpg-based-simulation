#!/usr/bin/env python3
"""
Surgically sync docs/brainstorm/simulation_capabilities.html's mapped card `tier` (and, only where
it's hand-written to match, `tierLabel`) to mechanisms.yaml's own (state, verified) -- and nothing
else.

TCK-20260915-ARTIFACT-STATE-CONVERGENCE (scope item 3). Same discipline as
tools/mechanism_registry/mechanism_atlas_regenerate.py, tightened by peer review specifically for this file: the
capabilities page exists precisely because its prose is written for a non-dev reader, and no
mapping can generate that -- so `title`/`desc` are NEVER touched, only `tier`, and `tierLabel` only
when this ticket deliberately hand-writes a real replacement label (never templated from the tier
value). Proven safe by the same round-trip check used for the atlas
(json.dumps(indent=2, ensure_ascii=False) reproduces the real file's JSON block byte-for-byte when
unmodified) and by a dedicated body-preservation test.

Usage:
  python3 tools/mechanism_registry/mechanism_capabilities_regenerate.py               # writes the real file
  python3 tools/mechanism_registry/mechanism_capabilities_regenerate.py --check        # exit 1 if drift exists
  python3 tools/mechanism_registry/mechanism_capabilities_regenerate.py --path PATH    # target a different file (tests)
  python3 tools/mechanism_registry/mechanism_capabilities_regenerate.py --registry PATH  # target a different registry
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _REPO_ROOT / "docs" / "brainstorm" / "simulation_capabilities.html"
_DEFAULT_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"

sys.path.insert(0, str(_REPO_ROOT / "tools" / "mechanism_registry"))
from mechanism_capabilities_card_mapping import all_mechanism_card_badge_positions  # noqa: E402
from mechanism_capabilities_tier import resolve_tier  # noqa: E402

_BLOCK_RE = re.compile(
    r'(<script type="application/json" id="sections-data">\n)(.*?)(\n</script>)',
    re.S,
)

# Hand-written tierLabel replacements -- applied ONLY alongside a tier change on the SAME card, and
# ONLY for the specific mechanisms this ticket deliberately corrects. Never auto-generated from the
# tier value; deliberately small and reviewed, not a general templating mechanism. Extend this table
# by hand, with a real replacement label, whenever a real tier fix also needs its stale label fixed
# (the label is prose the mapping cannot regenerate correctly on its own).
TIER_LABEL_OVERRIDES: Dict[str, str] = {
    "camp": "Built, but never actually triggers",
    "demographic_cohort_cycle": "Built, but never actually triggers",
    # cross_episode_grief_nemesis: state done, verified.verdict observed (confirmed live, called
    # from the Campaign orchestrator) -- tier flips built->live correctly, but the label's own
    # "Built, but only active in one game mode" would read as a live/built contradiction unless its
    # leading word is corrected to match; the caveat itself (Campaign-mode-only) stays true and is
    # kept verbatim.
    "cross_episode_grief_nemesis": "Live, but only active in one game mode",
}


def load_registry(registry_path: Path) -> Tuple[Dict[str, str], Dict[str, Optional[dict]]]:
    data = yaml.safe_load(registry_path.read_text())
    states = {m["id"]: m["state"] for m in data["mechanisms"]}
    verified = {m["id"]: m.get("verified") for m in data["mechanisms"]}
    return states, verified


def extract_json_block(html: str) -> Tuple[str, int, int]:
    m = _BLOCK_RE.search(html)
    if not m:
        raise ValueError("sections-data script block not found in capabilities HTML")
    return m.group(2), m.start(2), m.end(2)


def _sections_by_id(data: list) -> Dict[str, dict]:
    """capabilities' sections-data is a LIST of {id, title, cards: [...]} dicts, unlike the atlas's
    dict-keyed-by-section structure -- index it once by id for lookup."""
    return {sec["id"]: sec for sec in data}


def compute_diffs(
    data: list, states: Dict[str, str], verified: Dict[str, Optional[dict]]
) -> List[dict]:
    """Returns a list of {mechanism_id, section, index, old_tier, new_tier, old_label, new_label}
    for every mapped card whose current tier disagrees with resolve_tier(). Never mutates data."""
    diffs = []
    sections = _sections_by_id(data)
    positions = all_mechanism_card_badge_positions()
    for mech_id, entries in positions.items():
        if mech_id not in states:
            raise KeyError(
                f"mechanism_capabilities_card_mapping references unknown mechanism id {mech_id!r} "
                "-- mapping table is stale against mechanisms.yaml"
            )
        expected_tier = resolve_tier(mech_id, states[mech_id], verified.get(mech_id))
        for section, index, _badge_index in entries:
            card = sections[section]["cards"][index]
            if card["tier"] != expected_tier:
                new_label = TIER_LABEL_OVERRIDES.get(mech_id, card["tierLabel"])
                diffs.append(
                    {
                        "mechanism_id": mech_id,
                        "section": section,
                        "index": index,
                        "title": card.get("title", ""),
                        "old_tier": card["tier"],
                        "new_tier": expected_tier,
                        "old_label": card["tierLabel"],
                        "new_label": new_label,
                    }
                )
    return diffs


def apply_diffs(data: list, diffs: List[dict]) -> list:
    """Returns a NEW deep-copied structure with only tier/tierLabel changed on diffed cards -- every
    other field (title/desc, and every non-diffed card) is untouched."""
    mutated = copy.deepcopy(data)
    sections = _sections_by_id(mutated)
    for d in diffs:
        card = sections[d["section"]]["cards"][d["index"]]
        card["tier"] = d["new_tier"]
        card["tierLabel"] = d["new_label"]
    return mutated


def render(check: bool, path: Path, registry_path: Path) -> int:
    states, verified = load_registry(registry_path)
    html = path.read_text()
    raw_json, start, end = extract_json_block(html)
    data = json.loads(raw_json)

    diffs = compute_diffs(data, states, verified)

    if not diffs:
        print("OK: capabilities tier values match the registry (0 mapped cards drifted).")
        return 0

    print(f"{'DRIFT' if check else 'FIXING'}: {len(diffs)} mapped card(s) disagree with the registry:")
    for d in diffs:
        print(
            f"  {d['section']}#{d['index']} ({d['title']!r}) -> {d['mechanism_id']}: "
            f"tier {d['old_tier']!r} -> {d['new_tier']!r}"
            + (f", label updated" if d["old_label"] != d["new_label"] else "")
        )

    if check:
        return 1

    mutated = apply_diffs(data, diffs)
    new_json = json.dumps(mutated, indent=2, ensure_ascii=False)
    new_html = html[:start] + new_json + html[end:]
    path.write_text(new_html)
    print(f"Wrote {len(diffs)} fix(es) to {path}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift, write nothing, exit 1 if any.")
    parser.add_argument("--path", type=Path, default=_DEFAULT_PATH, help="Capabilities HTML path.")
    parser.add_argument("--registry", type=Path, default=_DEFAULT_REGISTRY_PATH, help="Registry YAML path.")
    args = parser.parse_args()
    return render(check=args.check, path=args.path, registry_path=args.registry)


if __name__ == "__main__":
    raise SystemExit(main())

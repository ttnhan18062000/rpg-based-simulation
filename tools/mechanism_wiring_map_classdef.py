#!/usr/bin/env python3
"""
Derives the wiring map's Entity Operating Loop diagram's mermaid `classDef` state colouring from
the mechanism registry's real `state` field -- the one real part of "replace the wiring map's
hand-authored charts" (TCK-20260915-MECHANISM-PRIORITY-DERIVATION Scope item 3), per peer review:
the ticket's own verb overstated its intent; only the classDef state colouring (the "fifth
hand-maintained state surface") is derived, the diagram's own topology stays hand-authored.

Applies ONLY to the Entity Operating Loop diagram (`rpg_simulation_wiring_map.html` line ~447) --
the wiring map's other two diagrams (Layer Model, Entity Lifecycle Arc) do not map 1:1 onto
registry mechanism ids: Layer Model's nodes are layer-level containment groups (Entity, Faction,
World...), not individual mechanisms; Entity Lifecycle Arc's nodes are per-entity lifecycle states
(Alive, Wounded, Dead...), not mechanisms at all. Investigated directly before assuming a 1:1
mapping existed for all three diagrams -- it doesn't.

`DEC` ("Decide Route") has no corresponding registry mechanism id (route-decision logic is not
itself a separately seeded mechanism) -- excluded from the mapping and left with its existing
hand-assigned class, not derived, since there is nothing in the registry to derive it from.

Usage:
  python3 tools/mechanism_wiring_map_classdef.py         # report drift, exit 1 if any found
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_WIRING_MAP_PATH = _REPO_ROOT / "docs" / "brainstorm" / "rpg_simulation_wiring_map.html"

# Entity Operating Loop diagram node abbreviation -> real mechanism id. Only nodes with a genuine
# 1:1 registry mechanism are included; DEC is deliberately excluded (see module docstring).
OPERATING_LOOP_NODE_TO_MECHANISM_ID: Dict[str, str] = {
    "PER": "perception",
    "SELF": "self_model",
    "BEL": "belief_cycle",
    "MEM": "causal_spatial_memory",
    "GOAL": "goal_hierarchy",
    "INT": "committed_intentions",
    "MOT": "motivation_doctrine",
    "CAPT": "cognition_capacity_fatigue",
    "RDY": "action_pacing_readiness",
    "ENG": "combat_engagement",
    "TAC": "tactical_decision",
    "CMB": "combat_resolution",
    "MOV": "movement",
    "ITX": "interaction_channeling",
    "CNV": "conversation",
    "TRD": "entity_trade",
    "TUP": "team_up",
    "XP": "xp_leveling",
    "BRK": "breakthrough_bonuses",
    "REL": "affection_relationship_bonds",
    "REP": "reputation",
    "EMO": "emotion",
    "TRM": "trauma",
    "COM": "commitment_betrayal",
}

# state -> the wiring map's own 4-class vocabulary (live/gated/bug/proposed). The registry's six
# classes don't map 1:1 onto the wiring map's four -- gap/orphan/skeleton all read as "bug" in
# this diagram's own existing convention (nothing built/working), partial reads as "live" (matches
# this diagram's own pre-existing treatment of every currently-partial node before this ticket).
STATE_TO_CLASSDEF: Dict[str, str] = {
    "done": "live",
    "partial": "live",
    "gap": "bug",
    "orphan": "bug",
    "skeleton": "bug",
    "gated": "gated",
}


def _load_registry() -> dict:
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def compute_expected_classdef(registry: dict) -> Dict[str, str]:
    """node abbreviation -> the classDef it should carry, derived from the real registry state."""
    states = {m["id"]: m["state"] for m in registry.get("mechanisms", []) or []}
    result = {}
    for node, mech_id in OPERATING_LOOP_NODE_TO_MECHANISM_ID.items():
        state = states.get(mech_id)
        result[node] = STATE_TO_CLASSDEF.get(state, "bug")  # unknown state reads as bug, not silently live
    return result


def find_drift(registry: dict, wiring_map_text: str) -> Dict[str, dict]:
    """Compares expected classDef (from the registry) against the wiring map's own current
    per-node class assignment (parsed from the file text). Returns {node: {"expected": ..,
    "current": ..}} for every node that disagrees. Never raises on parse ambiguity -- a node whose
    current class can't be determined is reported as `current: "unknown"`, not skipped silently."""
    expected = compute_expected_classdef(registry)
    drift = {}
    for node, exp in expected.items():
        # A node's inline `:::classname` override, if present, wins; otherwise it falls back to
        # whatever the diagram's trailing `class A,B,C classname` line assigns it (checked for
        # "live" specifically, since that's the only bare `class ...` line this diagram uses).
        inline = f'{node}["'
        idx = wiring_map_text.find(inline)
        current = "unknown"
        if idx != -1:
            # Look for a `:::classname` immediately after this node's own bracketed label closes.
            close_idx = wiring_map_text.find("]", idx)
            newline_idx = wiring_map_text.find("\n", close_idx)
            segment = wiring_map_text[close_idx:newline_idx] if newline_idx != -1 else wiring_map_text[close_idx:close_idx + 40]
            if ":::" in segment:
                current = segment.split(":::", 1)[1].strip()
            else:
                # No inline override -- check the diagram's own trailing `class A,B,C,... live`
                # line for this node (parsed generically, not a hardcoded node list -- that list
                # changes whenever a node's own class assignment changes).
                for line in wiring_map_text.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("class ") and stripped.endswith(" live"):
                        node_list = stripped[len("class "):-len(" live")].split(",")
                        if node in node_list:
                            current = "live"
                            break
        if current != exp:
            drift[node] = {"expected": exp, "current": current}
    return drift


def main() -> int:
    registry = _load_registry()
    text = _WIRING_MAP_PATH.read_text(encoding="utf-8")
    drift = find_drift(registry, text)
    if drift:
        print(f"DRIFT: {len(drift)} node(s) in the Entity Operating Loop diagram disagree with "
              f"the registry's real state:")
        for node, d in sorted(drift.items()):
            mech_id = OPERATING_LOOP_NODE_TO_MECHANISM_ID[node]
            print(f"  {node} ({mech_id}): diagram shows '{d['current']}', registry state says "
                  f"'{d['expected']}'")
        return 1
    print("OK: Entity Operating Loop diagram's classDef assignments match the registry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

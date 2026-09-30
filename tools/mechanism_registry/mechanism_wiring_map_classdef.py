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
  python3 tools/mechanism_registry/mechanism_wiring_map_classdef.py               # writes the real file
  python3 tools/mechanism_registry/mechanism_wiring_map_classdef.py --check        # exit 1 if drift exists, writes nothing
  python3 tools/mechanism_registry/mechanism_wiring_map_classdef.py --path PATH    # target a different wiring map file (tests)
  python3 tools/mechanism_registry/mechanism_wiring_map_classdef.py --registry PATH  # target a different registry (tests)

TCK-20260919-MECHANISM-WIRING-MAP-CLASSDEF-REGENERATE-MODE-GAP: default-write / `--check`-reports-
only, mirroring `mechanism_atlas_regenerate.py`'s own CLI shape exactly -- this tool previously had
no write mode at all, so every state correction touching this diagram needed a hand `Edit`.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REGISTRY_PATH = _REPO_ROOT / "registries" / "mechanisms.yaml"
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
    "XP": "evolution",
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


_CLASS_LIVE_LINE_RE = re.compile(r"^(\s*)class ([A-Za-z0-9_,]+) live$")


def _remove_node_from_class_live_lines(text: str, node: str) -> str:
    """Removes `node` from any trailing `class A,B,C,... live` line it's currently a member of,
    dropping the whole line if `node` was its only member. A no-op if `node` isn't in any such
    line (already inline-overridden, or never colored at all)."""
    out_lines = []
    for line in text.split("\n"):
        m = _CLASS_LIVE_LINE_RE.match(line)
        if m:
            indent, node_list_str = m.group(1), m.group(2)
            node_list = node_list_str.split(",")
            if node in node_list:
                node_list = [n for n in node_list if n != node]
                if node_list:
                    out_lines.append(f"{indent}class {','.join(node_list)} live")
                continue  # replaced above, or dropped entirely if now empty
        out_lines.append(line)
    return "\n".join(out_lines)


def _apply_inline_override(text: str, node: str, expected: str) -> str:
    """Sets `node`'s classDef to an inline `:::expected` override immediately after its own `]`
    bracket close -- replacing an existing inline override if present (mirrors `find_drift()`'s
    own "immediately after this node's own bracketed label closes" parsing), otherwise inserting
    a new one."""
    inline = f'{node}["'
    idx = text.find(inline)
    if idx == -1:
        raise ValueError(f"node {node!r} not found in wiring map text")
    close_idx = text.find("]", idx)
    if close_idx == -1:
        raise ValueError(f"unterminated label for node {node!r}")
    after_bracket = close_idx + 1
    override_match = re.match(r":::[A-Za-z0-9_]*", text[after_bracket:])
    end = after_bracket + override_match.end() if override_match else after_bracket
    return text[:after_bracket] + f":::{expected}" + text[end:]


def apply_classdef_fix(text: str, node: str, expected: str) -> str:
    """Surgically sets `node`'s classDef to `expected`: first removes it from any `class A,B,C,...
    live` line it currently sits in (so it's never simultaneously inline-overridden AND
    class-line-assigned -- mermaid applies the class-line assignment last, which would silently
    shadow the inline override), then applies the inline `:::expected` override."""
    text = _remove_node_from_class_live_lines(text, node)
    return _apply_inline_override(text, node, expected)


def render(check: bool, wiring_map_path: Path, registry_path: Path) -> int:
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    text = wiring_map_path.read_text(encoding="utf-8")
    drift = find_drift(registry, text)

    if not drift:
        print("OK: Entity Operating Loop diagram's classDef assignments match the registry.")
        return 0

    print(f"{'DRIFT' if check else 'FIXING'}: {len(drift)} node(s) in the Entity Operating Loop "
          f"diagram disagree with the registry's real state:")
    for node, d in sorted(drift.items()):
        mech_id = OPERATING_LOOP_NODE_TO_MECHANISM_ID[node]
        print(f"  {node} ({mech_id}): diagram shows '{d['current']}', registry state says "
              f"'{d['expected']}'")

    if check:
        return 1

    for node, d in drift.items():
        text = apply_classdef_fix(text, node, d["expected"])
    wiring_map_path.write_text(text, encoding="utf-8")
    print(f"Wrote {len(drift)} classDef fix(es) to {wiring_map_path}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift, write nothing, exit 1 if any.")
    parser.add_argument("--path", type=Path, default=_WIRING_MAP_PATH, help="Wiring map HTML path.")
    parser.add_argument("--registry", type=Path, default=_REGISTRY_PATH, help="Registry YAML path.")
    args = parser.parse_args()
    return render(check=args.check, wiring_map_path=args.path, registry_path=args.registry)


if __name__ == "__main__":
    sys.exit(main())

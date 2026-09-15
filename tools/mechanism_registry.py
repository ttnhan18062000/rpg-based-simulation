#!/usr/bin/env python3
"""
Reader and validator for docs/brainstorm/mechanisms.yaml — the single hand-authored source for
what simulation mechanisms exist, which layer each belongs to, and what each depends on.

TCK-20260915-MECHANISM-REGISTRY-FOUNDATION (child of TCK-20260915-EPIC-MECHANISM-REGISTRY).
Pattern imitated from src/engine/capability.py (a working hand-authored-YAML-registry + reader +
validator precedent for a different subject), adapted for this registry's extra invariants
(depends_on resolution, DAG acyclicity) that capability.py's simpler flat list did not need.

Four invariants enforced by validate():
  1. every `depends_on` id resolves to a declared mechanism
  2. the dependency graph is acyclic
  3. every mechanism's `layer` is declared in the `layers` block
  4. every `state` is one of the six classes already used by the atlas

`validate()` returns a list of human-readable error strings (empty if valid) rather than
raising/returning a bool, so a caller can report every violation in one run instead of stopping at
the first -- "build the failure loud" (this ticket's own Implementation Notes).

Usage:
  python3 tools/mechanism_registry.py               # validate the real committed file
  python3 tools/mechanism_registry.py <path>         # validate an arbitrary file (used by tests)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"

VALID_STATES = frozenset({"done", "partial", "gap", "orphan", "gated", "skeleton"})


class MechanismRegistry:
    """Read-only view of the mechanism registry (docs/brainstorm/mechanisms.yaml)."""

    def __init__(self, registry_path: Path = _DEFAULT_PATH) -> None:
        with open(registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self.layers: Dict[str, dict] = data.get("layers", {}) or {}
        self._mechanisms: Dict[str, dict] = {
            m["id"]: m for m in (data.get("mechanisms", []) or [])
        }

    def get_state(self, mechanism_id: str) -> Optional[str]:
        """Return the state string for a mechanism_id, or None if not found."""
        entry = self._mechanisms.get(mechanism_id)
        return entry.get("state") if entry else None

    def all_mechanisms(self) -> List[dict]:
        """Return all mechanism entries as a list of dicts."""
        return list(self._mechanisms.values())

    def dependents_of(self, mechanism_id: str) -> List[str]:
        """Mechanisms that declare `mechanism_id` in their own depends_on.

        Computed by traversal over depends_on every call -- never stored, per Acceptance
        Criteria #2 (depends_on is the only hand-authored edge; a stored dependent-count would
        disagree with the real edges within a month, and the stored one is the one people read).
        """
        return [
            m["id"]
            for m in self._mechanisms.values()
            if mechanism_id in (m.get("depends_on") or [])
        ]


def validate(data: dict) -> List[str]:
    """Returns a list of human-readable error strings, empty if valid.

    Only raises for a structurally malformed file (missing top-level keys entirely); every
    business-logic violation (the four invariants) is returned as a string, never raised, so every
    violation in one file is reported in a single run.
    """
    errors: List[str] = []
    layers = data.get("layers", {}) or {}
    mechanisms = data.get("mechanisms", []) or []

    ids = {m["id"] for m in mechanisms if "id" in m}

    # Invariant 3: every layer is declared in the layers block.
    for m in mechanisms:
        mid = m.get("id", "<missing id>")
        layer = m.get("layer")
        if layer not in layers:
            errors.append(
                f"mechanism '{mid}' declares layer '{layer}', which is not in the layers block"
            )

    # Invariant 4: every state is one of the six classes.
    for m in mechanisms:
        mid = m.get("id", "<missing id>")
        state = m.get("state")
        if state not in VALID_STATES:
            errors.append(
                f"mechanism '{mid}' has state '{state}', not one of {sorted(VALID_STATES)}"
            )

    # Invariant 1: every depends_on id resolves to a declared mechanism.
    for m in mechanisms:
        mid = m.get("id", "<missing id>")
        for dep in m.get("depends_on") or []:
            if dep not in ids:
                errors.append(
                    f"mechanism '{mid}' depends_on unresolved id '{dep}'"
                )

    # Invariant 2: the dependency graph is acyclic. DFS with a visiting-set (not pairwise-only --
    # a longer cycle a->b->c->a must be caught too, not just direct a<->b symmetry). Only walk
    # edges that resolved above, so a broken edge doesn't also mask/duplicate a cycle report.
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {mid: WHITE for mid in ids}
    dep_map = {m["id"]: [d for d in (m.get("depends_on") or []) if d in ids] for m in mechanisms if "id" in m}

    def _dfs(node: str, stack: List[str]) -> Optional[List[str]]:
        color[node] = GRAY
        stack.append(node)
        for dep in dep_map.get(node, []):
            if color[dep] == GRAY:
                cycle_start = stack.index(dep)
                return stack[cycle_start:] + [dep]
            if color[dep] == WHITE:
                found = _dfs(dep, stack)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    reported_cycle = False
    for mid in ids:
        if color[mid] == WHITE and not reported_cycle:
            cycle = _dfs(mid, [])
            if cycle:
                errors.append(f"dependency cycle detected: {' -> '.join(cycle)}")
                reported_cycle = True

    return errors


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else _DEFAULT_PATH

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    errors = validate(data)
    if errors:
        print(f"FAIL: {len(errors)} violation(s) in {path}")
        for e in errors:
            print(f"  - {e}")
        return 1

    n_mechanisms = len(data.get("mechanisms", []) or [])
    print(f"OK: {path} valid, {n_mechanisms} mechanisms")
    return 0


if __name__ == "__main__":
    sys.exit(main())

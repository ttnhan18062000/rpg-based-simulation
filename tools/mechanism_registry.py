#!/usr/bin/env python3
"""
Reader and validator for docs/brainstorm/mechanisms.yaml — the single hand-authored source for
what simulation mechanisms exist, which layer each belongs to, and what each depends on.

TCK-20260915-MECHANISM-REGISTRY-FOUNDATION (child of TCK-20260915-EPIC-MECHANISM-REGISTRY).
Pattern imitated from src/engine/capability.py (a working hand-authored-YAML-registry + reader +
validator precedent for a different subject), adapted for this registry's extra invariants
(depends_on resolution, DAG acyclicity) that capability.py's simpler flat list did not need.

Six invariants enforced by validate():
  1. every `depends_on` id resolves to a declared mechanism
  2. the dependency graph is acyclic
  3. every mechanism's `layer` is declared in the `layers` block
  4. every `state` is one of the six classes already used by the atlas
  5. every present `verified.instrument` is one of the four known values (TCK-20260915-MECHANISM-
     VERIFICATION-AXIS)
  6. every present `verified.verdict` is one of the three known values, and all four `verified`
     sub-fields (instrument/verdict/date/note) are present when the block itself is present

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

# TCK-20260915-MECHANISM-VERIFICATION-AXIS. STATIC vs RUNTIME kept explicitly distinct -- a
# code_trace verdict proves what the code *says*, never that reachable code has its claimed
# runtime effect (combat judgement's own write-only near-miss: a clean code trace, write-only in
# practice, caught only by a runtime instrument). See mechanisms.yaml's own header comment for the
# full reasoning.
STATIC_INSTRUMENTS = frozenset({"code_trace"})
RUNTIME_INSTRUMENTS = frozenset({"census", "scenario", "corpus_run"})
VALID_INSTRUMENTS = STATIC_INSTRUMENTS | RUNTIME_INSTRUMENTS
VALID_VERDICTS = frozenset({"observed", "contradicted", "inconclusive"})
_REQUIRED_VERIFIED_FIELDS = frozenset({"instrument", "verdict", "date", "note"})


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

    def transitive_dependents_of(self, mechanism_id: str) -> List[str]:
        """Every mechanism that transitively depends on mechanism_id (a dependent-of-a-dependent
        chain, not just direct). Computed by traversal every call -- never stored, same rule as
        dependents_of() (TCK-20260915-MECHANISM-PRIORITY-DERIVATION Acceptance Criteria #1).
        Safe on a DAG (the real registry's own acyclicity is enforced by validate()); a cycle in
        unvalidated input raises rather than looping forever -- see the module-level
        transitive_dependents() docstring for the real reasoning."""
        dep_map = {mid: m.get("depends_on") or [] for mid, m in self._mechanisms.items()}
        return sorted(transitive_dependents(mechanism_id, dep_map))

    def get_verification(self, mechanism_id: str) -> Optional[dict]:
        """Return the `verified` block for mechanism_id, or None if unverified (absent, explicit
        `null`, or an unknown id -- an unknown id is not itself an error here, mirroring
        get_state()'s own unknown-id-returns-None contract)."""
        entry = self._mechanisms.get(mechanism_id)
        return entry.get("verified") if entry else None


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

    # Invariants 5/6: a present `verified` block has all 4 required sub-fields, and
    # instrument/verdict are each one of the known values.
    for m in mechanisms:
        mid = m.get("id", "<missing id>")
        verified = m.get("verified")
        if verified is None:
            continue
        missing = _REQUIRED_VERIFIED_FIELDS - verified.keys()
        if missing:
            errors.append(
                f"mechanism '{mid}' has a verified block missing required field(s): "
                f"{sorted(missing)}"
            )
            continue  # don't also flag an absent instrument/verdict as "unknown" below
        instrument = verified.get("instrument")
        if instrument not in VALID_INSTRUMENTS:
            errors.append(
                f"mechanism '{mid}' verified.instrument is '{instrument}', not one of "
                f"{sorted(VALID_INSTRUMENTS)}"
            )
        verdict = verified.get("verdict")
        if verdict not in VALID_VERDICTS:
            errors.append(
                f"mechanism '{mid}' verified.verdict is '{verdict}', not one of "
                f"{sorted(VALID_VERDICTS)}"
            )

    return errors


def build_verification_view(records: Dict[str, List[dict]], mechanisms: List[dict]) -> List[dict]:
    """One row per mechanism (Acceptance Criteria #1), including unverified ones rendered
    explicitly rather than omitted (AC #2) -- the load-bearing rule this whole ticket exists for.

    `records`: mechanism_id -> list of verification dicts (each with instrument/verdict/date/note).
    Today's real registry only ever has 0 or 1 entries per id (hand-authored, no multi-source feed
    -- automated ingestion is explicitly out of scope), but this function still collapses >1 to the
    latest-by-date (AC #4), future-proofing for whenever an ingestion pipeline exists without a
    schema change. `mechanisms`: the full mechanism list, so every id appears even with zero
    records.

    Rows are grouped and ordered: runtime-verified first, static (code_trace)-verified next,
    unverified last -- each group sorted by id for determinism. This groups static evidence
    separately from runtime evidence per mechanisms.yaml's own documented distinction: a
    code_trace verdict must never read as equally strong as a runtime-confirmed one.
    """
    rows: List[dict] = []
    for m in mechanisms:
        mid = m["id"]
        mech_records = records.get(mid) or []
        if not mech_records:
            rows.append({
                "id": mid,
                "layer": m.get("layer"),
                "state": m.get("state"),
                "verified": False,
                "instrument": None,
                "verdict": "unverified",
                "date": None,
                "note": None,
            })
            continue
        latest = max(mech_records, key=lambda r: r.get("date") or "")
        rows.append({
            "id": mid,
            "layer": m.get("layer"),
            "state": m.get("state"),
            "verified": True,
            "instrument": latest.get("instrument"),
            "verdict": latest.get("verdict"),
            "date": latest.get("date"),
            "note": latest.get("note"),
        })

    def _group_key(row: dict) -> tuple:
        if not row["verified"]:
            group = 2
        elif row["instrument"] in STATIC_INSTRUMENTS:
            group = 1
        else:
            group = 0
        return (group, row["id"])

    return sorted(rows, key=_group_key)


def verification_records_from_registry(data: dict) -> Dict[str, List[dict]]:
    """Adapts the real registry's single verified-block-per-mechanism shape into
    build_verification_view()'s records input (mechanism_id -> list of 0 or 1 verification
    dicts) -- the real file never has more than one, but the function signature stays list-based
    for the future-ingestion reason documented on build_verification_view() itself."""
    result: Dict[str, List[dict]] = {}
    for m in data.get("mechanisms", []) or []:
        verified = m.get("verified")
        result[m["id"]] = [verified] if verified else []
    return result


# ── TCK-20260915-MECHANISM-PRIORITY-DERIVATION ─────────────────────────────────────────────────
#
# Priority is derived, never hand-ranked, so disagreements are about *edges* (a real, checkable
# claim) rather than about rankings (an opinion). rank * transitive-dependent-count, decided
# transitive over direct against real data: the real 75-mechanism graph has the same 26 hubs
# either way, but the RANKING differs meaningfully -- e.g. combat_engagement (1 direct dependent /
# 13 transitive) would rank the project's single most-verified, most-central mechanism near the
# bottom under direct-count alone. See staging_artifacts/TCK-20260915-MECHANISM-PRIORITY-
# DERIVATION/investigation.md for the full real-data comparison.


class DependencyCycleError(ValueError):
    """Raised by transitive_dependents() when the input graph contains a cycle. The real
    registry's own acyclicity is already enforced by validate() (a different code path, at the
    schema-validation layer) -- this is an independent guard for this module's own traversal
    functions, proven against a deliberately invalid fixture rather than assumed inherited
    (TCK-20260915-MECHANISM-PRIORITY-DERIVATION Acceptance Criteria #6)."""


def transitive_dependents(mechanism_id: str, dep_map: Dict[str, List[str]]) -> Set[str]:
    """Every mechanism that transitively depends on mechanism_id, via reverse-BFS over dep_map
    (mechanism_id -> its own depends_on list). Raises DependencyCycleError on a cycle rather than
    looping forever -- explicit cycle detection here, not assumed safe from validate() having
    already run on this exact input."""
    # A node is "visiting" while its own DFS branch is still open; a repeat visit while still
    # open is a real cycle. Fully "done" nodes are cached and never re-walked.
    VISITING, DONE = 1, 2
    status: Dict[str, int] = {}
    result: Set[str] = set()

    def _walk(node: str, path: List[str]) -> None:
        if status.get(node) == DONE:
            return
        if status.get(node) == VISITING:
            cycle = path[path.index(node):] + [node]
            raise DependencyCycleError(f"dependency cycle detected: {' -> '.join(cycle)}")
        status[node] = VISITING
        path.append(node)
        for candidate, deps in dep_map.items():
            if node in deps:
                result.add(candidate)
                _walk(candidate, path)
        path.pop()
        status[node] = DONE

    _walk(mechanism_id, [])
    return result


def priority(mechanism_id: str, dep_map: Dict[str, List[str]], layer: str, layers: Dict[str, dict]) -> int:
    """rank * transitive-dependent-count. A multiply, not a two-key sort -- lets a heavily-
    depended-on higher-layer mechanism outrank a low-dependent leaf in a lower layer, per this
    ticket's own explicit design intent (checked against real data in investigation.md, not
    assumed correct)."""
    rank = (layers.get(layer) or {}).get("rank", 0)
    return rank * len(transitive_dependents(mechanism_id, dep_map))


def unverified_priority_ranking(data: dict) -> List[dict]:
    """The primary generated view (reframed per peer review, following T2's own seed finding: 69
    of 75 mechanisms are unverified -- 'which one to verify next' is the real question, not an
    abstract ranking over all 75). Returns unverified mechanisms only, ordered by priority
    descending, each row {id, layer, state, priority, transitive_dependent_count}."""
    mechanisms = data.get("mechanisms", []) or []
    layers = data.get("layers", {}) or {}
    dep_map = {m["id"]: m.get("depends_on") or [] for m in mechanisms}

    rows = []
    for m in mechanisms:
        if m.get("verified"):
            continue
        mid = m["id"]
        dependents = transitive_dependents(mid, dep_map)
        rows.append({
            "id": mid,
            "layer": m.get("layer"),
            "state": m.get("state"),
            "priority": priority(mid, dep_map, m.get("layer"), layers),
            "transitive_dependent_count": len(dependents),
        })
    return sorted(rows, key=lambda r: (-r["priority"], r["id"]))


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

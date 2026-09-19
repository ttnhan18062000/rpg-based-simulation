#!/usr/bin/env python3
"""
Reader and validator for registries/mechanisms.yaml — the single hand-authored source for
what simulation mechanisms exist, which layer each belongs to, and what each depends on.

TCK-20260915-MECHANISM-REGISTRY-FOUNDATION (child of TCK-20260915-EPIC-MECHANISM-REGISTRY).
Pattern imitated from src/engine/capability.py (a working hand-authored-YAML-registry + reader +
validator precedent for a different subject), adapted for this registry's extra invariants
(depends_on resolution, DAG acyclicity) that capability.py's simpler flat list did not need.

Ten invariants enforced by validate() (the header count was already stale at "Seven" before this
edit -- invariant 8 had already been added without updating it; fixed here rather than repeated):
  1. every `depends_on` id resolves to a declared mechanism
  2. the dependency graph is acyclic
  3. every mechanism's `layer` is declared in the `layers` block
  4. every `state` is one of the six classes already used by the atlas
  5. every present `verified.instrument` is one of the four known values (TCK-20260915-MECHANISM-
     VERIFICATION-AXIS)
  6. every present `verified.verdict` is one of the three known values, and all four `verified`
     sub-fields (instrument/verdict/date/note) are present when the block itself is present
  7. every present `implemented_by` is a list of strings, each an existing repo-relative path
     (TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING) -- a real code binding, checked against disk
     so a deleted implementing module fails validation immediately rather than the registry
     silently keeping a stale claim
  8. every `unaudited_depends_on_edges` entry names a real, currently-declared depends_on edge
     (TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT) -- a stale marker for an edge that
     was since removed or never existed would misrepresent an unchecked edge as audited
  9. every value in a mechanism's `systems: []` resolves to a system registered in
     registries/system_registry.jsonl (TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION) --
     "no missing system"
  10. every system registered in registries/system_registry.jsonl has at least one mechanism
      declaring it (same ticket) -- "no orphan system": a declared system with zero members is
      dead vocabulary and should fail rather than accumulate silently

`validate()` returns a list of human-readable error strings (empty if valid) rather than
raising/returning a bool, so a caller can report every violation in one run instead of stopping at
the first -- "build the failure loud" (this ticket's own Implementation Notes).

Usage:
  python3 tools/mechanism_registry/registry.py               # validate the real committed file
  python3 tools/mechanism_registry/registry.py <path>         # validate an arbitrary file (used by tests)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _REPO_ROOT / "registries" / "mechanisms.yaml"

sys.path.insert(0, str(_REPO_ROOT / "tools" / "mechanism_registry"))
from system_registry import load_registry as _load_system_registry  # noqa: E402

# TCK-20260916-MECHANISM-IMPLEMENTED-BY-SYMBOL-LEVEL-BINDING. An `implemented_by` entry is either
# a bare repo-relative path (file-level -- the whole file is the binding) or "<path>::<Symbol>"
# (symbol-level -- one specific class or module-level function within the file is the binding).
# Symbol-level exists because file-level granularity produces a misleading signal when one file
# defines multiple loosely-related symbols: demographic_cohort_cycle's own cohort.py defines both
# `PopulationCohort` (a data class used widely and unrelated to this mechanism's own claim) and
# `DemographicCycleService` (the actual entry point) -- a caller-count check aggregating across
# both cannot tell "the data class is used elsewhere" from "the service is actually invoked."
_TOP_LEVEL_SYMBOL_RE_TEMPLATE = r"^(?:class|def)\s+{}\b"


def parse_implemented_by_entry(entry: str) -> Tuple[str, Optional[str]]:
    """Splits one `implemented_by` string into (path, symbol_or_None)."""
    if "::" in entry:
        path, symbol = entry.split("::", 1)
        return path, symbol
    return entry, None


def symbol_defined_in_file(path: Path, symbol: str) -> bool:
    """True if `symbol` is a top-level class or module-level function in the real file at path."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    pattern = re.compile(_TOP_LEVEL_SYMBOL_RE_TEMPLATE.format(re.escape(symbol)), re.MULTILINE)
    return bool(pattern.search(text))

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
    """Read-only view of the mechanism registry (registries/mechanisms.yaml)."""

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

    # Invariant 7: a present `implemented_by` is a list of real, existing repo-relative paths,
    # optionally with a "::Symbol" suffix that must itself be a real top-level class or function
    # in that file. TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING / -SYMBOL-LEVEL-BINDING. The
    # original 75 mechanisms cite atlas cards, never source -- this is the real code binding, and
    # the existence check is the whole point: a deleted implementing module (or a renamed/deleted
    # symbol, for a symbol-level entry) fails validation the day it happens, instead of the
    # registry silently reading "confirmed live" for eight days, the way `motivation_doctrine` did
    # before this field existed.
    for m in mechanisms:
        mid = m.get("id", "<missing id>")
        implemented_by = m.get("implemented_by")
        if implemented_by is None:
            continue
        if not isinstance(implemented_by, list) or not all(
            isinstance(p, str) for p in implemented_by
        ):
            errors.append(
                f"mechanism '{mid}' implemented_by must be a list of strings, got {implemented_by!r}"
            )
            continue
        for entry in implemented_by:
            rel_path, symbol = parse_implemented_by_entry(entry)
            real_path = _REPO_ROOT / rel_path
            if not real_path.is_file():
                errors.append(
                    f"mechanism '{mid}' implemented_by path does not exist: '{rel_path}'"
                )
                continue
            if symbol is not None and not symbol_defined_in_file(real_path, symbol):
                errors.append(
                    f"mechanism '{mid}' implemented_by symbol '{symbol}' not found as a "
                    f"top-level class/function in '{rel_path}'"
                )

    # Invariant 8: every `unaudited_depends_on_edges` entry names a real, currently-declared
    # depends_on edge (TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT). This list exists so
    # a ranking/priority consumer can surface "N of these edges are unvalidated" instead of
    # treating an edge no one could confirm as equivalent to a confirmed one -- the same
    # visible-not-silent rule this file already applies to `verified: null`. An entry that no
    # longer matches a real depends_on pair (the edge was since removed, or never existed) is a
    # stale marker, not a harmless leftover -- it would make a real edge look audited-but-unproven
    # when it was never checked at all.
    unaudited_edges = data.get("unaudited_depends_on_edges") or []
    dep_map_raw = {m["id"]: m.get("depends_on") or [] for m in mechanisms if "id" in m}
    for entry in unaudited_edges:
        if not (isinstance(entry, list) and len(entry) == 2):
            errors.append(
                f"unaudited_depends_on_edges entry must be a [dependent, dependency] pair, got {entry!r}"
            )
            continue
        dependent, dependency = entry
        if dependent not in dep_map_raw:
            errors.append(
                f"unaudited_depends_on_edges names unknown dependent mechanism '{dependent}'"
            )
            continue
        if dependency not in dep_map_raw.get(dependent, []):
            errors.append(
                f"unaudited_depends_on_edges entry [{dependent}, {dependency}] is not a currently "
                f"declared depends_on edge -- stale marker, remove it or restore the edge"
            )

    # Invariants 9/10: mechanism `systems: []` membership, checked against
    # registries/system_registry.jsonl (TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION).
    # Declared membership never touches depends_on -- these two invariants are independent of
    # every dependency-graph check above.
    registered_systems = set(_load_system_registry().keys())
    systems_declared_by: Dict[str, List[str]] = {s: [] for s in registered_systems}
    for m in mechanisms:
        mid = m.get("id", "<missing id>")
        mech_systems = m.get("systems") or []
        for sys_name in mech_systems:
            if sys_name not in registered_systems:
                errors.append(
                    f"mechanism '{mid}' declares system '{sys_name}', which is not registered in "
                    f"registries/system_registry.jsonl"
                )
                continue
            systems_declared_by[sys_name].append(mid)

    for sys_name, members in systems_declared_by.items():
        if not members:
            errors.append(
                f"system '{sys_name}' is registered in registries/system_registry.jsonl but no "
                f"mechanism declares it -- orphan system, dead vocabulary"
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
# claim) rather than about rankings (an opinion). weight * transitive-dependent-count, decided
# transitive over direct against real data: the real 75-mechanism graph has the same 26 hubs
# either way, but the RANKING differs meaningfully -- e.g. combat_engagement (1 direct dependent /
# 13 transitive) would rank the project's single most-verified, most-central mechanism near the
# bottom under direct-count alone. See staging_artifacts/TCK-20260915-MECHANISM-PRIORITY-
# DERIVATION/investigation.md for the full real-data comparison. (`weight`, not `rank`, per
# TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED -- `rank * dependents` was a shipped
# defect that rewarded the rarest layers.)


class DependencyCycleError(ValueError):
    """Raised by transitive_dependents() when the input graph contains a cycle. The real
    registry's own acyclicity is already enforced by validate() (a different code path, at the
    schema-validation layer) -- this is an independent guard for this module's own traversal
    functions, proven against a deliberately invalid fixture rather than assumed inherited
    (TCK-20260915-MECHANISM-PRIORITY-DERIVATION Acceptance Criteria #6)."""


def transitive_dependencies_of(mechanism_id: str, dep_map: Dict[str, List[str]]) -> Set[str]:
    """The forward closure: every mechanism mechanism_id transitively depends on (its own
    ancestors in dependency terms -- "what does X actually need", the ticket's own worked
    example). The mirror of transitive_dependents() below (backward closure); same cycle-safety."""
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
        for dep in dep_map.get(node, []):
            result.add(dep)
            _walk(dep, path)
        path.pop()
        status[node] = DONE

    _walk(mechanism_id, [])
    return result


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


def count_unaudited_edges_in_transitive_dependents(
    mechanism_id: str, dep_map: Dict[str, List[str]], unaudited_edges: Set[Tuple[str, str]]
) -> int:
    """How many edges feeding `transitive_dependents(mechanism_id, dep_map)` are in
    `unaudited_edges` (TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT). Same reverse-BFS
    shape as `transitive_dependents`, but counts traversed edges `(candidate, node)` -- candidate
    depends_on node -- against the unaudited set instead of just collecting reachable nodes. This
    is what lets a priority row say "N of the edges behind this ranking are unvalidated" instead of
    silently treating an edge no one could confirm as equivalent to a confirmed one."""
    VISITING, DONE = 1, 2
    status: Dict[str, int] = {}
    count = 0

    def _walk(node: str, path: List[str]) -> None:
        nonlocal count
        if status.get(node) == DONE:
            return
        if status.get(node) == VISITING:
            cycle = path[path.index(node):] + [node]
            raise DependencyCycleError(f"dependency cycle detected: {' -> '.join(cycle)}")
        status[node] = VISITING
        path.append(node)
        for candidate, deps in dep_map.items():
            if node in deps:
                if (candidate, node) in unaudited_edges:
                    count += 1
                _walk(candidate, path)
        path.pop()
        status[node] = DONE

    _walk(mechanism_id, [])
    return count


def priority(mechanism_id: str, dep_map: Dict[str, List[str]], layer: str, layers: Dict[str, dict]) -> int:
    """weight * transitive-dependent-count. A multiply, not a two-key sort -- lets a heavily-
    depended-on mechanism in a frequent layer outrank a low-dependent leaf in a rare one.

    Uses `weight`, NEVER `rank` (TCK-20260916-MECHANISM-PRIORITY-LAYER-WEIGHT-INVERTED): `rank` is
    an ordinal (position from the bottom, low=frequent), not a priority multiplier. Multiplying by
    `rank` rewards the rarest layers and was a real, shipped defect -- confirmed on real data
    (`betrayal_siege_war`, a deliberately deprioritized faction-war mechanism, ranked #1 unverified
    ahead of `action_pacing_readiness`, a per-tick entity mechanism with double its dependents).
    `weight` is the explicit, independently-settable field stating "how often this runs," so the
    direction can never again be silently re-derived wrong from an ordinal that means something
    else."""
    weight = (layers.get(layer) or {}).get("weight", 0)
    return weight * len(transitive_dependents(mechanism_id, dep_map))


def all_mechanisms_combined_view(data: dict) -> List[dict]:
    """TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW. Every mechanism in the registry, one row
    each, both axes together -- unlike unverified_priority_ranking() (priority only, unverified
    only, top-25) and build_verification_view() (verification only, no priority), this answers
    "what matters most, and do we know it works" in a single read. Reuses both existing builders rather than
    reimplementing either axis. Sorted by priority descending, id as tiebreak -- a verified
    mechanism still gets its real priority number, so it isn't silently dropped from the ranking
    the way it is in the unverified-only view."""
    mechanisms = data.get("mechanisms", []) or []
    layers = data.get("layers", {}) or {}
    dep_map = {m["id"]: m.get("depends_on") or [] for m in mechanisms}

    verification_rows = {
        r["id"]: r
        for r in build_verification_view(verification_records_from_registry(data), mechanisms)
    }

    rows = []
    for m in mechanisms:
        mid = m["id"]
        v = verification_rows[mid]
        evidence = "unverified" if not v["verified"] else (
            "runtime" if v["instrument"] in RUNTIME_INSTRUMENTS else "static"
        )
        rows.append({
            "id": mid,
            "layer": m.get("layer"),
            "state": m.get("state"),
            "evidence": evidence,
            "instrument": v["instrument"],
            "verdict": v["verdict"],
            "date": v["date"],
            "note": v["note"],
            "priority": priority(mid, dep_map, m.get("layer"), layers),
            "transitive_dependent_count": len(transitive_dependents(mid, dep_map)),
        })
    return sorted(rows, key=lambda r: (-r["priority"], r["id"]))


def unverified_priority_ranking(data: dict) -> List[dict]:
    """The primary generated view (reframed per peer review, following T2's own seed finding: 69
    of 75 mechanisms are unverified -- 'which one to verify next' is the real question, not an
    abstract ranking over all 75). Returns unverified mechanisms only, ordered by priority
    descending, each row {id, layer, state, priority, transitive_dependent_count}."""
    mechanisms = data.get("mechanisms", []) or []
    layers = data.get("layers", {}) or {}
    dep_map = {m["id"]: m.get("depends_on") or [] for m in mechanisms}
    unaudited_edges = {
        (pair[0], pair[1]) for pair in (data.get("unaudited_depends_on_edges") or [])
        if isinstance(pair, list) and len(pair) == 2
    }

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
            "unaudited_edge_count": count_unaudited_edges_in_transitive_dependents(
                mid, dep_map, unaudited_edges
            ),
        })
    return sorted(rows, key=lambda r: (-r["priority"], r["id"]))


def mechanisms_by_system(data: dict) -> Dict[str, List[str]]:
    """TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION. Every registered system mapped to the
    sorted list of mechanism ids that declare it, PLUS a real `"unassigned"` key holding every
    mechanism whose own `systems: []` is empty or absent.

    A mechanism with no system is **rendered explicitly under `"unassigned"`, never silently
    dropped** -- the same rule this registry already applies to `verified: null` (AC #4/#5 of the
    foundation ticket). `"unassigned"` is a real key in the returned dict even when its own list
    is empty, so a caller can always find it rather than needing a `.get(..., [])` guess.

    Read-only query, matching `transitive_dependents()`/`all_mechanisms_combined_view()`'s own
    shape -- computes nothing that feeds priority or verdict (Acceptance Criteria #6: membership
    stays a review lens, never load-bearing)."""
    mechanisms = data.get("mechanisms", []) or []
    registered_systems = set(_load_system_registry().keys())

    result: Dict[str, List[str]] = {s: [] for s in registered_systems}
    result["unassigned"] = []

    for m in mechanisms:
        mid = m.get("id")
        if mid is None:
            continue
        mech_systems = m.get("systems") or []
        if not mech_systems:
            result["unassigned"].append(mid)
            continue
        for sys_name in mech_systems:
            if sys_name in result:
                result[sys_name].append(mid)

    for key in result:
        result[key].sort()

    return result


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

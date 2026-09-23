#!/usr/bin/env python3
"""
Reader and validator for registries/mechanisms.yaml — the single hand-authored source for
what simulation mechanisms exist, which layer each belongs to, and what each depends on.

TCK-20260915-MECHANISM-REGISTRY-FOUNDATION (child of TCK-20260915-EPIC-MECHANISM-REGISTRY).
Pattern imitated from src/engine/capability.py (a working hand-authored-YAML-registry + reader +
validator precedent for a different subject), adapted for this registry's extra invariants
(depends_on resolution, DAG acyclicity) that capability.py's simpler flat list did not need.

Eleven invariants enforced across validate() and check_duplicate_keys() (the header count was
already stale at "Seven" before a prior edit -- invariant 8 had already been added without
updating it; fixed then rather than repeated):
  1. every `depends_on` id resolves to a declared mechanism
  2. the dependency graph is acyclic
  3. every mechanism's `layer` is declared in the `layers` block
  4. every `state` is one of the six classes already used by the atlas
  5. every present `verified.instrument` is one of the four known values (TCK-20260915-MECHANISM-
     VERIFICATION-AXIS)
  6. every present `verified.verdict` is one of the three known values, and all four `verified`
     sub-fields (instrument/verdict/date/note) are present when the block itself is present
  7. every present `implemented_by` is a list of strings, each an existing repo-relative path,
     optionally suffixed `::Symbol` (file-level vs symbol-level, TCK-20260916-MECHANISM-
     IMPLEMENTED-BY-SYMBOL-LEVEL-BINDING) or `::Class::method` (method-level, TCK-20260920-
     MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION) -- a real code binding, checked against disk
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
  11. no mapping in the file defines the same key twice (`check_duplicate_keys()`,
      TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION) -- `yaml.safe_load()`
      silently keeps only the LAST value for a duplicate key, which let a stale, pre-edit
      `verified:` block survive undetected through all ten invariants above (they only ever see
      the dict `yaml.safe_load()` already produced, where the duplicate has no trace left).
      Checked separately from `validate()`'s own ten, against the real file path rather than an
      already-parsed dict, since that is the only point where the duplication is still visible.

`validate()` returns a list of human-readable error strings (empty if valid) rather than
raising/returning a bool, so a caller can report every violation in one run instead of stopping at
the first -- "build the failure loud" (this ticket's own Implementation Notes). `check_duplicate_
keys()` (invariant 11) follows the same shape but is a separate function, not folded into
`validate()`'s own body -- see its own docstring for why.

See `docs/plans/status_axis_model.md` for how this module's `VALID_STATES`/`VALID_VERDICTS` axes
relate to the compass's §10 runtime-status vocabulary and the semantic control plane's Rule
realization vocabulary -- the same shape, three deliberately separate axes, never conflated.

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
#
# TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION settles a question left open by
# `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`: symbol-level alone is not fine
# enough when several mechanisms share one multi-concern class (e.g. `LevelingService` implements
# both `xp_leveling` and `skill_unlocks` via different methods; `StrategicIntelligenceSystem`
# implements both `goal_hierarchy` and `strategic_intelligence_core` the same way). A class-level
# binding there would misattribute one mechanism's logic to another's entry -- the same shape of
# error `docs/plans/mechanism_claims_as_tests_initiative.md` §3.2 already catalogues, just from
# imprecision rather than a wrong guess. Decision: extend `implemented_by` one level finer,
# "<path>::<Class>::<method>", rather than leave these permanently unbound -- the recurrence (2
# classes, 4 mechanisms, found within two consecutive coverage batches) crossed the "worth
# building for two mechanisms alone" bar the earlier ticket declined to cross. This is a validator
# capability extension, not a schema change: `implemented_by` is still a list of strings; a third
# `::`-delimited segment is simply matched against the class's own method definitions instead of
# the file's top-level symbols.
_TOP_LEVEL_SYMBOL_RE_TEMPLATE = r"^(?:class|def)\s+{}\b"
_TOP_LEVEL_BOUNDARY_RE = re.compile(r"^(?:class|def)\s+\w+", re.MULTILINE)


def parse_implemented_by_entry(entry: str) -> Tuple[str, Optional[str]]:
    """Splits one `implemented_by` string into (path, symbol_or_None). `symbol` may itself be
    "Class::method" for a method-level binding -- callers pass it whole to
    `symbol_defined_in_file`, which is the one place that distinction is interpreted."""
    if "::" in entry:
        path, symbol = entry.split("::", 1)
        return path, symbol
    return entry, None


def symbol_defined_in_file(path: Path, symbol: str) -> bool:
    """True if `symbol` is a top-level class or module-level function in the real file at path.

    If `symbol` is itself "Class::method", true only if `method` is defined (at any indentation)
    within that top-level class's own body -- a real method-level binding, not just "the class
    exists somewhere in this file."
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if "::" in symbol:
        class_name, method_name = symbol.split("::", 1)
        return _method_defined_in_class(text, class_name, method_name)
    pattern = re.compile(_TOP_LEVEL_SYMBOL_RE_TEMPLATE.format(re.escape(symbol)), re.MULTILINE)
    return bool(pattern.search(text))


def _method_defined_in_class(text: str, class_name: str, method_name: str) -> bool:
    """True if `method_name` is defined inside the body of a real top-level `class_name` in
    `text` -- bounded by the next top-level class/def (or end of file), so a same-named method on
    an unrelated later class can't produce a false match."""
    class_pattern = re.compile(rf"^class\s+{re.escape(class_name)}\b", re.MULTILINE)
    class_match = class_pattern.search(text)
    if not class_match:
        return False
    body_start = class_match.end()
    boundary = _TOP_LEVEL_BOUNDARY_RE.search(text, body_start)
    body = text[body_start: boundary.start()] if boundary else text[body_start:]
    method_pattern = re.compile(rf"^\s+def\s+{re.escape(method_name)}\b", re.MULTILINE)
    return bool(method_pattern.search(body))

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


class DuplicateYamlKeyError(ValueError):
    """Raised by _load_yaml_checking_duplicate_keys when the same key appears twice in one
    mapping. Carries the raw message; check_duplicate_keys() turns it into a normal validate()-
    style error string."""


def _load_yaml_checking_duplicate_keys(path: Path):
    """Loads a YAML file exactly like `yaml.safe_load()`, except it raises
    `DuplicateYamlKeyError` on ANY duplicate key within the same mapping, instead of silently
    keeping the last value.

    TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION's own registry-corruption
    incident: an imprecise edit left `strategic_intelligence_core`'s entry with two
    `implemented_by:` keys and two `verified:` keys inside the same mechanism mapping.
    `yaml.safe_load()` silently resolved both duplicates to their LAST value -- the stale,
    pre-edit one -- so the entry's real `instrument:` field read `code_trace` while every prose
    note in the (correct, first) block claimed `scenario`. All ten of `validate()`'s own
    invariants passed, because by the time `validate()` ever sees the data, the duplicate
    information is already gone -- `data` is just a dict, and a dict cannot represent "this key
    was written twice." The corruption was found only by chance, because one close-out's own
    hand arithmetic happened to disagree with the registry's real count by exactly one. This is a
    fifth way the registry can produce a confident wrong answer, distinct from the four already
    catalogued in `docs/plans/mechanism_claims_as_tests_initiative.md` -- those are all epistemic
    (a search or a judgement went wrong); this one is mechanical (the YAML parser silently chose
    for us, with no judgement involved at all). It cannot be caught downstream of parsing, only
    at parse time itself -- hence this dedicated loader rather than a new check inside
    `validate()`'s own body.

    A mapping is checked independently of its nesting depth: this catches a duplicate top-level
    mechanism field (`implemented_by:` appearing twice) exactly as it would catch a duplicate key
    inside a `verified:` sub-block, since each `MappingNode` PyYAML visits is scanned on its own.
    """
    class _DuplicateKeyCheckingLoader(yaml.SafeLoader):
        pass

    def _construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False):
        mapping: dict = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise DuplicateYamlKeyError(
                    f"duplicate key {key!r} at {path.name}:{key_node.start_mark.line + 1} "
                    "(yaml.safe_load() would silently keep only the LAST occurrence's value)"
                )
            value = loader.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

    _DuplicateKeyCheckingLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
    )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=_DuplicateKeyCheckingLoader)


def check_duplicate_keys(path: Path) -> List[str]:
    """Invariant 11: no mapping in the file (a mechanism's own top-level fields, or any nested
    block like `verified:`) may define the same key twice. Returns a list of error strings
    (empty if clean) in the same shape `validate()`'s own errors use, so a caller can merge the
    two lists. Must be run against a real file path -- unlike `validate()`'s other ten
    invariants, this one is structurally impossible to check from an already-parsed dict, since
    `yaml.safe_load()` has already discarded the duplicate by the time any dict exists."""
    try:
        _load_yaml_checking_duplicate_keys(path)
    except DuplicateYamlKeyError as e:
        return [str(e)]
    return []


def validate(data: dict) -> List[str]:
    """Returns a list of human-readable error strings, empty if valid.

    Only raises for a structurally malformed file (missing top-level keys entirely); every
    business-logic violation (the four invariants) is returned as a string, never raised, so every
    violation in one file is reported in a single run.

    Does NOT include invariant 11 (no duplicate keys within one mapping) -- that check requires
    the real file path, not just the already-parsed `data` dict (see `check_duplicate_keys()`'s
    own docstring for why). Callers with a real path should also call `check_duplicate_keys(path)`
    and merge its errors; `main()` below does this for the real committed file.
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
                kind = "method" if "::" in symbol else "top-level class/function"
                errors.append(
                    f"mechanism '{mid}' implemented_by symbol '{symbol}' not found as a "
                    f"{kind} in '{rel_path}'"
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
    #
    # Invariant 10 (orphan system) is NON-COMPOSITIONAL, unlike every other invariant in this
    # function. Every other invariant here (layers, unaudited_depends_on_edges) is a
    # self-contained property of the `data` dict this function already received: it holds or
    # fails on that dict alone, so it also holds or fails the same way on any valid subset of it.
    # Invariant 10 does not have that property -- "every registered system has >=1 declaring
    # mechanism" is a property of the WHOLE corpus (all mechanisms x all registered systems), not
    # of any individual mechanism or any arbitrary slice of the mechanism list. A synthetic test
    # fixture with 2-3 mechanisms will make most of the 7 real registered systems look orphaned
    # (zero members) even when nothing is wrong, because the fixture was never meant to be a
    # complete corpus in the first place. This is exactly what broke 18 pre-existing, unrelated
    # tests the moment this invariant was added -- fixed by tests/unit/tools/conftest.py's
    # autouse fixture, which patches `_load_system_registry` to return {} by default (zero
    # registered systems => both invariants are vacuously satisfied for any fixture that doesn't
    # mention `systems` at all). Tests that DO want to exercise invariant 9/10 must define their
    # own explicit "registered systems + mechanism list" pair via their own monkeypatch (see
    # `_fixture_registry()` in test_mechanism_registry.py) -- the requirement is a CLOSED universe,
    # not the real one: a small synthetic fixture works fine as long as it is complete and
    # self-contained on its own terms (every system it declares has a member within that same
    # fixture). What breaks the invariant is a PARTIAL slice of a larger universe (e.g. the real
    # 93-mechanism/7-system registry with only 2-3 mechanisms taken out of it), not synthetic data
    # itself. The next person adding a new whole-corpus-shaped invariant here should expect the
    # same non-compositionality and reach for a small closed fixture, not assume it will behave
    # like every invariant that came before it, and not assume real data is required to test it.
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


def _rollup_stats(ids: List[str], by_id: Dict[str, dict]) -> dict:
    """Shared counting logic for one group of mechanism ids (one system, `"unassigned"`, or the
    whole-registry baseline) -- COUNTS only, never a derived verdict or badge
    (TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW AC #1/#5)."""
    n = len(ids)
    bound = sum(1 for i in ids if by_id[i].get("implemented_by"))
    bound_unverified = 0
    runtime_verified = 0
    static_verified = 0
    state_counts: Dict[str, int] = {s: 0 for s in VALID_STATES}
    for i in ids:
        m = by_id[i]
        verified = m.get("verified")
        is_bound = bool(m.get("implemented_by"))
        if verified:
            if verified.get("instrument") in RUNTIME_INSTRUMENTS:
                runtime_verified += 1
            else:
                static_verified += 1
        elif is_bound:
            # Real code binding, real caller located, never confirmed to do anything --
            # peer-review finding (TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW): distinct from
            # "unbound and unverified" (we don't even know where to look) and the CHEAPEST
            # verification target available, since the expensive part -- locating the
            # implementation -- is already done.
            bound_unverified += 1
        state = m.get("state")
        if state in state_counts:
            state_counts[state] += 1
    verified_total = runtime_verified + static_verified
    return {
        "count": n,
        "bound": bound,
        "bound_rate": (bound / n) if n else 0.0,
        "bound_unverified": bound_unverified,
        "runtime_verified": runtime_verified,
        "static_verified": static_verified,
        "verified": verified_total,
        "verified_rate": (verified_total / n) if n else 0.0,
        # TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY. What fraction of this
        # group's own VERIFIED mechanisms were confirmed by a runtime instrument (scenario/
        # corpus_run -- the simulation actually doing the thing) versus a static one (code_trace --
        # the code says it should). Denominator is `verified`, not `count`: this is a property of
        # the verification method used, not of coverage. Added after a real peer-caught gap: a
        # 20-mechanism code_trace-only verification batch moved the registry's own runtime share
        # from 27% to 11% while reading, in prose, as unqualified progress -- the raw
        # runtime_verified/static_verified counts already existed but nothing rendered the RATE, so
        # the regression was invisible until computed by hand under direct challenge. 0.0 (not
        # undefined) when `verified` is 0, matching this file's own established zero-count
        # convention for bound_rate/verified_rate above.
        "runtime_verified_share": (runtime_verified / verified_total) if verified_total else 0.0,
        "unverified": n - verified_total,
        "state_counts": state_counts,
    }


def build_system_rollup(data: dict) -> dict:
    """TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW (child 3 of
    TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP). Per-system COUNTS -- mechanism count,
    `implemented_by`-bound count/rate, verified count/rate (runtime vs static), and a full state
    breakdown -- plus a whole-registry `baseline` computed the same way, so every system's rate is
    read next to the baseline rather than in isolation
    (TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION's own finding: a raw per-system
    percentage looked informative until checked against baseline and found statistically
    indistinguishable from it).

    Never renders or computes a single summary status/badge for a system (AC #1) and never derives
    a ranking or verdict from membership (AC #5, same read-only rule as `mechanisms_by_system()`).
    Read-only query; consumes `mechanisms_by_system()` unmodified rather than re-deriving groups.
    """
    mechanisms = data.get("mechanisms", []) or []
    by_id = {m["id"]: m for m in mechanisms if m.get("id")}
    groups = mechanisms_by_system(data)

    baseline = _rollup_stats(list(by_id.keys()), by_id)

    systems: List[dict] = []
    for system in sorted(k for k in groups if k != "unassigned"):
        systems.append({"system": system, **_rollup_stats(groups[system], by_id)})

    unassigned = {"system": "unassigned", **_rollup_stats(groups.get("unassigned", []), by_id)}

    return {"baseline": baseline, "systems": systems, "unassigned": unassigned}


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else _DEFAULT_PATH

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Invariant 11 first: a duplicate key means `data` above is already unreliable (yaml.safe_load
    # silently kept only the last value), so every other invariant below would be checking
    # corrupted input without knowing it.
    errors = check_duplicate_keys(path)
    errors += validate(data)
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

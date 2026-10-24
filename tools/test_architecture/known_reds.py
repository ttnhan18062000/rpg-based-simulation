"""Shared known-reds registry: schema, loader, matcher and lint for every report that gives a red an owner.

TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE (child 1 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC). The `Slow regression`
report (`slow_regression_report.py`, registry `slow_known_reds.yaml`) gave each failing test an owner, a ticket, ``added_on`` /
``expires_on`` and a kind. The rpg gate report needs the same ownership model for metric ids, so the rules live here once and each
registry is described by a :class:`RegistrySpec`.

Rules (identical for every registry):

* An entry is a mapping with the spec's required fields. ``match`` is an ``fnmatch`` pattern on the id.
* An id resolves to the FIRST entry whose pattern matches (and whose ``state`` matches, for a registry that has states). A later entry
  an earlier, broader one also covers is *shadowed*, and the lint rejects it. Entries in different states never shadow each other.
* An id matching no entry is UNOWNED. One matching an entry whose ``expires_on`` is before today is EXPIRED. An entry matching nothing
  that is failing is a stale mapping.
* An entry of a registry that allows ``cases`` (the rpg gate) may be SCOPED: ``cases: [{world, seed, entity_id?}]``. A scoped entry owns a run-scope
  fail only through :func:`owner_of_finding`, which checks the finding's world, seed and (when a case names one) every example's ``entity_id``.
  The string lookups (:func:`owner_of`, :func:`classify`, :func:`stale_mappings`) never see a scoped entry. A scoped entry never shadows a later
  entry: when its cases do not cover a finding the search goes on, so several scoped entries can share one ``match``.
* ``[`` is rejected in a pattern: ``fnmatch`` reads it as a character class, so an exact parametrized id would never match itself.

Registries:

* :data:`SLOW_SPEC` - ``slow_known_reds.yaml``, top key ``known_reds``; ids are JUnit ``classname::name``; each entry has a ``kind``
  (``broken`` or ``flaky``). Unknown extra fields are tolerated (the file carries a free ``note``).
* :data:`RPG_GATE_SPEC` - ``rpg_gate_known.yaml``, top key ``known``; ids are ``<metric_id>[:<group>]`` (the brackets there mean "optional
  group", not a character class); each entry carries the ``state`` it covers, ``fail`` (a VALIDITY fail needs an owner ticket) or
  ``drift`` (a DRIFT entry's ticket is a *trace* ticket). It has no ``kind``. Unknown fields are rejected so a typo is caught.

Extending a registry: declare another :class:`RegistrySpec` with ``optional_fields`` (for example perf's debt ledger could add
``expected_signature``); the lint then accepts the field and, for a strict registry, still rejects any other. No behaviour here
changes per registry except through the spec.
"""

from __future__ import annotations

import datetime as dt
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

REQUIRED_ENTRY_FIELDS = ("match", "ticket", "owner", "added_on", "expires_on", "kind")
KINDS = ("broken", "flaky")
GATE_STATES = ("fail", "drift")


@dataclass(frozen=True)
class RegistrySpec:
    """What one registry file looks like. ``kinds`` / ``states`` empty means the registry has no such field."""

    name: str
    top_key: str
    required_fields: Tuple[str, ...]
    kinds: Tuple[str, ...] = ()
    states: Tuple[str, ...] = ()
    optional_fields: Tuple[str, ...] = ()
    strict_fields: bool = False

    @property
    def known_fields(self) -> Tuple[str, ...]:
        return tuple(dict.fromkeys((*self.required_fields, *self.optional_fields)))


SLOW_SPEC = RegistrySpec("slow", "known_reds", REQUIRED_ENTRY_FIELDS, kinds=KINDS, optional_fields=("note",))
RPG_GATE_SPEC = RegistrySpec(
    "rpg_gate",
    "known",
    ("match", "ticket", "owner", "added_on", "expires_on", "state"),
    states=GATE_STATES,
    optional_fields=("note", "cases"),
    strict_fields=True,
)
CASE_KEYS = ("world", "seed", "entity_id")


def load_known_reds(path: Optional[Path], spec: RegistrySpec = SLOW_SPEC) -> List[dict]:
    """The entries under ``spec.top_key``; a missing path or file, an empty file or an empty list give ``[]``."""
    if path is None or not Path(path).exists():
        return []
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return list(data.get(spec.top_key) or [])


def lint_known_reds(entries: Sequence[dict], spec: RegistrySpec = SLOW_SPEC) -> List[str]:
    """Problems with the entries (a missing field, a bad date, expires_on before added_on, a bad kind or state, a shadowed entry)."""
    problems: List[str] = []
    for index, entry in enumerate(entries):
        label = entry.get("match", f"entry {index}")
        for name in spec.required_fields:
            if not entry.get(name):
                problems.append(f"{label}: missing {name}")
        if spec.strict_fields:
            for name in entry:
                if name not in spec.known_fields:
                    problems.append(f"{label}: unknown field {name!r}")
        dates = {}
        for name in ("added_on", "expires_on"):
            value = entry.get(name)
            if not value:
                continue
            try:
                dates[name] = dt.date.fromisoformat(str(value))
            except ValueError:
                problems.append(f"{label}: {name} is not an ISO date: {value!r}")
        if len(dates) == 2 and dates["expires_on"] < dates["added_on"]:
            problems.append(f"{label}: expires_on is before added_on")
        if spec.kinds and entry.get("kind") and entry["kind"] not in spec.kinds:
            problems.append(f"{label}: kind must be one of {spec.kinds}, got {entry['kind']!r}")
        if spec.states and entry.get("state") and entry["state"] not in spec.states:
            problems.append(f"{label}: state must be one of {spec.states}, got {entry['state']!r}")
        if "[" in str(entry.get("match", "")):
            # fnmatch reads `[...]` as a character class, so an exact parametrized id such as
            # `t::test_x[5000]` would never match itself and its failure would show as UNOWNED.
            problems.append(f"{label}: '[' is a character class in fnmatch; write the parameter part with '*' or '?' instead")
        if "cases" in entry:
            problems.extend(_lint_cases(label, entry, spec))
    problems.extend(shadowed_entries(entries))
    problems.extend(_overlapping_cases(entries))
    return problems


def _lint_cases(label: object, entry: dict, spec: RegistrySpec) -> List[str]:
    """Problems with one entry's ``cases``: not allowed by this registry, not on a ``fail`` entry, empty, or a malformed case."""
    if "cases" not in spec.optional_fields:
        return [f"{label}: cases is not allowed in the {spec.name} registry"]
    problems: List[str] = []
    if entry.get("state") != "fail":
        problems.append(f"{label}: cases is allowed only on a state: fail entry")
    cases = entry["cases"]
    if not isinstance(cases, list) or not cases:
        return problems + [f"{label}: cases must be a non-empty list"]
    for i, case in enumerate(cases):
        where = f"{label}: cases[{i}]"
        if not isinstance(case, dict):
            problems.append(f"{where} is not a mapping")
            continue
        for key in case:
            if key not in CASE_KEYS:
                problems.append(f"{where}: unknown key {key!r}")
        if not isinstance(case.get("world"), str) or not case.get("world"):
            problems.append(f"{where}: world is required and must be a non-empty string")
        if not isinstance(case.get("seed"), int) or isinstance(case.get("seed"), bool):
            problems.append(f"{where}: seed is required and must be an integer")
        if "entity_id" in case and (case["entity_id"] is None or isinstance(case["entity_id"], (bool, dict, list))):
            problems.append(f"{where}: entity_id must be a scalar when given")
    return problems


def _well_formed_cases(entry: dict) -> List[dict]:
    cases = entry.get("cases")
    if not isinstance(cases, list):
        return []
    return [c for c in cases if isinstance(c, dict) and isinstance(c.get("world"), str) and isinstance(c.get("seed"), int)]


def _cases_overlap(a: dict, b: dict) -> bool:
    if (a["world"], a["seed"]) != (b["world"], b["seed"]):
        return False
    return "entity_id" not in a or "entity_id" not in b or str(a["entity_id"]) == str(b["entity_id"])


def _overlapping_cases(entries: Sequence[dict]) -> List[str]:
    """Two cases (in one entry or two) naming the same (world, seed[, entity_id]) are an error: one fail would have two owners."""
    problems: List[str] = []
    flat = [(i, j, c) for i, e in enumerate(entries) for j, c in enumerate(_well_formed_cases(e))]
    for x in range(len(flat)):
        for y in range(x + 1, len(flat)):
            (i, _, a), (k, _, b) = flat[x], flat[y]
            if entries[i].get("state") == entries[k].get("state") and _cases_overlap(a, b):
                problems.append(
                    f"{entries[k].get('match', f'entry {k}')}: case {b['world']}/{b['seed']}"
                    f"{'/' + str(b['entity_id']) if 'entity_id' in b else ''} overlaps one in {entries[i].get('match', f'entry {i}')!r}"
                )
    return problems


def lint_file(path: Path, spec: RegistrySpec) -> List[str]:
    """Load ``path`` under ``spec`` and lint it; a file that is not a mapping, or whose top key is not a list, is a problem."""
    if not Path(path).exists():
        return [f"{path}: file not found"]
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get(spec.top_key), list):
        return [f"{path}: expected a mapping with a list under {spec.top_key!r}"]
    return lint_known_reds(load_known_reds(path, spec), spec)


def _sample_id(pattern: str) -> str:
    """A concrete id the pattern matches: `*` -> nothing, `?` -> one character (the lint forbids `[` in patterns)."""
    return pattern.replace("*", "").replace("?", "x")


def shadowed_entries(entries: Sequence[dict]) -> List[str]:
    """Entries an id can never reach, because owner_of() returns the first match and an earlier, broader
    pattern also matches the later entry's ids. A catch-all must come after every narrower entry it covers.
    Entries in different states (a registry with a ``state`` field) never shadow each other."""
    problems: List[str] = []
    for later_index, later in enumerate(entries):
        pattern = later.get("match")
        if not pattern:
            continue
        sample = _sample_id(pattern)
        for earlier in entries[:later_index]:
            if earlier.get("state") != later.get("state") or earlier.get("cases"):
                continue
            if earlier.get("match") and fnmatch.fnmatchcase(sample, earlier["match"]):
                problems.append(f"{pattern}: shadowed by the earlier entry {earlier['match']!r}; move it before that entry")
                break
    return problems


def _require_state_when_entries_have_one(known: Sequence[dict], state: Optional[str]) -> None:
    """A registry with states must be asked about a state: an entry of either state would otherwise own an id (a drift entry hiding a fail)."""
    if state is None and any(entry.get("state") for entry in known):
        raise ValueError("this registry has entries with a state; pass state= so only that state's entries are considered")


def owner_of(test_id: str, known: Sequence[dict], state: Optional[str] = None) -> Optional[dict]:
    """The first entry matching ``test_id``; with ``state`` given, only entries covering that state are considered.
    A registry whose entries carry a ``state`` requires it (``ValueError`` otherwise)."""
    _require_state_when_entries_have_one(known, state)
    for entry in known:
        if state is not None and entry.get("state") != state:
            continue
        if entry.get("cases"):
            continue  # a scoped entry owns only a finding it can verify: owner_of_finding
        if fnmatch.fnmatchcase(test_id, entry["match"]):
            return entry
    return None


def _example_ids(examples: Sequence[object]) -> Optional[List[str]]:
    """The ``entity_id`` of every example as a string, or ``None`` when any example has none."""
    ids = []
    for example in examples:
        if not isinstance(example, Mapping) or example.get("entity_id") is None:
            return None
        ids.append(str(example["entity_id"]))
    return ids


def _scoped_entry_owns(entry: dict, finding: Mapping[str, object]) -> bool:
    """Whether a scoped entry's cases cover this finding. Anything that can not be verified is not owned."""
    if finding.get("scope", "run") != "run" or finding.get("seed") is None:
        return False
    here = [c for c in entry["cases"] if c.get("world") == finding.get("world") and c.get("seed") == finding.get("seed")]
    if not here:
        return False
    if any("entity_id" not in c for c in here):
        return True
    examples = list(finding.get("examples") or [])
    violations = finding.get("violations")
    if not isinstance(violations, int) or isinstance(violations, bool) or violations != len(examples) or not examples:
        return False  # an example was cut by the module's cap (or none were given): an unseen entity may be among the violations
    ids = _example_ids(examples)
    return ids is not None and set(ids) <= {str(c["entity_id"]) for c in here}


def owner_of_finding(test_id: str, finding: Mapping[str, object], known: Sequence[dict], state: Optional[str] = None) -> Optional[dict]:
    """The first entry that owns this finding: an unscoped entry matching ``test_id``, or a scoped one whose cases cover it
    (see :func:`_scoped_entry_owns`). A scoped entry that matches but does not cover the finding is skipped, not final."""
    _require_state_when_entries_have_one(known, state)
    for entry in known:
        if state is not None and entry.get("state") != state:
            continue
        if not fnmatch.fnmatchcase(test_id, entry["match"]):
            continue
        if not entry.get("cases") or _scoped_entry_owns(entry, finding):
            return entry
    return None


def is_expired(entry: dict, today: dt.date) -> bool:
    return dt.date.fromisoformat(str(entry["expires_on"])) < today


def days_to_expiry(entry: dict, today: dt.date) -> int:
    return (dt.date.fromisoformat(str(entry["expires_on"])) - today).days


def classify(failing: Mapping[str, str], known: Sequence[dict], today: dt.date, state: Optional[str] = None) -> Tuple[List[str], List[str]]:
    """(UNOWNED ids, EXPIRED ids) among the failing ids; with ``state`` given, only entries of that state own an id."""
    _require_state_when_entries_have_one(known, state)
    unowned, expired = [], []
    for test_id in sorted(failing):
        entry = owner_of(test_id, known, state)
        if entry is None:
            unowned.append(test_id)
        elif is_expired(entry, today):
            expired.append(test_id)
    return unowned, expired


def stale_mappings(failing: Mapping[str, str], known: Sequence[dict], state: Optional[str] = None) -> List[dict]:
    """Entries (of ``state``, when given) that match none of the failing ids."""
    _require_state_when_entries_have_one(known, state)
    return [
        e
        for e in known
        if (state is None or e.get("state") == state) and not e.get("cases") and not any(fnmatch.fnmatchcase(t, e["match"]) for t in failing)
    ]


def stale_cases(findings: Sequence[Mapping[str, object]], known: Sequence[dict], id_of, state: str = "fail") -> List[str]:
    """One label ``<match> <world>/<seed>[/<entity_id>]`` per case of a scoped entry that no failing finding still uses.
    ``id_of(finding)`` gives the finding's ``<metric_id>[:<group>]``. A case with no ``entity_id`` is live when its (world, seed) fails the metric."""
    stale: List[str] = []
    for entry in known:
        if entry.get("state") != state or not entry.get("cases"):
            continue
        live: Dict[Tuple[object, object], set] = {}
        for f in findings:
            if f.get("state") == state and f.get("scope", "run") == "run" and fnmatch.fnmatchcase(id_of(f), entry["match"]):
                live.setdefault((f.get("world"), f.get("seed")), set()).update(_example_ids(list(f.get("examples") or [])) or [])
        for case in entry["cases"]:
            ids = live.get((case.get("world"), case.get("seed")))
            if ids is None or ("entity_id" in case and str(case["entity_id"]) not in ids):
                stale.append(f"{entry['match']} {case.get('world')}/{case.get('seed')}" + (f"/{case['entity_id']}" if "entity_id" in case else ""))
    return stale


def entries_by_state(known: Sequence[dict]) -> Dict[str, List[dict]]:
    """Entries grouped by their ``state`` field (entries without one are grouped under the empty string)."""
    grouped: Dict[str, List[dict]] = {}
    for entry in known:
        grouped.setdefault(entry.get("state", ""), []).append(entry)
    return grouped

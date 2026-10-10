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
    optional_fields=("note",),
    strict_fields=True,
)


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
    problems.extend(shadowed_entries(entries))
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
            if earlier.get("state") != later.get("state"):
                continue
            if earlier.get("match") and fnmatch.fnmatchcase(sample, earlier["match"]):
                problems.append(f"{pattern}: shadowed by the earlier entry {earlier['match']!r}; move it before that entry")
                break
    return problems


def owner_of(test_id: str, known: Sequence[dict], state: Optional[str] = None) -> Optional[dict]:
    """The first entry matching ``test_id``; with ``state`` given, only entries covering that state are considered."""
    for entry in known:
        if state is not None and entry.get("state") != state:
            continue
        if fnmatch.fnmatchcase(test_id, entry["match"]):
            return entry
    return None


def is_expired(entry: dict, today: dt.date) -> bool:
    return dt.date.fromisoformat(str(entry["expires_on"])) < today


def days_to_expiry(entry: dict, today: dt.date) -> int:
    return (dt.date.fromisoformat(str(entry["expires_on"])) - today).days


def classify(failing: Mapping[str, str], known: Sequence[dict], today: dt.date, state: Optional[str] = None) -> Tuple[List[str], List[str]]:
    """(UNOWNED ids, EXPIRED ids) among the failing ids; with ``state`` given, only entries of that state own an id."""
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
    return [
        e
        for e in known
        if (state is None or e.get("state") == state) and not any(fnmatch.fnmatchcase(t, e["match"]) for t in failing)
    ]


def entries_by_state(known: Sequence[dict]) -> Dict[str, List[dict]]:
    """Entries grouped by their ``state`` field (entries without one are grouped under the empty string)."""
    grouped: Dict[str, List[dict]] = {}
    for entry in known:
        grouped.setdefault(entry.get("state", ""), []).append(entry)
    return grouped

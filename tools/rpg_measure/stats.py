"""The pure arithmetic of the paired table: the people set, per-seed differences, the standard error, the verdict and the extinction check.

Everything here reads the typed facts ``arm_child.py`` wrote (start roster, final alive/cause/kind per entity) and nothing else, so it is testable without a run.

* People = the entities of the BASE arm's tick-0 roster whose species keeps coin, matched by id; both arms are read on those same ids (the keeps_coin
  set of the new arm never changes who is counted). Anything that exists at the end but not at tick 0 is "added" and listed apart.
* SE = standard deviation of the per-seed (new - base) difference / sqrt(n_seeds). The base-vs-base spread is only the self-check (must be 0).
* Verdict per world: drift = |mean difference| > 2 * SE AND > floor. The floor's value is the designer's: ``DEFAULT_FLOOR`` is a named placeholder.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set

DEFAULT_FLOOR = 0.0  # PLACEHOLDER: the designer sets the minimum delta that counts as drift; until then every >2 SE drift is reported and the header says the floor is unset
SE_MULTIPLE = 2.0

Run = Mapping[str, Any]


def people_ids(base_start: Sequence[Sequence[Any]]) -> Set[str]:
    """Ids of the base arm's tick-0 roster whose species keeps coin (roster row: id, kind, keeps_coin 0/1, alive 0/1)."""
    return {str(row[0]) for row in base_start if row[2]}


def roster_mismatch(base_start: Sequence[Sequence[Any]], new_start: Sequence[Sequence[Any]]) -> Dict[str, List[Any]]:
    """Ids present in only one arm at tick 0, and ids whose kind or keeps_coin flag differs: the arms did not start from the same world."""
    base, new = {str(r[0]): (r[1], r[2]) for r in base_start}, {str(r[0]): (r[1], r[2]) for r in new_start}
    return {
        "only_base": sorted(set(base) - set(new)), "only_new": sorted(set(new) - set(base)),
        "changed": sorted(i for i in set(base) & set(new) if base[i] != new[i]),
    }


def is_dead(run: Run, entity_id: str) -> bool:
    """True when the entity is dead at the end or no longer exists (a removed entity counts as dead)."""
    row = run["final"].get(str(entity_id))
    return row is None or not row[0]


def people_deaths(run: Run, ids: Iterable[str]) -> int:
    return sum(1 for i in ids if is_dead(run, i))


def added(run: Run) -> List[str]:
    """Ids that exist at the end but were not in the tick-0 roster (born, spawned or added later)."""
    start = {str(r[0]) for r in run["start"]}
    return sorted(i for i in run["final"] if i not in start)


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def standard_error(diffs: Sequence[float]) -> float:
    """SD (n-1) of the per-seed differences / sqrt(n); 0.0 for fewer than two seeds."""
    n = len(diffs)
    if n < 2:
        return 0.0
    m = mean(diffs)
    return math.sqrt(sum((d - m) ** 2 for d in diffs) / (n - 1)) / math.sqrt(n)


def drifts(diffs: Sequence[float], floor: float = DEFAULT_FLOOR) -> bool:
    """The verdict line: |mean difference| > 2 SE AND > floor."""
    m = abs(mean(diffs))
    return m > SE_MULTIPLE * standard_error(diffs) and m > floor


def deaths_by_kind(run: Run, ids: Iterable[str] = None) -> Counter:
    """Dead (or vanished) entities per kind among ``ids`` (default: every entity of the tick-0 roster)."""
    start_kind = {str(r[0]): r[1] for r in run["start"]}
    chosen = list(start_kind) if ids is None else [str(i) for i in ids]
    out: Counter = Counter()
    for i in chosen:
        if is_dead(run, i):
            out[start_kind.get(i) or run["final"].get(i, [0, None, "unknown"])[2]] += 1
    return out


def causes_by_kind(run: Run) -> Counter:
    """``kind|cause`` of every dead entity, the cause read from the typed death record."""
    out: Counter = Counter()
    for row in run["final"].values():
        if not row[0]:
            out[f"{row[2]}|{row[1]}"] += 1
    return out


def alive_by_kind(run: Run) -> Counter:
    out: Counter = Counter()
    for row in run["final"].values():
        if row[0]:
            out[row[2]] += 1
    return out


def extinct_kinds(runs: Sequence[Run]) -> Set[str]:
    """Kinds present at tick 0 in at least one seed that end with 0 alive in every seed."""
    present = {r[1] for run in runs for r in run["start"]}
    alive = [alive_by_kind(run) for run in runs]
    return {k for k in present if all(a.get(k, 0) == 0 for a in alive)}


def extinction_verdict(base_runs: Sequence[Run], new_runs: Sequence[Run]) -> Dict[str, List[str]]:
    """STOP: extinct in the new arm and not in the base. BASE-STATE: extinct in both. (Extinct only in the base is reported as ``recovered``.)"""
    base, new = extinct_kinds(base_runs), extinct_kinds(new_runs)
    return {"stop": sorted(new - base), "base_state": sorted(new & base), "recovered": sorted(base - new)}


def self_check_spread(first: Sequence[Run], second: Sequence[Run]) -> List[str]:
    """Names of the (world, seed) pairs where two runs of the same arm differ in final hash, start hash, or any people/cause/alive fact: must be empty."""
    bad = []
    for a, b in zip(first, second):
        same = (a["final_hash"] == b["final_hash"] and a["start_hash"] == b["start_hash"] and a["final"] == b["final"] and a["counters"] == b["counters"])
        if not same:
            bad.append(f"{a['world']}:{a['seed']}")
    return bad

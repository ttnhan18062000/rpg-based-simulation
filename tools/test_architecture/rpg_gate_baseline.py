"""The rpg gate baseline: a versioned, immutable file with provenance, staleness, a dual reference and a cited re-baseline.

TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS (child 2 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC). Testing owns the
format and the rules here; rpg owns the content (metric ids, groups, values) and the stop lines. This module never names a metric id.
The convention is the mutation baselines' (``tests/mutation/baselines/*_vN.json``): one file per version, never edited after it is written.

File: ``<baselines dir>/rpg_gate_v<N>.json`` (proposed dir ``tests/simulation_quality/rpg_gate/baselines/``). Schema ``rpg-gate-baseline/v1``::

    {"schema": "rpg-gate-baseline/v1", "version": 3, "milestone": "M1",
     "provenance": {"commit_sha": "...", "harness_hash": "...", "worlds": ["w"], "seeds": [1, 2, 3, 4, 5], "ticks": 5000,
                    "recorded_at": "2026-10-11T00:00:00Z", "stale_after": "2026-11-10T00:00:00Z", "cites": ["<ticket, PR, divergence id, memo row>"]},
     "metrics": [
        {"id": "O2.deaths", "class": "outcome", "scope": "run", "world": "w", "group": "guards", "key": "STARVATION", "tick": 5000,
         "per_seed": {"1": 3, "2": 4}, "mean": 3.5, "se": 0.5},
        {"id": "O9.share", "class": "outcome", "scope": "pooled", "world": "w", "group": "*", "value": 0.4},
        {"id": "V1", "class": "validity", "scope": "run", "world": "w", "group": "*", "per_seed": {"1": 0, "2": 0}, "violations": 0}],
     "omitted_validity": [{"row": "V3:run:w:*", "known_match": "V3", "ticket": "TCK-..."}],   # optional
     "rebaseline": null | {"previous_version": 2, "divergence_id": "...", "memo_row": "...", "pr": "#123",
                           "changes": [{"row": "...", "before": 3.0, "after": 3.5}],
                           "stop_lines_crossed": ["R1"], "owner_ruling": {"ref": "<memo row or decision id>", "date": "2026-10-11"}}}

* A row is identified by ``(id, scope, world, group, key, tick)``; ``key`` and ``tick`` are optional. This row key is the pairing key the report
  (child 4) must use to match a run's metric with a baseline row. ``scope`` is ``run`` or ``pooled`` (the metric contract's spelling). A run outcome
  row carries ``per_seed`` values plus their ``mean`` and ``se``; a pooled outcome row carries one ``value`` and no ``per_seed``. A validity row
  carries ``violations`` and, when it is a run row, ``per_seed`` counts.
* ``omitted_validity`` (optional) lists validity rows that failed but are owned in ``rpg_gate_known.yaml`` (``state: fail``) and so were left out of ``metrics`` by the
  candidate builder (``rpg_gate_candidate``); the lint requires ``row``, ``known_match`` and ``ticket`` and rejects a listed row that is still in ``metrics``.
* ``undefined_rows`` (optional) lists pooled shares whose denominator summed to 0 (``{row, reason: "empty_denominator"}``): the candidate leaves them out of ``metrics`` and
  ``rebaseline`` carries the list. A later run in which such a row is defined reads "no reference (undefined at baseline)" against it, never drift; only a re-baseline gives it a reference.
* A baseline holds validity rows only at ``violations == 0``. Validity is absolute (any non-zero value is a FAIL) and is never compared with a
  baseline, so a re-baseline can not normalise a validity fail; the lint, the loader and ``rebaseline()`` all refuse it and no ruling overrides that.
  A known validity fail is owned in ``rpg_gate_known.yaml`` (``state: fail``), never here.
* ``provenance.cites`` is a required, non-empty list on every version. Version 1 cites what justifies it (the metric-set ticket); a later version
  must contain the PR and at least one divergence id or memo row.
* ``version`` 1 has ``rebaseline: null`` (it has no earlier baseline to cite, but ``provenance.cites`` still names its source). Every later version has a re-baseline record: the previous version, a divergence id and/or a memo row,
  the PR, the before/after of every row that changed (computed here from the two files, never typed by hand), the stop lines the new values
  cross and the ``owner_ruling`` those need: a structured ``{ref, date}`` (a memo row or decision id, and an ISO date), never free text. Only the
  owner's ruling counts: a peer's or the designer's message does not, while a designer-recorded memo row the owner confirmed does.

Dual reference (:func:`resolve_references`): a run is reported against the LAST baseline and the FIRST baseline of the current milestone (the
milestone of the last one), so a slow drift that each re-baseline absorbs is still visible.

Staleness (:func:`staleness`): a baseline is stale when it is past ``stale_after``, when its harness hash differs from the current harness
(an unknown current hash counts: it cannot be verified), or when its worlds, seeds or ticks differ from the config (worlds and seeds
compare as sets, so their order does not matter). A stale baseline never
yields a pass (roadmap principle 4); the report (child 4) turns any reason here into the ``stale`` state.

Re-baseline (:func:`rebaseline`, CLI ``rebaseline``): writes version N+1 from a candidate document (same shape as a baseline without ``version`` and
``rebaseline``; ``recorded_at`` defaults to now and ``stale_after`` to ``recorded_at`` plus the config's ``stale_after_days``). It REFUSES without a divergence id and/or memo row plus a PR, REFUSES when a new value crosses a stop line from the config
unless an ``owner_ruling`` is given (or when ``--undecided-world-semantic-change`` is set, which needs the same ruling), and REFUSES when the target file
exists, so an old file is never modified. ``stop_lines`` come from rpg's config (``load_config``)::

    worlds: [w]
    seeds: [1, 2, 3, 4, 5]
    ticks: 5000
    stale_after_days: 30
    stop_lines: [{name: R1, metric: "O2.*", group: "*", min: 0, max: 10}]   # min/max optional; metric and group are fnmatch patterns

Stop lines apply to outcome rows only (never validity). A stop line is crossed when a candidate row's value (the ``mean`` of a run outcome row, the ``value`` of a pooled outcome row) is outside ``[min, max]``. It is checked on every candidate row, not only the changed ones, so a ruling is needed at each re-baseline
while a value stays past the line; that is intended. The config lives at ``tests/simulation_quality/rpg_gate/config.yaml`` and is rpg's. ``group`` is
a property-based kind group (D42), never an EntityRole name; ``metric`` and ``group`` are free fnmatch patterns.

CLI (stdlib plus PyYAML)::

    python -m tools.test_architecture.rpg_gate_baseline lint [--dir DIR]
    python -m tools.test_architecture.rpg_gate_baseline rebaseline --candidate FILE --config FILE [--dir DIR] [--milestone M] [--known FILE]
        [--divergence-id ID] [--memo-row ROW] [--pr REF] [--cite TEXT ...] [--owner-ruling-ref REF --owner-ruling-date YYYY-MM-DD]
        [--undecided-world-semantic-change]
        (version 1 needs at least one --cite; a later version builds its cites from the divergence id, memo row and PR plus any --cite)
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Mapping, Optional, Sequence, Tuple

import yaml

from tools.test_architecture import known_reds

SCHEMA = "rpg-gate-baseline/v1"
DEFAULT_DIR = Path("tests/simulation_quality/rpg_gate/baselines")
FILENAME_RE = re.compile(r"^rpg_gate_v(\d+)\.json$")
CLASSES = ("outcome", "validity")
VALIDITY_ID_RE = re.compile(r"^V\d+$")
PROVENANCE_FIELDS = ("commit_sha", "harness_hash", "worlds", "seeds", "ticks", "recorded_at", "stale_after", "cites")
SCOPES = ("run", "pooled")


class BaselineError(ValueError):
    """A baseline or candidate that cannot be used."""


class RebaselineRefused(BaselineError):
    """A re-baseline the rules do not allow; the message names the rule."""


# ---------------------------------------------------------------- config


@dataclass(frozen=True)
class StopLine:
    name: str
    metric: str
    group: str = "*"
    min: Optional[float] = None
    max: Optional[float] = None


@dataclass(frozen=True)
class GateConfig:
    worlds: Tuple[str, ...]
    seeds: Tuple[int, ...]
    ticks: int
    stale_after_days: int
    stop_lines: Tuple[StopLine, ...] = ()
    required_validity: Mapping[str, Tuple[str, ...]] = field(default_factory=dict)  # level ("run" | "pooled") -> ids required in documents of that level

    def required_at(self, level: str) -> Tuple[str, ...]:
        return tuple(self.required_validity.get(level, ()))


REQUIRED_VALIDITY_LEVELS = ("run", "pooled")


def _load_required_validity(path: Path, raw: Any) -> dict:
    """``{level: [ids]}``. A row is judged at one level (a seed document is ``run``, the pooled document is ``pooled``), so a plain list of ids is refused: it can not
    say which documents must carry which id (TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL)."""
    if isinstance(raw, list):
        raise BaselineError(f"{path}: required_validity must map a level to its ids, for example {{run: [V1, V2], pooled: [V7]}}; a plain list is refused because it does not say which documents carry which id, got {raw!r}")
    if not isinstance(raw, dict):
        raise BaselineError(f"{path}: required_validity must map a level to its ids, for example {{run: [V1, V2], pooled: [V7]}}, got {raw!r}")
    unknown = sorted(str(level) for level in raw if level not in REQUIRED_VALIDITY_LEVELS)
    if unknown:
        raise BaselineError(f"{path}: required_validity has an unknown level {unknown}; the levels are {list(REQUIRED_VALIDITY_LEVELS)}")
    out = {}
    for level, ids in raw.items():
        if not isinstance(ids, list):
            raise BaselineError(f"{path}: required_validity[{level}] must be a list of validity row ids, got {ids!r}")
        for rid in ids:
            if not isinstance(rid, str) or not VALIDITY_ID_RE.match(rid):
                raise BaselineError(f"{path}: required_validity[{level}] entry {rid!r} is not a validity row id of the form V<n>")
        if len(set(ids)) != len(ids):
            raise BaselineError(f"{path}: required_validity[{level}] has a duplicate: {ids!r}")
        out[level] = tuple(ids)
    return out


def load_config(path: Path) -> GateConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    for name in ("worlds", "seeds", "ticks", "stale_after_days"):
        if name not in data:
            raise BaselineError(f"{path}: config is missing {name!r}")
    for name in ("worlds", "seeds"):
        if len(set(data[name])) != len(data[name]):
            raise BaselineError(f"{path}: {name} has a duplicate: {data[name]!r}")
    required = _load_required_validity(path, data.get("required_validity", {}))
    lines = []
    for raw in data.get("stop_lines") or []:
        if not raw.get("name") or not raw.get("metric"):
            raise BaselineError(f"{path}: a stop line needs a name and a metric: {raw!r}")
        lines.append(StopLine(raw["name"], raw["metric"], raw.get("group", "*"), raw.get("min"), raw.get("max")))
    return GateConfig(
        tuple(data["worlds"]), tuple(data["seeds"]), int(data["ticks"]), int(data["stale_after_days"]), tuple(lines), required,
    )


# ---------------------------------------------------------------- rows


def row_key(row: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (row.get("id"), row.get("scope"), row.get("world"), row.get("group"), row.get("key"), row.get("tick"))


def row_label(row: Mapping[str, Any]) -> str:
    return ":".join(str(p) for p in row_key(row) if p is not None)


def row_value(row: Mapping[str, Any]) -> Optional[float]:
    """The single number a row stands for: the mean of a run outcome row, the value of a pooled one, the violations of a validity row."""
    if row.get("class") != "outcome":
        return row.get("violations")
    return row.get("value") if row.get("scope") == "pooled" else row.get("mean")


def _parse_time(value: Any) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("no timezone")
    return parsed


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------- lint


def lint_baseline(doc: Any, filename: Optional[str] = None) -> List[str]:
    """Problems with one baseline document (and, with ``filename``, with its name not matching its version)."""
    if not isinstance(doc, dict):
        return ["not a JSON object"]
    problems: List[str] = []
    if doc.get("schema") != SCHEMA:
        problems.append(f"schema must be {SCHEMA!r}, got {doc.get('schema')!r}")
    version = doc.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        problems.append(f"version must be an integer >= 1, got {version!r}")
    elif filename is not None:
        match = FILENAME_RE.match(filename)
        if not match:
            problems.append(f"file name {filename!r} is not rpg_gate_v<N>.json")
        elif int(match.group(1)) != version:
            problems.append(f"file name {filename!r} does not match version {version}")
    if not doc.get("milestone"):
        problems.append("missing milestone")
    problems.extend(_lint_provenance(doc.get("provenance")))
    if "owner_ruling" in doc and _ruling_problem(doc["owner_ruling"]):
        problems.append(_ruling_problem(doc["owner_ruling"]))
    problems.extend(_lint_metrics(doc.get("metrics")))
    problems.extend(_lint_omitted_validity(doc.get("omitted_validity"), doc.get("metrics")))
    problems.extend(_lint_undefined_rows(doc.get("undefined_rows"), doc.get("metrics")))
    problems.extend(_lint_rebaseline(doc.get("rebaseline"), version, (doc.get("provenance") or {}).get("cites")))
    return problems


def _lint_provenance(prov: Any) -> List[str]:
    if not isinstance(prov, dict):
        return ["missing provenance"]
    problems = [f"provenance: missing {name}" for name in PROVENANCE_FIELDS if prov.get(name) in (None, "", [])]
    for name in ("recorded_at", "stale_after"):
        if prov.get(name):
            try:
                _parse_time(prov[name])
            except ValueError:
                problems.append(f"provenance: {name} is not a timezone-aware ISO time: {prov[name]!r}")
    if not problems and _parse_time(prov["stale_after"]) <= _parse_time(prov["recorded_at"]):
        problems.append("provenance: stale_after is not after recorded_at")
    if prov.get("cites") and not (isinstance(prov["cites"], list) and all(isinstance(c, str) and c.strip() for c in prov["cites"])):
        problems.append("provenance: cites must be a list of non-empty strings")
    if prov.get("ticks") is not None and not (isinstance(prov["ticks"], int) and prov["ticks"] > 0):
        problems.append("provenance: ticks must be a positive integer")
    return problems


def _lint_metrics(metrics: Any) -> List[str]:
    if not isinstance(metrics, list) or not metrics:
        return ["metrics must be a non-empty list"]
    problems: List[str] = []
    seen = set()
    for index, row in enumerate(metrics):
        if not isinstance(row, dict):
            problems.append(f"metrics[{index}]: not an object")
            continue
        label = row_label(row) or f"metrics[{index}]"
        for name in ("id", "class", "scope", "world", "group"):
            if not row.get(name):
                problems.append(f"{label}: missing {name}")
        if row_key(row) in seen:
            problems.append(f"{label}: duplicate row")
        seen.add(row_key(row))
        klass, scope = row.get("class"), row.get("scope")
        if klass not in CLASSES:
            problems.append(f"{label}: class must be one of {CLASSES}, got {klass!r}")
            continue
        if scope is not None and scope not in SCOPES:
            problems.append(f"{label}: scope must be one of {SCOPES}, got {scope!r}")
        per_seed = row.get("per_seed")
        if per_seed is not None and not (isinstance(per_seed, dict) and all(_is_number(v) for v in per_seed.values())):
            problems.append(f"{label}: per_seed must map a seed to a number")
        if scope == "pooled" and per_seed is not None:
            problems.append(f"{label}: a pooled row has no per_seed")
        if klass == "outcome" and scope == "pooled":
            if not _is_number(row.get("value")):
                problems.append(f"{label}: a pooled outcome row needs a numeric value")
        elif klass == "outcome":
            if not per_seed:
                problems.append(f"{label}: a run outcome row needs per_seed")
            for name in ("mean", "se"):
                if not _is_number(row.get(name)):
                    problems.append(f"{label}: an outcome row needs a numeric {name}")
            if _is_number(row.get("se")) and row["se"] < 0:
                problems.append(f"{label}: se is negative")
        else:
            violations = row.get("violations")
            if not (isinstance(violations, int) and not isinstance(violations, bool)):
                problems.append(f"{label}: a validity row needs an integer violations")
            elif violations != 0:
                problems.append(f"{label}: a baseline holds validity rows at 0 violations; a validity fail is owned in rpg_gate_known.yaml, never normalised here")
            elif per_seed and sum(per_seed.values()) != violations:
                problems.append(f"{label}: violations {violations} is not the sum of per_seed {sum(per_seed.values())}")
    return problems


def _lint_omitted_validity(omitted: Any, metrics: Any) -> List[str]:
    """``omitted_validity`` lists validity rows that failed but were owned in ``rpg_gate_known.yaml`` and so left out of ``metrics``; each needs a row label,
    the ``known_match`` pattern and the ``ticket`` that owns it, and a listed row must not also be in ``metrics`` (a baseline never holds a validity fail)."""
    if omitted is None:
        return []
    if not isinstance(omitted, list):
        return ["omitted_validity must be a list"]
    present = {row_label(r) for r in metrics if isinstance(r, dict)} if isinstance(metrics, list) else set()
    problems: List[str] = []
    for index, entry in enumerate(omitted):
        if not isinstance(entry, dict):
            problems.append(f"omitted_validity[{index}]: not an object")
            continue
        for name in ("row", "known_match", "ticket"):
            if not entry.get(name):
                problems.append(f"omitted_validity[{index}]: missing {name}")
        if entry.get("row") in present:
            problems.append(f"omitted_validity[{index}]: {entry['row']} is listed as omitted but is still in metrics")
    return problems


def _lint_undefined_rows(undefined: Any, metrics: Any) -> List[str]:
    """``undefined_rows`` lists pooled shares the module marked undefined (``reason: empty_denominator``) and the candidate left out of ``metrics``; each needs a ``row`` label
    and a ``reason``, and a listed row must not also be in ``metrics``."""
    if undefined is None:
        return []
    if not isinstance(undefined, list):
        return ["undefined_rows must be a list"]
    present = {row_label(r) for r in metrics if isinstance(r, dict)} if isinstance(metrics, list) else set()
    problems: List[str] = []
    for index, entry in enumerate(undefined):
        if not isinstance(entry, dict):
            problems.append(f"undefined_rows[{index}]: not an object")
            continue
        for name in ("row", "reason"):
            if not entry.get(name):
                problems.append(f"undefined_rows[{index}]: missing {name}")
        if entry.get("row") in present:
            problems.append(f"undefined_rows[{index}]: {entry['row']} is listed as undefined but is still in metrics")
    return problems


def _ruling_problem(ruling: Any) -> Optional[str]:
    if not isinstance(ruling, dict) or not ruling.get("ref") or not ruling.get("date"):
        return "owner_ruling must be {ref, date}, not free text"
    try:
        dt.date.fromisoformat(str(ruling["date"]))
    except ValueError:
        return f"owner_ruling date is not an ISO date: {ruling['date']!r}"
    return None


def _lint_rebaseline(record: Any, version: Any, cites: Any = None) -> List[str]:
    if version == 1:
        return [] if record is None else ["version 1 must have rebaseline null"]
    if not isinstance(record, dict):
        return ["a version after 1 needs a rebaseline record"]
    problems = []
    if record.get("previous_version") != (version - 1 if isinstance(version, int) else None):
        problems.append(f"rebaseline: previous_version must be {version - 1 if isinstance(version, int) else '?'}")
    if not (record.get("divergence_id") or record.get("memo_row")):
        problems.append("rebaseline: needs a divergence_id and/or a memo_row")
    if not record.get("pr"):
        problems.append("rebaseline: missing pr")
    if isinstance(cites, list):
        if record.get("pr") and record["pr"] not in cites:
            problems.append("rebaseline: provenance.cites must contain the PR")
        if not any(c in cites for c in (record.get("divergence_id"), record.get("memo_row")) if c):
            problems.append("rebaseline: provenance.cites must contain a divergence id or memo row")
    if not isinstance(record.get("changes"), list):
        problems.append("rebaseline: changes must be a list")
    if record.get("stop_lines_crossed") or record.get("undecided_world_semantic_change") or record.get("owner_ruling"):
        problem = _ruling_problem(record.get("owner_ruling"))
        if problem:
            problems.append(f"rebaseline: {problem} (needed for a stop line or an undecided world-semantic change)")
    return problems


def lint_dir(directory: Path) -> List[str]:
    """Lint every ``*.json`` in ``directory`` (a missing directory has no baselines yet), plus the version sequence having no gap."""
    directory = Path(directory)
    if not directory.exists():
        return []
    problems: List[str] = []
    versions: List[int] = []
    for path in sorted(directory.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: invalid JSON ({exc})")
            continue
        problems.extend(f"{path.name}: {p}" for p in lint_baseline(doc, path.name))
        if isinstance(doc, dict) and isinstance(doc.get("version"), int):
            versions.append(doc["version"])
    if versions and sorted(versions) != list(range(1, max(versions) + 1)):
        problems.append(f"versions are not 1..{max(versions)} without a gap: {sorted(versions)}")
    return problems


# ---------------------------------------------------------------- loader


def load_baselines(directory: Path) -> List[dict]:
    """Every valid baseline in ``directory``, oldest version first. An invalid file raises: a gate must not guess which file is the baseline."""
    directory = Path(directory)
    docs = []
    if directory.exists():
        for path in directory.glob("*.json"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            problems = lint_baseline(doc, path.name)
            if problems:
                raise BaselineError(f"{path.name}: {'; '.join(problems)}")
            docs.append(doc)
    return sorted(docs, key=lambda d: d["version"])


@dataclass(frozen=True)
class References:
    """The two baselines a run is compared with. They are the same document when the milestone has one baseline so far."""

    last: dict
    milestone_first: dict


def resolve_references(baselines: Sequence[dict]) -> Optional[References]:
    """The last baseline and the first baseline of the last one's milestone; ``None`` when there is no baseline (the report's no-data state)."""
    if not baselines:
        return None
    ordered = sorted(baselines, key=lambda d: d["version"])
    last = ordered[-1]
    first = next(d for d in ordered if d["milestone"] == last["milestone"])
    return References(last=last, milestone_first=first)


# ---------------------------------------------------------------- staleness


@dataclass(frozen=True)
class Staleness:
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def stale(self) -> bool:
        return bool(self.reasons)


def staleness(baseline: Mapping[str, Any], now: dt.datetime, current_harness_hash: Optional[str], config: GateConfig) -> Staleness:
    """Why ``baseline`` cannot be trusted now; no reasons means it is current. An unverifiable fact is a reason, never a pass."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    prov = baseline["provenance"]
    reasons: List[str] = []
    if now >= _parse_time(prov["stale_after"]):
        reasons.append(f"past stale_after {prov['stale_after']}")
    if not current_harness_hash:
        reasons.append("the current harness hash is unknown, so the baseline's cannot be verified")
    elif prov["harness_hash"] != current_harness_hash:
        reasons.append(f"harness hash differs (baseline {prov['harness_hash']}, current {current_harness_hash})")
    for name, wanted in (("worlds", list(config.worlds)), ("seeds", list(config.seeds)), ("ticks", config.ticks)):
        have = prov[name]
        if (set(have) != set(wanted)) if name != "ticks" else (have != wanted):
            reasons.append(f"{name} differ (baseline {prov[name]}, config {wanted})")
    return Staleness(tuple(reasons))


# ---------------------------------------------------------------- re-baseline


def stop_lines_crossed(rows: Sequence[Mapping[str, Any]], stop_lines: Sequence[StopLine]) -> List[str]:
    """Names of the stop lines some row's value is outside of (each name once, in config order)."""
    crossed: List[str] = []
    for line in stop_lines:
        for row in rows:
            value = row_value(row)
            if row.get("class") != "outcome" or value is None or not fnmatch.fnmatchcase(str(row.get("id")), line.metric) or not fnmatch.fnmatchcase(str(row.get("group")), line.group):
                continue
            if (line.min is not None and value < line.min) or (line.max is not None and value > line.max):
                crossed.append(line.name)
                break
    return crossed


def changes_between(previous: Sequence[Mapping[str, Any]], candidate: Sequence[Mapping[str, Any]]) -> List[dict]:
    """Before/after of every row whose value differs, plus rows that appear or disappear (a missing side is ``None``)."""
    before = {row_key(r): r for r in previous}
    after = {row_key(r): r for r in candidate}
    out = []
    for key in sorted(set(before) | set(after), key=lambda k: tuple("" if p is None else str(p) for p in k)):
        old = row_value(before[key]) if key in before else None
        new = row_value(after[key]) if key in after else None
        if old != new:
            out.append({"row": row_label(before.get(key) or after[key]), "before": old, "after": new})
    return out


def rebaseline(
    candidate: Mapping[str, Any],
    config: GateConfig,
    directory: Path,
    *,
    pr: Optional[str],
    divergence_id: Optional[str] = None,
    memo_row: Optional[str] = None,
    owner_ruling: Optional[Mapping[str, str]] = None,
    cites: Sequence[str] = (),
    undecided_world_semantic_change: bool = False,
    now: Optional[dt.datetime] = None,
    milestone: Optional[str] = None,
    known: Optional[Sequence[dict]] = None,
    today: Optional[dt.date] = None,
) -> Path:
    """Write the next version from ``candidate`` and return its path, or raise :class:`RebaselineRefused`. Never modifies an existing file.
    A candidate marked ``evidence_only`` (from a branch-ref dispatch) is refused; ``milestone`` overrides the candidate's. A candidate that omitted owned validity
    fails needs ``known`` (the current ``rpg_gate_known.yaml`` entries): each omission's ``known_match`` must still be a ``state: fail`` entry and not expired."""
    directory = Path(directory)
    if candidate.get("evidence_only"):
        raise RebaselineRefused("this candidate is evidence only (a branch-ref dispatch); a baseline is recorded from a main run's candidate")
    for omitted in candidate.get("omitted_validity") or []:
        if known is None:
            raise RebaselineRefused("this candidate omitted owned validity fails; pass the current rpg_gate_known.yaml (--known) so each owner can be re-checked")
        entry = next((e for e in known if e.get("match") == omitted.get("known_match") and e.get("state") == "fail"), None)
        if entry is None:
            raise RebaselineRefused(f"omitted validity row {omitted.get('row')}: its owner entry {omitted.get('known_match')!r} is no longer a state: fail entry in rpg_gate_known.yaml")
        if known_reds.is_expired(entry, today or dt.datetime.now(dt.timezone.utc).date()):
            raise RebaselineRefused(f"omitted validity row {omitted.get('row')}: its owner entry {entry['match']!r} expired on {entry['expires_on']}")
    existing = load_baselines(directory)
    if existing and not (divergence_id or memo_row):
        raise RebaselineRefused("a re-baseline needs a divergence id and/or a memo row")
    if existing and not pr:
        raise RebaselineRefused("a re-baseline needs the PR that makes the change")
    version = existing[-1]["version"] + 1 if existing else 1
    rows = candidate.get("metrics") or []
    crossed = stop_lines_crossed(rows, config.stop_lines)
    if (crossed or undecided_world_semantic_change) and not owner_ruling:
        why = f"crosses stop line(s) {crossed}" if crossed else "carries an undecided world-semantic change"
        raise RebaselineRefused(f"this re-baseline {why}; it needs an owner_ruling {{ref, date}}")
    if owner_ruling and _ruling_problem(owner_ruling):
        raise RebaselineRefused(_ruling_problem(owner_ruling))
    now = now or dt.datetime.now(dt.timezone.utc)
    prov = dict(candidate.get("provenance") or {})
    prov["cites"] = list(dict.fromkeys([*cites, *(c for c in (pr, divergence_id, memo_row) if c)]))
    if not prov["cites"]:
        raise RebaselineRefused("a baseline needs at least one cite (--cite); version 1 cites the metric-set ticket")
    prov.setdefault("recorded_at", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    if "stale_after" not in prov:
        prov["stale_after"] = (_parse_time(prov["recorded_at"]) + dt.timedelta(days=config.stale_after_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc: dict = {
        "schema": SCHEMA,
        "version": version,
        "milestone": milestone or candidate.get("milestone"),
        "provenance": prov,
        "metrics": list(rows),
        "rebaseline": None,
    }
    if candidate.get("omitted_validity"):
        doc["omitted_validity"] = list(candidate["omitted_validity"])
    if candidate.get("undefined_rows"):
        doc["undefined_rows"] = list(candidate["undefined_rows"])
    if owner_ruling and not existing:
        doc["owner_ruling"] = dict(owner_ruling)  # version 1 has no rebaseline record to hold it
        doc["stop_lines_crossed"] = crossed
    if existing:
        doc["rebaseline"] = {
            "previous_version": existing[-1]["version"],
            **({"divergence_id": divergence_id} if divergence_id else {}),
            **({"memo_row": memo_row} if memo_row else {}),
            "pr": pr,
            "changes": changes_between(existing[-1]["metrics"], rows),
            "stop_lines_crossed": crossed,
            **({"owner_ruling": dict(owner_ruling)} if owner_ruling else {}),
            **({"undecided_world_semantic_change": True} if undecided_world_semantic_change else {}),
        }
    problems = lint_baseline(doc, f"rpg_gate_v{version}.json")
    if problems:
        raise BaselineError("; ".join(problems))
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"rpg_gate_v{version}.json"
    with target.open("x", encoding="utf-8") as handle:  # "x": an existing file is an error, never overwritten
        json.dump(doc, handle, indent=2)
        handle.write("\n")
    return target


# ---------------------------------------------------------------- CLI


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    lint = sub.add_parser("lint")
    lint.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    reb = sub.add_parser("rebaseline")
    reb.add_argument("--candidate", type=Path, required=True)
    reb.add_argument("--config", type=Path, required=True)
    reb.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    reb.add_argument("--milestone", help="the milestone id (overrides the candidate's; the workflow's candidate has none)")
    reb.add_argument("--known", type=Path, help="rpg_gate_known.yaml; required when the candidate omitted owned validity fails")
    reb.add_argument("--divergence-id")
    reb.add_argument("--memo-row")
    reb.add_argument("--pr")
    reb.add_argument("--cite", action="append", default=[])
    reb.add_argument("--owner-ruling-ref")
    reb.add_argument("--owner-ruling-date")
    reb.add_argument("--undecided-world-semantic-change", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "lint":
        problems = lint_dir(args.dir)
        for problem in problems:
            print(problem)
        return 1 if problems else 0
    try:
        target = rebaseline(
            json.loads(args.candidate.read_text(encoding="utf-8")),
            load_config(args.config),
            args.dir,
            pr=args.pr,
            divergence_id=args.divergence_id,
            memo_row=args.memo_row,
            owner_ruling={"ref": args.owner_ruling_ref, "date": args.owner_ruling_date} if (args.owner_ruling_ref or args.owner_ruling_date) else None,
            cites=args.cite,
            undecided_world_semantic_change=args.undecided_world_semantic_change,
            milestone=args.milestone,
            known=known_reds.load_known_reds(args.known, known_reds.RPG_GATE_SPEC) if args.known else None,
        )
    except BaselineError as exc:
        print(f"REFUSED: {exc}" if isinstance(exc, RebaselineRefused) else f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

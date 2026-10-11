"""The rpg gate baseline: a versioned, immutable file with provenance, staleness, a dual reference and a cited re-baseline.

TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS (child 2 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC). Testing owns the
format and the rules here; rpg owns the content (metric ids, groups, values) and the stop lines. This module never names a metric id.
The convention is the mutation baselines' (``tests/mutation/baselines/*_vN.json``): one file per version, never edited after it is written.

File: ``<baselines dir>/rpg_gate_v<N>.json`` (proposed dir ``tests/simulation_quality/rpg_gate/baselines/``). Schema ``rpg-gate-baseline/v1``::

    {"schema": "rpg-gate-baseline/v1", "version": 3, "milestone": "M1",
     "provenance": {"commit_sha": "...", "harness_hash": "...", "worlds": ["w"], "seeds": [1, 2, 3, 4, 5], "ticks": 5000,
                    "recorded_at": "2026-10-11T00:00:00Z", "stale_after": "2026-11-10T00:00:00Z"},
     "metrics": [
        {"id": "O2.deaths", "class": "outcome", "world": "w", "group": "guards", "key": "STARVATION", "tick": 5000,
         "per_seed": {"1": 3, "2": 4}, "mean": 3.5, "se": 0.5},
        {"id": "V1", "class": "validity", "world": "w", "group": "*", "per_seed": {"1": 0, "2": 0}, "violations": 0}],
     "rebaseline": null | {"previous_version": 2, "divergence_id": "...", "memo_row": "...", "pr": "#123",
                           "changes": [{"row": "...", "before": 3.0, "after": 3.5}],
                           "stop_lines_crossed": ["R1"], "owner_ruling": "..."}}

* A row is identified by ``(id, world, group, key, tick)``; ``key`` and ``tick`` are optional. An outcome row carries ``per_seed`` values plus
  their ``mean`` and ``se``; a validity row carries ``per_seed`` violation counts (a pooled row has none per seed) and the total ``violations``.
* ``version`` 1 has ``rebaseline: null`` (it has no earlier baseline to cite). Every later version has a re-baseline record: the previous version, a divergence id and/or a memo row,
  the PR, the before/after of every row that changed (computed here from the two files, never typed by hand), the stop lines the new values
  cross and the ``owner_ruling`` those need.

Dual reference (:func:`resolve_references`): a run is reported against the LAST baseline and the FIRST baseline of the current milestone (the
milestone of the last one), so a slow drift that each re-baseline absorbs is still visible.

Staleness (:func:`staleness`): a baseline is stale when it is past ``stale_after``, when its harness hash differs from the current harness
(an unknown current hash counts: it cannot be verified), or when its worlds, seeds or ticks differ from the config. A stale baseline never
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

A stop line is crossed when a candidate row's value (the ``mean`` of an outcome row, the ``violations`` of a validity row) is outside ``[min, max]``.

CLI (stdlib plus PyYAML)::

    python -m tools.test_architecture.rpg_gate_baseline lint [--dir DIR]
    python -m tools.test_architecture.rpg_gate_baseline rebaseline --candidate FILE --config FILE [--dir DIR]
        (--divergence-id ID | --memo-row ROW) --pr REF [--owner-ruling TEXT] [--undecided-world-semantic-change]
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

SCHEMA = "rpg-gate-baseline/v1"
DEFAULT_DIR = Path("tests/simulation_quality/rpg_gate/baselines")
FILENAME_RE = re.compile(r"^rpg_gate_v(\d+)\.json$")
CLASSES = ("outcome", "validity")
PROVENANCE_FIELDS = ("commit_sha", "harness_hash", "worlds", "seeds", "ticks", "recorded_at", "stale_after")


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


def load_config(path: Path) -> GateConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    for name in ("worlds", "seeds", "ticks", "stale_after_days"):
        if name not in data:
            raise BaselineError(f"{path}: config is missing {name!r}")
    lines = []
    for raw in data.get("stop_lines") or []:
        if not raw.get("name") or not raw.get("metric"):
            raise BaselineError(f"{path}: a stop line needs a name and a metric: {raw!r}")
        lines.append(StopLine(raw["name"], raw["metric"], raw.get("group", "*"), raw.get("min"), raw.get("max")))
    return GateConfig(tuple(data["worlds"]), tuple(data["seeds"]), int(data["ticks"]), int(data["stale_after_days"]), tuple(lines))


# ---------------------------------------------------------------- rows


def row_key(row: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (row.get("id"), row.get("world"), row.get("group"), row.get("key"), row.get("tick"))


def row_label(row: Mapping[str, Any]) -> str:
    return ":".join(str(p) for p in row_key(row) if p is not None)


def row_value(row: Mapping[str, Any]) -> Optional[float]:
    """The single number a row stands for: the mean of an outcome row, the total violations of a validity row."""
    return row.get("mean") if row.get("class") == "outcome" else row.get("violations")


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
    problems.extend(_lint_metrics(doc.get("metrics")))
    problems.extend(_lint_rebaseline(doc.get("rebaseline"), version))
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
        for name in ("id", "class", "world", "group"):
            if not row.get(name):
                problems.append(f"{label}: missing {name}")
        if row_key(row) in seen:
            problems.append(f"{label}: duplicate row")
        seen.add(row_key(row))
        klass = row.get("class")
        if klass not in CLASSES:
            problems.append(f"{label}: class must be one of {CLASSES}, got {klass!r}")
            continue
        per_seed = row.get("per_seed")
        if per_seed is not None and not (isinstance(per_seed, dict) and all(_is_number(v) for v in per_seed.values())):
            problems.append(f"{label}: per_seed must map a seed to a number")
        if klass == "outcome":
            if not per_seed:
                problems.append(f"{label}: an outcome row needs per_seed")
            for name in ("mean", "se"):
                if not _is_number(row.get(name)):
                    problems.append(f"{label}: an outcome row needs a numeric {name}")
            if _is_number(row.get("se")) and row["se"] < 0:
                problems.append(f"{label}: se is negative")
        else:
            violations = row.get("violations")
            if not (isinstance(violations, int) and not isinstance(violations, bool) and violations >= 0):
                problems.append(f"{label}: a validity row needs a non-negative integer violations")
            elif per_seed and sum(per_seed.values()) != violations:
                problems.append(f"{label}: violations {violations} is not the sum of per_seed {sum(per_seed.values())}")
    return problems


def _lint_rebaseline(record: Any, version: Any) -> List[str]:
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
    if not isinstance(record.get("changes"), list):
        problems.append("rebaseline: changes must be a list")
    if record.get("stop_lines_crossed") and not record.get("owner_ruling"):
        problems.append("rebaseline: crosses a stop line without an owner_ruling")
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
        if prov[name] != wanted:
            reasons.append(f"{name} differ (baseline {prov[name]}, config {wanted})")
    return Staleness(tuple(reasons))


# ---------------------------------------------------------------- re-baseline


def stop_lines_crossed(rows: Sequence[Mapping[str, Any]], stop_lines: Sequence[StopLine]) -> List[str]:
    """Names of the stop lines some row's value is outside of (each name once, in config order)."""
    crossed: List[str] = []
    for line in stop_lines:
        for row in rows:
            value = row_value(row)
            if value is None or not fnmatch.fnmatchcase(str(row.get("id")), line.metric) or not fnmatch.fnmatchcase(str(row.get("group")), line.group):
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
    owner_ruling: Optional[str] = None,
    undecided_world_semantic_change: bool = False,
    now: Optional[dt.datetime] = None,
) -> Path:
    """Write the next version from ``candidate`` and return its path, or raise :class:`RebaselineRefused`. Never modifies an existing file."""
    directory = Path(directory)
    existing = load_baselines(directory)
    if existing and not (divergence_id or memo_row):
        raise RebaselineRefused("a re-baseline needs a divergence id and/or a memo row")
    if existing and not pr:
        raise RebaselineRefused("a re-baseline needs the PR that makes the change")
    version = existing[-1]["version"] + 1 if existing else 1
    rows = candidate.get("metrics") or []
    crossed = stop_lines_crossed(rows, config.stop_lines)
    if existing and (crossed or undecided_world_semantic_change) and not owner_ruling:
        why = f"crosses stop line(s) {crossed}" if crossed else "carries an undecided world-semantic change"
        raise RebaselineRefused(f"this re-baseline {why}; it needs an owner_ruling")
    now = now or dt.datetime.now(dt.timezone.utc)
    prov = dict(candidate.get("provenance") or {})
    prov.setdefault("recorded_at", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    if "stale_after" not in prov:
        prov["stale_after"] = (_parse_time(prov["recorded_at"]) + dt.timedelta(days=config.stale_after_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc: dict = {
        "schema": SCHEMA,
        "version": version,
        "milestone": candidate.get("milestone"),
        "provenance": prov,
        "metrics": list(rows),
        "rebaseline": None,
    }
    if existing:
        doc["rebaseline"] = {
            "previous_version": existing[-1]["version"],
            **({"divergence_id": divergence_id} if divergence_id else {}),
            **({"memo_row": memo_row} if memo_row else {}),
            "pr": pr,
            "changes": changes_between(existing[-1]["metrics"], rows),
            "stop_lines_crossed": crossed,
            **({"owner_ruling": owner_ruling} if owner_ruling else {}),
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
    reb.add_argument("--divergence-id")
    reb.add_argument("--memo-row")
    reb.add_argument("--pr")
    reb.add_argument("--owner-ruling")
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
            owner_ruling=args.owner_ruling,
            undecided_world_semantic_change=args.undecided_world_semantic_change,
        )
    except BaselineError as exc:
        print(f"REFUSED: {exc}" if isinstance(exc, RebaselineRefused) else f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

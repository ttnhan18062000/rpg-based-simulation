"""Build a baseline candidate from a harness run's metric documents, so a baseline is recorded from a real run and never typed.

TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS (child 6 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC). ``rebaseline()`` in
``rpg_gate_baseline`` writes ``rpg_gate_vN.json`` from a *candidate*: the baseline shape without ``version``, ``rebaseline`` and the fields it fills itself
(``recorded_at``, ``stale_after``, ``cites``). The harness writes ``rpg-gate-metrics/v1`` documents (one per (world, seed) plus one pooled per world); this
module turns them into that candidate. It is a separate module (not a ``rpg_gate_baseline`` subcommand) because the baseline module never reads harness
documents and must stay importable by the report without them.

Input: the harness output directory (``<world>__s<seed>.json``, ``<world>__pooled.json``) and the config (worlds, seeds, ticks). Output, deterministic for the
same inputs (sorted keys, rows sorted by their key)::

    {"schema": "rpg-gate-baseline/v1", "milestone": "M0" (optional),
     "provenance": {"commit_sha", "harness_hash", "worlds", "seeds", "ticks"},
     "metrics": [run outcome   {id, class, scope: run, world, group, key?, tick?, per_seed, mean, se, k, floor},
                 pooled outcome {id, class, scope: pooled, world, group, key?, tick?, value, floor},
                 run validity   {id, class, scope: run, world, group, per_seed, violations: 0, oracle},
                 pooled validity {id, class, scope: pooled, world, group, violations: 0, oracle}]}

``se`` is the sample standard deviation over the seeds divided by sqrt(n), the estimator the report uses for paired differences. The report pairs per seed
and never reads a baseline's ``se``, so it is provenance only.

A candidate is never partial. :func:`build_candidate` raises :class:`CandidateRefused` (naming the document and the rule) when:

* a document is missing, unexpected for the config's worlds and seeds, unreadable, or ``no-data`` (any reason: a baseline can not be recorded from a run that did not run);
* the documents disagree on ``sha`` or ``harness_hash`` (or ``sha`` differs from ``commit_sha`` when one is given);
* a document's ``ticks`` or ``world`` / ``seed`` differs from the config or its file name;
* a validity row has ``violations > 0`` with no current owner, or no integer ``violations`` / no ``oracle``. A baseline holds validity rows at 0 only, and
  validity is judged absolutely on every run, never against a baseline. So a row that fails but has a current, unexpired ``state: fail`` entry in
  ``rpg_gate_known.yaml`` (``known_reds.owner_of``, matched by ``<metric_id>[:<group>]``) is OMITTED from the candidate (all its seeds and its pooled row)
  and listed in ``omitted_validity: [{row, known_match, ticket}]``; without that, one owned fail would block the whole baseline and every outcome drift
  behind it. An unowned or expired fail still refuses;
* ``k``, ``floor`` or ``oracle`` disagree across the documents for one (id, group), or an outcome row lacks its numeric ``k`` / ``floor`` / value;
* a run outcome row is not present in every seed of its world, or the config has fewer than 2 seeds (no standard error).

``evidence_only`` marks a candidate from a branch-ref dispatch: ``rebaseline()`` refuses it, because only a main run is a baseline source.

CLI::

    python -m tools.test_architecture.rpg_gate_candidate --config FILE --docs DIR --known FILE --out FILE [--milestone M] [--commit-sha SHA] [--evidence-only]

Exit 0 and the file written, or exit 2 and the refusal on stderr (nothing written).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import datetime as dt

from tools.test_architecture import known_reds
from tools.test_architecture.rpg_gate_baseline import SCHEMA, BaselineError, GateConfig, load_config, row_label
from tools.test_architecture.rpg_gate_report import metric_test_id

DOC_RE = re.compile(r"^(?P<world>.+)__(?:s(?P<seed>-?\d+)|pooled)\.json$")
MIN_SEEDS = 2


class CandidateRefused(BaselineError):
    """The documents can not make a candidate; the message names the document and the rule."""


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _expected_names(config: GateConfig) -> Dict[str, Tuple[str, Optional[int]]]:
    names: Dict[str, Tuple[str, Optional[int]]] = {}
    for world in config.worlds:
        for seed in config.seeds:
            names[f"{world}__s{seed}.json"] = (world, seed)
        names[f"{world}__pooled.json"] = (world, None)
    return names


def _load(docs_dir: Path, config: GateConfig) -> Dict[Tuple[str, Optional[int]], dict]:
    docs_dir = Path(docs_dir)
    expected = _expected_names(config)
    present = {p.name for p in docs_dir.glob("*.json") if DOC_RE.match(p.name)} if docs_dir.is_dir() else set()
    extra = sorted(present - set(expected))
    if extra:
        raise CandidateRefused(f"matrix mismatch: {extra[0]} is not a (world, seed) of the config (worlds {list(config.worlds)}, seeds {list(config.seeds)})")
    docs: Dict[Tuple[str, Optional[int]], dict] = {}
    for name, key in expected.items():
        path = docs_dir / name
        if not path.is_file():
            raise CandidateRefused(f"matrix mismatch: {name} is missing; a candidate needs every (world, seed) and every pooled document of the config")
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise CandidateRefused(f"{name}: not valid JSON ({exc})") from exc
        if not isinstance(doc, dict):
            raise CandidateRefused(f"{name}: not a JSON object")
        if doc.get("status") != "ok":
            raise CandidateRefused(f"{name}: no-data ({doc.get('reason', 'unknown reason')}): a baseline can not be recorded from a run without data")
        if (doc.get("world"), doc.get("seed")) != (key[0], key[1]):
            raise CandidateRefused(f"{name}: records world {doc.get('world')!r} seed {doc.get('seed')!r}, not {key[0]!r} seed {key[1]!r}")
        if doc.get("ticks") != config.ticks:
            raise CandidateRefused(f"{name}: ran {doc.get('ticks')!r} ticks, the config says {config.ticks}")
        docs[key] = doc
    return docs


def _single(docs: Mapping[Any, dict], field: str, what: str) -> str:
    values = {doc.get(field) for doc in docs.values()}
    if len(values) != 1 or not next(iter(values)):
        by_doc = sorted(f"{doc['world']}/{doc.get('seed', 'pooled')}={doc.get(field)}" for doc in docs.values())
        raise CandidateRefused(f"documents disagree on {what}: {', '.join(by_doc)}")
    return next(iter(values))


def _thresholds(docs: Mapping[Any, dict]) -> None:
    """k, floor and oracle must be one value per (id, group) across all documents."""
    seen: Dict[Tuple[str, str], Tuple[Any, Any, Any]] = {}
    for key, doc in sorted(docs.items(), key=lambda kv: (kv[0][0], -1 if kv[0][1] is None else kv[0][1])):
        name = f"{key[0]}__s{key[1]}.json" if key[1] is not None else f"{key[0]}__pooled.json"
        for row in doc["metrics"]:
            ident = (row.get("id"), row.get("group", "*"))
            triple = (row.get("k"), row.get("floor"), row.get("oracle"))
            if row.get("class") == "outcome" and row.get("scope") != "pooled" and not (_is_number(row.get("k")) and _is_number(row.get("floor"))):
                raise CandidateRefused(f"{name}: outcome row {ident[0]} has no numeric k and floor (the metric module must carry them)")
            if row.get("class") == "outcome" and row.get("scope") == "pooled" and not _is_number(row.get("floor")):
                raise CandidateRefused(f"{name}: pooled outcome row {ident[0]} has no numeric floor")
            if ident in seen and seen[ident] != triple:
                raise CandidateRefused(f"{name}: threshold mismatch for {ident[0]}: k/floor/oracle {triple} differ from {seen[ident]} in an earlier document (mixed metric module versions)")
            seen.setdefault(ident, triple)


def _validity(row: Mapping[str, Any], name: str) -> Tuple[int, str]:
    violations = row.get("violations")
    if not isinstance(violations, int) or isinstance(violations, bool) or violations < 0:
        raise CandidateRefused(f"{name}: validity row {row.get('id')} has no integer violations")
    if not row.get("oracle"):
        raise CandidateRefused(f"{name}: validity row {row.get('id')} has no oracle to cite")
    return violations, row["oracle"]


def _omissions(docs: Mapping[Any, dict], config: GateConfig, known: Sequence[dict], today: dt.date) -> Dict[Tuple[str, str, str], dict]:
    """``(world, id, group) -> known entry`` for every validity row that fails and is owned; an unowned or expired fail refuses the candidate."""
    omitted: Dict[Tuple[str, str, str], dict] = {}
    for key, doc in docs.items():
        name = f"{key[0]}__s{key[1]}.json" if key[1] is not None else f"{key[0]}__pooled.json"
        for row in doc["metrics"]:
            if row.get("class") != "validity":
                continue
            violations, _ = _validity(row, name)
            if violations == 0:
                continue
            group = row.get("group", "*")
            entry = known_reds.owner_of(metric_test_id({"id": row["id"], "group": group}), known, state="fail")
            if entry is None:
                raise CandidateRefused(f"{name}: validity row {row['id']} has {violations} violation(s) and no owner in rpg_gate_known.yaml (state: fail); a baseline holds validity rows at 0, so the fail must be owned or fixed first")
            if known_reds.is_expired(entry, today):
                raise CandidateRefused(f"{name}: validity row {row['id']} has {violations} violation(s) and its owner entry {entry['match']!r} expired on {entry['expires_on']}")
            omitted[(key[0], row["id"], group)] = entry
    return omitted


def _sort_key(row: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (row["world"], row["scope"], row["id"], row["group"], str(row.get("key", "")), -1 if row.get("tick") is None else row["tick"])


def build_candidate(
    docs_dir: Path,
    config: GateConfig,
    known: Sequence[dict],
    *,
    milestone: Optional[str] = None,
    commit_sha: Optional[str] = None,
    evidence_only: bool = False,
    today: Optional[dt.date] = None,
) -> dict:
    """The candidate for ``docs_dir`` under ``config`` and the ``state: fail`` registry ``known``, or raise :class:`CandidateRefused`."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    if len(config.seeds) < MIN_SEEDS:
        raise CandidateRefused(f"the config has {len(config.seeds)} seed(s); a run outcome row needs at least {MIN_SEEDS} for a standard error")
    docs = _load(docs_dir, config)
    sha = _single(docs, "sha", "the commit sha")
    hhash = _single(docs, "harness_hash", "the harness hash")
    if commit_sha and commit_sha != sha:
        raise CandidateRefused(f"the documents are from {sha}, not the requested commit {commit_sha}")
    _thresholds(docs)
    omitted = _omissions(docs, config, known, today)
    omitted_rows: List[dict] = []

    def omit(row: Mapping[str, Any], world: str, scope: str) -> bool:
        entry = omitted.get((world, row["id"], row.get("group", "*")))
        if entry is None:
            return False
        label = row_label({"id": row["id"], "scope": scope, "world": world, "group": row.get("group", "*")})
        if not any(o["row"] == label for o in omitted_rows):
            omitted_rows.append({"row": label, "known_match": entry["match"], "ticket": entry["ticket"]})
        return True

    rows: List[dict] = []
    for world in config.worlds:
        run_rows: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
        for seed in config.seeds:
            name = f"{world}__s{seed}.json"
            for row in docs[(world, seed)]["metrics"]:
                ident = (row["id"], row.get("group", "*"), row.get("key"), row.get("tick"))
                if row.get("class") == "validity":
                    if omit(row, world, "run"):
                        continue
                    violations, oracle = _validity(row, name)
                    entry = run_rows.setdefault(("validity", *ident), {"oracle": oracle, "per_seed": {}})
                    entry["per_seed"][seed] = violations
                elif row.get("class") == "outcome":
                    value = row.get("value") if _is_number(row.get("value")) else row.get("mean")
                    if not _is_number(value):
                        raise CandidateRefused(f"{name}: outcome row {row['id']} has no numeric value or mean")
                    entry = run_rows.setdefault(("outcome", *ident), {"k": row["k"], "floor": row["floor"], "per_seed": {}})
                    entry["per_seed"][seed] = value
        for (klass, mid, group, key, tick), entry in run_rows.items():
            missing = [s for s in config.seeds if s not in entry["per_seed"]]
            if missing:
                raise CandidateRefused(f"{world}: row {mid} (group {group}) is absent from seed(s) {missing}; every seed must report the same rows")
            base: Dict[str, Any] = {"id": mid, "class": klass, "scope": "run", "world": world, "group": group}
            if key is not None:
                base["key"] = key
            if tick is not None:
                base["tick"] = tick
            per_seed = {str(s): entry["per_seed"][s] for s in config.seeds}
            values = list(entry["per_seed"].values())
            if klass == "validity":
                rows.append({**base, "per_seed": per_seed, "violations": sum(values), "oracle": entry["oracle"]})
            else:
                rows.append({**base, "per_seed": per_seed, "mean": statistics.fmean(values), "se": statistics.stdev(values) / math.sqrt(len(values)),
                             "k": entry["k"], "floor": entry["floor"]})
        for row in docs[(world, None)]["metrics"]:
            name = f"{world}__pooled.json"
            base = {"id": row["id"], "class": row.get("class"), "scope": "pooled", "world": world, "group": row.get("group", "*")}
            for field in ("key", "tick"):
                if row.get(field) is not None:
                    base[field] = row[field]
            if row.get("class") == "validity":
                if omit(row, world, "pooled"):
                    continue
                violations, oracle = _validity(row, name)
                rows.append({**base, "violations": violations, "oracle": oracle})
            elif row.get("class") == "outcome":
                if not _is_number(row.get("value")):
                    raise CandidateRefused(f"{name}: pooled outcome row {row['id']} has no numeric value")
                rows.append({**base, "value": row["value"], "floor": row["floor"]})
    if not rows:
        raise CandidateRefused("the documents carry no metric rows")
    rows.sort(key=_sort_key)
    candidate: Dict[str, Any] = {
        "schema": SCHEMA,
        "provenance": {"commit_sha": sha, "harness_hash": hhash, "worlds": list(config.worlds), "seeds": list(config.seeds), "ticks": config.ticks},
        "metrics": rows,
    }
    if omitted_rows:
        candidate["omitted_validity"] = sorted(omitted_rows, key=lambda o: o["row"])
    if milestone:
        candidate["milestone"] = milestone
    if evidence_only:
        candidate["evidence_only"] = True
    return candidate


def dump_candidate(candidate: Mapping[str, Any]) -> str:
    return json.dumps(candidate, sort_keys=True, indent=2) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--docs", type=Path, required=True)
    parser.add_argument("--known", type=Path, required=True, help="rpg_gate_known.yaml: owned validity fails are omitted and recorded")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--milestone")
    parser.add_argument("--commit-sha")
    parser.add_argument("--evidence-only", action="store_true", help="mark the candidate as evidence from a branch-ref dispatch; rebaseline refuses it")
    args = parser.parse_args(argv)
    try:
        candidate = build_candidate(args.docs, load_config(args.config), known_reds.load_known_reds(args.known, known_reds.RPG_GATE_SPEC), milestone=args.milestone, commit_sha=args.commit_sha, evidence_only=args.evidence_only)
    except BaselineError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dump_candidate(candidate), encoding="utf-8")
    print(f"wrote {args.out} ({len(candidate['metrics'])} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

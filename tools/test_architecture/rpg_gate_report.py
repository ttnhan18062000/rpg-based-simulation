"""The rpg gate report: evaluate the harness documents, rerun the same SHA once on a non-pass, and report six states.

TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN (child 4 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC). Testing owns the rules here; rpg owns the
metric ids, ``k``, the floors and the oracles. Those thresholds travel on the metric rows themselves (outcome rows carry ``k`` and ``floor``, validity rows an
``oracle``), so the report reads only the documents, never imports ``src/`` and has no threshold table of its own; the harness hash covers them through the
metrics module's source. The config holds only the run matrix, ``stale_after_days`` and the stop lines.

States of one finding:

* ``pass``: a validity metric with 0 violations, or an outcome metric inside its band against every reference.
* ``fail`` (VALIDITY only): ``violations > 0`` (exact; up to 5 examples). ``run``-scope validity is judged per (world, seed); ``pooled``-scope per world from
  the pooled document.
* ``drift`` (OUTCOME only, "trace the cause"; never a fail on its own): paired by ``(id, group, key, tick)`` across seeds (per world); the per-seed difference
  against a reference baseline has mean ``d`` and standard error ``se``; drift when ``|d| > k * se`` AND ``|d| > floor(id)`` (the floor applies to every key and
  tick of that id). A ``pooled`` outcome row has one value and no standard error, so it drifts on ``|d| > floor`` alone. A run outcome row without a numeric
  ``k`` and ``floor`` (a pooled one without ``floor``) is a contract error: ``no-data`` with the reason, never a made-up threshold. Every row with the same
  ``(id, group)`` must carry the same ``k``, ``floor`` and ``oracle`` across all documents of the run set; a mismatch is ``no-data`` with the reason
  "mixed metric module versions". Each outcome result shows the seeds it was judged on ("judged on 3/5 seeds"); at least 2 paired seeds are needed.
  Both references are always reported: the LAST baseline and the FIRST baseline of the current milestone (child 2). Drift against either is drift.
* ``stale``: the reference baseline is stale (child 2's :func:`staleness`); a stale baseline never yields a pass.
* ``no-data``: the run (or its pooled document) has no data, the outcome has fewer than two paired seeds, there is no baseline row, there is no baseline, or the
  rows break the contract. A document without data says why (its ``reason``): ``run_error`` (an exception in the simulation; an rpg DEFECT, shown prominently in
  the summary even though it does not turn the job red), ``metric_error`` (an exception in rpg's compute or pool), ``harness_error`` (timeout, bad document,
  child never started) or ``seed_no_data``.
* ``unstable``: a ``fail`` or ``drift`` that the same-SHA rerun did not reproduce. Routed to test infrastructure (roadmap §4.5, nondeterminism), not to the feature team.

Every document's ``harness_hash`` must equal the current harness hash and the documents must agree with each other; otherwise they are ``no-data`` with the
reason "documents from another harness version". A validity row without an integer ``violations`` or without an ``oracle`` (the report must cite it), and an
outcome row without a numeric value or mean, are likewise contract errors (``no-data``), never a pass and never a crash.

Same-SHA rerun: when the first pass has any ``fail`` or ``drift``, the affected (world, seed) set is rerun ONCE (fresh processes, via the ``rerun`` callable) and
evaluated again; a finding whose state differs the second time becomes ``unstable``. A run-scope validity ``fail`` reruns its seed; everything else reruns every
seed of its world.

Ownership (child 1's registry, ``rpg_gate_known.yaml``, ids ``<metric_id>`` or ``<metric_id>:<group>``): a ``fail`` is ``known`` (an owner, not expired),
``unowned`` or ``expired``; a ``drift`` is ``traced`` (a ``state: drift`` entry, whose ticket is a trace ticket) or ``needs-trace-ticket`` (advisory) or ``expired``.
Entries matching no current fail/drift are listed as stale mappings.

Verdict (for CI): ``red`` only for an unowned or expired ``fail``, or for ``unstable``; a drift never makes the job red, and neither do ``stale`` / ``no-data``
(they are visible in the summary and the counts).

Output: a JSON report (``rpg-gate-report/v1``) and a markdown summary (:func:`render_markdown`) with states per metric, both references, the examples and the
cited oracle per validity metric (from the config).

CLI::

    python -m tools.test_architecture.rpg_gate_report --config FILE --docs DIR --baselines DIR --known FILE --out-json FILE --out-md FILE
        [--metrics-module MOD] [--sha SHA] [--no-rerun] [--fail-on-red]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from tools.test_architecture import known_reds
from tools.test_architecture.rpg_gate_baseline import GateConfig, References, load_baselines, load_config, resolve_references, staleness

SCHEMA = "rpg-gate-report/v1"
PASS, FAIL, DRIFT, STALE, NO_DATA, UNSTABLE = "pass", "fail", "drift", "stale", "no-data", "unstable"
STATES = (PASS, FAIL, DRIFT, UNSTABLE, STALE, NO_DATA)
NO_DATA_REASONS = ("run_error", "metric_error", "harness_error", "seed_no_data", "contract_error")
MAX_EXAMPLES = 5
TEST_INFRA = "test-infrastructure"

Docs = Dict[Tuple[str, Optional[int]], dict]  # (world, seed) -> per-run document; (world, None) -> the pooled document
Rerun = Callable[[Sequence[Tuple[str, int]]], Docs]


# ---------------------------------------------------------------- helpers


def metric_test_id(finding: Mapping[str, Any]) -> str:
    """The id the ownership registry matches: ``<metric_id>`` or ``<metric_id>:<group>``."""
    return finding["id"] if finding.get("group") in (None, "*") else f"{finding['id']}:{finding['group']}"


def finding_key(f: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (f["world"], f["scope"], f["id"], f.get("group"), f.get("key"), f.get("tick"), f.get("seed"))


def load_documents(directory: Path, config: GateConfig) -> Docs:
    """Read the harness output for the configured worlds and seeds; a document that is missing is simply absent (it reports as ``no-data``)."""
    docs: Docs = {}
    for world in config.worlds:
        for seed in (*config.seeds, None):
            path = Path(directory) / (f"{world}__s{seed}.json" if seed is not None else f"{world}__pooled.json")
            if path.is_file():
                docs[(world, seed)] = json.loads(path.read_text(encoding="utf-8"))
    return docs


def _no_data(world: str, seed: Optional[int], detail: str, reason: str = "harness_error") -> dict:
    scope = "run" if seed is not None else "pooled"
    return {"world": world, "scope": scope, "id": "*", "group": "*", "class": "run", "state": NO_DATA, "reason": reason, "detail": detail, **({"seed": seed} if seed is not None else {})}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _threshold_problems(docs: Docs) -> Dict[Tuple[str, str, str], str]:
    """``(world, id, group) -> reason`` for rows that break the threshold contract: an outcome row without a numeric ``k`` / ``floor`` (a pooled one needs only the
    floor), or rows of one (world, id, group) that disagree on ``k``, ``floor`` or ``oracle`` across that world's documents (floors may differ between worlds; the row key carries the world)."""
    seen: Dict[Tuple[str, str, str], set] = {}
    problems: Dict[Tuple[str, str, str], str] = {}
    for (world, _seed), doc in docs.items():
        if doc.get("status") != "ok":
            continue
        for row in doc["metrics"]:
            key = (world, row["id"], row.get("group", "*"))
            if row.get("class") == "outcome":
                pooled = row.get("scope") == "pooled"
                need = ("floor", "value") if pooled else ("k", "floor")
                missing = [n for n in need if not _is_number(row.get(n))]
                if not pooled and not (_is_number(row.get("value")) or _is_number(row.get("mean"))):
                    missing.append("value")
                if missing:
                    problems[key] = f"contract error: outcome row without a numeric {' and '.join(missing)}"
            elif row.get("class") == "validity":
                violations = row.get("violations")
                if not isinstance(violations, int) or isinstance(violations, bool) or violations < 0:
                    problems[key] = "contract error: validity row without an integer violations count"
                elif not row.get("oracle"):
                    problems[key] = "contract error: validity row without an oracle to cite"
            seen.setdefault(key, set()).add((row.get("k"), row.get("floor"), row.get("oracle")))
    for key, versions in seen.items():
        if len(versions) > 1:
            problems[key] = "mixed metric module versions"
    return problems


# ---------------------------------------------------------------- evaluation


def _validity(row: Mapping[str, Any], world: str, seed: Optional[int], config: GateConfig) -> dict:
    violations = row["violations"]
    finding = {
        "world": world, "scope": row.get("scope", "run"), "id": row["id"], "group": row.get("group", "*"), "class": "validity",
        "state": FAIL if violations > 0 else PASS, "violations": violations,
    }
    if seed is not None:
        finding["seed"] = seed
    if violations > 0:
        finding["examples"] = list(row.get("examples") or [])[:MAX_EXAMPLES]
    if row.get("oracle"):
        finding["oracle"] = row["oracle"]
    return finding


def _baseline_row(baseline: Mapping[str, Any], row: Mapping[str, Any], world: str) -> Optional[dict]:
    for candidate in baseline["metrics"]:
        if (candidate.get("id"), candidate.get("scope"), candidate.get("world"), candidate.get("group"), candidate.get("key"), candidate.get("tick")) == (
            row["id"], row.get("scope", "run"), world, row.get("group", "*"), row.get("key"), row.get("tick"),
        ):
            return candidate
    return None


def _compare(label: str, baseline: Mapping[str, Any], reasons: Sequence[str], row_values: Mapping[str, Any], cur_row: Mapping[str, Any], world: str, config: GateConfig) -> dict:
    """The outcome of one reference for one outcome metric: ``{"ref", "version", "state", ...numbers}``."""
    result: Dict[str, Any] = {"ref": label, "version": baseline["version"]}
    if reasons:
        return {**result, "state": STALE, "reasons": list(reasons)}
    base = _baseline_row(baseline, cur_row, world)
    if base is None:
        return {**result, "state": NO_DATA, "detail": "no row for this metric in the baseline"}
    pooled = cur_row.get("scope") == "pooled"
    floor, k = base.get("floor"), base.get("k")
    if not _is_number(floor) or (not pooled and not _is_number(k)):  # the reference's own thresholds judge it; never the candidate's (TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD)
        return {**result, "state": NO_DATA, "reason": "contract_error", "detail": "reference row has no recorded threshold"}
    moved = _threshold_moved(cur_row, base, pooled)
    extra = {"threshold_moved": moved} if moved else {}
    if pooled:
        diff = row_values["value"] - base["value"]
        return {**result, "state": DRIFT if abs(diff) > floor else PASS, "diff": diff, "floor": floor, **extra}
    base_seeds = base.get("per_seed") or {}
    diffs = [row_values["per_seed"][seed] - base_seeds[str(seed)] for seed in sorted(row_values["per_seed"]) if str(seed) in base_seeds]
    if len(diffs) < 2:
        return {**result, "state": NO_DATA, "n": len(diffs), "of": len(config.seeds), "detail": f"judged on {len(diffs)}/{len(config.seeds)} seeds; at least 2 are needed for a standard error", **extra}
    mean = statistics.fmean(diffs)
    se = statistics.stdev(diffs) / math.sqrt(len(diffs))
    drift = abs(mean) > k * se and abs(mean) > floor
    return {**result, "state": DRIFT if drift else PASS, "diff": mean, "se": se, "k": k, "floor": floor, "threshold": k * se, "n": len(diffs), "of": len(config.seeds), **extra}


def _threshold_moved(cur_row: Mapping[str, Any], base: Mapping[str, Any], pooled: bool) -> Dict[str, Dict[str, Any]]:
    """``{field: {"candidate": c, "reference": r}}`` for each of ``k`` / ``floor`` / ``oracle`` that differs between the candidate and the reference row. Reported, never
    used to judge. ``oracle`` is compared whenever either side carries one (a missing side is ``None``); ``k`` is not part of a pooled row."""
    moved: Dict[str, Dict[str, Any]] = {}
    for name in ("floor",) if pooled else ("k", "floor"):
        if cur_row.get(name) != base.get(name):
            moved[name] = {"candidate": cur_row.get(name), "reference": base.get(name)}
    if (cur_row.get("oracle") or base.get("oracle")) and cur_row.get("oracle") != base.get("oracle"):
        moved["oracle"] = {"candidate": cur_row.get("oracle"), "reference": base.get("oracle")}
    return moved


def _outcome(cur_row: dict, world: str, refs: Optional[References], reasons_by_version: Mapping[int, Sequence[str]], config: GateConfig) -> dict:
    finding = {"world": world, "scope": cur_row.get("scope", "run"), "id": cur_row["id"], "group": cur_row.get("group", "*"), "class": "outcome"}
    for name in ("key", "tick"):
        if cur_row.get(name) is not None:
            finding[name] = cur_row[name]
    if refs is None:
        return {**finding, "state": NO_DATA, "detail": "no baseline exists", "refs": []}
    results = [
        _compare(label, base, reasons_by_version.get(base["version"], ()), cur_row, cur_row, world, config)
        for label, base in (("last", refs.last), ("milestone-first", refs.milestone_first))
    ]
    states = {r["state"] for r in results}
    state = DRIFT if DRIFT in states else STALE if STALE in states else NO_DATA if NO_DATA in states else PASS
    if state == NO_DATA:  # a contract error of a reference must reach the no-data tally; when the state is DRIFT or STALE the per-reference text still names it
        broken = next((r for r in results if r["state"] == NO_DATA and r.get("reason") == "contract_error"), None)
        if broken is not None:
            return {**finding, "state": state, "reason": "contract_error", "detail": broken["detail"], "refs": results}
    return {**finding, "state": state, "refs": results}


def _contract_no_data(world: str, row: Mapping[str, Any], seed: Optional[int], detail: str) -> dict:
    finding = {"world": world, "scope": row.get("scope", "run"), "id": row["id"], "group": row.get("group", "*"), "class": row.get("class", "outcome"),
               "state": NO_DATA, "reason": "contract_error", "detail": detail}
    if seed is not None:
        finding["seed"] = seed
    for name in ("key", "tick"):
        if row.get(name) is not None:
            finding[name] = row[name]
    return finding


def _check_harness_versions(docs: Docs, current: str) -> Docs:
    """Documents from another harness version are ``no-data`` (contract error): each document's ``harness_hash`` must equal the current one (when known) and
    the documents must agree with each other."""
    hashes = {d.get("harness_hash") for d in docs.values() if d.get("status") == "ok"}
    if len(hashes) <= 1 and (not current or hashes <= {current}):
        return docs
    bad = (lambda d: d.get("harness_hash") != current) if current else (lambda d: True)
    return {k: ({**d, "status": "no-data", "reason": "contract_error", "metrics": [], "error": "documents from another harness version"} if d.get("status") == "ok" and bad(d) else d)
            for k, d in docs.items()}


def evaluate(docs: Docs, config: GateConfig, refs: Optional[References], reasons_by_version: Mapping[int, Sequence[str]], harness_hash: str = "") -> List[dict]:
    """Findings for every metric of every (world, seed) / world in ``docs``; nothing is guessed for a missing document or a contract error (it is ``no-data``)."""
    findings: List[dict] = []
    docs = _check_harness_versions(docs, harness_hash)
    problems = _threshold_problems(docs)

    def validity(row: Mapping[str, Any], world: str, seed: Optional[int]) -> dict:
        problem = problems.get((world, row["id"], row.get("group", "*")))
        return _contract_no_data(world, row, seed, problem) if problem else _validity(row, world, seed, config)

    def missing_required(doc: Mapping[str, Any], world: str, seed: Optional[int]) -> List[dict]:
        """A validity row the config requires at this document's level (``run`` for a seed document, ``pooled`` for the pooled one) but the document leaves out is ``no-data``, never a pass: a metric module that drops a check must not look clean."""
        present = {r.get("id") for r in doc["metrics"] if r.get("class") == "validity"}
        return [{**_contract_no_data(world, {"id": rid, "class": "validity", "scope": "pooled" if seed is None else "run", "group": "*"}, seed, f"required validity row {rid} missing"),
                 "required_missing": True}
                for rid in config.required_at("pooled" if seed is None else "run") if rid not in present]

    for world in config.worlds:
        seed_docs = {seed: docs.get((world, seed)) for seed in config.seeds}
        all_ok = True
        for seed, doc in seed_docs.items():
            if doc is None or doc.get("status") != "ok":
                all_ok = False
                findings.append(_no_data(world, seed, (doc or {}).get("error", "no document"), (doc or {}).get("reason", "harness_error")))
                continue
            findings.extend(validity(r, world, seed) for r in doc["metrics"] if r.get("class") == "validity")  # judged from the seeds that have data
            findings.extend(missing_required(doc, world, seed))
        pooled = docs.get((world, None))
        if pooled is None or pooled.get("status") != "ok":
            findings.append(_no_data(world, None, (pooled or {}).get("error", "no pooled document"), (pooled or {}).get("reason", "harness_error")))
        else:
            findings.extend(validity(r, world, None) for r in pooled["metrics"] if r.get("class") == "validity")
            findings.extend(missing_required(pooled, world, None))
            for r in pooled["metrics"]:
                if r.get("class") == "outcome":
                    problem = problems.get((world, r["id"], r.get("group", "*")))
                    findings.append(_contract_no_data(world, r, None, problem) if problem else _outcome(r, world, refs, reasons_by_version, config))
        if not all_ok:
            continue  # a partial seed set would change what an outcome means; the missing seeds already report as no-data
        grouped: Dict[Tuple[Any, ...], dict] = {}
        for seed, doc in seed_docs.items():
            for r in doc["metrics"]:
                if r.get("class") == "outcome":
                    key = (r["id"], r.get("group", "*"), r.get("key"), r.get("tick"))
                    row = grouped.setdefault(key, {"id": r["id"], "group": r.get("group", "*"), "key": r.get("key"), "tick": r.get("tick"), "scope": "run",
                                                   "k": r.get("k"), "floor": r.get("floor"), **({"oracle": r["oracle"]} if r.get("oracle") else {}), "per_seed": {}})
                    row["per_seed"][seed] = r["value"] if _is_number(r.get("value")) else r.get("mean")
        for row in grouped.values():
            problem = problems.get((world, row["id"], row["group"]))
            findings.append(_contract_no_data(world, row, None, problem) if problem else _outcome(row, world, refs, reasons_by_version, config))
    return findings


# ---------------------------------------------------------------- rerun, ownership, verdict


def _affected_pairs(suspects: Sequence[Mapping[str, Any]], config: GateConfig) -> List[Tuple[str, int]]:
    pairs = set()
    for f in suspects:
        if f["scope"] == "run" and f["class"] == "validity":
            pairs.add((f["world"], f["seed"]))
        else:
            pairs.update((f["world"], seed) for seed in config.seeds)
    return sorted(pairs)


def _apply_rerun(first: List[dict], second: List[dict]) -> List[dict]:
    """Mark a first-pass fail/drift ``unstable`` when the rerun's finding for the same key has a different state."""
    again = {finding_key(f): f for f in second}
    out = []
    for f in first:
        if f["state"] in (FAIL, DRIFT):
            other = again.get(finding_key(f))
            if other is None or other["state"] != f["state"]:
                f = {**f, "state": UNSTABLE, "first_state": f["state"], "rerun_state": other["state"] if other else "absent", "route": TEST_INFRA}
        out.append(f)
    return out


def _ownership(findings: List[dict], known: Sequence[dict], today: dt.date) -> List[dict]:
    out = []
    for f in findings:
        if f["state"] in (FAIL, DRIFT):
            entry = known_reds.owner_of(metric_test_id(f), known, state=f["state"])
            if entry is None:
                f = {**f, "ownership": "unowned" if f["state"] == FAIL else "needs-trace-ticket"}
            elif known_reds.is_expired(entry, today):
                f = {**f, "ownership": "expired", "ticket": entry["ticket"], "owner": entry["owner"]}
            else:
                f = {**f, "ownership": "known" if f["state"] == FAIL else "traced", "ticket": entry["ticket"], "owner": entry["owner"]}
        out.append(f)
    return out


def verdict(findings: Sequence[Mapping[str, Any]]) -> Tuple[str, List[str]]:
    reasons = [
        f"{f['state']} {metric_test_id(f)} ({f['world']}{'/' + str(f['seed']) if 'seed' in f else ''}): {f.get('ownership', f.get('route', ''))}"
        for f in findings
        if (f["state"] == FAIL and f.get("ownership") in ("unowned", "expired")) or f["state"] == UNSTABLE
    ]
    return ("red" if reasons else "green"), reasons


def build_report(
    config: GateConfig,
    docs: Docs,
    refs: Optional[References],
    reasons_by_version: Mapping[int, Sequence[str]],
    known: Sequence[dict],
    today: dt.date,
    *,
    sha: str = "",
    harness_hash: str = "",
    rerun: Optional[Rerun] = None,
) -> dict:
    """Evaluate, rerun once on a fail/drift, apply ownership and the verdict, and return the JSON-able report."""
    findings = evaluate(docs, config, refs, reasons_by_version, harness_hash)
    suspects = [f for f in findings if f["state"] in (FAIL, DRIFT)]
    rerun_info: Dict[str, Any] = {"performed": False}
    if suspects and rerun is not None:
        pairs = _affected_pairs(suspects, config)
        second = evaluate({**docs, **rerun(pairs)}, config, refs, reasons_by_version, harness_hash)
        findings = _apply_rerun(findings, second)
        skipped = [list(p) for p in getattr(rerun, "skipped", [])]
        rerun_info = {"performed": True, "pairs": [list(p) for p in pairs], "unstable": sum(1 for f in findings if f["state"] == UNSTABLE)}
        if skipped:
            rerun_info["not_performed_budget"] = skipped  # these pairs were not rerun; their findings keep the first pass's state, so they are not marked unstable
    findings = _ownership(findings, known, today)
    stale_known = {
        state: [e["match"] for e in known_reds.stale_mappings({metric_test_id(f): "" for f in findings if f["state"] == state}, known, state=state)]
        for state in known_reds.GATE_STATES
    }
    outcome, reasons = verdict(findings)
    counts = {state: sum(1 for f in findings if f["state"] == state) for state in STATES}
    return {
        "schema": SCHEMA,
        "sha": sha,
        "harness_hash": harness_hash,
        "verdict": outcome,
        "reasons": reasons,
        "module_absent": any(f["state"] == NO_DATA and f.get("reason") == "metric_error" and str(f.get("detail", "")).startswith("ModuleNotFoundError") for f in findings),
        "run_errors": [
            {"world": f["world"], "seed": f.get("seed"), "error": f.get("detail", "")} for f in findings if f.get("reason") == "run_error"
        ],
        "no_data_reasons": {name: sum(1 for f in findings if f["state"] == NO_DATA and f.get("reason") == name) for name in NO_DATA_REASONS},
        "counts": counts,
        "references": (
            [{"ref": "last", "version": refs.last["version"], "milestone": refs.last["milestone"], "stale": list(reasons_by_version.get(refs.last["version"], ()))},
             {"ref": "milestone-first", "version": refs.milestone_first["version"], "milestone": refs.milestone_first["milestone"], "stale": list(reasons_by_version.get(refs.milestone_first["version"], ()))}]
            if refs else []
        ),
        "rerun": rerun_info,
        "stale_known_entries": stale_known,
        "findings": findings,
    }


# ---------------------------------------------------------------- markdown


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [f"## rpg gate report: {report['verdict'].upper()}", ""]
    lines.append(f"SHA `{report['sha'][:9]}`, harness `{report['harness_hash'][:12]}`. " + ", ".join(f"{s}: {report['counts'][s]}" for s in STATES))
    if report.get("module_absent"):
        lines += ["", "> **rpg's metric module is absent** (`ModuleNotFoundError`): every run is `metric_error` / `no-data`, so this report judges nothing yet. The job stays green."]
    if report["references"]:
        lines.append("References: " + "; ".join(f"{r['ref']} = v{r['version']} ({r['milestone']}){' STALE: ' + '; '.join(r['stale']) if r['stale'] else ''}" for r in report["references"]))
    else:
        lines.append("References: none (no baseline exists)")
    if report["rerun"].get("performed"):
        lines.append(f"Same-SHA rerun: {len(report['rerun']['pairs'])} (world, seed) run(s), {report['rerun']['unstable']} metric(s) unstable.")
        if report["rerun"].get("not_performed_budget"):
            lines.append(f"- rerun not performed (budget) for {len(report['rerun']['not_performed_budget'])} run(s): their fail/drift findings are unconfirmed.")
    for reason in report["reasons"]:
        lines.append(f"- **RED**: {reason}")
    if report["run_errors"]:
        lines += ["", f"### RUN ERRORS ({len(report['run_errors'])}): an exception in the simulation, an rpg defect (does not turn the job red in the advisory phase)"]
        lines += [f"- **{e['world']}{'/' + str(e['seed']) if e['seed'] is not None else ''}**: {e['error']}" for e in report["run_errors"]]
    required_missing = sorted({f["id"] for f in report["findings"] if f.get("required_missing")})
    if required_missing:
        lines += ["", f"> **Required validity row(s) missing: {', '.join(required_missing)}.** The metric module did not emit them, so they are `no-data` (`contract_error`), not a pass."]
    reasons_seen = {k: v for k, v in report["no_data_reasons"].items() if v}
    if reasons_seen:
        lines.append("No-data reasons: " + ", ".join(f"{k}: {v}" for k, v in reasons_seen.items()))
    shown = [f for f in report["findings"] if f["state"] != PASS]
    if shown:
        lines += ["", "| state | metric | world | detail |", "|---|---|---|---|"]
        for f in sorted(shown, key=lambda f: (STATES.index(f["state"]), metric_test_id(f), f["world"])):
            lines.append(f"| {f['state']} | `{metric_test_id(f)}`{' ' + str(f['key']) if f.get('key') else ''} | {f['world']}{'/' + str(f['seed']) if 'seed' in f else ''} | {_detail(f)} |")
    else:
        lines.append("\nEvery metric passes.")
    return "\n".join(lines) + "\n"


def _detail(f: Mapping[str, Any]) -> str:
    parts: List[str] = []
    if f["state"] == FAIL:
        parts.append(f"{f['violations']} violation(s); examples: {f.get('examples', [])}")
        if f.get("oracle"):
            parts.append(f"oracle: {f['oracle']}")
    if f["state"] == UNSTABLE:
        parts.append(f"was {f['first_state']}, rerun {f['rerun_state']}; route: {f['route']}")
    shown: set = set()
    for r in f.get("refs", []):
        numbers = f" d={r['diff']:.4g}" + (f" se={r['se']:.4g} k*se={r['threshold']:.4g}" if "se" in r else "") + f" floor={r['floor']:.4g}" if "diff" in r else ""
        judged = f", judged on {r['n']}/{r['of']} seeds" if "n" in r else ""
        moved = "".join(f"; threshold moved: {n} {m['reference']} -> {m['candidate']}" for n, m in sorted((r.get("threshold_moved") or {}).items()))
        cause = (f" [{r['reason']}] {r['detail']}" if r.get("reason") else f" {r['detail']}") if r.get("detail") and r["state"] == "no-data" else ""
        shown.add(r.get("detail"))
        parts.append(f"vs {r['ref']} v{r['version']}: {r['state']}{numbers}{judged}{moved}{cause}")
    if f.get("detail") and f["detail"] not in shown:
        parts.append((f"[{f['reason']}] " if f.get("reason") else "") + f["detail"])
    if f.get("ownership"):
        parts.append(f"{f['ownership']}{' ' + f['ticket'] if f.get('ticket') else ''}")
    return "; ".join(parts).replace("|", "\\|")


# ---------------------------------------------------------------- CLI


def _harness_rerun(config: GateConfig, config_path: Path, docs_dir: Path, metrics_module: str, sha: str, workers: int = 2, budget_s: float = 5400.0) -> Rerun:
    from tools.test_architecture import rpg_gate_harness as harness

    hhash = harness.harness_hash(config_path, metrics_module=metrics_module)
    token = f"rerun-{os.getpid()}-{int(time.time()) % 100000}"  # per invocation, like the harness's own run ids

    def rerun(pairs: Sequence[Tuple[str, int]]) -> Docs:
        """Rerun the pairs in fresh processes, ``workers`` at a time, starting none after ``budget_s``; the pairs never started are in ``rerun.skipped``."""
        out = Path(str(docs_dir) + "-rerun")
        out.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + budget_s
        rerun.skipped = []

        def one(pair: Tuple[str, int]) -> None:
            if time.monotonic() >= deadline:
                rerun.skipped.append(pair)
                return
            harness.run_one(pair[0], pair[1], config, out, metrics_module=metrics_module, sha=sha, hhash=hhash, keep_runs=False,
                            timeout_s=min(harness.DEFAULT_TIMEOUT_S, max(60.0, deadline - time.monotonic())), token=token)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(one, pairs))
        pairs = [p for p in pairs if p not in rerun.skipped]
        for world in sorted({w for w, _ in pairs}):
            if not all((world, seed) in set(pairs) for seed in config.seeds):
                continue  # a pooled document needs every seed; the first pass's pooled document stands
            harness.pool_world(world, [out / harness.doc_name(world, s) for s in config.seeds], config, out,
                               metrics_module=metrics_module, sha=sha, hhash=hhash, timeout_s=harness.DEFAULT_TIMEOUT_S)
        return load_documents(out, config)

    return rerun


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--docs", type=Path, required=True)
    parser.add_argument("--baselines", type=Path, required=True)
    parser.add_argument("--known", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--metrics-module", default=None)
    parser.add_argument("--sha", default="")
    parser.add_argument("--no-rerun", action="store_true")
    parser.add_argument("--rerun-workers", type=int, default=2)
    parser.add_argument("--rerun-budget", type=float, default=5400.0, help="seconds after which no further rerun is started")
    parser.add_argument("--fail-on-red", action="store_true")
    args = parser.parse_args(argv)
    from tools.test_architecture import rpg_gate_harness as harness

    metrics_module = args.metrics_module or harness.DEFAULT_METRICS_MODULE
    config = load_config(args.config)
    hhash = harness.harness_hash(args.config, metrics_module=metrics_module)
    now = dt.datetime.now(dt.timezone.utc)
    baselines = load_baselines(args.baselines)
    refs = resolve_references(baselines)
    reasons = {b["version"]: staleness(b, now, hhash, config).reasons for b in ((refs.last, refs.milestone_first) if refs else ())}
    rerun = None if args.no_rerun else _harness_rerun(config, args.config, args.docs, metrics_module, args.sha, args.rerun_workers, args.rerun_budget)
    report = build_report(
        config, load_documents(args.docs, config), refs, reasons, known_reds.load_known_reds(args.known, known_reds.RPG_GATE_SPEC), now.date(),
        sha=args.sha, harness_hash=hhash, rerun=rerun,
    )
    args.out_json.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"verdict={report['verdict']} " + " ".join(f"{s}={n}" for s, n in report["counts"].items()))
    return 1 if (args.fail_on_red and report["verdict"] == "red") else 0


if __name__ == "__main__":
    sys.exit(main())

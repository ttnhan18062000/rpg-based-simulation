"""The standard paired measurement of one behaviour step: a base arm and a new arm, 3 worlds x seeds 42-46 x 5000 ticks, audit_mode forced.

    python -m tools.rpg_measure.paired --base <rev> --new <rev> --step "D75 route" --div 2.128 [--terrain] [--jobs 2] [--out table.md]
    python -m tools.rpg_measure.paired --base <rev> --new <rev> --neutral        # byte-identical state-hash check, 3 worlds, 1 seed

Each arm is the ``git archive`` of a commit, run by ``arm_child.py`` with that tree as its working directory; results are cached by commit
(``<cache>/results/<sha>-<child hash>-<ticks>/``) so step N's child arm is step N+1's parent arm and is never re-run. A base-vs-base repeat of the base arm
(seed 42 of every world, or all seeds with ``--self-check full``) must be byte-identical; otherwise the pair is refused. Runs whose manifest is not
``signals_zeroed`` are refused (``require_host_independent_runs``). People are the base arm's tick-0 keeps_coin roster matched by id (see ``stats.py``).
Run data is removed by the child by run id; ``--clean-cache`` also removes the extracted arm trees. Summary tables only are written.

    python -m tools.rpg_measure.paired --collected DIR --base <40-hex sha> --new <40-hex sha> [same flags]

``--collected DIR`` compares results that were produced elsewhere (a CI matrix job per world x seed) and never executes a run: DIR is a paired cache root
(``DIR/results/<sha12>-<child hash>-<ticks>[-repeat]/<world>_<seed>.json``, plus an optional ``<world>_<seed>.cost.json`` of ``wall_seconds``,
``peak_rss_mb`` and ``runner`` {name, image, cpu_model, nproc, mem_total_mb, python, os}). There is no git call and no tree extraction, so ``--base``/``--new``
are full shas and ``--repo`` is unused; ``--jobs`` and ``--clean-cache`` are rejected. A result that should exist and does not is REFUSED (exit 2) with its
(arm, world, seed) keys; a repeat result is read and never unlinked; a runner whose python, os or image differs between the arms (and the repeat) of a key
is REFUSED, because the pair is then not host-independent. A missing cost.json is not a refusal (its wall and RSS are null). The child hash is the sha256 of
THIS tool checkout's ``arm_child.py``: the off-host jobs must run ``arm_child.py`` from the same tool commit as the aggregate job, or the result
directories do not match. The report is the local report plus one ``- runners:`` line.

``--verdict-json PATH`` (either mode) writes ``{"outcome": "PASS"|"STOP"|"REFUSED", "mode": "step"|"neutral"|"report_only", "detail": str|null}``; a write
failure only warns on stderr. Exit codes: 0 the report was produced (a STOP is in the table), 2 REFUSED, 1 a neutral mismatch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.observability.reporting.run_determinism import NonAuditRunError, require_host_independent_runs
from tools.rpg_measure import stats

WORLDS = ("frontier_living_world", "urban_political", "crowded_frontier")
TERRAIN_WORLD = "highland_traverse"
SEEDS = (42, 43, 44, 45, 46)
TICKS = 5000
HASHSEED = "0"
CHILD = Path(__file__).with_name("arm_child.py")
DEFAULT_CACHE = Path(os.environ.get("RPG_MEASURE_CACHE", "/mnt/data/scratch-rpg-measure"))
NEUTRAL_TICKS = 1000
Key = Tuple[str, int]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def child_hash() -> str:
    return hashlib.sha256(CHILD.read_bytes()).hexdigest()[:8]


def prepare_tree(repo: Path, rev: str, cache: Path) -> Tuple[str, Path]:
    """Resolve a revision to a commit and extract its tree once into the cache."""
    sha = _git(repo, "rev-parse", "--verify", rev + "^{commit}")
    tree = cache / "trees" / sha[:12]
    if not (tree / ".extracted").exists():
        tree.mkdir(parents=True, exist_ok=True)
        archive = subprocess.Popen(["git", "-C", str(repo), "archive", sha], stdout=subprocess.PIPE)
        subprocess.run(["tar", "-x", "-C", str(tree)], stdin=archive.stdout, check=True)
        if archive.wait() != 0:
            raise RuntimeError(f"git archive failed for {sha}")
        (tree / ".extracted").write_text(sha, encoding="utf-8")
    return sha, tree


def result_path(cache: Path, sha: str, ticks: int, world: str, seed: int, repeat: bool = False) -> Path:
    return cache / "results" / f"{sha[:12]}-{child_hash()}-{ticks}{'-repeat' if repeat else ''}" / f"{world}_{seed}.json"


def run_one(tree: Path, world: str, seed: int, ticks: int, out: Path) -> None:
    env = {**os.environ, "PYTHONHASHSEED": HASHSEED, "PYTHONPATH": str(tree)}
    proc = subprocess.run([sys.executable, str(CHILD), world, str(seed), str(ticks), str(out)], cwd=tree, env=env, capture_output=True, text=True)
    if proc.returncode != 0 or not out.exists():
        raise RuntimeError(f"arm run failed ({tree.name} {world} {seed}): {proc.stderr.strip()[-400:]}")


def run_arm(tree: Path, cache: Path, sha: str, jobs: Sequence[Key], ticks: int, workers: int, repeat: bool = False) -> Dict[Key, Dict[str, Any]]:
    """Run (or load from the cache) every (world, seed); a repeat arm is never cached."""
    todo = []
    for world, seed in jobs:
        out = result_path(cache, sha, ticks, world, seed, repeat)
        if repeat and out.exists():
            out.unlink()
        if not out.exists():
            todo.append((world, seed, out))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda j: run_one(tree, j[0], j[1], ticks, j[2]), todo))
    return {(w, s): json.loads(result_path(cache, sha, ticks, w, s, repeat).read_text(encoding="utf-8")) for w, s in jobs}


def refuse_non_audit(arm: str, runs: Dict[Key, Dict[str, Any]], legacy: bool = False) -> None:
    """Both flags recorded by the run's own manifest: audit_mode and signals_zeroed must be True, else the comparison measures host speed.

    ``legacy`` (a base older than the determinism fix, whose manifest has no typed record): accept a manifest that says nothing (None) when the child verified
    that the arm's kernel was built with audit_mode and no_frame_pacing; a manifest that records ``False`` is still refused. The caller must also have
    proved the arm by a full base-vs-base repeat.
    """
    if legacy:
        bad = [f"{arm}:{w}:{s}" for (w, s), r in runs.items()
               if r.get("signals_zeroed") is False or r.get("audit_mode") is False or r.get("forced_flags") != {"audit_mode": True, "no_frame_pacing": True}]
        if bad:
            raise NonAuditRunError(f"legacy runs not forced to audit_mode and no_frame_pacing, or recorded live: {sorted(bad)}")
        return
    require_host_independent_runs({f"{arm}:{w}:{s}": {"signals_zeroed": r.get("signals_zeroed")} for (w, s), r in runs.items()})
    off = [f"{arm}:{w}:{s}" for (w, s), r in runs.items() if r.get("audit_mode") is not True]
    if off:
        raise NonAuditRunError(f"runs not recorded with audit_mode: {sorted(off)}")


def _fmt(x: float) -> str:
    return f"{x:+.2f}"


def _counter_sum(runs: Sequence[Dict[str, Any]], prefix: str) -> Optional[int]:
    if any(r["counters"] is None for r in runs):
        return None
    return sum(v for r in runs for k, v in r["counters"].items() if k.startswith(prefix))


def world_section(world: str, base: List[Dict[str, Any]], new: List[Dict[str, Any]], floor_per_seed: float, headline: Optional[str], report_only: bool = False) -> Tuple[List[str], Dict[str, Any]]:
    seeds = [r["seed"] for r in base]
    ids = [stats.people_ids(b["start"]) for b in base]
    mismatch = [stats.roster_mismatch(b["start"], n["start"]) for b, n in zip(base, new)]
    pb = [stats.people_deaths(b, i) for b, i in zip(base, ids)]
    pn = [stats.people_deaths(n, i) for n, i in zip(new, ids)]
    diffs = [n - b for b, n in zip(pb, pn)]
    se, mean = stats.standard_error(diffs), stats.mean(diffs)
    verdict = stats.verdict(diffs, floor_per_seed)
    verdict = stats.REPORT_ONLY if report_only and verdict else verdict  # a report-only reading never trips a stop
    ext = stats.extinction_verdict(base, new)
    if report_only:
        ext = {**ext, "stop": []}
    lines = [f"### {world}", "",
             f"People deaths (tick-0 base roster, keeps_coin, by id; n={len(ids[0])} per seed): base {pb} -> new {pn}",
             f"- total {sum(pb)} -> {sum(pn)} (delta {sum(pn) - sum(pb):+d}); mean per-seed delta {_fmt(mean)}, SE {se:.2f}, floor {floor_per_seed * len(diffs):g} total; verdict (more deaths past {stats.SE_MULTIPLE:g}·SE and the floor stops, fewer is report-only): **{verdict or 'no drift'}**"]
    if any(m["only_base"] or m["only_new"] or m["changed"] for m in mismatch):
        lines.append(f"- ROSTER MISMATCH at tick 0 (the arms did not start from the same world): {[ (s, m) for s, m in zip(seeds, mismatch) if any(m.values()) ]}")
    kinds = sorted({k for r in base + new for k in stats.deaths_by_kind(r)})
    kb = {k: [stats.deaths_by_kind(r)[k] for r in base] for k in kinds}
    kn = {k: [stats.deaths_by_kind(r)[k] for r in new] for k in kinds}
    lines += ["", "| kind (all entities of the tick-0 roster) | dead base | dead new | mean delta | SE | verdict |", "|---|---|---|---|---|---|"]
    for k in kinds:
        d = [b - a for a, b in zip(kb[k], kn[k])]
        lines.append(f"| {k} | {sum(kb[k])} | {sum(kn[k])} | {_fmt(stats.mean(d))} | {stats.standard_error(d):.2f} | {(stats.REPORT_ONLY if report_only and stats.verdict(d, floor_per_seed) else stats.verdict(d, floor_per_seed))} |")
    cb, cn = sum((stats.causes_by_kind(r) for r in base), stats.Counter()), sum((stats.causes_by_kind(r) for r in new), stats.Counter())
    moved = sorted(k for k in set(cb) | set(cn) if cb[k] != cn[k])
    lines += ["", f"Deaths by kind|cause (death_record), rows that moved: " + (", ".join(f"{k} {cb[k]}->{cn[k]}" for k in moved) or "none")]
    ab, an = sum((stats.alive_by_kind(r) for r in base), stats.Counter()), sum((stats.alive_by_kind(r) for r in new), stats.Counter())
    lines.append("Alive at end by kind (sum of seeds): " + ", ".join(f"{k} {ab[k]}->{an[k]}" for k in sorted(set(ab) | set(an))))
    lines.append(f"Added after tick 0 (count of seeds' ids): base {sum(len(stats.added(r)) for r in base)} -> new {sum(len(stats.added(r)) for r in new)}")
    lines.append(("REPORT-ONLY reading: STOP is suppressed; extinct in the new arm only: " + str(sorted(stats.extinction_verdict(base, new)['stop']) or 'none')) if report_only else "")
    lines.append(f"Extinctions: STOP {ext['stop'] or 'none'}; base-state (extinct in both arms) {ext['base_state'] or 'none'}; recovered {ext['recovered'] or 'none'}")
    lines.append("")
    for name, prefix in (("flee ticks", "flee_ticks"), ("flee episodes", "flee_episodes"), ("pursuit ticks", "pursuit_ticks"), ("pursuit episodes", "pursuit_episodes"),
                         ("combat_retreat flight ticks", "combat_retreat_flight_ticks"), ("combat_retreat flight episodes", "combat_retreat_flight_episodes"),
                         ("entity-samples that perceived a hostile", "perceiving_ticks"), ("steps (all terrain)", "steps|")):
        b, n = _counter_sum(base, prefix), _counter_sum(new, prefix)
        lines.append(f"- {name}: " + (f"{b} -> {n}" if b is not None and n is not None else "n/a (an arm tree predates the ledger counters)"))
    lines.append(f"- perception samples taken per run: {sorted({r['perception_samples'] for r in base + new if r['perception_samples'] is not None}) or 'n/a'} (perceived_hostiles every 10 ticks)")
    terr = sorted({k.split("|", 1)[1] for r in base + new if r["counters"] for k in r["counters"] if k.startswith("steps|")})
    for t in terr:
        lines.append(f"- steps onto {t}: {_counter_sum(base, 'steps|' + t)} -> {_counter_sum(new, 'steps|' + t)}")
    lines.append("- pre-check refusals: not measured (no typed record exists at this commit)")
    if headline:
        lines.append(f"- headline `{headline}`: {_counter_sum(base, headline)} -> {_counter_sum(new, headline)}")
    lines.append("")
    row = {"world": world, "people_base": sum(pb), "people_new": sum(pn), "delta": sum(pn) - sum(pb), "mean_delta": mean, "se": se, "verdict": verdict, "stop": ext["stop"]}
    return lines, row


def watch_rows(step: str, div: str, rows: Sequence[Dict[str, Any]], report_only: bool = False) -> List[str]:
    out = ["### Watch-table rows (cumulative table, D76)" + (" - REPORT-ONLY reading, never trips a stop" if report_only else ""), "", "| Step | Div | World | People deaths base->new | Delta | SE | Extinctions |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        ext = ("STOP " + ", ".join(r["stop"])) if r["stop"] else "none"
        flag = f" ({r['verdict']})" if r["verdict"] else ""
        out.append(f"| {step} | {div} | {r['world']} | {r['people_base']}->{r['people_new']} | {r['delta']:+d}{flag} | {r['se']:.2f} | {ext} |")
    return out


SHA40 = re.compile(r"^[0-9a-f]{40}$")


def cost_path(result: Path) -> Path:
    """``<world>_<seed>.cost.json`` beside ``<world>_<seed>.json``."""
    return result.with_name(result.stem + ".cost.json")


def load_cost(result: Path) -> Optional[Dict[str, Any]]:
    """The cost and runner identity beside a result; None when it is absent (not a refusal) or not a JSON object."""
    try:
        data = json.loads(cost_path(result).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


Entry = Tuple[str, str, Sequence[Key], int, bool]  # (arm label, sha, jobs, ticks, repeat)


def missing_results(cache: Path, entries: Sequence[Entry]) -> List[str]:
    """Every (arm, world, seed) whose result file is not in a collected cache."""
    return [f"{arm}{'-repeat' if rep else ''}:{w}:{s}" for arm, sha, js, ticks, rep in entries for w, s in js if not result_path(cache, sha, ticks, w, s, rep).exists()]


def runner_identity(cache: Path, entries: Sequence[Entry]) -> Tuple[List[str], List[str]]:
    """(mismatches, distinct runners): python, os and image must agree across the base, new and repeat results of every key (DET-PORT-0)."""
    by_key: Dict[Key, Dict[str, set]] = {}
    seen = set()
    for _arm, sha, js, ticks, rep in entries:
        for w, s in js:
            cost = load_cost(result_path(cache, sha, ticks, w, s, rep))
            runner = (cost or {}).get("runner")
            if not isinstance(runner, dict):
                continue
            seen.add(f"{runner.get('name')}/{runner.get('image')} python {runner.get('python')} {runner.get('os')} ({runner.get('cpu_model')}, nproc {runner.get('nproc')})")
            slot = by_key.setdefault((w, s), {f: set() for f in ("python", "os", "image")})
            for f in slot:
                slot[f].add(str(runner.get(f)))
    bad = [f"{w}:{s} {f} {sorted(v)}" for (w, s), slot in sorted(by_key.items()) for f, v in slot.items() if len(v) > 1]
    return bad, sorted(seen)


def neutral_report(base: Dict[Key, Dict[str, Any]], new: Dict[Key, Dict[str, Any]], bsha: str, nsha: str) -> Tuple[int, List[str]]:
    """(exit code, differing worlds) of the byte-identical check; prints the per-world lines and the verdict line."""
    jobs = [(w, 42) for w in WORLDS]
    bad = [w for (w, _s) in jobs if base[(w, 42)]["final_hash"] != new[(w, 42)]["final_hash"] or base[(w, 42)]["start_hash"] != new[(w, 42)]["start_hash"]]
    for (w, _s) in jobs:
        print(f"{w} seed 42 {NEUTRAL_TICKS}t: base {base[(w, 42)]['final_hash'][:16]} new {new[(w, 42)]['final_hash'][:16]} {'IDENTICAL' if w not in bad else 'DIFFERENT'}")
    print(f"NEUTRAL {'PASS' if not bad else 'FAIL ' + str(bad)} (base {bsha[:12]}, new {nsha[:12]})")
    return (0 if not bad else 1), bad


def neutral(repo: Path, base_rev: str, new_rev: str, cache: Path, workers: int, verdict: Optional[Dict[str, Any]] = None) -> int:
    """The new arm's state is byte-identical to the base arm's on 3 worlds at seed 42: start hash, final hash and every entity's fate."""
    (bsha, btree), (nsha, ntree) = prepare_tree(repo, base_rev, cache), prepare_tree(repo, new_rev, cache)
    jobs = [(w, 42) for w in WORLDS]
    base, new = run_arm(btree, cache, bsha, jobs, NEUTRAL_TICKS, workers), run_arm(ntree, cache, nsha, jobs, NEUTRAL_TICKS, workers)
    rc, bad = neutral_report(base, new, bsha, nsha)
    _neutral_verdict(verdict, bad)
    return rc


def _neutral_verdict(verdict: Optional[Dict[str, Any]], bad: Sequence[str]) -> None:
    if verdict is not None:
        verdict.update(outcome="STOP" if bad else "PASS", detail=f"state differs in {list(bad)}" if bad else None)


def _check_jobs(self_check: str, worlds: Sequence[str], jobs: Sequence[Key]) -> List[Key]:
    return [] if self_check == "off" else list(jobs) if self_check == "full" else [(w, 42) for w in worlds if (w, 42) in set(jobs)]


def _refuse(verdict: Dict[str, Any], detail: str, message: Optional[str] = None) -> int:
    print(f"REFUSED: {message or detail}", file=sys.stderr)
    verdict.update(outcome="REFUSED", detail=detail)
    return 2


def write_verdict(path: Optional[str], verdict: Dict[str, Any]) -> None:
    """The machine-readable verdict (run-ledger/v1 values). Never raises: a write failure warns and the exit code stands."""
    if not path:
        return
    try:
        Path(path).write_text(json.dumps({"outcome": verdict.get("outcome") or "REFUSED", "mode": verdict["mode"], "detail": verdict.get("detail")}, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - bookkeeping must never change the measurement's result
        print(f"WARNING: could not write --verdict-json {path}: {exc}", file=sys.stderr)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--step", default="step")
    ap.add_argument("--div", default="-")
    ap.add_argument("--terrain", action="store_true", help=f"also run {TERRAIN_WORLD}")
    ap.add_argument("--ticks", type=int, default=TICKS)
    ap.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    ap.add_argument("--jobs", type=int, default=None, help="parallel runs, default 2 (memory: the reaper kills at 3 heavy processes); rejected with --collected")
    ap.add_argument("--floor-per-seed", type=float, default=stats.FLOOR_PER_SEED, help="people deaths per seed a world's delta must exceed (owner's D76 floor: 1)")
    ap.add_argument("--self-check", choices=("seed42", "full", "off"), default="seed42")
    ap.add_argument("--legacy-base", action="store_true", help="accept a base older than the determinism fix (no typed audit_mode/signals_zeroed in its manifest) ONLY with a full base-vs-base repeat")
    ap.add_argument("--legacy-new", action="store_true", help="the same for the NEW arm (a pre-fix commit read against the stop base); the new arm is then repeated in full too")
    ap.add_argument("--report-only", action="store_true", help="suppress STOP (verdicts and extinctions) and label the whole output report-only")
    ap.add_argument("--headline", default=None, help="a ledger counter prefix to show as the step's headline metric")
    ap.add_argument("--neutral", action="store_true")
    ap.add_argument("--clean-cache", action="store_true")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--cache", default=str(DEFAULT_CACHE))
    ap.add_argument("--out", default=None)
    ap.add_argument("--collected", default=None, metavar="DIR", help="compare results already in this paired cache root (produced elsewhere); executes nothing, needs full --base/--new shas")
    ap.add_argument("--verdict-json", default=None, metavar="PATH", help='write {"outcome": PASS|STOP|REFUSED, "mode": step|neutral|report_only, "detail"} (run-ledger/v1 values)')
    a = ap.parse_args(argv)
    if a.collected is not None:
        if a.jobs is not None or a.clean_cache:
            ap.error("--collected executes nothing and extracts no trees: --jobs and --clean-cache are not allowed with it")
        for flag, sha in (("--base", a.base), ("--new", a.new)):
            if not SHA40.match(sha):
                ap.error(f"{flag} must be a full 40-hex lowercase sha with --collected (no git is run), got {sha!r}")
    a.jobs = 2 if a.jobs is None else a.jobs
    verdict: Dict[str, Any] = {"outcome": None, "mode": "neutral" if a.neutral else "report_only" if a.report_only else "step", "detail": None}
    try:
        return _run(a, verdict)
    except BaseException as exc:
        if verdict["outcome"] is None:
            verdict.update(outcome="REFUSED", detail=f"{type(exc).__name__}: {str(exc)[:300]}")
        raise
    finally:
        write_verdict(a.verdict_json, verdict)


def _run(a: argparse.Namespace, verdict: Dict[str, Any]) -> int:
    collected = a.collected is not None
    legacy_msg = "--legacy-base / --legacy-new need --self-check full (the audit is proven only by a byte-identical repeat of every seed and world)"
    if collected:
        cache, bsha, nsha = Path(a.collected), a.base, a.new
        btree = ntree = None
    else:
        repo, cache = Path(_git(Path(a.repo), "rev-parse", "--show-toplevel")), Path(a.cache)
        if a.neutral:
            return neutral(repo, a.base, a.new, cache, a.jobs, verdict)
    if collected and a.neutral:
        jobs = [(w, 42) for w in WORLDS]
        entries: List[Entry] = [("base", bsha, jobs, NEUTRAL_TICKS, False), ("new", nsha, jobs, NEUTRAL_TICKS, False)]
        missing = missing_results(cache, entries)
        if missing:
            return _refuse(verdict, f"missing results {missing}", f"missing collected results (arm:world:seed) {missing}")
        mismatched, _runners = runner_identity(cache, entries)
        if mismatched:
            return _refuse(verdict, f"runner identity differs {mismatched}", f"runner python/os/image differs between arms of a key: {mismatched}; the pair is not host-independent")
        read = lambda sha: {k: json.loads(result_path(cache, sha, NEUTRAL_TICKS, *k).read_text(encoding="utf-8")) for k in jobs}
        rc, bad = neutral_report(read(bsha), read(nsha), bsha, nsha)
        _neutral_verdict(verdict, bad)
        return rc
    worlds = WORLDS + ((TERRAIN_WORLD,) if a.terrain else ())
    jobs = [(w, s) for w in worlds for s in a.seeds]
    check_jobs = _check_jobs(a.self_check, worlds, jobs)
    runner_lines: List[str] = []
    if collected:
        if (a.legacy_base or a.legacy_new) and a.self_check != "full":
            return _refuse(verdict, legacy_msg)
        entries = [("base", bsha, jobs, a.ticks, False), ("new", nsha, jobs, a.ticks, False)]
        if check_jobs:
            entries.append(("base", bsha, check_jobs, a.ticks, True))
            if a.legacy_new:
                entries.append(("new", nsha, check_jobs, a.ticks, True))
        missing = missing_results(cache, entries)
        if missing:
            return _refuse(verdict, f"missing results {missing}", f"missing collected results (arm:world:seed) {missing}")
        mismatched, runners = runner_identity(cache, entries)
        if mismatched:
            return _refuse(verdict, f"runner identity differs {mismatched}", f"runner python/os/image differs between arms of a key: {mismatched}; the pair is not host-independent")
        runner_lines = ["- runners (collected off host): " + ("; ".join(runners) if runners else "none recorded (no cost.json beside the results)")]
        load = lambda sha, js, repeat=False: {k: json.loads(result_path(cache, sha, a.ticks, *k, repeat).read_text(encoding="utf-8")) for k in js}
        base, new = load(bsha, jobs), load(nsha, jobs)
    else:
        (bsha, btree), (nsha, ntree) = prepare_tree(repo, a.base, cache), prepare_tree(repo, a.new, cache)
        base, new = run_arm(btree, cache, bsha, jobs, a.ticks, a.jobs), run_arm(ntree, cache, nsha, jobs, a.ticks, a.jobs)
        load = lambda sha, js, repeat=False: run_arm(btree if sha == bsha else ntree, cache, sha, js, a.ticks, a.jobs, repeat=repeat)
        if (a.legacy_base or a.legacy_new) and a.self_check != "full":
            return _refuse(verdict, legacy_msg)
    refuse_non_audit("base", base, legacy=a.legacy_base)
    refuse_non_audit("new", new, legacy=a.legacy_new)
    repeat = load(bsha, check_jobs, True) if check_jobs else {}
    bad = stats.self_check_spread([base[k] for k in check_jobs], [repeat[k] for k in check_jobs])
    if a.legacy_new:
        repeat_new = load(nsha, check_jobs, True)
        bad += [f"new:{x}" for x in stats.self_check_spread([new[k] for k in check_jobs], [repeat_new[k] for k in check_jobs])]
    if bad:
        return _refuse(verdict, f"base-vs-base is not byte-identical for {bad}", f"base-vs-base is not byte-identical for {bad}; the measurement is not host-independent")
    lines = [f"## Paired measurement: {a.step} (div {a.div})" + (" - REPORT-ONLY" if a.report_only else ""), "",
             *(["- **legacy base, audit proven by repeat**: the base arm predates the determinism fix (no typed audit_mode/signals_zeroed in its manifest); its kernel was verified built with audit_mode and no_frame_pacing, and the full base-vs-base repeat below is byte-identical"] if a.legacy_base else []),
             *(["- **legacy new arm, audit proven by repeat**: the new arm also predates the determinism fix; its kernel was verified forced and its own full repeat is byte-identical"] if a.legacy_new else []),
             f"- base {bsha[:12]} -> new {nsha[:12]}; {', '.join(worlds)}; seeds {a.seeds}; {a.ticks} ticks; PYTHONHASHSEED={HASHSEED}; audit_mode and signals_zeroed recorded True in every run of " + ("the new arm (base: see the legacy line)" if a.legacy_base and not a.legacy_new else "neither arm (see the legacy lines)" if a.legacy_new else "both arms"),
             (f"- base-vs-base self-check ({a.self_check}, {len(check_jobs)} runs): spread 0 (byte-identical final and start hashes, fates and counters)" if check_jobs else "- base-vs-base self-check: NOT RUN (--self-check off)"),
             *runner_lines,
             f"- SE = sd(per-seed new-base)/sqrt({len(a.seeds)}); STOP = more people deaths by > {stats.SE_MULTIPLE:g}·SE AND > floor ({a.floor_per_seed:g} per seed = {a.floor_per_seed * len(a.seeds):g} total); fewer past both is REPORT-ONLY; SD 0 is not special-cased",
             ""]
    rows = []
    for w in worlds:
        sect, row = world_section(w, [base[(w, s)] for s in a.seeds], [new[(w, s)] for s in a.seeds], a.floor_per_seed, a.headline, a.report_only)
        lines += sect
        rows.append(row)
    lines += watch_rows(a.step, a.div, rows, a.report_only)
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    stoppers = [r["world"] for r in rows if r["verdict"] == stats.STOP or r["stop"]]
    verdict.update(outcome="STOP" if stoppers and not a.report_only else "PASS", detail=f"STOP in {stoppers}" if stoppers and not a.report_only else None)
    if a.clean_cache:
        subprocess.run(["rm", "-rf", str(cache / "trees" / bsha[:12]), str(cache / "trees" / nsha[:12])], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

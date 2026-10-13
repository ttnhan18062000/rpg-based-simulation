"""Re-record the tripwire baselines under the canonical variants (TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS).

``record <name>`` measures one baseline three times, each in a fresh process and one after the other, writes the three records and a summary
under ``reports/perf/t08/<name>/`` (uncommitted), and picks the run with the median average tick latency as the candidate. A spread
(max / min of the three averages, minus one) above ``NOISY_SPREAD`` marks the record NOISY and it is not promotable. The tool never writes
under ``tests/perf/baselines/``: promotion is only ``tools/perf/baseline_lifecycle.py promote``, and the exact command (with the load notes
the promotion must carry) is printed.

``measure`` is the one-process worker ``record`` spawns. A record is made with the canonical variant of the profile the old committed file
named (``SIGNAL_CONTRACT=canonical``, so the mode sequence cannot depend on the host), ``runner.controlled=false`` and the tripwire gate, so a
tripwire head run (``tools/perf/tripwire.py``) compares against it. The two declared tripwire scenarios reuse ``tripwire.TRIPWIRE_SCENARIOS``'
``RunSpec`` unchanged (50 sampled ticks), because a record of any other protocol would be INCONCLUSIVE against the nightly lane; every other
synthetic scenario keeps the committed protocol (10 warmup, 20 sampled). Corpus worlds keep 100 + 1000 on ``PERF_512MB_LOCAL``.

Exit codes: 0 done (a NOISY record is reported, not an error), 1 could not run.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SELF_ROOT = Path(__file__).resolve().parents[2]
if str(_SELF_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELF_ROOT))

from tools.perf import capacity_run, tripwire  # noqa: E402
from tools.perf.capacity_run import CapacityRunError, RunSpec  # noqa: E402

from src.perf.benchmark_record import BenchmarkRecord, GateTier, RecordOptions, Runner  # noqa: E402

#: Runs per record, each a fresh process.
RUNS = 3
#: Above this spread (max / min of the average tick latency, minus one) a record is NOISY and not promoted.
NOISY_SPREAD = 0.15
WARMUP_TICKS = 10
SAMPLE_TICKS = 20
CORPUS_WARMUP_TICKS = 100
CORPUS_SAMPLE_TICKS = 1000
CORPUS_PROFILE = "PERF_512MB_LOCAL"
CORPUS_WORLDS = ("crowded_frontier", "frontier_extended", "frontier_marches")
CAUSE = "TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS"
OUT_ROOT = Path("reports") / "perf" / "t08"

#: name -> (scenario builder key, entities, profile). The profile is the old committed file's ``profile`` field (read, not inferred from the name).
SYNTHETIC: Dict[str, Tuple[str, int, str]] = {
    "idle_100_local": ("idle", 100, "PERF_512MB_LOCAL"),
    "idle_100_concurrent": ("idle", 100, "PERF_1GB_CONC"),
    "movement_100_local": ("movement", 100, "PERF_1GB_LOCAL"),
    "movement_100_concurrent": ("movement", 100, "PERF_2GB_CONC"),
    "resource_100_local": ("resource", 100, "PERF_1GB_LOCAL"),
    "resource_100_concurrent": ("resource", 100, "PERF_2GB_CONC"),
    "combat_10_local": ("combat", 10, "PERF_2GB_LOCAL"),
    "combat_10_concurrent": ("combat", 10, "PERF_2GB_CONC"),
    "strategic_100_local": ("strategic", 100, "PERF_2GB_LOCAL"),
    "strategic_100_concurrent": ("strategic", 100, "PERF_2GB_CONC"),
}


class RerunError(Exception):
    """A usage or input problem: the tool cannot run and says why."""


def corpus_name(world: str) -> str:
    return f"simq_corpus_{world}"


def known_names() -> List[str]:
    return sorted(SYNTHETIC) + [corpus_name(w) for w in CORPUS_WORLDS]


def spec_for(name: str) -> RunSpec:
    """The ``RunSpec`` of a baseline name: the declared tripwire spec when there is one, else the committed protocol."""
    for declared, spec in tripwire.TRIPWIRE_SCENARIOS:
        if declared == name:
            return spec
    if name in SYNTHETIC:
        scenario, entities, profile = SYNTHETIC[name]
        return RunSpec(scenario, entities, profile, "canonical", WARMUP_TICKS, SAMPLE_TICKS, 42, None, "tripwire", "tripwire_paired")
    for world in CORPUS_WORLDS:
        if name == corpus_name(world):
            return RunSpec(f"corpus:{world}", 0, CORPUS_PROFILE, "canonical", CORPUS_WARMUP_TICKS, CORPUS_SAMPLE_TICKS, 42, None, "tripwire", "tripwire_paired")
    raise RerunError(f"unknown baseline {name!r}; choose one of {known_names()}")


def build_state(scenario: str, entities: int, seed: int) -> Any:
    """The scenario's state, with the call shape of ``tools/perf/run_benchmarks.py`` (combat: ``team_a_count = team_b_count``, resource: ``node_count = n // 2``)."""
    from src.perf.scenarios import SCENARIO_BUILDERS

    if scenario not in SCENARIO_BUILDERS:
        raise RerunError(f"unknown scenario {scenario!r}")
    builder = SCENARIO_BUILDERS[scenario]
    if scenario == "combat":
        return builder(team_a_count=entities, team_b_count=entities, seed=seed)
    if scenario == "resource":
        return builder(entity_count=entities, node_count=entities // 2, seed=seed)
    return builder(entity_count=entities, seed=seed)


def measure_record(name: str) -> BenchmarkRecord:
    """One measured record of ``name`` in this process."""
    from src.perf.bench_harness import BenchHarness

    spec = spec_for(name)
    world: Optional[str] = None
    if spec.scenario.startswith("corpus:"):
        world = spec.scenario.split(":", 1)[1]
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from calibrate_simq import _load_world_state  # type: ignore[import-not-found]

        state, report = _load_world_state(world, spec.seed)
        if state is None:
            raise RerunError(f"world {world!r} has no resolved world spec")
        scenario_id = corpus_name(world)
        region_count = report.get("region_count") if isinstance(report, dict) else None
    else:
        state = build_state(spec.scenario, spec.entities, spec.seed)
        scenario_id = f"{spec.scenario}_{spec.entities}"
        region_count = None
    options = RecordOptions(GateTier(spec.gate_tier), spec.gate_projection, None, Runner(controlled=False, name=platform.node() or "unknown"))
    harness = BenchHarness(capacity_run._profile(spec))
    harness.run_benchmark(scenario_id, state, spec.warmup, spec.ticks, record_options=options)
    record = harness.last_record
    if record is None:
        raise CapacityRunError("BenchHarness built no record")
    if world is not None:
        content = dataclasses.replace(record.identity.content, world_id=world)
        workload = dataclasses.replace(record.identity.workload, region_count=region_count)
        record = dataclasses.replace(record, identity=dataclasses.replace(record.identity, content=content, workload=workload))
    return record


def host_load() -> Dict[str, Any]:
    """The 1-minute load average and the swap in use, read at the start of a run."""
    load1 = os.getloadavg()[0]
    swap_used_mb = 0.0
    try:
        fields = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, _, rest = line.partition(":")
            fields[key] = float(rest.split()[0])
        swap_used_mb = round((fields["SwapTotal"] - fields["SwapFree"]) / 1024.0, 1)
    except (OSError, KeyError, ValueError):
        pass
    return {"loadavg_1min": round(load1, 2), "swap_used_mb": swap_used_mb}


@dataclass(frozen=True)
class Run:
    """One of the runs of a record: its average tick latency and the host's load when it started."""

    path: str
    avg_ms: float
    loadavg_1min: float
    swap_used_mb: float
    peak_rss_mb: float
    wall_s: float


@dataclass(frozen=True)
class Summary:
    runs: Tuple[Run, ...]
    median_index: int
    spread: float
    noisy: bool


def summarize(runs: Sequence[Run], noisy_spread: float = NOISY_SPREAD) -> Summary:
    """The median run (by average tick latency; the lower one for an even count), the spread and whether it is NOISY."""
    if not runs:
        raise RerunError("no run produced a record")
    order = sorted(range(len(runs)), key=lambda i: runs[i].avg_ms)
    median_index = order[(len(order) - 1) // 2]
    values = [r.avg_ms for r in runs]
    lowest = min(values)
    spread = (max(values) / lowest - 1.0) if lowest > 0 else float("inf")
    return Summary(tuple(runs), median_index, round(spread, 4), spread > noisy_spread)


def promotion_note(name: str, summary: Summary, host: str) -> str:
    """The text ``baseline_lifecycle promote --note`` records: every run's avg and its load, the spread and the host."""
    parts = [f"run {i + 1}: avg {r.avg_ms:.3f} ms, loadavg1 {r.loadavg_1min}, swap {r.swap_used_mb} MB" for i, r in enumerate(summary.runs)]
    return (
        f"{name}: median of {len(summary.runs)} fresh-process runs (promoted run {summary.median_index + 1}); spread {summary.spread * 100:.1f} %; "
        + "; ".join(parts)
        + f"; host {host}; canonical variant, provisional, claims none (runner.controlled=false)"
    )


def _child_env() -> Dict[str, str]:
    return {**os.environ, "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", "0")}


def cmd_measure(name: str, out: Path) -> int:
    started = host_load()
    t0 = time.perf_counter()
    record = measure_record(name)
    wall = time.perf_counter() - t0
    out.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    meta = {**started, "wall_s": round(wall, 2), "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def cmd_record(name: str, out_root: Path) -> int:
    spec_for(name)  # raises RerunError for an unknown name before anything runs
    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)
    runs: List[Run] = []
    for index in range(1, RUNS + 1):
        path = out_dir / f"run{index}.json"
        done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "measure", "--name", name, "--out", str(path)], env=_child_env(), check=False)
        if done.returncode != 0 or not path.exists():
            print(f"cannot run: run {index} of {name} exited {done.returncode}", file=sys.stderr)
            return 1
        record = BenchmarkRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
        meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
        runs.append(Run(str(path), record.result.latency_ms["avg"], meta["loadavg_1min"], meta["swap_used_mb"], meta["peak_rss_mb"], meta["wall_s"]))
    summary = summarize(runs)
    median = Path(runs[summary.median_index].path)
    candidate = out_dir / "candidate.json"
    candidate.write_text(median.read_text(encoding="utf-8"), encoding="utf-8")
    cand = BenchmarkRecord.from_dict(json.loads(candidate.read_text(encoding="utf-8")))
    cpu = cand.identity.runtime.cpu_model
    off_normal = sorted({m.mode for m in cand.result.runtime_mode_sequence} - {"NORMAL"})
    host = f"{platform.node()} / {cpu} / {os.cpu_count()} vCPU"
    note = promotion_note(name, summary, host)
    doc = {"name": name, "spread": summary.spread, "noisy": summary.noisy, "off_normal": off_normal, "median_run": summary.median_index + 1, "host": host,
           "runs": [dataclasses.asdict(r) for r in summary.runs], "note": note}
    (out_dir / "summary.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(note)
    if off_normal:
        print(f"NOT A BASELINE: the run left NORMAL ({', '.join(off_normal)}) under the canonical contract; promote would refuse (performance_contract.md 3.1)")
    if summary.noisy:
        print(f"NOISY: spread {summary.spread * 100:.1f} % is above {NOISY_SPREAD * 100:.0f} %: NOT promotable; re-run on a quieter host")
    elif not off_normal:
        print(f"PROMOTE: python3 tools/perf/baseline_lifecycle.py promote --candidate {candidate} --name {name} --cause {CAUSE} --note {json.dumps(note)}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record", help="measure a baseline 3 times in fresh processes and pick the median")
    rec.add_argument("name", choices=known_names())
    rec.add_argument("--out-root", type=Path, default=OUT_ROOT)
    mea = sub.add_parser("measure", help="one measured record in this process (the worker of ``record``)")
    mea.add_argument("--name", required=True, choices=known_names())
    mea.add_argument("--out", required=True, type=Path)
    sub.add_parser("list", help="the baseline names this tool knows")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "list":
            print("\n".join(known_names()))
            return 0
        if args.command == "measure":
            return cmd_measure(args.name, args.out)
        return cmd_record(args.name, args.out_root)
    except (RerunError, CapacityRunError) as exc:
        print(f"cannot run: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

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
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

_SELF_ROOT = Path(__file__).resolve().parents[2]
if str(_SELF_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELF_ROOT))

from tools.perf import capacity_run, tripwire  # noqa: E402
from tools.perf.capacity_run import CapacityRunError, RunSpec  # noqa: E402

from src.perf.benchmark_record import BenchmarkRecord, GateTier, RecordOptions, Runner  # noqa: E402

#: Runs per record, each a fresh process.
RUNS = 3
#: The owner's spread rule (2026-10-16, option "(a) Middle-3 spread", perf_baseline_policy.md section 2.1): these three records are measured in 5 fresh
#: processes, the median is promoted and the 15 % spread is computed on the middle 3 (the lowest and the highest average dropped). Fixed here by name:
#: the rule is never chosen at run time and no other record uses it.
MIDDLE_THREE_RECORDS = ("idle_100_local", "movement_100_local", "combat_10_local")
RUNS_MIDDLE_THREE = 5
#: The quiet-window precondition of every measured run (perf-planner, 2026-10-16): 1-minute load average below this and at least this much available
#: memory when the run starts; ``record`` waits up to ``QUIET_WAIT_S`` for it and gives up (exit 1, nothing promotable) rather than measure outside it.
MAX_LOAD_1MIN = 1.5
MIN_AVAILABLE_MB = 2500.0
QUIET_WAIT_S = 900.0
QUIET_POLL_S = 15.0
RULE_ALL_RUNS = "all_runs"
RULE_MIDDLE_THREE = "middle_3"
#: Above this spread (max / min of the average tick latency, minus one) a record is NOISY and not promoted.
NOISY_SPREAD = 0.15
WARMUP_TICKS = 10
SAMPLE_TICKS = 20
#: Sampled ticks of a synthetic record that is not a declared tripwire scenario and whose 20 ticks (about 1 s) were shorter than the host's speed
#: regimes (TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES, investigation.md): the new count is written to ``protocol.measured_ticks``.
SAMPLE_TICKS_OVERRIDE: Dict[str, int] = {"combat_10_local": 100}
#: Iterations of the host-speed probe: a fixed, deterministic pure-Python integer spin, about 50 to 100 ms on this 6-vCPU VM.
PROBE_ITERATIONS = 400_000
#: Probes per side of a run (before and after); the median is what the promotion note carries.
PROBE_CALLS = 5
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
    # waited for TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION (#544): the old mixed_200 records measured a state with two objects on one tile
    "mixed_200_local": ("mixed", 200, "PERF_1GB_LOCAL"),
    "mixed_200_concurrent": ("mixed", 200, "PERF_2GB_CONC"),
}


class RerunError(Exception):
    """A usage or input problem: the tool cannot run and says why."""


def rule_for(name: str) -> str:
    """The spread rule of a record, by name: ``middle_3`` for the three records the owner named, ``all_runs`` (3 runs, spread over all of them) for every other one."""
    return RULE_MIDDLE_THREE if name in MIDDLE_THREE_RECORDS else RULE_ALL_RUNS


def runs_for(name: str) -> int:
    return RUNS_MIDDLE_THREE if rule_for(name) == RULE_MIDDLE_THREE else RUNS


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
        ticks = SAMPLE_TICKS_OVERRIDE.get(name, SAMPLE_TICKS)
        return RunSpec(scenario, entities, profile, "canonical", WARMUP_TICKS, ticks, 42, None, "tripwire", "tripwire_paired")
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


def load_corpus_state(world: str, seed: int) -> Tuple[Any, Any]:
    """The compiled state of a corpus world and its compile report: the one corpus-world loader of ``tools/perf`` (``profile_tick`` uses it too)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from calibrate_simq import _load_world_state  # type: ignore[import-not-found]

    state, report = _load_world_state(world, seed)
    if state is None:
        raise RerunError(f"world {world!r} has no resolved world spec")
    return state, report


def measure_record(name: str, samples_dir: Optional[Path] = None) -> BenchmarkRecord:
    """One measured record of ``name`` in this process. ``samples_dir`` keeps every sampled tick's latency in a file the record points to (OD-6)."""
    from src.perf.bench_harness import BenchHarness

    spec = spec_for(name)
    world: Optional[str] = None
    if spec.scenario.startswith("corpus:"):
        world = spec.scenario.split(":", 1)[1]
        state, report = load_corpus_state(world, spec.seed)
        scenario_id = corpus_name(world)
        region_count = report.get("region_count") if isinstance(report, dict) else None
    else:
        state = build_state(spec.scenario, spec.entities, spec.seed)
        scenario_id = f"{spec.scenario}_{spec.entities}"
        region_count = None
    options = RecordOptions(GateTier(spec.gate_tier), spec.gate_projection, samples_dir, Runner(controlled=False, name=platform.node() or "unknown"))
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


def host_conditions() -> Dict[str, Optional[float]]:
    """The 1-minute load average and the available memory (MB, ``MemAvailable``; ``None`` where ``/proc/meminfo`` cannot be read)."""
    available: Optional[float] = None
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                available = round(float(line.split()[1]) / 1024.0, 1)
                break
    except (OSError, IndexError, ValueError):
        pass
    return {"loadavg_1min": round(os.getloadavg()[0], 2), "available_mb": available}


def wait_for_quiet_window(
    max_load: float = MAX_LOAD_1MIN,
    min_available_mb: float = MIN_AVAILABLE_MB,
    wait_s: float = QUIET_WAIT_S,
    poll_s: float = QUIET_POLL_S,
    read: Callable[[], Dict[str, Optional[float]]] = host_conditions,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Tuple[bool, str]:
    """Poll until the host is quiet (load below ``max_load``, memory at or above ``min_available_mb``) or ``wait_s`` has passed; ``(ok, what was read last)``.

    Memory that cannot be read is not a reason to refuse; load always is. ``wait_s`` 0 checks once.
    """
    deadline = clock() + wait_s
    while True:
        now = read()
        load, available = now["loadavg_1min"], now["available_mb"]
        text = f"loadavg1 {load}, available {available} MB"
        if load is not None and load < max_load and (available is None or available >= min_available_mb):
            return True, text
        if clock() >= deadline:
            return False, text
        sleep(poll_s)


def host_speed_probe(iterations: int = PROBE_ITERATIONS) -> float:
    """Milliseconds a fixed, deterministic pure-Python spin takes right now. The work is identical every call (an integer recurrence, no allocation, no
    I/O), so a change of the result between two calls is the host's speed, not the engine's: ``/proc/stat`` steal and ``cpu MHz`` do not move on this
    VirtualBox guest (investigation.md)."""
    x = 1
    t0 = time.perf_counter()
    for _ in range(iterations):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
    elapsed = (time.perf_counter() - t0) * 1000.0
    if x < 0:  # never true; keeps the loop's result live
        raise AssertionError(x)
    return round(elapsed, 3)


def host_speed_series(calls: int = PROBE_CALLS) -> Dict[str, Any]:
    """``calls`` probes back to back: every value plus their min, median and max (one 50 ms sample says little when regimes last 0.5 to 2 s)."""
    values = [host_speed_probe() for _ in range(calls)]
    return {"values": values, "min": min(values), "median": round(statistics.median(values), 3), "max": max(values)}


def cpu_counters() -> Dict[str, Optional[float]]:
    """Cumulative steal jiffies (``/proc/stat``) and the mean ``cpu MHz`` (``/proc/cpuinfo``); a field is ``None`` when it cannot be read."""
    steal: Optional[float] = None
    mhz: Optional[float] = None
    try:
        for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines():
            if line.startswith("cpu "):
                steal = float(line.split()[8])
                break
    except (OSError, IndexError, ValueError):
        pass
    try:
        values = [float(line.split(":", 1)[1]) for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines() if line.startswith("cpu MHz")]
        mhz = round(sum(values) / len(values), 3) if values else None
    except (OSError, IndexError, ValueError):
        pass
    return {"steal_jiffies": steal, "cpu_mhz": mhz}


@dataclass(frozen=True)
class Run:
    """One of the runs of a record: its average tick latency and the host's load when it started."""

    path: str
    avg_ms: float
    loadavg_1min: float
    swap_used_mb: float
    peak_rss_mb: float
    wall_s: float
    #: Median of 5 host-speed probes (ms) before and after the measured run (before the state build, outside the sampled ticks), ``None`` for a run
    #: measured before the probe existed.
    probe_before_ms: Optional[float] = None
    probe_after_ms: Optional[float] = None


@dataclass(frozen=True)
class Summary:
    runs: Tuple[Run, ...]
    median_index: int
    spread: float
    noisy: bool
    #: ``all_runs`` (spread over every run) or ``middle_3`` (spread over the runs left after the lowest and the highest average are dropped).
    rule: str = RULE_ALL_RUNS
    #: The spread over every run, recorded whichever rule decided NOISY.
    spread_all_runs: float = 0.0


def _spread(values: Sequence[float]) -> float:
    lowest = min(values)
    return (max(values) / lowest - 1.0) if lowest > 0 else float("inf")


def summarize(runs: Sequence[Run], noisy_spread: float = NOISY_SPREAD, rule: str = RULE_ALL_RUNS) -> Summary:
    """The median run (by average tick latency; the lower one for an even count), the spread and whether it is NOISY.

    ``rule`` ``all_runs``: the spread is max / min of every run's average, minus one. ``middle_3``: 5 runs, the lowest and the highest average are dropped and
    the spread is taken over the other 3 (the median run is the same either way); the spread over all runs is recorded too.
    """
    if not runs:
        raise RerunError("no run produced a record")
    order = sorted(range(len(runs)), key=lambda i: runs[i].avg_ms)
    median_index = order[(len(order) - 1) // 2]
    values = [r.avg_ms for r in runs]
    spread_all = _spread(values)
    if rule == RULE_MIDDLE_THREE:
        if len(runs) != RUNS_MIDDLE_THREE:
            raise RerunError(f"the middle_3 rule needs exactly {RUNS_MIDDLE_THREE} runs, got {len(runs)}")
        spread = _spread(sorted(values)[1:-1])
    elif rule == RULE_ALL_RUNS:
        spread = spread_all
    else:
        raise RerunError(f"unknown spread rule {rule!r}")
    return Summary(tuple(runs), median_index, round(spread, 4), spread > noisy_spread, rule, round(spread_all, 4))


def promotion_note(name: str, summary: Summary, host: str) -> str:
    """The text ``baseline_lifecycle promote --note`` records: every run's avg and its load, the spread and the host."""
    parts = [
        f"run {i + 1}: avg {r.avg_ms:.3f} ms, loadavg1 {r.loadavg_1min}, swap {r.swap_used_mb} MB"
        + (f", probe median of {PROBE_CALLS} {r.probe_before_ms} -> {r.probe_after_ms} ms (before the state build)" if r.probe_before_ms is not None and r.probe_after_ms is not None else "")
        for i, r in enumerate(summary.runs)
    ]
    spread_text = (
        f"spread {summary.spread * 100:.1f} % over the middle 3 of {len(summary.runs)} (all {len(summary.runs)}: {summary.spread_all_runs * 100:.1f} %, owner rule 2026-10-16)"
        if summary.rule == RULE_MIDDLE_THREE
        else f"spread {summary.spread * 100:.1f} %"
    )
    return (
        f"{name}: median of {len(summary.runs)} fresh-process runs (promoted run {summary.median_index + 1}); {spread_text}; "
        + "; ".join(parts)
        + f"; host {host}; canonical variant, provisional, claims none (runner.controlled=false)"
    )


def _child_env() -> Dict[str, str]:
    return {**os.environ, "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", "0")}


def cmd_measure(name: str, out: Path, samples_dir: Optional[Path] = None) -> int:
    started = host_load()
    counters_before = cpu_counters()
    probe_before = host_speed_series()
    t0 = time.perf_counter()
    record = measure_record(name, samples_dir)
    wall = time.perf_counter() - t0
    probe_after = host_speed_series()
    counters_after = cpu_counters()
    out.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    meta = {**started, "wall_s": round(wall, 2), "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
            "probe_before": probe_before, "probe_after": probe_after,
            "probe_note": "the before-probe runs before the state build and warm-up (BenchHarness.run_benchmark does both in one call); both sides are outside the sampled ticks", "cpu_before": counters_before, "cpu_after": counters_after}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def cmd_record(name: str, out_root: Path, keep_samples: bool = False, wait_s: float = QUIET_WAIT_S) -> int:
    spec_for(name)  # raises RerunError for an unknown name before anything runs
    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)
    runs: List[Run] = []
    for index in range(1, runs_for(name) + 1):
        path = out_dir / f"run{index}.json"
        quiet, seen = wait_for_quiet_window(wait_s=wait_s)
        if not quiet:
            print(f"cannot run: run {index} of {name} would start outside the quiet window ({seen}; need loadavg1 < {MAX_LOAD_1MIN}, >= {MIN_AVAILABLE_MB:.0f} MB): attempt discarded", file=sys.stderr)
            return 1
        argv = [sys.executable, str(Path(__file__).resolve()), "measure", "--name", name, "--out", str(path)]
        if keep_samples:
            argv += ["--samples-dir", str(out_dir / "samples")]
        done = subprocess.run(argv, env=_child_env(), check=False)
        if done.returncode != 0 or not path.exists():
            print(f"cannot run: run {index} of {name} exited {done.returncode}", file=sys.stderr)
            return 1
        record = BenchmarkRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
        meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
        runs.append(Run(str(path), record.result.latency_ms["avg"], meta["loadavg_1min"], meta["swap_used_mb"], meta["peak_rss_mb"], meta["wall_s"],
                        (meta.get("probe_before") or {}).get("median"), (meta.get("probe_after") or {}).get("median")))
    summary = summarize(runs, rule=rule_for(name))
    median = Path(runs[summary.median_index].path)
    candidate = out_dir / "candidate.json"
    candidate.write_text(median.read_text(encoding="utf-8"), encoding="utf-8")
    cand = BenchmarkRecord.from_dict(json.loads(candidate.read_text(encoding="utf-8")))
    cpu = cand.identity.runtime.cpu_model
    off_normal = sorted({m.mode for m in cand.result.runtime_mode_sequence} - {"NORMAL"})
    host = f"{platform.node()} / {cpu} / {os.cpu_count()} vCPU"
    note = promotion_note(name, summary, host)
    doc = {"name": name, "spread": summary.spread, "spread_all_runs": summary.spread_all_runs, "rule": summary.rule, "noisy": summary.noisy, "off_normal": off_normal, "median_run": summary.median_index + 1, "host": host,
           "runs": [dataclasses.asdict(r) for r in summary.runs], "note": note}
    (out_dir / "summary.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(note)
    if off_normal:
        print(f"NOT A BASELINE: the run left NORMAL ({', '.join(off_normal)}) under the canonical contract; promote would refuse (performance_contract.md 3.1)")
    if summary.noisy:
        print(f"NOISY: spread {summary.spread * 100:.1f} % ({summary.rule}) is above {NOISY_SPREAD * 100:.0f} %: NOT promotable; stays PENDING-NOISY")
    elif not off_normal:
        print(f"PROMOTE: python3 tools/perf/baseline_lifecycle.py promote --candidate {candidate} --name {name} --cause {CAUSE} --note {json.dumps(note)}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record", help="measure a baseline 3 times in fresh processes and pick the median")
    rec.add_argument("name", choices=known_names())
    rec.add_argument("--out-root", type=Path, default=OUT_ROOT)
    rec.add_argument("--wait-s", type=float, default=QUIET_WAIT_S, help="how long to wait before each run for loadavg1 < 1.5 and 2.5 GB available (0 = check once); a run never starts outside that window")
    rec.add_argument("--keep-samples", action="store_true", help="keep every sampled tick's latency of each run under <out>/<name>/samples/ (for a noise diagnosis)")
    mea = sub.add_parser("measure", help="one measured record in this process (the worker of ``record``)")
    mea.add_argument("--name", required=True, choices=known_names())
    mea.add_argument("--out", required=True, type=Path)
    mea.add_argument("--samples-dir", type=Path)
    sub.add_parser("list", help="the baseline names this tool knows")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "list":
            print("\n".join(known_names()))
            return 0
        if args.command == "measure":
            return cmd_measure(args.name, args.out, args.samples_dir)
        return cmd_record(args.name, args.out_root, args.keep_samples, args.wait_s)
    except (RerunError, CapacityRunError) as exc:
        print(f"cannot run: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

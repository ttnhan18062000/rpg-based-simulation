"""Capacity-run projection: N repetitions of a long benchmark, each in a fresh process (PERF-M2-T04).

``python3 tools/perf/capacity_run.py --scenario movement --entities 100 --repetitions 5`` runs ``BenchHarness`` with 100 warmup and 1000
sampled ticks, once per repetition, each repetition in its own subprocess. Every repetition emits one schema-1.1 ``BenchmarkRecord`` with
``gate.tier = capacity_run``, ``gate.projection = capacity_run``, ``runner.controlled = false`` and a ``{uri, sha256}`` pointer to its raw
samples under ``reports/perf/samples/`` (uncommitted). The summary and the records go under ``reports/perf/capacity/<run id>/``.

**It makes no capacity claim.** No controlled runner exists (owner decision OD-5), so a result here is evidence about this host on this day, not
a "sustains X on class Y" statement, and no performance target is enforced. ``pyperf`` is not used (OD-7).

Outcome of an unpaired run, over the repetitions: ``INCONCLUSIVE`` when the tree is dirty (``engine.dirty_src``), a repetition left ``NORMAL`` or
crashed, there is only one repetition, or the coefficient of variation of the average tick latency across repetitions exceeds ``--cv-limit``
(the reason names the variance); otherwise ``NOT_APPLICABLE`` ("no comparison made"). It is never ``PASS``: a pass would read as a capacity claim.

Paired mode (``--base ROOT --head ROOT``, two checkouts) runs every repetition of each side in a fresh process under that side's own ``src/``, assesses
each side the same way, and returns ``compare(base, head)`` of the median repetition of each. A side that cannot emit records (a base from before
``src/perf/benchmark_record.py``) is ``INCONCLUSIVE``.

Exit codes: 0 the run completed and reported (read the printed ``OUTCOME:``: an INCONCLUSIVE or REGRESSION is reported, never blocking, per the M2
lift), 1 it could not run. Not part of default CI.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import platform
import statistics
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT_ENV = "CAPACITY_RUN_ROOT"
#: The checkout whose ``src/`` this process measures. A paired run points each side's worker at its own checkout through ``CAPACITY_RUN_ROOT``.
REPO_ROOT = Path(os.environ.get(ROOT_ENV) or Path(__file__).resolve().parents[2])
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.perf.bench_harness import BenchHarness  # noqa: E402
from src.perf.benchmark_record import (  # noqa: E402
    BenchmarkRecord,
    GateTier,
    Outcome,
    OutcomeState,
    RecordOptions,
    Runner,
    Thresholds,
    compare,
)
from src.perf.profiles import PERF_CANONICAL_PROFILES, PERF_PROFILES  # noqa: E402
from src.perf.scenarios import SCENARIO_BUILDERS  # noqa: E402

DEFAULT_WARMUP = 100
DEFAULT_TICKS = 1000
DEFAULT_REPETITIONS = 5
#: Declared variance limit: coefficient of variation of the average tick latency across repetitions.
DEFAULT_CV_LIMIT = 0.10
NO_CLAIM = "none: runner.controlled=false, no approved runner (PERF-M2 OD-5)"
WORKER_TIMEOUT_S = 3600
_RECORD_PREFIX = "RECORD:"


class CapacityRunError(Exception):
    """A repetition could not produce a record."""


@dataclass(frozen=True)
class RunSpec:
    """Everything one repetition needs; it crosses the process boundary as JSON."""

    scenario: str
    entities: int
    profile: str
    contract: str = "canonical"
    warmup: int = DEFAULT_WARMUP
    ticks: int = DEFAULT_TICKS
    seed: int = 42
    samples_dir: Optional[str] = None
    #: The projection a record is for. Defaults are the capacity run; ``tools/perf/tripwire.py`` uses ``tripwire`` / ``tripwire_paired``.
    gate_tier: str = "capacity_run"
    gate_projection: str = "capacity_run"


def _profile(spec: RunSpec) -> Any:
    table = PERF_CANONICAL_PROFILES if spec.contract == "canonical" else PERF_PROFILES
    if spec.profile not in table:
        raise CapacityRunError(f"unknown profile {spec.profile!r} for contract {spec.contract!r}; choose one of {sorted(table)}")
    return table[spec.profile]


def run_once(spec: RunSpec) -> BenchmarkRecord:
    """One repetition, in this process: a capacity-run record from ``BenchHarness``."""
    if spec.scenario not in SCENARIO_BUILDERS:
        raise CapacityRunError(f"unknown scenario {spec.scenario!r}; choose one of {sorted(SCENARIO_BUILDERS)}")
    state = SCENARIO_BUILDERS[spec.scenario](entity_count=spec.entities, seed=spec.seed)
    harness = BenchHarness(_profile(spec))
    options = RecordOptions(
        GateTier(spec.gate_tier),
        spec.gate_projection,
        Path(spec.samples_dir) if spec.samples_dir else None,
        Runner(controlled=False, name=platform.node() or "unknown"),
    )
    harness.run_benchmark(f"{spec.scenario}_{spec.entities}", state, spec.warmup, spec.ticks, record_options=options)
    if harness.last_record is None:
        raise CapacityRunError("BenchHarness built no record")
    return harness.last_record


def spawn(spec: RunSpec, root: Path) -> BenchmarkRecord:
    """One repetition in a fresh process, measuring the ``src/`` of the checkout at ``root``."""
    env = {**os.environ, ROOT_ENV: str(root)}
    argv = [sys.executable, str(Path(__file__).resolve()), "worker", "--spec", json.dumps(dataclasses.asdict(spec))]
    try:
        done = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True, timeout=WORKER_TIMEOUT_S, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CapacityRunError(f"repetition could not run under {root}: {exc}") from None
    lines = [line for line in done.stdout.splitlines() if line.startswith(_RECORD_PREFIX)]
    if done.returncode != 0 or not lines:
        tail = (done.stderr or done.stdout).strip().splitlines()[-1:] or ["no output"]
        raise CapacityRunError(f"repetition under {root} produced no record (exit {done.returncode}): {tail[0]}")
    return BenchmarkRecord.from_dict(json.loads(lines[-1][len(_RECORD_PREFIX):]))


def assess(records: Sequence[BenchmarkRecord], cv_limit: float = DEFAULT_CV_LIMIT) -> Outcome:
    """The outcome of one side's repetitions: ``INCONCLUSIVE`` with a named reason, or ``NOT_APPLICABLE`` (no comparison, no claim)."""
    if not records:
        return Outcome(OutcomeState.INCONCLUSIVE, "no repetition produced a record")
    if any(r.identity.engine.dirty_src for r in records):
        return Outcome(OutcomeState.INCONCLUSIVE, "dirty_src: the src/ tree has uncommitted changes, so the run is not attributable to a commit")
    off_normal = sorted({run.mode for r in records for run in r.result.runtime_mode_sequence} - {"NORMAL"})
    if off_normal or any(not r.result.runtime_mode_sequence for r in records):
        return Outcome(OutcomeState.INCONCLUSIVE, f"a repetition left NORMAL or recorded no mode sequence ({', '.join(off_normal) or 'empty'})")
    if len(records) < 2:
        return Outcome(OutcomeState.INCONCLUSIVE, "variance cannot be assessed from one repetition")
    averages = [r.result.latency_ms["avg"] for r in records]
    mean = statistics.fmean(averages)
    if mean <= 0:
        return Outcome(OutcomeState.INCONCLUSIVE, "variance: the mean tick latency is zero")
    cv = statistics.stdev(averages) / mean
    if cv > cv_limit:
        return Outcome(OutcomeState.INCONCLUSIVE, f"variance: the coefficient of variation of avg tick latency across {len(records)} repetitions is {cv:.3f}, above the limit {cv_limit:.3f}")
    return Outcome(OutcomeState.NOT_APPLICABLE, f"coefficient of variation {cv:.3f} is within {cv_limit:.3f} across {len(records)} repetitions; no comparison was made; no capacity claim (runner.controlled=false)")


def with_outcome(record: BenchmarkRecord, outcome: Outcome) -> BenchmarkRecord:
    """A copy of ``record`` carrying ``outcome``."""
    return dataclasses.replace(record, result=dataclasses.replace(record.result, outcome=outcome))


def median_record(records: Sequence[BenchmarkRecord]) -> BenchmarkRecord:
    """The repetition with the median average latency (the lower one when the count is even)."""
    ordered = sorted(records, key=lambda r: r.result.latency_ms["avg"])
    return ordered[(len(ordered) - 1) // 2]


def repeat(spec: RunSpec, root: Path, repetitions: int) -> Tuple[List[BenchmarkRecord], Optional[str]]:
    """``repetitions`` fresh-process runs; stops at the first crash and returns what it has plus the crash reason."""
    records: List[BenchmarkRecord] = []
    for _ in range(repetitions):
        try:
            records.append(spawn(spec, root))
        except CapacityRunError as exc:
            return records, str(exc)
    return records, None


def run_unpaired(spec: RunSpec, root: Path, repetitions: int, cv_limit: float) -> Tuple[Outcome, List[BenchmarkRecord]]:
    """N repetitions of ``spec`` under ``root``; each returned record carries the run's outcome."""
    records, crash = repeat(spec, root, repetitions)
    outcome = Outcome(OutcomeState.INCONCLUSIVE, crash) if crash else assess(records, cv_limit)
    return outcome, [with_outcome(r, outcome) for r in records]


def run_paired(
    spec: RunSpec, base_root: Path, head_root: Path, repetitions: int, cv_limit: float, thresholds: Thresholds
) -> Tuple[Outcome, Dict[str, List[BenchmarkRecord]]]:
    """Base and head, each side in fresh processes under its own checkout, then ``compare`` of the median repetition of each."""
    sides: Dict[str, List[BenchmarkRecord]] = {}
    for side, root in (("base", base_root), ("head", head_root)):
        outcome, sides[side] = run_unpaired(spec, root, repetitions, cv_limit)
        if outcome.state is not OutcomeState.NOT_APPLICABLE:
            return Outcome(OutcomeState.INCONCLUSIVE, f"{side} side: {outcome.reason}"), sides
    return compare(median_record(sides["base"]), median_record(sides["head"]), thresholds), sides


def _summary(outcome: Outcome, spec: RunSpec, repetitions: int, cv_limit: float, files: List[str], mode: str) -> Dict[str, Any]:
    return {
        "mode": mode,
        "outcome": {"state": outcome.state.value, "reason": outcome.reason},
        "claim": NO_CLAIM,
        "spec": dataclasses.asdict(spec),
        "repetitions": repetitions,
        "cv_limit": cv_limit,
        "records": files,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def write_run(out_dir: Path, records: Dict[str, List[BenchmarkRecord]], summary_fields: Dict[str, Any]) -> Path:
    """Write every record and ``summary.json`` under ``out_dir``; returns the summary path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files: List[str] = []
    for side, side_records in records.items():
        for index, record in enumerate(side_records, start=1):
            name = f"{side}_rep{index:02d}.json"
            (out_dir / name).write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            files.append(name)
    summary = {**summary_fields, "records": files}
    path = out_dir / "summary.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command")
    worker = sub.add_parser("worker", help="(internal) run one repetition in this process and print its record")
    worker.add_argument("--spec", required=True, help="a RunSpec as JSON")
    parser.add_argument("--scenario", default="movement", choices=sorted(SCENARIO_BUILDERS))
    parser.add_argument("--entities", type=int, default=100)
    parser.add_argument("--profile", default="PERF_1GB_LOCAL", help="a PERF_* profile name")
    parser.add_argument("--contract", choices=("canonical", "live"), default="canonical", help="canonical (default) is the contract timing baselines use")
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP)
    parser.add_argument("--ticks", type=int, default=DEFAULT_TICKS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cv-limit", type=float, default=DEFAULT_CV_LIMIT, help="declared variance limit (coefficient of variation of avg latency)")
    parser.add_argument("--base", type=Path, help="paired mode: the base checkout")
    parser.add_argument("--head", type=Path, help="paired mode: the head checkout (default: this one)")
    parser.add_argument("--out-dir", type=Path, help="default: reports/perf/capacity/<run id>")
    parser.add_argument("--samples-dir", help="where raw samples go (default: reports/perf/samples)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point (see the module docstring for the exit codes)."""
    args = _build_parser().parse_args(argv)
    if args.command == "worker":
        record = run_once(RunSpec(**json.loads(args.spec)))
        print(_RECORD_PREFIX + json.dumps(record.to_dict(), sort_keys=True))
        return 0
    spec = RunSpec(args.scenario, args.entities, args.profile, args.contract, args.warmup, args.ticks, args.seed, args.samples_dir)
    out_dir = args.out_dir or REPO_ROOT / "reports" / "perf" / "capacity" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:6])
    try:
        _profile(spec)
        if args.base:
            outcome, sides = run_paired(spec, args.base, args.head or REPO_ROOT, args.repetitions, args.cv_limit, Thresholds())
            mode = "paired"
        else:
            outcome, records = run_unpaired(spec, REPO_ROOT, args.repetitions, args.cv_limit)
            sides, mode = {"head": records}, "unpaired"
    except CapacityRunError as exc:
        print(f"cannot run: {exc}", file=sys.stderr)
        return 1
    path = write_run(out_dir, sides, _summary(outcome, spec, args.repetitions, args.cv_limit, [], mode))
    print(f"OUTCOME: {outcome.state.value}: {outcome.reason}")
    print(f"CLAIM: {NO_CLAIM}")
    print(f"SUMMARY: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

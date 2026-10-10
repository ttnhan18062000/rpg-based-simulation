"""The CI-fast performance tripwire: base and head, paired on one runner, each side in a fresh process (PERF-M2-T03, owner decision OD-2).

``python3 tools/perf/tripwire.py run --base /tmp/base-checkout --head .`` runs every scenario in ``TRIPWIRE_SCENARIOS`` (10 warmup, 50 sampled ticks, the
canonical signal contract) once on the base checkout and once on the head checkout, each in its own subprocess under that checkout's own ``src/``, and
passes both ``BenchmarkRecord`` s to ``compare(base, head, TRIPWIRE_THRESHOLDS)``. Both sides share one runtime identity, so ``cpu_model`` can stay blocking
without making every pull request INCONCLUSIVE.

**It makes no capacity claim and blocks nothing.** The outcome per scenario is ``PASS``, ``REGRESSION`` or ``INCONCLUSIVE`` with a reason. The process
exits 0 whatever the outcomes (read the report, or the ``::warning`` annotations with ``--github-annotations``); it exits 1 only when it could not run.

**One diagnostic retry.** A scenario whose first comparison is not ``PASS`` is run once more, and the report carries both outcomes. The retry never turns
a failure into a pass: when the two disagree the result is ``INCONCLUSIVE`` ("not reproducible"). Repeating until one sample passes is forbidden.

``calibrate`` runs the same code against itself (A/A) and reports how far a head/base ratio moves with no code change, which is the evidence the noise
budget in ``TRIPWIRE_THRESHOLDS`` has to sit above.

``load_baseline`` / ``compare_with_baseline`` serve the nightly lane (``tests/perf/test_perf_regression_baseline.py``): head against a promoted baseline
record, with a missing or legacy baseline reported as ``INCONCLUSIVE`` and a named reason, never as a skip.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import statistics
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

_SELF_ROOT = Path(__file__).resolve().parents[2]
if str(_SELF_ROOT) not in sys.path:  # run as a script, ``tools`` is not importable until the repository root is on the path
    sys.path.insert(0, str(_SELF_ROOT))

from tools.perf import baseline_lifecycle, capacity_run  # noqa: E402
from tools.perf.capacity_run import REPO_ROOT, CapacityRunError, RunSpec  # noqa: E402

from src.perf.benchmark_record import BenchmarkRecord, Outcome, OutcomeState, Thresholds, compare  # noqa: E402

WARMUP_TICKS = 10
SAMPLE_TICKS = 50
#: The declared scenario set: small, so a pull request pays for two fresh processes per scenario. The names are the committed baseline names, so a
#: promotion by ``baseline_lifecycle`` lands under them. Combat and the corpus worlds are PERF-M2-T08's.
TRIPWIRE_SCENARIOS: Tuple[Tuple[str, RunSpec], ...] = tuple(
    (name, RunSpec(scenario, entities, profile, "canonical", WARMUP_TICKS, SAMPLE_TICKS, 42, None, "tripwire", "tripwire_paired"))
    for name, scenario, entities, profile in (
        ("idle_100_local", "idle", 100, "PERF_512MB_LOCAL"),
        ("movement_100_local", "movement", 100, "PERF_1GB_LOCAL"),
    )
)
#: The noise budget: the largest head/base deviation seen with *identical* code on both sides (``calibrate``, 2026-10-10, this 6-vCPU VM, 22 A/A pairs per
#: scenario, 44 in all, idle_100_local and movement_100_local): 0.35 for avg latency of idle_100_local (0.31 for movement_100_local). The median was no steadier
#: (up to 0.40 for movement), so the noise is whole-process variance, not tail ticks. It is the host's, not the engine's: recalibrate on the CI runner.
NOISE_BUDGET = 0.35
#: relative + absolute floor (``compare`` regresses above ``max(absolute_ms, base * (1 + relative))``). ``relative`` must clear ``NOISE_BUDGET`` (a test
#: pins that), so on this host the tripwire detects only changes above about 40%: a finer tripwire needs a quieter runner or a larger sample, not a tighter
#: number. The margin is small (0.35 against 0.40). PROVISIONAL: owner-approved 2026-10-10 as provisional (docs/engine/performance_contract.md section 5).
TRIPWIRE_THRESHOLDS = Thresholds(relative=0.40, absolute_ms=5.0, metric="avg")
MAX_RETRIES = 1

Spawn = Callable[[RunSpec, Path], BenchmarkRecord]


@dataclass(frozen=True)
class Attempt:
    """One paired comparison of a scenario."""

    outcome: Outcome
    base_avg_ms: Optional[float] = None
    head_avg_ms: Optional[float] = None
    #: False when a side could not produce a record: a retry would fail the same way and only cost runtime.
    retryable: bool = True


@dataclass(frozen=True)
class ScenarioResult:
    """The result for one scenario: the first attempt, the diagnostic retry if there was one, and the reported outcome."""

    name: str
    first: Attempt
    retry: Optional[Attempt]
    outcome: Outcome


def _avg(record: Optional[BenchmarkRecord]) -> Optional[float]:
    return record.result.latency_ms.get("avg") if record is not None else None


def pair(spec: RunSpec, base_root: Path, head_root: Path, thresholds: Thresholds, spawn: Spawn, head_first: bool = False) -> Attempt:
    """One base run and one head run, each in a fresh process, compared. A side that cannot produce a record is INCONCLUSIVE.

    ``head_first`` swaps the order of the two runs. The diagnostic retry uses it, so a systematic order effect (a warm cache, thermal state) cannot show up
    as a regression in both attempts.
    """
    records: Dict[str, BenchmarkRecord] = {}
    sides = [("base", base_root), ("head", head_root)]
    for side, root in reversed(sides) if head_first else sides:
        try:
            records[side] = spawn(spec, root)
        except CapacityRunError as exc:
            return Attempt(Outcome(OutcomeState.INCONCLUSIVE, f"{side} side: {exc}"), retryable=False)
    return Attempt(compare(records["base"], records["head"], thresholds), _avg(records["base"]), _avg(records["head"]))


def _final(first: Attempt, retry: Optional[Attempt]) -> Outcome:
    if retry is None:
        return first.outcome
    if retry.outcome.state is first.outcome.state:
        return Outcome(first.outcome.state, f"{first.outcome.reason} (reproduced on the diagnostic retry)")
    return Outcome(
        OutcomeState.INCONCLUSIVE,
        f"not reproducible: the first run was {first.outcome.state.value} ({first.outcome.reason}) and the retry was {retry.outcome.state.value} ({retry.outcome.reason})",
    )


def run_scenario(
    name: str, spec: RunSpec, base_root: Path, head_root: Path, thresholds: Thresholds = TRIPWIRE_THRESHOLDS, spawn: Spawn = capacity_run.spawn
) -> ScenarioResult:
    """The first paired comparison, and at most ``MAX_RETRIES`` diagnostic retry (head first) when it is not PASS and a retry could change it."""
    first = pair(spec, base_root, head_root, thresholds, spawn)
    needs_retry = first.retryable and first.outcome.state not in (OutcomeState.PASS, OutcomeState.NOT_APPLICABLE) and MAX_RETRIES >= 1
    retry = pair(spec, base_root, head_root, thresholds, spawn, head_first=True) if needs_retry else None
    return ScenarioResult(name, first, retry, _final(first, retry))


def run_all(
    base_root: Path,
    head_root: Path,
    scenarios: Sequence[Tuple[str, RunSpec]] = TRIPWIRE_SCENARIOS,
    thresholds: Thresholds = TRIPWIRE_THRESHOLDS,
    spawn: Spawn = capacity_run.spawn,
) -> List[ScenarioResult]:
    """Every declared scenario, in order."""
    return [run_scenario(name, spec, base_root, head_root, thresholds, spawn) for name, spec in scenarios]


def _attempt_dict(attempt: Optional[Attempt]) -> Optional[Dict[str, Any]]:
    if attempt is None:
        return None
    return {
        "state": attempt.outcome.state.value,
        "reason": attempt.outcome.reason,
        "base_avg_ms": attempt.base_avg_ms,
        "head_avg_ms": attempt.head_avg_ms,
    }


def report(results: Sequence[ScenarioResult], thresholds: Thresholds = TRIPWIRE_THRESHOLDS) -> Dict[str, Any]:
    """The machine-readable report. ``blocking`` is always false: a tripwire outcome never fails a build (OD-8)."""
    return {
        "projection": "tripwire_paired",
        "blocking": False,
        "claim": capacity_run.NO_CLAIM,
        "thresholds": dataclasses.asdict(thresholds),
        "protocol": {"warmup_ticks": WARMUP_TICKS, "sample_ticks": SAMPLE_TICKS, "max_retries": MAX_RETRIES},
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "scenarios": [
            {
                "name": r.name,
                "outcome": {"state": r.outcome.state.value, "reason": r.outcome.reason},
                "first": _attempt_dict(r.first),
                "retry": _attempt_dict(r.retry),
            }
            for r in results
        ],
    }


def annotations(results: Sequence[ScenarioResult]) -> List[str]:
    """GitHub annotation lines: a ``::warning`` for every scenario that is not PASS, a ``::notice`` for the rest. Neither fails the job."""
    lines = []
    for r in results:
        level = "notice" if r.outcome.state is OutcomeState.PASS else "warning"
        lines.append(f"::{level} title=perf tripwire {r.name}::{r.outcome.state.value}: {r.outcome.reason}")
    return lines


# ── the nightly lane: head against a promoted baseline record ────────────────────────────────────────────────────────────────


def load_baseline(name: str, baselines_dir: Path = baseline_lifecycle.DEFAULT_BASELINES_DIR) -> Tuple[Optional[BenchmarkRecord], str]:
    """The latest promoted version of baseline ``name``, or ``(None, reason)``. A legacy file has no identity, so it is a reason, not a baseline."""
    versions = baseline_lifecycle.version_files(baselines_dir, name)
    if versions:
        try:
            data = json.loads(versions[-1][1].read_text(encoding="utf-8"))
            return BenchmarkRecord.from_dict({k: v for k, v in data.items() if k != "promotion"}), ""
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return None, f"the latest promoted version {versions[-1][1].name} is not a valid record: {exc}"
    if (baselines_dir / f"{name}.json").exists():
        return None, f"{name}.json is a legacy tripwire reference with no recorded identity; PERF-M2-T08 re-records it through baseline_lifecycle promote"
    return None, f"no baseline named {name} exists in {baselines_dir}"


def compare_with_baseline(baseline: Optional[BenchmarkRecord], reason: str, head: Optional[BenchmarkRecord], thresholds: Thresholds = TRIPWIRE_THRESHOLDS) -> Outcome:
    """``compare`` of a head record against a loaded baseline; a missing baseline is INCONCLUSIVE with its named reason, never a skip."""
    if baseline is None:
        return Outcome(OutcomeState.INCONCLUSIVE, reason or "no baseline record")
    return compare(baseline, head, thresholds)


# ── calibration ──────────────────────────────────────────────────────────────────────────────────────────────────────────────


CALIBRATION_METRICS = ("avg", "p50")


def calibrate(root: Path, trials: int, scenarios: Sequence[Tuple[str, RunSpec]] = TRIPWIRE_SCENARIOS, spawn: Spawn = capacity_run.spawn) -> Dict[str, Any]:
    """A/A: the same code as base and as head, ``trials`` times per scenario. Reports, per latency metric, how far head/base moves with no code change."""
    out: Dict[str, Any] = {}
    for name, spec in scenarios:
        pairs = []
        for trial in range(trials):
            if trial % 2 == 0:
                base = spawn(spec, root)
                head = spawn(spec, root)
            else:  # alternate which run goes first, so an order effect shows up as a bias between the two groups
                head = spawn(spec, root)
                base = spawn(spec, root)
            pairs.append((base, head))
        per_metric: Dict[str, Any] = {}
        for metric in CALIBRATION_METRICS:
            ratios = [head.result.latency_ms[metric] / base.result.latency_ms[metric] for base, head in pairs]
            deviations = [abs(r - 1.0) for r in ratios]
            per_metric[metric] = {
                "ratios": [round(r, 4) for r in ratios],
                "max_deviation": round(max(deviations), 4),
                "mean_deviation": round(statistics.fmean(deviations), 4),
                "mean_ratio_base_first": round(statistics.fmean(ratios[0::2]), 4),
                "mean_ratio_head_first": round(statistics.fmean(ratios[1::2]), 4) if len(ratios) > 1 else None,
            }
        out[name] = {"trials": trials, "metrics": per_metric}
    return out


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="paired base/head tripwire over the declared scenarios")
    run.add_argument("--base", type=Path, required=True, help="the base checkout")
    run.add_argument("--head", type=Path, default=REPO_ROOT, help="the head checkout (default: this one)")
    run.add_argument("--scenario", action="append", help="limit to this declared scenario (repeatable)")
    run.add_argument("--out-dir", type=Path)
    run.add_argument("--github-annotations", action="store_true", help="print ::warning/::notice lines")
    cal = sub.add_parser("calibrate", help="A/A noise measurement on this checkout")
    cal.add_argument("--trials", type=int, default=5)
    cal.add_argument("--root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. 0: it ran and reported (whatever the outcomes). 1: it could not run."""
    args = _parser().parse_args(argv)
    if args.command == "calibrate":
        print(json.dumps(calibrate(args.root, args.trials), indent=2, sort_keys=True))
        return 0
    chosen = [(n, s) for n, s in TRIPWIRE_SCENARIOS if not args.scenario or n in args.scenario]
    if not chosen:
        print(f"cannot run: no declared scenario matches {args.scenario}; declared: {[n for n, _ in TRIPWIRE_SCENARIOS]}", file=sys.stderr)
        return 1
    results = run_all(args.base, args.head, chosen)
    out_dir = args.out_dir or REPO_ROOT / "reports" / "perf" / "tripwire" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:6])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report(results), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for r in results:
        print(f"{r.name}: {r.outcome.state.value}: {r.outcome.reason}")
    if args.github_annotations:
        print("\n".join(annotations(results)))
    print(f"REPORT: {out_dir / 'report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

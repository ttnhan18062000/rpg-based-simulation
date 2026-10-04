#!/usr/bin/env python3
# Compliance IDs: PERF-001, PERF-004, PERF-011
"""
Optimization Proof Report Generator for V2 Engine.

Runs the 5 core benchmark scenarios and compares each one against ``reports/perf/baseline.json``.
A scenario is compared only when the baseline entry and the current run have the same profile and
sample-tick count (and the same warmup count, where both record it). Otherwise it is reported as
``not_comparable`` with the reason, and no ratio is computed. Nothing is defaulted: a missing
measured value makes the scenario not comparable.

Every number in the report is provisional under the RPG-core stability entry gate and is not a
capacity claim (TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS).
"""

from __future__ import annotations

import inspect
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config.profiles import PROD_DEFAULT, PROD_LARGE
from src.perf.bench_harness import BenchHarness
from src.perf.scenarios import SCENARIO_BUILDERS
from tools.perf.perf_baseline import validate_latest

REPORTS_DIR = Path("reports/perf")
BASELINE_PATH = REPORTS_DIR / "baseline.json"
PROOF_JSON_PATH = REPORTS_DIR / "optimization_proof.json"
PROOF_MD_PATH = REPORTS_DIR / "optimization_proof.md"

# Flags passed to every run; the audit section reports exactly these.
RUN_FLAGS = {"no_replay": True, "no_frame_pacing": True}
FULL_WARMUP_TICKS = 20
QUICK_WARMUP_TICKS = 5
QUICK_SAMPLE_TICKS = 10

SCENARIO_CONFIGS = {
    "MOVEMENT_1000": {
        "builder": "movement",
        "kwargs": {"entity_count": 1000},
        "profile": PROD_DEFAULT,
        "sample_ticks": 50,
    },
    "RESOURCE_1000": {
        "builder": "resource",
        "kwargs": {"entity_count": 700, "node_count": 300},
        "profile": PROD_DEFAULT,
        "sample_ticks": 50,
    },
    "COMBAT_100": {
        "builder": "combat",
        "kwargs": {"team_a_count": 50, "team_b_count": 50},
        "profile": PROD_DEFAULT,
        "sample_ticks": 50,
    },
    "STRATEGIC_500": {
        "builder": "strategic",
        "kwargs": {"entity_count": 500},
        "profile": PROD_DEFAULT,
        "sample_ticks": 50,
    },
    "MIXED_1000": {
        "builder": "mixed",
        "kwargs": {"entity_count": 1000},
        "profile": PROD_LARGE,
        "sample_ticks": 50,
    },
}

# What the comparison cannot see because the baseline does not record it. "compared" therefore means
# only that profile and sample_ticks matched (warmup_ticks is checked only if both sides ever carry it).
UNCHECKED_IDENTITY = ("workload cardinality (builder kwargs)", "warmup_ticks", "run flags")

STATUS_COMPARED = "compared"
STATUS_NOT_COMPARABLE = "not_comparable"


def _number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _baseline_values(base: Dict[str, Any]) -> Dict[str, Optional[float]]:
    tps = base.get("compute_tps", base.get("avg_tps"))
    return {
        "tps": _number(tps),
        "p95_ms": _number((base.get("tick_ms") or {}).get("p95")),
        "peak_rss_mb": _number((base.get("mem_rss_mb") or {}).get("max")),
    }


def _current_values(res: Dict[str, Any]) -> Dict[str, Optional[float]]:
    return {
        "tps": _number(res.get("compute_tps")),
        "p95_ms": _number((res.get("tick_ms") or {}).get("p95")),
        "peak_rss_mb": _number((res.get("mem_rss_mb") or {}).get("max")),
    }


def compare_scenario(
    name: str,
    base: Optional[Dict[str, Any]],
    res: Dict[str, Any],
    warmup_ticks: int,
    workload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compare one scenario. Pure: returns the JSON record for it, never raises on bad data."""
    base = base if isinstance(base, dict) else None
    b = _baseline_values(base) if base else {"tps": None, "p95_ms": None, "peak_rss_mb": None}
    o = _current_values(res)

    reasons: List[str] = []
    if base is None:
        reasons.append(f"scenario {name} is absent from the baseline")
    else:
        for field in ("profile", "sample_ticks"):
            if field not in base:
                reasons.append(f"baseline has no {field}")
            elif base[field] != res.get(field):
                reasons.append(f"{field} differs: baseline={base[field]!r} current={res.get(field)!r}")
        # warmup_ticks is compared only when both sides record it (the harness dict does not today).
        if "warmup_ticks" in base and "warmup_ticks" in res and base["warmup_ticks"] != res["warmup_ticks"]:
            reasons.append(
                f"warmup_ticks differs: baseline={base['warmup_ticks']!r} current={res['warmup_ticks']!r}"
            )
        for label, key in (("TPS", "tps"), ("p95", "p95_ms"), ("peak RSS", "peak_rss_mb")):
            if b[key] is None:
                reasons.append(f"baseline is missing {label}")
    for label, key in (("TPS", "tps"), ("p95", "p95_ms"), ("peak RSS", "peak_rss_mb")):
        if o[key] is None:
            reasons.append(f"current run is missing {label}")
    if not reasons:
        if b["tps"] <= 0:
            reasons.append(f"baseline TPS is not positive ({b['tps']})")
        if o["p95_ms"] <= 0:
            reasons.append(f"current p95 is not positive ({o['p95_ms']})")

    record: Dict[str, Any] = {
        "scenario": name,
        "status": STATUS_NOT_COMPARABLE if reasons else STATUS_COMPARED,
        "baseline": {
            "tps": b["tps"],
            "p95_ms": b["p95_ms"],
            "peak_rss_mb": b["peak_rss_mb"],
            "profile": base.get("profile") if base else None,
            "sample_ticks": base.get("sample_ticks") if base else None,
            "phase_breakdown": (base or {}).get("phase_breakdown", {}),
        },
        "optimized": {
            "tps": o["tps"],
            "p95_ms": o["p95_ms"],
            "peak_rss_mb": o["peak_rss_mb"],
            "profile": res.get("profile"),
            "sample_ticks": res.get("sample_ticks"),
            "warmup_ticks": warmup_ticks,
            "workload": dict(workload) if workload is not None else None,
            "phase_breakdown": res.get("phase_breakdown", {}),
            "metrics": res.get("metrics", {}),
        },
    }
    if reasons:
        record["reason"] = "; ".join(reasons)
    else:
        record["speedup_x"] = round(o["tps"] / b["tps"], 2)
        record["latency_reduction_x"] = round(b["p95_ms"] / o["p95_ms"], 2)
    return record


def _builder_seed(builder_fn: Any) -> Any:
    try:
        param = inspect.signature(builder_fn).parameters.get("seed")
    except (TypeError, ValueError):
        return None
    if param is None or param.default is inspect.Parameter.empty:
        return None
    return param.default


def summarize(comparisons: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Counts and ranges computed from the comparison records only."""
    compared = [c for c in comparisons.values() if c["status"] == STATUS_COMPARED]
    not_comparable = [c for c in comparisons.values() if c["status"] == STATUS_NOT_COMPARABLE]
    speedups = [c["speedup_x"] for c in compared]
    return {
        "total": len(comparisons),
        "compared": len(compared),
        "not_comparable": len(not_comparable),
        "faster": sum(1 for s in speedups if s > 1),
        "slower": sum(1 for s in speedups if s < 1),
        "unchanged": sum(1 for s in speedups if s == 1),
        "min_speedup_x": min(speedups) if speedups else None,
        "max_speedup_x": max(speedups) if speedups else None,
    }


def run_proof(quick_test: bool = False) -> Dict[str, Any]:
    print("Starting V2 Engine Optimization Proof Execution...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if not BASELINE_PATH.exists():
        print(f"Baseline file not found at {BASELINE_PATH}")
        sys.exit(1)

    with open(BASELINE_PATH, "r") as f:
        try:
            baseline_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"{BASELINE_PATH} is not valid JSON ({e})")
            sys.exit(1)

    problem = validate_latest(baseline_data)
    if problem:
        print(f"Refusing to run: {BASELINE_PATH} is not a scenario-keyed baseline: {problem}")
        sys.exit(1)

    proof_results: Dict[str, Any] = {
        "metadata": {
            "timestamp": time.time(),
            "quick_test": quick_test,
            "provisional": True,
            "unchecked_identity": list(UNCHECKED_IDENTITY),
            "run_flags": dict(RUN_FLAGS),
            "seeds": {},
        },
        "comparisons": {},
    }

    for name, cfg in SCENARIO_CONFIGS.items():
        print(f"\n--- Benchmarking Scenario: {name} ---")
        builder_fn = SCENARIO_BUILDERS[cfg["builder"]]
        initial_state = builder_fn(**cfg["kwargs"])
        proof_results["metadata"]["seeds"][name] = _builder_seed(builder_fn)

        sample_ticks = QUICK_SAMPLE_TICKS if quick_test else cfg["sample_ticks"]
        warmup_ticks = QUICK_WARMUP_TICKS if quick_test else FULL_WARMUP_TICKS

        harness = BenchHarness(cfg["profile"])
        res = harness.run_benchmark(
            scenario_id=name,
            initial_state=initial_state,
            warmup_ticks=warmup_ticks,
            sample_ticks=sample_ticks,
            flags=dict(RUN_FLAGS),
        )

        record = compare_scenario(name, baseline_data.get(name), res, warmup_ticks, cfg["kwargs"])
        proof_results["comparisons"][name] = record
        if record["status"] == STATUS_COMPARED:
            print(f"  {name}: compared; speedup {record['speedup_x']}x, latency reduction {record['latency_reduction_x']}x")
        else:
            print(f"  {name}: NOT COMPARABLE: {record['reason']}")

    proof_results["summary"] = summarize(proof_results["comparisons"])

    with open(PROOF_JSON_PATH, "w") as f:
        json.dump(proof_results, f, indent=2)
    print(f"\nSaved JSON proof data to {PROOF_JSON_PATH}")

    generate_markdown_report(proof_results)
    return proof_results


def _fmt(value: Any, spec: str = ".1f") -> str:
    return "-" if value is None else format(value, spec)


def generate_markdown_report(proof_results: Dict[str, Any]) -> None:
    meta = proof_results["metadata"]
    comparisons = proof_results["comparisons"]
    summary = summarize(comparisons)

    md = [
        "# V2 RPG Engine Optimization Proof Report",
        f"\n**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(meta['timestamp']))}",
        "\n> **Provisional.** Every number in this report is provisional under the RPG-core stability "
        "entry gate, and none of it is a capacity claim.",
        "\n## Summary",
        f"\n{summary['compared']} of {summary['total']} scenarios were compared against the baseline; "
        f"{summary['not_comparable']} were not comparable.",
        "\nComparability was checked on profile and sample_ticks only; "
        f"{', '.join(meta.get('unchecked_identity', UNCHECKED_IDENTITY))} "
        "are not recorded in the baseline and were not checked.",
    ]
    if summary["compared"]:
        md.append(
            f"\nAmong the compared scenarios, {summary['faster']} were faster, {summary['slower']} slower and "
            f"{summary['unchanged']} unchanged in TPS; the speedup ranged from {summary['min_speedup_x']}x "
            f"to {summary['max_speedup_x']}x."
        )
    not_comparable = [c for c in comparisons.values() if c["status"] == STATUS_NOT_COMPARABLE]
    if not_comparable:
        md.append("\nNot comparable:\n")
        for c in not_comparable:
            md.append(f"- **{c['scenario']}**: {c['reason']}")

    md.extend([
        "\n## Comparison Matrix",
        "\nRatios appear only for compared scenarios.",
        "\n| Scenario | Status | Baseline TPS | Optimized TPS | Speedup (x) | Baseline p95 (ms) | Optimized p95 (ms) | Latency Red. (x) | Peak RSS (MB) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])
    for name, data in comparisons.items():
        compared = data["status"] == STATUS_COMPARED
        md.append(
            f"| **{name}** | {data['status']} | {_fmt(data['baseline']['tps'])} | {_fmt(data['optimized']['tps'])} | "
            f"{data['speedup_x'] if compared else '-'} | {_fmt(data['baseline']['p95_ms'])} | "
            f"{_fmt(data['optimized']['p95_ms'])} | {data['latency_reduction_x'] if compared else '-'} | "
            f"{_fmt(data['optimized']['peak_rss_mb'])} |"
        )

    md.extend([
        "\n## Recorded Counters",
        "\nCounters recorded during the optimized run, as measured; no interpretation is attached.",
        "\n```json",
        json.dumps({k: v["optimized"].get("metrics", {}) for k, v in comparisons.items()}, indent=2),
        "```",
        "\n## Audit Statement",
        "\nWhat the code set for this run:",
        f"\n- quick_test: {meta['quick_test']}",
        f"- run flags: {json.dumps(meta.get('run_flags', {}), sort_keys=True)}",
    ])
    for name, data in comparisons.items():
        opt = data["optimized"]
        seed = meta.get("seeds", {}).get(name)
        md.append(
            f"- {name}: profile={opt['profile']}, warmup_ticks={opt['warmup_ticks']}, "
            f"sample_ticks={opt['sample_ticks']}, seed={'builder default ' + str(seed) if seed is not None else 'not recorded'}"
        )

    with open(PROOF_MD_PATH, "w") as f:
        f.write("\n".join(md) + "\n")
    print(f"Saved Markdown proof report to {PROOF_MD_PATH}")


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    results = run_proof(quick_test="--quick" in argv)
    if results["summary"]["compared"] == 0:
        print("No scenario was comparable; the reports were written but this run proves nothing.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

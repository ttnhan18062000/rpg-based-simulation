"""The child process of the rpg gate harness: one (world, seed) run, or one world's pooling. See ``rpg_gate_harness`` for the contract."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import resource
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SCHEMA = "rpg-gate-metrics/v1"


def _resolve(spec: str, attr_default: str) -> Callable[..., Any]:
    """``module`` -> ``module.<attr_default>``; ``module:attr`` names the function itself."""
    module_name, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module_name), attr or attr_default)


def _write(path: Path, doc: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)  # Linux reports KiB


@dataclass(frozen=True)
class RunArtifacts:
    """What the harness hands rpg's ``compute``: the run's identity, its final state and its recorded run directory (typed events and death records)."""

    world: str
    seed: int
    ticks: int
    sha: str
    state: Any
    run_dir: Path

    @property
    def events_path(self) -> Path:
        return self.run_dir / "simulation_events.jsonl"


def build_kernel(world: str, seed: int, run_id: str):
    """The pinned kernel: pinned governor, sequential executor, audit mode (no wall-clock throttle), no frame pacing."""
    from src.config.profiles import PROD_SMALL
    from src.engine.executor import LocalSequentialExecutor
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from tests.helpers.kernel_pinning import PinnedNormalGovernor
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context(world)
    state, _report = WorldCompiler.compile(spec, seed, context=context)
    return Kernel(
        PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state, DeterministicRNG(seed),
        governor=PinnedNormalGovernor(), executor=LocalSequentialExecutor(),
        flags={"audit_mode": True, "no_frame_pacing": True}, run_id=run_id,
    )


def run(args: argparse.Namespace) -> int:
    compute = _resolve(args.metrics_module, "compute")
    kernel = build_kernel(args.world, args.seed, args.run_id)
    try:
        for _ in range(args.ticks):
            kernel.tick_once()
    finally:
        kernel.shutdown()  # flushes the recorded event stream before the metrics read it
    run_dir = Path("data") / "runs" / args.run_id
    result = compute(RunArtifacts(args.world, args.seed, args.ticks, args.sha, kernel.state, run_dir))
    metrics = result["metrics"] if isinstance(result, dict) else result  # rpg returns a whole document; the harness writes the header itself
    doc = {"schema": SCHEMA, "status": "ok", "world": args.world, "seed": args.seed, "ticks": args.ticks, "sha": args.sha, "harness_hash": args.harness_hash, "metrics": list(metrics)}
    out = Path(args.out)
    _write(out, doc)
    _write(out.with_name(out.name + ".cost.json"), {"peak_rss_mb": _peak_rss_mb()})
    return 0


def pool(args: argparse.Namespace) -> int:
    pool_fn = _resolve(args.metrics_module, "pool")
    docs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.docs]
    metrics = pool_fn(docs)
    _write(Path(args.out), {"schema": SCHEMA, "status": "ok", "world": args.world, "ticks": args.ticks, "sha": args.sha, "harness_hash": args.harness_hash, "metrics": list(metrics)})
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    for name in ("--world", "--metrics-module", "--sha", "--harness-hash", "--out"):
        common.add_argument(name, required=True)
    common.add_argument("--ticks", type=int, required=True)
    r = sub.add_parser("run", parents=[common])
    r.add_argument("--seed", type=int, required=True)
    r.add_argument("--run-id", required=True)
    p = sub.add_parser("pool", parents=[common])
    p.add_argument("--docs", nargs="+", required=True)
    args = parser.parse_args(argv)
    return run(args) if args.cmd == "run" else pool(args)


if __name__ == "__main__":
    sys.exit(main())

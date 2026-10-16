"""Counterfactual for TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION (a reproduction script kept with the ticket, not a maintained tool).

Question: is the kernel's ``resolution_overhead`` mostly ``StrategicIntelligenceSystem.fused_strategic_pass``, whose time the shadowed ``t_start`` in
``AuthoritativeApplyPipeline.refine`` (``src/engine/pipeline.py:431``) leaves unattributed? It wraps that class attribute with a timer in THIS process only
(no ``src/`` edit; ``run_phase``'s lambda looks the attribute up at call time, so the wrapper is seen) and runs the same seed twice, unwrapped then wrapped.

Proof the wrapper is inert: the end-of-run ``state.fingerprint()`` (sha256 of its sorted JSON) must be identical with and without the wrapper, and the
wrapper's own cost (two ``perf_counter_ns`` reads and a list append per call, calibrated on a no-op) is reported per tick.

Report per scenario: wrapped ms per tick, ``resolution_overhead`` per tick (from the unwrapped run and from the wrapped run), the residual after subtracting
(overhead - wrapped) and its share of the overhead; AC1 is met when the residual share is below 20 %.

Run from the repo root with the venv python:  .venv/bin/python3 <this file> --scenario idle --entities 100 --warmup 10 --ticks 30 --contract pinned
``--selftest`` checks the wrapper and the arithmetic on a stub class without running the engine. Heavy scenarios (corpus worlds, movement_2000) need lead's go.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class CallTimer:
    """Wrap ``owner.<name>`` (a staticmethod/classmethod/function on a class) with a timer; ``restore()`` puts the original back."""

    def __init__(self, owner: Any, name: str) -> None:
        self.owner, self.name = owner, name
        self.original = owner.__dict__[name]
        self.calls_ms: List[float] = []
        inner = getattr(owner, name)
        calls = self.calls_ms

        def timed(*args: Any, **kwargs: Any) -> Any:
            t0 = time.perf_counter_ns()
            try:
                return inner(*args, **kwargs)
            finally:
                calls.append((time.perf_counter_ns() - t0) / 1e6)

        self.timed = timed

    def install(self) -> None:
        setattr(self.owner, self.name, staticmethod(self.timed))

    def restore(self) -> None:
        setattr(self.owner, self.name, self.original)

    def take(self) -> float:
        """Total ms of the calls since the last ``take`` (one tick's worth)."""
        total = sum(self.calls_ms)
        self.calls_ms.clear()
        return total


def fingerprint_hash(state: Any) -> str:
    return hashlib.sha256(json.dumps(state.fingerprint(), sort_keys=True, default=str).encode()).hexdigest()


def wrapper_overhead_ms_per_call(samples: int = 200_000) -> float:
    """Cost of the wrapper itself, calibrated on a no-op static method."""

    class Probe:
        @staticmethod
        def noop() -> None:
            return None

    bare = time.perf_counter_ns()
    for _ in range(samples):
        Probe.noop()
    bare = time.perf_counter_ns() - bare
    timer = CallTimer(Probe, "noop")
    timer.install()
    wrapped = time.perf_counter_ns()
    for _ in range(samples):
        Probe.noop()
    wrapped = time.perf_counter_ns() - wrapped
    timer.restore()
    return max(0.0, (wrapped - bare) / samples / 1e6)


def run_once(args: argparse.Namespace, wrap: bool) -> Tuple[Dict[str, Any], str]:
    from src.config import profiles as profiles_module
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from src.systems.strategic import StrategicIntelligenceSystem
    from tools.perf import _profiling_common as common

    state = common.build_state(args.scenario, args.entities, args.seed)
    profile, governor, flags = common.contract_kernel_args(getattr(profiles_module, args.profile), args.contract)
    kernel = Kernel(profile, state, DeterministicRNG(args.seed), governor=governor, flags=flags)
    timer = CallTimer(StrategicIntelligenceSystem, "fused_strategic_pass")
    if wrap:
        timer.install()
    per_tick: List[Dict[str, Any]] = []
    try:
        for i in range(args.warmup + args.ticks):
            t0 = time.perf_counter_ns()
            kernel.tick_once()
            wall = (time.perf_counter_ns() - t0) / 1e6
            wrapped_ms = timer.take()
            if i >= args.warmup:
                per_tick.append({"wall_ms": wall, "resolution_overhead": float(kernel._phase_costs.get("resolution_overhead", 0.0)),
                                 "final_integrity": float(kernel._phase_costs.get("final_integrity", 0.0)), "wrapped_ms": wrapped_ms,
                                 "mode": kernel.status.current_mode.name})
        digest = fingerprint_hash(kernel._state)
    finally:
        timer.restore()
        kernel.shutdown()
    return {"ticks": per_tick}, digest


def summarize(off: Dict[str, Any], on: Dict[str, Any], overhead_per_call_ms: float, calls_per_tick: float = 1.0) -> Dict[str, Any]:
    m = lambda rows, k: statistics.mean(r[k] for r in rows)  # noqa: E731
    wrapped, over_on, over_off = m(on["ticks"], "wrapped_ms"), m(on["ticks"], "resolution_overhead"), m(off["ticks"], "resolution_overhead")
    residual = over_on - wrapped
    return {
        "wrapped_ms_per_tick": round(wrapped, 3),
        "resolution_overhead_unwrapped_ms": round(over_off, 3),
        "resolution_overhead_wrapped_run_ms": round(over_on, 3),
        "residual_ms": round(residual, 3),
        "residual_share_of_overhead": round(residual / over_on, 4) if over_on > 0 else None,
        "final_integrity_ms": round(m(on["ticks"], "final_integrity"), 3),
        "wrapper_overhead_ms_per_tick": round(overhead_per_call_ms * calls_per_tick, 6),
        "ac1_met": bool(over_on > 0 and residual / over_on < 0.20),
        "modes": sorted({r["mode"] for r in on["ticks"]}),
    }


def selftest() -> int:
    class Stub:
        @staticmethod
        def work(x: int) -> int:
            time.sleep(0.002)
            return x + 1

    timer = CallTimer(Stub, "work")
    timer.install()
    assert Stub.work(1) == 2 and len(timer.calls_ms) == 1 and timer.calls_ms[0] >= 1.5
    assert timer.take() >= 1.5 and timer.calls_ms == []
    timer.restore()
    assert Stub.__dict__["work"] is timer.original and Stub.work(2) == 3 and timer.calls_ms == []
    off = {"ticks": [{"wall_ms": 100.0, "resolution_overhead": 30.0, "final_integrity": 0.1, "wrapped_ms": 0.0, "mode": "NORMAL"}]}
    on = {"ticks": [{"wall_ms": 100.0, "resolution_overhead": 30.0, "final_integrity": 0.1, "wrapped_ms": 27.0, "mode": "NORMAL"}]}
    s = summarize(off, on, 0.0001)
    assert s["residual_ms"] == 3.0 and s["residual_share_of_overhead"] == 0.1 and s["ac1_met"] is True
    assert summarize(off, {"ticks": [{**on["ticks"][0], "wrapped_ms": 10.0}]}, 0.0001)["ac1_met"] is False
    print(f"selftest ok; wrapper overhead {wrapper_overhead_ms_per_call() * 1e6:.0f} ns per call")
    return 0


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--scenario", default="idle")
    p.add_argument("--entities", type=int, default=100)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--ticks", type=int, default=30)
    p.add_argument("--profile", default="PROD_LARGE")
    p.add_argument("--contract", default="pinned", choices=["live", "pinned", "canonical", "audit"])
    p.add_argument("--out", default=None, help="write the JSON report here")
    p.add_argument("--control", action="store_true", help="run the unwrapped pass a second time: a pinned run is not deterministic when the wall-clock budget throttle fires, so the inert check "
                   "only counts against the wrapper when the two unwrapped runs agree")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args(argv)
    if args.selftest:
        return selftest()
    from tools.perf import _profiling_common as common

    off, digest_off = run_once(args, wrap=False)
    control_digest = run_once(args, wrap=False)[1] if args.control else None
    on, digest_on = run_once(args, wrap=True)
    per_call = wrapper_overhead_ms_per_call()
    report = {
        "header": {**common.header_fields(args.scenario, args.entities, args.seed, args.warmup, args.ticks), "contract": args.contract, "profile": args.profile,
                   "loadavg_1min": os.getloadavg()[0], "platform": platform.platform()},
        "inert": digest_off == digest_on, "fingerprint_unwrapped": digest_off, "fingerprint_wrapped": digest_on,
        "fingerprint_unwrapped_control": control_digest,
        "unwrapped_runs_agree": None if control_digest is None else control_digest == digest_off,
        "summary": summarize(off, on, per_call), "ticks_unwrapped": off["ticks"], "ticks_wrapped": on["ticks"],
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"header": report["header"], "inert": report["inert"], "unwrapped_runs_agree": report["unwrapped_runs_agree"], "summary": report["summary"]}, indent=2, sort_keys=True))
    if report["inert"]:
        return 0
    if report["unwrapped_runs_agree"] is False:
        print("NOTE: the two unwrapped runs already differ, so the fingerprint difference is not evidence against the wrapper")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

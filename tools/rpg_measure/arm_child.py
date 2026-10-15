"""One run of one arm: build the pinned kernel (audit_mode, no frame pacing), run it, and write a small JSON of typed facts (never a raw event dump).

Executed by ``paired.py`` with the ARM'S source tree as the working directory and on PYTHONPATH, so it must import only what every arm tree has
(``tools.test_architecture.rpg_gate_run.build_kernel``, the engine, ``keeps_coin``). Counters that an older arm tree does not record are written as null,
never as zero.

Usage: python arm_child.py <world> <seed> <ticks> <out.json>
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

LEDGER_TALLY = "rpg_gate_ledger_tally"


def _cause(entity) -> str | None:
    """The typed cause recorded at death (``death_record``), else the older passive cause or reason string (``legacy:``), else None while alive."""
    if entity.combat.alive:
        return None
    record = getattr(entity.lifecycle, "death_record", None)
    if record is not None:
        return str(getattr(record.cause, "value", record.cause))
    legacy = getattr(entity.lifecycle.passive_death_cause, "value", None) or entity.lifecycle.death_reason or "unknown"
    return f"legacy:{legacy}"


def _roster(state, keeps_coin) -> list:
    return [[e.id, e.kind, int(bool(keeps_coin(e))), int(e.combat.alive)] for e in sorted(state.entities.values(), key=lambda x: x.id)]


def _tally(run_dir: Path) -> dict | None:
    path = run_dir / "simulation_events.jsonl"
    if not path.exists():
        return None
    found = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if LEDGER_TALLY in line:
            found = json.loads(line).get("payload")
    return found


def main(argv: list[str]) -> int:
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.serves import keeps_coin
    from tools.test_architecture.rpg_gate_run import build_kernel

    run_id = f"rpgm_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    start = _roster(kernel.state, keeps_coin)
    start_hash = CanonicalStateHasher.get_hash(kernel.state)
    for _ in range(ticks):
        kernel.tick_once()
    state = kernel.state
    kernel.shutdown()
    run_dir = Path("data") / "runs" / run_id
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8")) if (run_dir / "run_manifest.json").exists() else {}
    tally = _tally(run_dir)
    final = {str(e.id): [int(e.combat.alive), _cause(e), e.kind] for e in state.entities.values()}
    doc = {
        "world": world, "seed": seed, "ticks": ticks, "hashseed": os.environ.get("PYTHONHASHSEED"),
        "start_hash": start_hash, "final_hash": CanonicalStateHasher.get_hash(state),
        "audit_mode": manifest.get("audit_mode"), "signals_zeroed": manifest.get("signals_zeroed"),
        "start": start, "final": final,
        "counters": (tally or {}).get("behaviour") if tally and "behaviour" in tally else None,
        "perception_samples": (tally or {}).get("perception_samples"),
        "adds": (tally or {}).get("adds"),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    shutil.rmtree(run_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

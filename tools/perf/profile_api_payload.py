#!/usr/bin/env python3
"""API payload size profiler (TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS).

Usage:
    python tools/perf/profile_api_payload.py
    python tools/perf/profile_api_payload.py --ticks 20 --seed 42 --world dungeon_crawl

Builds a headless ``V2EngineManager`` (no server, no engine thread), advances it ``--ticks`` ticks with ``kernel.tick_once()`` (the same pattern as
``turbo_run.py``), and reports the size in bytes of the JSON each read endpoint returns, taken from the same ``StatePresenter`` calls the routes make:

    GET /api/v1/map           StatePresenter.present_map      (RLE terrain grid)
    GET /api/v1/static        StatePresenter.present_static   (buildings, nodes, chests, regions)
    GET /api/v1/state         StatePresenter.present_minimal  (the polled summary)
    full snapshot             StatePresenter.present_full     (every entity, expensive)
    one entity, slim and full StatePresenter.present_entity_slim / present_entity

The pre-optimization comparison of the V1 profiler is gone: the V1 payload shapes it estimated (``EntitySlimSchema``, ``/state`` with selection) no
longer exist. The world is chosen in exactly one place, ``build_manager``, so the way a live world is picked can be re-pointed there.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.api.engine_manager import V2EngineManager
from src.api.presenters.state_presenter import StatePresenter
from src.config.profiles import PROD_LARGE, RuntimeProfile

DEFAULT_WORLD_ID = "dungeon_crawl"
DEFAULT_ENTITIES = 25
DEFAULT_PROFILE = PROD_LARGE

ManagerFactory = Callable[..., Any]


def _fmt(size: float) -> str:
    """Format byte size as human-readable."""
    if size < 1024:
        return f"{size:,.0f} B"
    return f"{size:,.0f} B ({size / 1024:.1f} KB)"


def build_manager(
    seed: int,
    world_id: str = DEFAULT_WORLD_ID,
    entities: int = DEFAULT_ENTITIES,
    profile: RuntimeProfile = DEFAULT_PROFILE,
    factory: ManagerFactory = V2EngineManager,
) -> Any:
    """The one place this tool chooses its world: a headless ``V2EngineManager`` for ``world_id``. ``factory`` is replaceable so a test can build it with a stub."""
    return factory(profile, seed=seed, entities_count=entities, world_id=world_id)


def advance(mgr: Any, ticks: int) -> int:
    """Run ``ticks`` ticks on the manager's kernel without starting its engine thread; returns the tick reached."""
    kernel = mgr.kernel
    for _ in range(max(ticks, 0)):
        kernel.tick_once()
    return int(kernel.state.tick)


def _size(payload: Any) -> int:
    """Bytes of the compact JSON of a presenter payload (what a route returns, minus the HTTP envelope)."""
    return len(json.dumps(payload, default=str, separators=(",", ":")))


def measure(state: Any) -> Dict[str, Any]:
    """Payload sizes of every read endpoint for ``state`` (read-only: the presenters never mutate it)."""
    alive = [e for e in state.entities.values() if getattr(e, "alive", True)]
    first = alive[0] if alive else None
    slim = [StatePresenter.present_entity_slim(e) for e in alive]
    slim_total = _size(slim)
    map_payload = StatePresenter.present_map(state)
    static_payload = StatePresenter.present_static(state)
    return {
        "tick": int(state.tick),
        "entity_count": len(state.entities),
        "alive_count": len(alive),
        "map_size": _size(map_payload),
        "map_rle_pairs": len(map_payload.get("grid", [])) // 2 if isinstance(map_payload, dict) else 0,
        "static_size": _size(static_payload),
        "static_counts": {k: len(v) for k, v in static_payload.items() if isinstance(v, (list, dict))} if isinstance(static_payload, dict) else {},
        "state_size": _size(StatePresenter.present_minimal(state)),
        "full_size": _size(StatePresenter.present_full(state)),
        "slim_total": slim_total,
        "slim_avg": (slim_total / len(slim)) if slim else 0.0,
        "first_entity_id": getattr(first, "id", None),
        "entity_full_size": _size(StatePresenter.present_entity(first)) if first is not None else 0,
        "entity_slim_size": _size(StatePresenter.present_entity_slim(first)) if first is not None else 0,
    }


def render(sizes: Dict[str, Any]) -> str:
    """The report text for a ``measure`` result."""
    lines = ["=" * 70, "  API PAYLOAD SIZE REPORT", "=" * 70]
    lines.append(f"\n  tick {sizes['tick']}, {sizes['entity_count']} entities ({sizes['alive_count']} alive)")
    lines.append("\n  GET /api/v1/map (one-time, RLE-encoded)")
    lines.append(f"  {'Payload:':<30} {_fmt(sizes['map_size'])}")
    lines.append(f"  {'RLE pairs:':<30} {sizes['map_rle_pairs']:,}")
    lines.append("\n  GET /api/v1/static (one-time)")
    lines.append(f"  {'Payload:':<30} {_fmt(sizes['static_size'])}")
    for name, count in sorted(sizes["static_counts"].items()):
        lines.append(f"  {name + ':':<30} {count}")
    lines.append("\n  GET /api/v1/state (polled summary)")
    lines.append(f"  {'Payload:':<30} {_fmt(sizes['state_size'])}")
    lines.append("\n  Entities")
    lines.append(f"  {'Slim, all alive:':<30} {sizes['alive_count']} x {sizes['slim_avg']:.0f} B avg = {_fmt(sizes['slim_total'])}")
    lines.append(f"  {'Full snapshot (all state):':<30} {_fmt(sizes['full_size'])}")
    if sizes["first_entity_id"] is not None:
        label = f"Entity #{sizes['first_entity_id']} slim / full:"
        lines.append(f"  {label:<30} {_fmt(sizes['entity_slim_size'])} / {_fmt(sizes['entity_full_size'])}")
    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Profile API payload sizes")
    parser.add_argument("--ticks", type=int, default=10, help="Run N ticks before measuring (default 10)")
    parser.add_argument("--seed", type=int, default=42, help="World seed")
    parser.add_argument("--world", type=str, default=DEFAULT_WORLD_ID, help="World id (default dungeon_crawl)")
    parser.add_argument("--entities", type=int, default=DEFAULT_ENTITIES, help="Entity count (default 25)")
    args = parser.parse_args(argv)

    print(f"Initializing world {args.world!r} (seed={args.seed}, entities={args.entities})...")
    t0 = time.perf_counter()
    mgr = build_manager(args.seed, args.world, args.entities)
    print(f"  World initialized in {time.perf_counter() - t0:.2f}s")
    try:
        if args.ticks > 0:
            print(f"  Advancing {args.ticks} ticks...")
        tick = advance(mgr, args.ticks)
        print(f"  Done. Tick={tick}")
        print(render(measure(mgr.kernel.state)))
    finally:
        mgr.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""API payload size profiler.

Usage:
    python scripts/profile_api_payload.py
    python scripts/profile_api_payload.py --ticks 20 --seed 42

Reports:
    - Per-endpoint JSON payload sizes (bytes/KB)
    - Breakdown: /map (RLE), /static, /state (no selection), /state (with selection)
    - Entity count and per-entity sizes
    - Comparison with estimated pre-optimization sizes
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.api.engine_manager import EngineManager
from src.api.routes.state import (
    _serialize_full_entity,
    _get_weapon_range,
)
from src.api.schemas import (
    BuildingSchema,
    EntitySchema,
    EntitySlimSchema,
    EventSchema,
    GroundItemSchema,
    LocationSchema,
    MapResponse,
    RegionSchema,
    ResourceNodeSchema,
    StaticDataResponse,
    TreasureChestSchema,
    WorldStateResponse,
)
from src.config import SimulationConfig


def _fmt(size: int) -> str:
    """Format byte size as human-readable."""
    if size < 1024:
        return f"{size:,} B"
    return f"{size:,} B ({size / 1024:.1f} KB)"


def _measure_map(mgr: EngineManager) -> dict:
    """Measure /map endpoint payload (RLE-encoded)."""
    grid = mgr.get_grid()
    tiles = grid._tiles
    total = grid.width * grid.height

    # RLE encode
    rle: list[int] = []
    cur_val = int(tiles[0])
    cur_count = 1
    for i in range(1, total):
        v = int(tiles[i])
        if v == cur_val:
            cur_count += 1
        else:
            rle.append(cur_val)
            rle.append(cur_count)
            cur_val = v
            cur_count = 1
    rle.append(cur_val)
    rle.append(cur_count)

    resp = MapResponse(width=grid.width, height=grid.height, grid=rle)
    rle_json = resp.model_dump_json()

    # Estimate raw 2D grid size for comparison
    raw_2d: list[list[int]] = []
    for y in range(grid.height):
        row = [int(tiles[y * grid.width + x]) for x in range(grid.width)]
        raw_2d.append(row)
    raw_json = json.dumps({"width": grid.width, "height": grid.height, "grid": raw_2d})

    return {
        "rle_size": len(rle_json),
        "raw_size": len(raw_json),
        "rle_pairs": len(rle) // 2,
        "width": grid.width,
        "height": grid.height,
    }


def _measure_static(mgr: EngineManager) -> dict:
    """Measure /static endpoint payload."""
    snap = mgr.get_snapshot()

    buildings = []
    for b in snap.buildings:
        buildings.append(BuildingSchema(
            building_id=b.building_id, name=b.name,
            x=b.pos.x, y=b.pos.y, building_type=b.building_type,
        ))

    resource_nodes = [
        ResourceNodeSchema(
            node_id=n.node_id, resource_type=n.resource_type, name=n.name,
            x=n.pos.x, y=n.pos.y, terrain=int(n.terrain),
            yields_item=n.yields_item, remaining=n.remaining,
            max_harvests=n.max_harvests, is_available=n.is_available,
            harvest_ticks=n.harvest_ticks,
        )
        for n in snap.resource_nodes
    ]

    treasure_chests = []
    if hasattr(snap, 'treasure_chests'):
        treasure_chests = [
            TreasureChestSchema(
                chest_id=c.chest_id, x=c.pos.x, y=c.pos.y,
                tier=c.tier, looted=c.looted,
                guard_entity_id=c.guard_entity_id,
            )
            for c in snap.treasure_chests
        ]

    regions = []
    if hasattr(snap, 'regions'):
        regions = [
            RegionSchema(
                region_id=r.region_id, name=r.name,
                terrain=int(r.terrain),
                center_x=r.center.x, center_y=r.center.y,
                radius=r.radius, difficulty=r.difficulty,
                locations=[
                    LocationSchema(
                        location_id=loc.location_id, name=loc.name,
                        location_type=loc.location_type,
                        x=loc.pos.x, y=loc.pos.y,
                        region_id=loc.region_id,
                    )
                    for loc in r.locations
                ],
            )
            for r in snap.regions
        ]

    resp = StaticDataResponse(
        buildings=buildings,
        resource_nodes=resource_nodes,
        treasure_chests=treasure_chests,
        regions=regions,
    )
    js = resp.model_dump_json()

    return {
        "size": len(js),
        "buildings": len(buildings),
        "resource_nodes": len(resource_nodes),
        "treasure_chests": len(treasure_chests),
        "regions": len(regions),
    }


def _measure_state(mgr: EngineManager, selected_id: int | None = None) -> dict:
    """Measure /state endpoint payload."""
    snap = mgr.get_snapshot()

    slim_entities: list[EntitySlimSchema] = []
    selected_entity: EntitySchema | None = None
    alive_entities = [e for e in snap.entities.values() if e.alive]

    for e in alive_entities:
        slim_entities.append(EntitySlimSchema(
            id=e.id, kind=e.kind, x=e.pos.x, y=e.pos.y,
            hp=e.stats.hp, max_hp=e.stats.max_hp,
            state=e.ai_state.name, level=e.stats.level,
            tier=e.tier, faction=e.faction.name.lower(),
            weapon_range=_get_weapon_range(e),
            combat_target_id=e.combat_target_id,
            loot_progress=e.loot_progress,
            loot_duration=mgr.config.loot_duration,
        ))
        if selected_id is not None and e.id == selected_id:
            selected_entity = _serialize_full_entity(e, mgr)

    events = [
        EventSchema(tick=ev.tick, category=ev.category, message=ev.message,
                     entity_ids=list(ev.entity_ids), metadata=ev.metadata)
        for ev in mgr.event_log.since_tick(0)
    ]

    ground_items = [
        GroundItemSchema(x=x, y=y, items=list(items))
        for (x, y), items in snap.ground_items.items()
        if items
    ]

    resp = WorldStateResponse(
        tick=snap.tick,
        alive_count=len(slim_entities),
        entities=slim_entities,
        selected_entity=selected_entity,
        events=events,
        ground_items=ground_items,
    )
    js = resp.model_dump_json()

    # Also measure the selected entity alone
    sel_size = 0
    sel_terrain_mem_size = 0
    sel_entity_mem_size = 0
    if selected_entity:
        sel_json = selected_entity.model_dump_json()
        sel_size = len(sel_json)
        sel_data = selected_entity.model_dump()
        sel_terrain_mem_size = len(json.dumps(sel_data.get("terrain_memory", {})))
        sel_entity_mem_size = len(json.dumps(sel_data.get("entity_memory", [])))

    # Measure slim entities total
    slim_total = sum(len(s.model_dump_json()) for s in slim_entities)
    avg_slim = slim_total / len(slim_entities) if slim_entities else 0

    return {
        "total_size": len(js),
        "entity_count": len(slim_entities),
        "slim_entities_total": slim_total,
        "avg_slim_entity": avg_slim,
        "selected_entity_size": sel_size,
        "selected_terrain_memory_size": sel_terrain_mem_size,
        "selected_entity_memory_size": sel_entity_mem_size,
        "events_count": len(events),
        "ground_items_count": len(ground_items),
    }


def _estimate_old_state(mgr: EngineManager) -> int:
    """Estimate old /state payload (all entities full, includes static data)."""
    snap = mgr.get_snapshot()
    alive = [e for e in snap.entities.values() if e.alive]

    total = 0
    for e in alive:
        full = _serialize_full_entity(e, mgr)
        total += len(full.model_dump_json())

    # Add static data estimate
    static = _measure_static(mgr)
    total += static["size"]

    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile API payload sizes")
    parser.add_argument("--ticks", type=int, default=10, help="Run N ticks before measuring (default 10)")
    parser.add_argument("--seed", type=int, default=42, help="World seed")
    args = parser.parse_args()

    cfg = SimulationConfig(world_seed=args.seed)
    print(f"Initializing world (seed={args.seed}, grid={cfg.grid_width}x{cfg.grid_height})...")
    t0 = time.perf_counter()
    mgr = EngineManager(cfg)
    print(f"  World initialized in {time.perf_counter() - t0:.2f}s")

    # Advance a few ticks so entities have memory/events
    if args.ticks > 0:
        print(f"  Advancing {args.ticks} ticks...")
        for _ in range(args.ticks):
            if mgr._loop:
                mgr._loop._step()
        print(f"  Done. Tick={mgr.get_snapshot().tick}")

    snap = mgr.get_snapshot()
    alive = [e for e in snap.entities.values() if e.alive]
    first_id = alive[0].id if alive else None

    print("\n" + "=" * 70)
    print("  API PAYLOAD SIZE REPORT")
    print("=" * 70)

    # --- /map ---
    map_data = _measure_map(mgr)
    print(f"\n  GET /api/v1/map (one-time, RLE-compressed)")
    print(f"  {'RLE payload:':<30} {_fmt(map_data['rle_size'])}")
    print(f"  {'Raw 2D (pre-optimization):':<30} {_fmt(map_data['raw_size'])}")
    reduction = (1 - map_data['rle_size'] / map_data['raw_size']) * 100
    print(f"  {'Compression ratio:':<30} {reduction:.1f}% smaller")
    print(f"  {'RLE pairs:':<30} {map_data['rle_pairs']:,}")

    # --- /static ---
    static_data = _measure_static(mgr)
    print(f"\n  GET /api/v1/static (one-time)")
    print(f"  {'Payload:':<30} {_fmt(static_data['size'])}")
    print(f"  {'Buildings:':<30} {static_data['buildings']}")
    print(f"  {'Resource nodes:':<30} {static_data['resource_nodes']}")
    print(f"  {'Treasure chests:':<30} {static_data['treasure_chests']}")
    print(f"  {'Regions:':<30} {static_data['regions']}")

    # --- /state (no selection) ---
    state_no_sel = _measure_state(mgr, selected_id=None)
    print(f"\n  GET /api/v1/state (polling, NO selection)")
    print(f"  {'Total payload:':<30} {_fmt(state_no_sel['total_size'])}")
    print(f"  {'Entities (slim):':<30} {state_no_sel['entity_count']} × {state_no_sel['avg_slim_entity']:.0f} B avg = {_fmt(state_no_sel['slim_entities_total'])}")
    print(f"  {'Events:':<30} {state_no_sel['events_count']}")
    print(f"  {'Ground items:':<30} {state_no_sel['ground_items_count']}")

    # --- /state (with selection) ---
    if first_id is not None:
        state_sel = _measure_state(mgr, selected_id=first_id)
        print(f"\n  GET /api/v1/state (polling, selected=#{first_id})")
        print(f"  {'Total payload:':<30} {_fmt(state_sel['total_size'])}")
        print(f"  {'Selected entity:':<30} {_fmt(state_sel['selected_entity_size'])}")
        print(f"  {'  terrain_memory:':<30} {_fmt(state_sel['selected_terrain_memory_size'])}")
        print(f"  {'  entity_memory:':<30} {_fmt(state_sel['selected_entity_memory_size'])}")

    # --- Comparison ---
    print(f"\n  {'─' * 50}")
    print(f"  COMPARISON WITH PRE-OPTIMIZATION")
    print(f"  {'─' * 50}")

    old_state = _estimate_old_state(mgr)
    new_state = state_no_sel['total_size']
    one_time = map_data['rle_size'] + static_data['size']
    old_one_time = map_data['raw_size'] + static_data['size']

    print(f"\n  {'Metric':<35} {'Before':>12} {'After':>12} {'Savings':>10}")
    print(f"  {'─' * 35} {'─' * 12} {'─' * 12} {'─' * 10}")
    print(f"  {'/state per poll':<35} {old_state // 1024:>10} KB {new_state // 1024:>10} KB {(1 - new_state / old_state) * 100:>8.1f}%")
    print(f"  {'/map + /static (one-time)':<35} {old_one_time // 1024:>10} KB {one_time // 1024:>10} KB {(1 - one_time / old_one_time) * 100:>8.1f}%")

    polls_per_sec = 1000 / 80  # 80ms poll interval
    old_bw = old_state * polls_per_sec
    new_bw = new_state * polls_per_sec
    print(f"\n  {'Bandwidth at 80ms poll:':<35}")
    print(f"  {'  Before:':<35} {old_bw / 1024 / 1024:.1f} MB/s")
    print(f"  {'  After:':<35} {new_bw / 1024 / 1024:.1f} MB/s")
    print(f"  {'  Saved:':<35} {(old_bw - new_bw) / 1024 / 1024:.1f} MB/s")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

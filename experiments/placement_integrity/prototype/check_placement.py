"""Prototype: does the proposed compile-time placement-legality check (experiments/placement_integrity/
PROPOSAL.md's new HardLawMonitor law) actually find real violations in real compiled worlds today?

This was never tested — the whole proposal was argued from the *absence* of a check, never from
evidence of real violations existing. Run from repo root:
    .venv/bin/python3 experiments/placement_integrity/prototype/check_placement.py

Not production code. Read-only — compiles worlds in-memory, writes nothing, mutates nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler


def check_world(world_id: str, seed: int = 42) -> dict:
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, report = WorldCompiler.compile(spec, seed=seed)

    terrain = state.terrain
    violations = []

    # WALL-terrain check only — unambiguous, no self-reference issue (unlike blocked_tiles,
    # which src/worldbuilding/compiler.py:258 confirms every building deliberately adds itself
    # to, making "is this object in blocked_tiles" trivially true for every building by design,
    # not a real violation — that was this prototype's first-pass bug, caught and fixed here).
    def on_wall(pos: tuple[float, float]) -> bool:
        p = (int(pos[0]), int(pos[1]))
        return terrain.get(p, "").upper() == "WALL"

    all_objects: list[tuple[str, int, tuple[float, float]]] = []
    for eid, ent in state.entities.items():
        if not getattr(ent.lifecycle, "active", True):
            continue
        all_objects.append(("entity", eid, ent.navigation.position))
    for bid, b in state.buildings.items():
        all_objects.append(("building", bid, b.position))
    for rid, r in state.resource_nodes.items():
        all_objects.append(("resource_node", rid, r.position))

    for kind, oid, pos in all_objects:
        if on_wall(pos):
            violations.append((kind, oid, pos, "WALL_TERRAIN"))

    # Object-to-object overlap: two *different* objects at the exact same discrete tile —
    # a genuine collision, independent of the blocked_tiles self-reference problem above.
    by_pos: dict[tuple[int, int], list[tuple[str, int]]] = {}
    for kind, oid, pos in all_objects:
        p = (int(pos[0]), int(pos[1]))
        by_pos.setdefault(p, []).append((kind, oid))
    overlaps = [(p, occupants) for p, occupants in by_pos.items() if len(occupants) > 1]

    return {
        "world_id": world_id,
        "entity_count": len(state.entities),
        "building_count": len(state.buildings),
        "resource_node_count": len(state.resource_nodes),
        "violations": violations,
        "overlaps": overlaps,
    }


def main() -> None:
    worlds = [
        "sandbox_world", "dungeon_crawl", "wilderness_survival",
        "crowded_frontier", "frontier_extended", "frontier_living_world", "frontier_marches",
        "generated_frontier_3_42", "hero_guild_routing", "highland_traverse",
        "resource_dense_basin", "simq_routing_test", "swamp_border_world",
        "unit_faction_tension", "unit_information_density", "unit_information_source",
        "unit_selfmodel_pilot", "urban_political",
    ]

    total_wall_violations = 0
    total_overlaps = 0
    worlds_with_findings = 0
    for wid in worlds:
        try:
            result = check_world(wid)
        except Exception as e:
            print(f"{wid}: COMPILE_ERROR {e}")
            continue
        n_wall = len(result["violations"])
        n_overlap = len(result["overlaps"])
        total_wall_violations += n_wall
        total_overlaps += n_overlap
        if n_wall or n_overlap:
            worlds_with_findings += 1
            print(f"{wid}: {n_wall} WALL violation(s), {n_overlap} overlap(s) "
                  f"(entities={result['entity_count']}, buildings={result['building_count']}, "
                  f"resource_nodes={result['resource_node_count']})")
            for kind, oid, pos, reason in result["violations"]:
                print(f"    WALL: {kind} id={oid} at {pos}")
            for pos, occupants in result["overlaps"]:
                print(f"    OVERLAP at {pos}: {occupants}")
        else:
            print(f"{wid}: clean (entities={result['entity_count']}, "
                  f"buildings={result['building_count']}, resource_nodes={result['resource_node_count']})")

    print()
    print(f"=== SUMMARY: {total_wall_violations} WALL violations, {total_overlaps} object-overlaps, "
          f"across {worlds_with_findings}/{len(worlds)} worlds with any finding ===")


if __name__ == "__main__":
    main()

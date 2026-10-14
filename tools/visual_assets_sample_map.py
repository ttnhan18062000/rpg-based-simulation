"""Sample-map data (`TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA`): what a typical compiled world places, read-only, mapped to the visual keys.

    python -m tools.visual_assets_sample_map data frontier_living_world      # writes reports/visual_assets/sample_map/<world>/world_data.json
    python -m tools.visual_assets_sample_map data --all                      # the three chosen worlds
    python -m tools.visual_assets_sample_map keytable                        # prints the name -> key table over the chosen worlds

The state is built exactly as the API builds it (`src/api/engine_manager.py:133-136`): `WorldRepository("data/worlds").load_world(id)`, then
`WorldCompiler.compile(spec, seed=42)` (42 is `EngineManager`'s default seed, `engine_manager.py:25`). Nothing is written by that path: `compile` writes only when
`output_report_path` is given (`src/worldbuilding/compiler.py`), and this tool never gives one, never calls `repository.rebuild_index()` (it rewrites `world_index.json`)
and never runs `world-compile` (it writes `world_compile_report.json` next to the world). Then `StatePresenter.present_map` and `present_static`
(`src/api/presenters/state_presenter.py:186`, `:221`) shape the map and the static objects.

`present_map`'s integer codes are PER WORLD (`terrain_code_map`, `state_presenter.py:183`, sorted names of that world's terrains), not the Live Map tile codes the
registry descriptions cite. Cells are therefore stored as terrain NAMES (the presenter's own codes are inverted through the same `terrain_code_map`) and mapped to keys
by name: a name maps to `terrain.<name>` when that key is registered, or, offline, through a REGISTRY alias (`terrain.plain` -> `terrain.grassland`, `Registry.resolve`; the live client does NOT do this). The rule is exact (lower case, spaces to underscores); a near match is listed as `near`
and is NEVER applied, so no key is guessed. The same exact rule maps building kinds to `icon.building.<kind>`, place kinds and resource-node kinds to
`icon.marker.<kind>` and entity kinds to `icon.class.<kind>`.

Output goes only under the gitignored `reports/visual_assets/sample_map/`; the file is deterministic (same world -> byte-identical). This tool is evidence tooling: it
activates nothing, adopts nothing and puts nothing into a release candidate. It is a tool, not part of `visual_assets/`, so the boundary guard does not police its
imports (it reads `src/` read-only and the registry through the store's own loader).
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO / "reports" / "visual_assets" / "sample_map"
REGISTRY_FILE = REPO / "visual_assets" / "catalog" / "definitions" / "visual_keys.yaml"
SEED = 42  # `EngineManager.__init__` default (`src/api/engine_manager.py:25`), the seed the running API compiles with

# The three worlds and the role each fills (asset-planner's starting choice, checked against `make world-list`; see the ticket for why a world was or was not swapped).
WORLDS = {
    "frontier_living_world": "town (town hall, inn, shop, blacksmith, healer) next to a mixed wilderness (forest, swamp, road, plain) and a dungeon area (cave, ruin, old mine)",
    "highland_traverse": "a wilderness with several terrains (mountain, river, forest, plain) and a watchtower",
    "dungeon_crawl": "a dungeon area (ruin, forest) with sentinels and scouts and no buildings or resource nodes",
}

FORMAT = "sample_map_world_data_v2"

# UNCONFIRMED proposals (asset-planner, for rpg-planner, issue #519): which registered key a name that has no exact key could draw with. They live ONLY in this data (never in the
# registry's `aliases`, and no key is added), every use is labelled, and the exact view stays the primary evidence. `river` could read better as `terrain.water`; it is a proposal either way.
ALIAS_LABEL = "unconfirmed: asset-planner proposal for rpg-planner (#519)"
PROPOSED_ALIASES = {
    # (the terrain proposals of 2026-10-11 became REGISTRY aliases on 2026-10-12, `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`; the exact view resolves them through `Registry.resolve`, see below)
    "building": {"shop": "icon.building.store"},
    "place": {"CAMP": "icon.marker.enemy_camp", "RUIN": "icon.marker.ruins"},
}


def sources() -> dict:
    """What produced the data, for the ticket and the file."""
    return {
        "build_state": "src/api/engine_manager.py:133-136 (WorldRepository('data/worlds').load_world(id); WorldCompiler.compile(spec, seed=42))",
        "compiler": "src/worldbuilding/compiler.py (WorldCompiler.compile, no output_report_path)",
        "presenters": "src/api/presenters/state_presenter.py:183 terrain_code_map, :186 present_map, :221 present_static",
        "registry": "visual_assets/catalog/definitions/visual_keys.yaml",
        "command": "python -m tools.visual_assets_sample_map data <world>",
    }


def _snake(name: str) -> str:
    return str(name).strip().lower().replace(" ", "_").replace("-", "_")


def _registry_keys() -> set[str]:
    from visual_assets.store.catalog.registry import load_registry

    return set(load_registry(REGISTRY_FILE).keys)


def _registry_aliases() -> dict[str, str]:
    """The registry's own aliases (alias -> target key): the V2 terrain names reach existing art through them. Offline only: no release, runtime export or client carries them (`store_contract.md`, Known gaps)."""
    from visual_assets.store.catalog.registry import load_registry

    return dict(load_registry(REGISTRY_FILE).aliases)


def _near(name: str, family_prefix: str, keys: set[str]) -> list[str]:
    """Registered keys of one family whose last segment is close to the name: reported, never applied."""
    pool = sorted(k for k in keys if k.startswith(family_prefix))
    stems = {k: k[len(family_prefix):] for k in pool}
    n = _snake(name)
    hits = [k for k in pool if stems[k] != n and (stems[k].rstrip("s") == n.rstrip("s") or n in stems[k] or stems[k] in n)]
    close = [k for stem in difflib.get_close_matches(n, list(stems.values()), n=2, cutoff=0.75) for k in pool if stems[k] == stem and k not in hits]
    return sorted(set(hits + close))


def key_rows(counts: Counter, family_prefix: str, keys: set[str], aliases: dict[str, str] | None = None, registry_aliases: dict[str, str] | None = None) -> list[dict]:
    """One row per distinct raw name: its count, the exact key (or null), the near keys that are NOT applied and, only for a name with no exact key, its UNCONFIRMED proposed alias."""
    rows = []
    for name in sorted(counts):
        exact = family_prefix + _snake(name)
        via = registry_aliases.get(exact) if registry_aliases and exact not in keys else None  # a REGISTRY alias: the name resolves, offline, through `Registry.resolve` (the live client does not)
        row = {"name": name, "count": counts[name], "key": exact if exact in keys else via, "near": [] if (exact in keys or via) else _near(name, family_prefix, keys)}
        if via:
            row["registry_alias"] = exact
        if row["key"] is None and aliases and name in aliases:
            assert aliases[name] in keys, f"proposed alias {aliases[name]!r} is not a registered key"
            row["proposed_alias"] = aliases[name]
        rows.append(row)
    return rows


def rle(names: list[str]) -> list:
    """Run-length encode a list of terrain-name indices: [index, run, index, run, ...] (row-major, y * width + x)."""
    out: list[int] = []
    last, run = None, 0
    for v in names:
        if v == last:
            run += 1
        else:
            if last is not None:
                out += [last, run]
            last, run = v, 1
    if last is not None:
        out += [last, run]
    return out


def build_data(world_id: str) -> dict:
    """Compile `world_id` in memory and describe it. Reads `data/worlds` and `src/`, writes nothing."""
    from src.api.presenters.state_presenter import StatePresenter
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec = WorldRepository("data/worlds").load_world(world_id)
    state, _report = WorldCompiler.compile(spec, seed=SEED)
    code_map = StatePresenter.terrain_code_map(state)
    inverse = {code: name for name, code in code_map.items()}
    pmap = StatePresenter.present_map(state)
    static = StatePresenter.present_static(state)
    width, height = pmap["width"], pmap["height"]

    names = sorted(code_map)  # raw terrain names, the presenter's own order
    flat: list[int] = []
    grid = pmap["grid"]
    for i in range(0, len(grid), 2):
        flat += [names.index(inverse[grid[i]])] * grid[i + 1]
    assert len(flat) == width * height

    keys = _registry_keys()
    terrain_counts = Counter(names[i] for i in flat)
    place_kinds = Counter(getattr(p.kind, "value", str(p.kind)) for p in state.places.values())
    entity_kinds = Counter(str(e.kind) for e in state.entities.values())
    node_kinds = Counter(n["resource_type"] for n in static["resource_nodes"])
    building_kinds = Counter(b["building_type"] for b in static["buildings"])

    return {
        "format": FORMAT,
        "world_id": world_id,
        "role": WORLDS.get(world_id, ""),
        "seed": SEED,
        "width": width,
        "height": height,
        "cell_order": "row-major, index = y * width + x",
        "terrain_names": names,
        "terrain_rle": rle(flat),
        "terrain": key_rows(terrain_counts, "terrain.", keys, registry_aliases=_registry_aliases()),
        "buildings": [{"id": b["building_id"], "kind": b["building_type"], "x": b["x"], "y": b["y"]} for b in static["buildings"]],
        "resource_nodes": [{"id": n["node_id"], "kind": n["resource_type"], "x": n["x"], "y": n["y"], "terrain": inverse.get(n["terrain"])} for n in static["resource_nodes"]],
        "treasure_chests": [{"id": c["chest_id"], "x": c["x"], "y": c["y"]} for c in static["treasure_chests"]],
        "regions": [
            {"id": r["region_id"], "name": r["name"], "kind": state.regions[r["region_id"]].kind, "bounds": list(state.regions[r["region_id"]].bounds)}
            for r in static["regions"]
        ],
        "places": [
            {"id": str(pid), "kind": getattr(p.kind, "value", str(p.kind)), "x": p.position[0], "y": p.position[1]}
            for pid, p in sorted(state.places.items(), key=lambda kv: str(kv[0]))
        ],
        "entities": [{"kind": str(e.kind), "x": e.position[0], "y": e.position[1]} for e in sorted(state.entities.values(), key=lambda e: e.id)],
        "kinds": {
            "building": key_rows(building_kinds, "icon.building.", keys, PROPOSED_ALIASES["building"]),
            "resource_node": key_rows(node_kinds, "icon.marker.", keys),
            "place": key_rows(place_kinds, "icon.marker.", keys, PROPOSED_ALIASES["place"]),
            "entity": key_rows(entity_kinds, "icon.class.", keys),
        },
        "proposed_aliases": {"label": ALIAS_LABEL, "applies_only_to_names_without_an_exact_key": True, **PROPOSED_ALIASES},
        "sources": sources(),
    }


def encode(data: dict) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def output_path(world_id: str, out_root: Path | None = None) -> Path:
    """`<root>/<world>/world_data.json`, refused unless the root is under the gitignored `reports/visual_assets/sample_map/`."""
    root = (out_root or OUT_ROOT).resolve()
    if not root.is_relative_to(OUT_ROOT.resolve()):
        raise SystemExit(f"refusing to write outside {OUT_ROOT.relative_to(REPO)}/ (got {root})")
    if world_id not in WORLDS and out_root is None:
        raise SystemExit(f"unknown world {world_id!r}; the sample map covers {', '.join(WORLDS)}")
    return root / world_id / "world_data.json"


def write_world(world_id: str, out_root: Path | None = None) -> Path:
    path = output_path(world_id, out_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode(build_data(world_id)))
    return path


def keytable(worlds: list[str]) -> str:
    """Markdown: every terrain name seen over the worlds, its worlds and total count, the key or `UNMAPPED`, near keys not applied."""
    merged: dict[str, dict] = {}
    for w in worlds:
        for row in build_data(w)["terrain"]:
            m = merged.setdefault(row["name"], {"count": 0, "worlds": [], "key": row["key"], "near": row["near"], "alias": row.get("registry_alias")})
            m["count"] += row["count"]
            m["worlds"].append(w)
    lines = ["| terrain name | cells | worlds | key (exact, or through a registry alias) | registry alias (registry-only: the live client does not resolve it) | near (not applied) |", "|---|---|---|---|---|---|"]
    for name in sorted(merged):
        m = merged[name]
        lines.append(f"| `{name}` | {m['count']} | {', '.join(m['worlds'])} | {('`' + m['key'] + '`') if m['key'] else '**UNMAPPED**'} | {('`' + m['alias'] + '`') if m['alias'] else '-'} | {', '.join('`' + k + '`' for k in m['near']) or '-'} |")
    return "\n".join(lines)


def ensure_export() -> Path:
    """The current release's runtime export under the report directory (written once, with the store's own `export-runtime`, which refuses an existing directory)."""
    from tools.visual_assets_sample_map_render import EXPORT_DIR, RELEASE_ID

    if not (EXPORT_DIR / "runtime_manifest.json").is_file():
        from visual_assets.store import runtime_export

        runtime_export.export_runtime("pilot", RELEASE_ID, EXPORT_DIR)
    return EXPORT_DIR


def render_command(worlds: list[str], *, page: bool) -> int:
    from tools import visual_assets_sample_map_render as render

    release = render.Release(ensure_export())
    results, datas = [], {}
    for w in worlds:
        data = build_data(w)
        datas[w] = data
        out = output_path(w).parent
        results.append(render.render_world(data, release, out))
        print(out.relative_to(REPO))
    if page:
        print(render.write_page(results, datas).relative_to(REPO))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="visual_assets_sample_map", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("data", help="write reports/visual_assets/sample_map/<world>/world_data.json")
    d.add_argument("world", nargs="?")
    d.add_argument("--all", action="store_true")
    sub.add_parser("keytable", help="print the terrain name -> key table over the chosen worlds")
    r = sub.add_parser("render", help="draw a world with the current release's runtime export: exact and alias views at x1 and x2, render_stats.json (and the page with --all)")
    r.add_argument("world", nargs="?")
    r.add_argument("--all", action="store_true")
    sub.add_parser("evidence", help="write the committed x1 evidence crops under docs/assets/sample_map/ (at most 256 KiB in all)")
    args = parser.parse_args(argv)
    if args.cmd == "evidence":
        from tools import visual_assets_sample_map_render as render

        sizes = render.write_evidence({w: build_data(w) for w in WORLDS}, render.Release(ensure_export()))
        for name, size in sizes.items():
            print(f"docs/assets/sample_map/{name}  {size} B")
        print(f"total {sum(sizes.values())} B of {render.EVIDENCE_CAP_BYTES} B")
        return 0
    if args.cmd == "keytable":
        print(keytable(list(WORLDS)))
        return 0
    worlds = list(WORLDS) if args.all else [args.world]
    if not all(worlds):
        parser.error("give a world or --all")
    if args.cmd == "render":
        return render_command(worlds, page=args.all)
    for w in worlds:
        print(write_world(w).relative_to(REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())

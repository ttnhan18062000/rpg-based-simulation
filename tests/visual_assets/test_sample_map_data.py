"""`tools/visual_assets_sample_map.py data` (`TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-DATA`): the sample-map data is read-only, deterministic, keyed by terrain NAME and exact."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from tools import visual_assets_sample_map as sm

REPO = Path(__file__).resolve().parents[2]
KEYS = {"terrain.forest", "terrain.ruins", "terrain.cave", "icon.building.inn", "icon.building.store", "icon.marker.ruins"}


def _tree(root: Path) -> dict[str, tuple[int, int]]:
    return {str(p.relative_to(root)): (p.stat().st_size, p.stat().st_mtime_ns) for p in sorted(root.rglob("*")) if p.is_file()}


# ---- the mapping rule: exact, by name, never by a per-world integer code ----

def test_a_name_maps_only_to_the_exact_registered_key_and_a_near_key_is_reported_but_never_applied():
    rows = {r["name"]: r for r in sm.key_rows(Counter({"forest": 3, "ruin": 2, "PLAIN": 9, "Cave": 1}), "terrain.", KEYS)}
    assert rows["forest"]["key"] == "terrain.forest" and rows["forest"]["near"] == []
    assert rows["Cave"]["key"] == "terrain.cave"  # case and spaces are normalised, nothing else
    assert rows["ruin"]["key"] is None and rows["ruin"]["near"] == ["terrain.ruins"]  # singular vs plural: reported, not applied
    assert rows["PLAIN"]["key"] is None and rows["PLAIN"]["near"] == []


def test_each_family_has_its_own_prefix():
    assert [r["key"] for r in sm.key_rows(Counter({"inn": 1, "shop": 1}), "icon.building.", KEYS)] == ["icon.building.inn", None]
    assert {r["name"]: r["key"] for r in sm.key_rows(Counter({"ruins": 1, "CITY": 1}), "icon.marker.", KEYS)} == {"ruins": "icon.marker.ruins", "CITY": None}


def test_the_rows_are_sorted_by_name_and_carry_the_counts():
    rows = sm.key_rows(Counter({"b": 2, "a": 1}), "terrain.", KEYS)
    assert [(r["name"], r["count"]) for r in rows] == [("a", 1), ("b", 2)]


def test_rle_round_trips_and_handles_empty_and_single_runs():
    assert sm.rle([]) == [] and sm.rle([3]) == [3, 1] and sm.rle([0, 0, 1, 0, 0, 0]) == [0, 2, 1, 1, 0, 3]


# ---- the output location ----

def test_output_is_refused_outside_the_gitignored_report_directory(tmp_path):
    with pytest.raises(SystemExit):
        sm.output_path("dungeon_crawl", tmp_path)
    with pytest.raises(SystemExit):
        sm.output_path("dungeon_crawl", REPO / "docs")
    assert sm.output_path("dungeon_crawl") == REPO / "reports" / "visual_assets" / "sample_map" / "dungeon_crawl" / "world_data.json"


def test_an_unknown_world_is_refused_and_the_report_directory_is_gitignored():
    with pytest.raises(SystemExit):
        sm.output_path("sandbox_world")
    gitignore = (REPO / ".gitignore").read_text().splitlines()
    assert "reports/*" in gitignore


# ---- the data of a real world (the smallest of the three) ----

@pytest.fixture(scope="module")
def dungeon():
    before = _tree(REPO / "data" / "worlds")
    first = sm.build_data("dungeon_crawl")
    second = sm.build_data("dungeon_crawl")
    return first, second, before, _tree(REPO / "data" / "worlds")


def test_building_a_world_is_deterministic_and_the_bytes_are_identical(dungeon):
    first, second, _, _ = dungeon
    assert first == second and sm.encode(first) == sm.encode(second)


def test_building_a_world_writes_nothing_into_the_world_repository(dungeon):
    _, _, before, after = dungeon
    assert before == after  # no world_index.json rewrite, no compile report


def test_cells_are_names_and_the_run_lengths_cover_the_grid_exactly(dungeon):
    data = dungeon[0]
    names, rle = data["terrain_names"], data["terrain_rle"]
    assert names == sorted(names) and set(names) == {r["name"] for r in data["terrain"]}
    assert sum(rle[1::2]) == data["width"] * data["height"] and all(0 <= i < len(names) for i in rle[0::2])
    by_name = Counter()
    for index, run in zip(rle[0::2], rle[1::2]):
        by_name[names[index]] += run
    assert dict(by_name) == {r["name"]: r["count"] for r in data["terrain"]}


def test_the_grid_equals_the_compiled_state_terrain_cell_by_cell(dungeon):
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    data = dungeon[0]
    state, _ = WorldCompiler.compile(WorldRepository("data/worlds").load_world("dungeon_crawl"), seed=sm.SEED)
    flat = [data["terrain_names"][i] for i, run in zip(data["terrain_rle"][0::2], data["terrain_rle"][1::2]) for _ in range(run)]
    width = data["width"]
    assert all(flat[y * width + x] == name for (x, y), name in state.terrain.items())


def test_every_kind_is_counted_and_each_unkeyed_kind_says_so(dungeon):
    data = dungeon[0]
    assert {r["name"]: r["count"] for r in data["kinds"]["entity"]} == dict(Counter(e["kind"] for e in data["entities"]))
    assert {r["name"]: r["count"] for r in data["kinds"]["place"]} == dict(Counter(p["kind"] for p in data["places"]))
    assert all(r["key"] is None or r["key"].startswith(("icon.", "terrain.")) for rows in data["kinds"].values() for r in rows)


def test_the_file_carries_its_sources_and_stays_small(dungeon):
    data = dungeon[0]
    assert data["format"] == sm.FORMAT and data["seed"] == 42 and "engine_manager.py" in data["sources"]["build_state"]
    assert len(sm.encode(data)) < 64 * 1024
    json.loads(sm.encode(data))


# ---- the proposed aliases: unconfirmed, only in the data, only for names without an exact key ----

def test_a_proposed_alias_is_added_only_to_a_name_without_an_exact_key_and_never_replaces_it():
    rows = {r["name"]: r for r in sm.key_rows(Counter({"forest": 1, "ruin": 1, "river": 1}), "terrain.", KEYS | {"terrain.grassland", "terrain.shallow_water"}, {"forest": "terrain.cave", "ruin": "terrain.ruins", "river": "terrain.shallow_water"})}
    assert "proposed_alias" not in rows["forest"] and rows["forest"]["key"] == "terrain.forest"  # an exact key wins and gets no alias
    assert rows["ruin"]["key"] is None and rows["ruin"]["proposed_alias"] == "terrain.ruins"
    assert rows["river"]["key"] is None and rows["river"]["proposed_alias"] == "terrain.shallow_water"


def test_an_alias_to_an_unregistered_key_is_refused():
    with pytest.raises(AssertionError):
        sm.key_rows(Counter({"river": 1}), "terrain.", KEYS, {"river": "terrain.not_registered"})


def test_every_proposed_alias_names_a_registered_key_and_the_registry_carries_exactly_the_three_v2_terrain_aliases():
    from visual_assets.store.catalog.registry import load_registry

    registry = load_registry(sm.REGISTRY_FILE)
    targets = {k for family in sm.PROPOSED_ALIASES.values() for k in family.values()}
    from tests.visual_assets import adopted_facts as af

    assert targets <= set(registry.keys) and dict(registry.aliases) == af.REGISTRY_ALIASES  # since `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES` the three terrain proposals are registry aliases too
    assert {f"terrain.{n.lower()}": k for n, k in sm.PROPOSED_ALIASES["terrain"].items()} == af.REGISTRY_ALIASES  # the proposals lowercased are exactly the registry's
    assert sm.ALIAS_LABEL == "unconfirmed: asset-planner proposal for rpg-planner (#519)"


def test_the_data_file_labels_the_aliases(dungeon):
    data = dungeon[0]
    assert data["proposed_aliases"]["label"] == sm.ALIAS_LABEL and data["proposed_aliases"]["terrain"]["ruin"] == "terrain.ruins"
    ruin = next(r for r in data["terrain"] if r["name"] == "ruin")
    assert ruin["key"] is None and ruin["proposed_alias"] == "terrain.ruins" and ruin["near"] == ["terrain.ruins"]

from src.api.presenters.state_presenter import StatePresenter
from src.core.state import (
    AuthoritativeState,
    BuildingState,
    ChestState,
    RegionState,
    ResourceNodeState,
)
from src.core.models.inventory import ItemStack


def _state(**overrides):
    defaults = dict(tick=0, seed=1)
    defaults.update(overrides)
    return AuthoritativeState(**defaults)


def test_present_map_empty_terrain():
    state = _state()
    assert StatePresenter.present_map(state) == {"width": 0, "height": 0, "grid": []}


def test_present_map_rle_round_trip():
    # 3x2 grid (width=3, height=2), row-major y*width+x:
    # row0: PLAIN PLAIN GRASS   row1: GRASS GRASS GRASS
    terrain = {
        (0, 0): "PLAIN", (1, 0): "PLAIN", (2, 0): "GRASS",
        (0, 1): "GRASS", (1, 1): "GRASS", (2, 1): "GRASS",
    }
    state = _state(terrain=terrain)
    result = StatePresenter.present_map(state)
    assert result["width"] == 3
    assert result["height"] == 2

    # Decode RLE back to a flat list, compare against expected codes.
    # Sorted distinct terrain types: ["GRASS", "PLAIN"] -> GRASS=0, PLAIN=1
    decoded = []
    grid = result["grid"]
    for i in range(0, len(grid), 2):
        decoded.extend([grid[i]] * grid[i + 1])
    assert decoded == [1, 1, 0, 0, 0, 0]


def test_present_map_deterministic_regardless_of_dict_insertion_order():
    terrain_a = {(0, 0): "WALL", (1, 0): "GRASS"}
    terrain_b = {(1, 0): "GRASS", (0, 0): "WALL"}
    result_a = StatePresenter.present_map(_state(terrain=terrain_a))
    result_b = StatePresenter.present_map(_state(terrain=terrain_b))
    assert result_a == result_b


def test_present_map_width_height_match_populated_extent():
    terrain = {(x, y): "PLAIN" for x in range(5) for y in range(4)}
    state = _state(terrain=terrain)
    result = StatePresenter.present_map(state)
    assert result["width"] == 5
    assert result["height"] == 4
    assert sum(result["grid"][1::2]) == 20  # total cell count preserved


def test_present_static_building_name_derived_owner_dropped():
    building = BuildingState(id=1, kind="BLACKSMITH", position=(3.0, 4.0))
    state = _state(buildings={1: building})
    result = StatePresenter.present_static(state)
    assert result["buildings"] == [{
        "building_id": "1",
        "name": "Blacksmith",
        "x": 3.0,
        "y": 4.0,
        "building_type": "BLACKSMITH",
        "owner_entity_id": None,
    }]


def test_present_static_resource_node_name_and_terrain_derived():
    node = ResourceNodeState(
        id=7, kind="IRON_VEIN", position=(2.0, 0.0), yields_item="iron_ore",
        remaining_charges=3, max_charges=3, required_ticks=10,
    )
    terrain = {(2, 0): "MOUNTAIN", (0, 0): "PLAIN"}
    state = _state(resource_nodes={7: node}, terrain=terrain)
    result = StatePresenter.present_static(state)
    rn = result["resource_nodes"][0]
    assert rn["node_id"] == 7
    assert rn["resource_type"] == "IRON_VEIN"
    assert rn["name"] == "Iron_Vein"
    assert rn["yields_item"] == "iron_ore"
    assert rn["max_harvests"] == 3
    assert rn["respawn_cooldown"] == node.respawn_cooldown
    assert rn["harvest_ticks"] == 10
    # sorted(["MOUNTAIN", "PLAIN"]) -> MOUNTAIN=0, PLAIN=1; node sits on MOUNTAIN
    assert rn["terrain"] == 0


def test_present_static_chest_guard_dropped_tier_defaulted_looted_derived():
    empty_chest = ChestState(id=1, position=(0.0, 0.0), items=[])
    full_chest = ChestState(id=2, position=(1.0, 1.0), items=[ItemStack(item_id="gold_coin", quantity=5)])
    state = _state(chests={1: empty_chest, 2: full_chest})
    result = StatePresenter.present_static(state)
    by_id = {c["chest_id"]: c for c in result["treasure_chests"]}
    assert by_id[1]["looted"] is True
    assert by_id[1]["tier"] == 1
    assert by_id[1]["guard_entity_id"] is None
    assert by_id[2]["looted"] is False
    assert by_id[2]["tier"] == 1
    assert by_id[2]["guard_entity_id"] is None


def test_present_static_region_derivation_from_bounds():
    region = RegionState(id="north_forest", name="North Forest", bounds=(0, 0, 10, 20), kind="FOREST", hazard_level=0.4)
    state = _state(regions={"north_forest": region})
    result = StatePresenter.present_static(state)
    r = result["regions"][0]
    assert r["region_id"] == "north_forest"
    assert r["name"] == "North Forest"
    assert r["center_x"] == 5.0
    assert r["center_y"] == 10.0
    assert r["radius"] == 10.0  # half of the larger dimension (20)
    assert r["difficulty"] == 0.4
    assert r["locations"] == []


def test_present_map_and_present_static_do_not_mutate_state():
    terrain = {(0, 0): "PLAIN"}
    region = RegionState(id="r1", name="R1", bounds=(0, 0, 4, 4))
    building = BuildingState(id=1, kind="SHOP", position=(0.0, 0.0))
    node = ResourceNodeState(id=1, kind="TREE", position=(0.0, 0.0), yields_item="wood",
                              remaining_charges=1, max_charges=1, required_ticks=5)
    chest = ChestState(id=1, position=(0.0, 0.0), items=[])
    state = _state(terrain=terrain, regions={"r1": region}, buildings={1: building},
                    resource_nodes={1: node}, chests={1: chest})
    before = state.to_canonical_dict() if hasattr(state, "to_canonical_dict") else None

    StatePresenter.present_map(state)
    StatePresenter.present_static(state)

    # Frozen dataclass: any attempted field assignment would already have raised
    # FrozenInstanceError during the calls above. Belt-and-suspenders: state is unchanged.
    assert state.terrain == terrain
    assert state.regions == {"r1": region}
    assert state.buildings == {1: building}
    if before is not None:
        assert state.to_canonical_dict() == before

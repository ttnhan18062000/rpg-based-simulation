import pytest
from src.content.repository import CatalogRepository
from src.core.registries import seed_phase1_content
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG


@pytest.fixture(autouse=True)
def cleanup_registries():
    """Automatically reset registries to default hardcoded fallback state after each test."""
    yield
    seed_phase1_content(None)


def get_test_profile():
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_C,
        max_ram_mb=512,
        max_cpu_percent=50,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5,
        max_tick_budget_ms=100.0,
        sampling_interval_ticks=1
    )


def create_smoke_spec() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "smoke_valley",
        "name": "Smoke Test Valley",
        "topology": {
            "width": 50,
            "height": 50,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "hometown", "type": "town", "bounds": [0, 0, 10, 10], "terrain": "GRASS"},
            {"id": "near_forest", "type": "wilderness", "bounds": [15, 15, 40, 40], "terrain": "FOREST"}
        ],
        "factions": [
            {"id": "town_council", "type": "civilian"},
            {"id": "goblin_warband", "type": "hostile"}
        ],
        "entities": [
            {"id": "citizen_group", "count": 2, "role": "citizen", "faction": "town_council", "spawn_region": "hometown"},
            {"id": "horde", "count": 1, "role": "raider", "faction": "goblin_warband", "spawn_region": "near_forest"}
        ],
        "resources": [
            {"id": "wood_node", "resource_type": "wood", "count": 2, "region": "near_forest"}
        ],
        "buildings": [
            {"id": "tavern", "type": "inn", "region": "hometown"}
        ],
        "quests": [
            {
                "id": "hunt_beasts",
                "name": "Hunt Wild Beasts",
                "kind": "hunt",
                "goal_value": 3.0,
                "reward": {"xp": 100, "gold": 50},
                "target_role": "raider",
                "target_region_id": "near_forest",
                "assignee": "citizen"
            }
        ]
    }


def test_catalog_mode_smoke_simulation():
    """Verify that a compiled catalog-seeded world can tick successfully in the simulator kernel."""
    # 1. Seed Content Catalog
    repo = CatalogRepository("data/content")
    repo.load_all()
    seed_phase1_content(repo)

    # 2. Compile world spec
    spec_data = create_smoke_spec()
    spec = WorldSpec.model_validate(spec_data)
    state, report = WorldCompiler.compile(spec, seed=42)
    
    assert state.tick == 0
    assert "hometown" in state.regions
    assert "near_forest" in state.regions
    assert len(state.entities) == 3

    # 3. Instantiate kernel and execute tick loop
    profile = get_test_profile()
    rng = DeterministicRNG(state.seed)
    
    kernel = Kernel(profile, state, rng, flags={"audit_mode": True})
    
    # Run 5 ticks and assert progress
    for _ in range(5):
        kernel.tick_once()
        
    assert kernel.state.tick == 5
    # Confirm entities still exist and simulator ticks proceeded cleanly
    assert len(kernel.state.entities) == 3

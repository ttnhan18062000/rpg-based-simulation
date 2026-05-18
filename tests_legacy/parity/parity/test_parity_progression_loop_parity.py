import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, InventoryComponent, ResourceNodeState, StrategicComponent, ItemStack
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.strategic import LeadState

@pytest.fixture
def profile():
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=100,
        max_cpu_percent=100,
        max_worker_count=0,
        max_queue_depth=10,
        max_replay_buffer_kb=100,
        max_observability_budget_percent=10,
        max_tick_budget_ms=100
    )

@pytest.fixture
def initial_state():
    # Hero at town, missing iron_ore, has wood and gold
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: EntityState(
                id=1,
                kind="hero",
                position=(0, 0),
                identity=IdentityComponent(
                    craft_target="craft_steel_sword",
                    known_recipes={"craft_steel_sword"}
                ),
                inventory=InventoryComponent(gold=100, items=[ItemStack("iron_ore", 1), ItemStack("wood", 1)])
            )
        },
        resource_nodes={
            101: ResourceNodeState(
                id=101,
                kind="ORE_VEIN",
                position=(1, 0), # Next to town
                yields_item="iron_ore",
                remaining_charges=5,
                max_charges=5,
                required_ticks=2 # Fast harvest for test
            )
        },
        town_tiles={(0,0)},
        building_tiles={(0,0): "blacksmith"}
    )

@pytest.mark.v2_contract
def test_full_resource_progression_loop(profile, initial_state):
    """
    Verify the integrated loop:
    1. Blacksmith Fail -> Blocker + Lead
    2. Redirection -> Move to Lead
    3. Interaction -> Harvest
    4. Auto-Resolution -> Blocker Cleared
    5. Redirection -> Return to Town
    6. Blacksmith Success
    """
    # Start with all materials except one iron_ore
    ent = initial_state.entities[1]
    initial_state = replace(initial_state, entities={
        1: replace(ent, strategic=StrategicComponent(leads={
            "lead_ore": LeadState(id="lead_ore", kind="location", subject="iron_ore", detail="1,0")
        }))
    })
    
    kernel = Kernel(profile, initial_state, DeterministicRNG(42))
    
    # Tick 1: At Blacksmith. Should fail and generate blockers.
    kernel.tick_once()
    hero = kernel.state.entities[1]
    assert "blocker_mat_iron_ore" in hero.strategic.blockers
    
    # Tick 1 resolution also moved hero to (1,0)
    assert hero.position == (1.0, 0.0)
    
    # Tick 2: Start Harvest
    kernel.tick_once()
    hero = kernel.state.entities[1]
    assert hero.interaction.progress == 1
    
    # Tick 3: Finish Harvest -> Redirect to Town
    kernel.tick_once()
    hero = kernel.state.entities[1]
    assert any(isinstance(i, ItemStack) and i.item_id == "iron_ore" and i.quantity == 2 for i in hero.inventory.items)
    assert hero.navigation.target == (0.0, 0.0)
    
    # Tick 4: Move back to town
    kernel.tick_once()
    hero = kernel.state.entities[1]
    assert hero.position == (0.0, 0.0)
    
    # Tick 5: At Blacksmith SUCCESS!
    kernel.tick_once()
    hero = kernel.state.entities[1]
    assert any(isinstance(i, ItemStack) and i.item_id == "steel_sword" for i in hero.inventory.items)
    assert hero.identity.craft_target == "" # Cleared on success
    
    print("LOOP PROOFS COMPLETE: 100% Loop Integrity Verified.")

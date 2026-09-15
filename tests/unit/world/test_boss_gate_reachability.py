"""World boss / Lair-occupant spawn gate: tier-5 stats, loot registration, and gate reachability."""
from dataclasses import replace

import pytest

from src.core.items import ItemRegistry
from src.core.models.inventory import InventoryComponent, ItemStack
from src.core.state import AuthoritativeState, PlaceKind, PlaceState, RegionState
from src.core.update_models.inventory import InventoryUpdate
from src.core.inventory import InventoryService
from src.systems.world_systems.generator import EntityGenerator
from src.world.boss import BossService
from src.world.spawn_config import DIFFICULTY_TIERS


def test_difficulty_tier_5_is_defined_and_stronger_than_tier_4():
    """Regression guard for the silent tier-1 fallback: DIFFICULTY_TIERS must have a
    real tier 5 entry, and it must be meaningfully stronger than tier 4 on every axis
    a world boss/Lair occupant cares about."""
    assert 5 in DIFFICULTY_TIERS
    tier4 = DIFFICULTY_TIERS[4]
    tier5 = DIFFICULTY_TIERS[5]
    assert tier5.hp > tier4.hp
    assert tier5.atk > tier4.atk
    assert tier5.def_stat > tier4.def_stat
    assert tier5.level_min > tier4.level_min
    assert tier5.level_max > tier4.level_max


def test_spawn_monster_at_tier_5_does_not_fall_back_to_tier_1():
    """The historical defect: EntityGenerator.spawn_monster()'s DIFFICULTY_TIERS.get()
    silently fell back to tier 1 for any unregistered tier. With tier 5 now defined,
    a tier-5 spawn must produce real tier-5 stats, not the tier-1 baseline."""
    state = AuthoritativeState(tick=0, seed=42)
    gen = EntityGenerator(seed=42)

    tier1_monster = gen.spawn_monster((0, 0), state, kind="world_boss", difficulty_tier=1)
    tier5_monster = gen.spawn_monster((0, 0), state, kind="world_boss", difficulty_tier=5)

    assert tier5_monster.combat.max_hp > tier1_monster.combat.max_hp
    assert tier5_monster.combat.atk > tier1_monster.combat.atk
    assert tier5_monster.combat.def_stat > tier1_monster.combat.def_stat

    mults = DIFFICULTY_TIERS[5]
    assert tier5_monster.combat.max_hp == int(50 * mults.hp)
    assert tier5_monster.combat.atk == int(10 * mults.atk)
    assert tier5_monster.combat.def_stat == int(5 * mults.def_stat)


def test_ancient_core_is_registered():
    """The world boss's own signature loot must exist in the real, non-raising
    ItemRegistry the inventory/equipment pipeline actually uses -- it silently
    dropped from inventory before this was registered."""
    defn = ItemRegistry.get("ancient_core")
    assert defn is not None
    assert defn.id == "ancient_core"


def test_ancient_core_survives_the_real_inventory_add_path():
    """Direct regression test for the defect: InventoryService.apply_update()'s
    `if not defn: continue` used to silently drop ancient_core on add. Now that it's
    registered, the add must actually land in the resulting inventory."""
    empty_inventory = InventoryComponent()
    update = InventoryUpdate(items_add=[ItemStack(item_id="ancient_core", quantity=1)])

    result = InventoryService.apply_update(empty_inventory, update)

    assert any(stack.item_id == "ancient_core" and stack.quantity == 1 for stack in result.items)


def test_boss_spawn_gate_reachable_at_lowered_thresholds():
    """The gate's own two halves (state.maturity, region.trauma_score) were each
    independently unreachable within the corpus's real 200-5,000 tick run lengths at
    the old values (50.0 / 20.0). At the new, lower thresholds, a region that meets
    them must actually spawn a formidable (tier-5) world boss, not a tier-1 fallback."""
    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=BossService.BOSS_SPAWN_TRAUMA_THRESHOLD,
    )
    state = AuthoritativeState(
        tick=2000,
        seed=42,
        maturity=BossService.BOSS_SPAWN_THRESHOLD,
        regions={"region_1": region},
    )

    update = BossService.check_for_boss_spawn(state, EntityGenerator(42))

    assert len(update.entities_add) == 1
    boss = update.entities_add[0]
    assert boss.kind == "world_boss"
    tier4 = DIFFICULTY_TIERS[4]
    # Formidable, not the historical tier-1-fallback bug: strictly stronger than tier 4.
    assert boss.combat.max_hp > int(50 * tier4.hp)
    assert boss.combat.atk > int(10 * tier4.atk)
    assert any(s.item_id == "ancient_core" for s in boss.inventory.items)


def test_boss_spawn_gate_still_closed_just_below_lowered_thresholds():
    """The gate must still be a real gate, not effectively always-open -- one tick of
    maturity or trauma below the new thresholds must not spawn a boss."""
    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=BossService.BOSS_SPAWN_TRAUMA_THRESHOLD - 0.01,
    )
    state = AuthoritativeState(
        tick=2000,
        seed=42,
        maturity=BossService.BOSS_SPAWN_THRESHOLD,
        regions={"region_1": region},
    )

    update = BossService.check_for_boss_spawn(state, EntityGenerator(42))

    assert update.entities_add == []


def test_lair_spawn_gate_reachable_at_lowered_thresholds_and_is_formidable():
    """Same reachability + formidability proof as the world-boss gate, for the
    Lair-occupant path (check_for_lair_spawn), which shares the identical gate."""
    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=BossService.BOSS_SPAWN_TRAUMA_THRESHOLD,
    )
    place = PlaceState(
        place_id="lair_1",
        region_id="region_1",
        kind=PlaceKind.LAIR,
        position=(50.0, 50.0),
    )
    state = AuthoritativeState(
        tick=2000,
        seed=42,
        maturity=BossService.BOSS_SPAWN_THRESHOLD,
        regions={"region_1": region},
        places={"lair_1": place},
    )

    update = BossService.check_for_lair_spawn(state, EntityGenerator(42))

    assert len(update.entities_add) == 1
    occupant = update.entities_add[0]
    assert occupant.kind == "dragonkin"
    tier4 = DIFFICULTY_TIERS[4]
    assert occupant.combat.max_hp > int(50 * tier4.hp)
    assert occupant.combat.atk > int(10 * tier4.atk)

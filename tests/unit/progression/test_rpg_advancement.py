"""
RPG advancement and specialized progression tests.

Covers:
- RPG-0070: xp_accumulation_determinism
- RPG-0075: skill_cooldown_gating
- RPG-0076: move_cost_stat_injection
"""

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ItemStack
from src.core.enums import EntityRole, Faction
from src.core.updates import StateUpdate, EntityUpdate, RewardUpdate
from src.engine.apply import ApplyPath
from src.engine.domain_logic import SimulationDomainLogic
from src.progression.leveling import LevelingService


def stack(item_id: str, quantity: int = 1) -> ItemStack:
    """Create an inventory stack using the V2 inventory shape."""
    return ItemStack(item_id=item_id, quantity=quantity)


def make_hero(
    entity_id: int = 1,
    *,
    pos: tuple[float, float] = (0.0, 0.0),
    hp: int = 100,
    max_hp: int = 100,
    atk: int = 10,
    def_stat: int = 5,
    attack_range: int = 1,
    readiness: float = 100.0,
    items: list[ItemStack] | None = None,
    max_slots: int | None = None,
    learned_skills: set[str] | None = None,
    cooldowns: dict[str, int] | None = None,
    evolution_level: int = 1,
    evolution_points: int = 0,
    unspent_ap: int = 0,
):
    """
    Build a fully valid hero for progression/combat tests.

    Fraud this catches:
    - tests accidentally create an invalid actor with missing faction/role
    - skill/combat tests fail before reaching the progression logic
    - inventory tests use raw strings instead of ItemStack
    """
    builder = (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(*pos)
        .identity(
            role=EntityRole.HERO,
            faction=Faction.HERO_GUILD,
            learned_skills=learned_skills or set(),
            cooldowns=cooldowns or {},
            evolution_level=evolution_level,
            evolution_points=evolution_points,
            unspent_ap=unspent_ap,
        )
        .combat(
            hp=hp,
            max_hp=max_hp,
            atk=atk,
            def_stat=def_stat,
            attack_range=attack_range,
            alive=hp > 0,
            readiness=readiness,
        )
        .lifecycle(active=True)
    )

    if items is not None or max_slots is not None:
        builder = builder.inventory(
            items=items or [],
            max_slots=max_slots,
        )

    return builder.build()


def make_goblin(
    entity_id: int = 2,
    *,
    pos: tuple[float, float] = (1.0, 0.0),
    hp: int = 30,
    max_hp: int = 30,
    atk: int = 8,
    def_stat: int = 2,
    attack_range: int = 1,
    readiness: float = 100.0,
):
    """Build a fully valid goblin target for combat/progression tests."""
    return (
        V2EntityBuilder(entity_id)
        .kind("goblin")
        .location(*pos)
        .identity(
            role=EntityRole.MONSTER,
            faction=Faction.MONSTER_HORDE,
            evolution_level=1,
        )
        .combat(
            hp=hp,
            max_hp=max_hp,
            atk=atk,
            def_stat=def_stat,
            attack_range=attack_range,
            alive=hp > 0,
            readiness=readiness,
        )
        .lifecycle(active=True)
        .build()
    )


def test_xp_accumulation_and_level_up():
    """
    Verify that XP rewards are applied through ApplyPath and trigger level-up.

    Fraud this catches:
    - reward XP is stored but level-up logic is skipped
    - XP threshold calculation changes unexpectedly
    - AP gain on hero level-up is not applied
    """
    hero = make_hero(
        1,
        evolution_level=1,
        evolution_points=0,
        unspent_ap=0,
    )

    assert hero.identity.evolution_level == 1
    assert hero.identity.evolution_points == 0
    assert hero.identity.unspent_ap == 0

    xp_needed = LevelingService.get_xp_required(1)
    assert xp_needed == 100

    state_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                reward=RewardUpdate(xp_gain=100),
            )
        }
    )

    state = AuthoritativeState(tick=0, seed=42, entities={1: hero})
    new_state = ApplyPath.apply_generation(state, state_upd)

    new_hero = new_state.entities[1]
    assert new_hero.identity.evolution_level == 2
    assert new_hero.identity.evolution_points == 0
    assert new_hero.identity.unspent_ap == 5


def test_level_99_cap_enforcement():
    """
    Verify that level 99 is a hard level cap while XP can still accumulate.

    New builder rule:
        evolution fields are part of IdentityComponent, so use
        `.identity(evolution_level=..., evolution_points=...)` instead of the
        removed `.evolution(...)` shortcut.
    """
    hero = make_hero(
        1,
        evolution_level=99,
        evolution_points=0,
        unspent_ap=0,
    )

    state_upd = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                reward=RewardUpdate(xp_gain=1000),
            )
        }
    )

    state = AuthoritativeState(tick=0, seed=42, entities={1: hero})
    new_state = ApplyPath.apply_generation(state, state_upd)

    new_hero = new_state.entities[1]
    assert new_hero.identity.evolution_level == 99
    assert new_hero.identity.evolution_points == 1000
    assert new_hero.identity.unspent_ap == 0


def test_xp_granted_even_if_inventory_full():
    """
    Verify that XP reward transfer is independent from slot-limited inventory.

    This test intentionally checks transfer generation instead of full resource
    resolution. The key law is that XP must be emitted as its own independent
    transfer and must not be grouped with slot-limited loot.

    Fraud this catches:
    - XP reward is coupled to item/gold transfer grouping
    - inventory-full reward handling can block XP progress
    - test uses raw string inventory items instead of ItemStack
    """
    full_inventory = [stack("iron_ore") for _ in range(16)]

    hero = make_hero(
        1,
        pos=(0.0, 0.0),
        atk=999,
        items=full_inventory,
        max_slots=16,
    )
    assert len(hero.inventory.items) == 16

    monster = make_goblin(2, pos=(1.0, 0.0), hp=30, max_hp=30)

    state = AuthoritativeState(
        tick=0,
        seed=42,
        entities={1: hero, 2: monster},
    )

    results = SimulationDomainLogic.execute_action(
        hero,
        {"action": "ATTACK", "target_id": 2},
        current_tick=0,
        neighbor_view=[(2, monster)],
        context=state,
    )

    hero_up = results[1]
    assert len(hero_up.resource_transfers) == 2

    xp_intent = next(
        intent for intent in hero_up.resource_transfers
        if intent.xp_reward > 0
    )
    gold_intent = next(
        intent for intent in hero_up.resource_transfers
        if intent.gold_delta > 0
    )

    assert xp_intent.group_id is None
    assert not xp_intent.is_group_required

    assert gold_intent.group_id is not None or gold_intent.is_group_required


def test_equipment_stat_injection_move_cost():
    """
    Verify that effective movement cost is derived from agility and equipment.

    This is a direct stat-scaling test, not a movement-system test.
    """
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .attributes(agility=5)
        .combat(readiness=100.0)
        .lifecycle(active=True)
        .build()
    )

    from src.engine.rpg_depth import SkillScalingService

    derived = SkillScalingService.get_effective_stats(
        hero.attributes,
        hero.equipment,
    )
    assert derived["move_cost"] == pytest.approx(9.5)

    from src.core.state import EquipmentComponent, EquipSlot
    from src.core.items import ItemRegistry as CoreItemRegistry, ItemDefinition, ItemKind

    # Ensure iron_plate is registered regardless of which seed order ran before this test.
    # The catalog bootstrap (triggered by test collection order) may omit iron_plate;
    # register it directly so the weight (12.0) contributes to move_cost as expected.
    if CoreItemRegistry.get("iron_plate") is None:
        existing = dict(CoreItemRegistry._items)
        existing["iron_plate"] = ItemDefinition(
            id="iron_plate", name="Iron Plate", kind=ItemKind.ARMOR, weight=12.0,
            stack_size=1, properties={"def_bonus": 15, "slot": EquipSlot.TORSO}
        )
        CoreItemRegistry._items = existing

    plate_equip = EquipmentComponent(slots={EquipSlot.TORSO: "iron_plate"})

    derived_heavy = SkillScalingService.get_effective_stats(
        hero.attributes,
        plate_equip,
    )
    assert derived_heavy["move_cost"] == pytest.approx(11.9)


def test_skill_cooldown_gating():
    """
    Verify skill cooldown behavior.

    Scenario:
    - a hero that knows `power_strike` uses it successfully at tick 10
    - the skill writes cooldown tick 13
    - the same hero cannot use the skill again before tick 13

    Fraud this catches:
    - skill cooldown is not emitted on successful use
    - cooldown rejection path accidentally adds a new cooldown update
    - second hero setup forgets learned_skills and fails for the wrong reason
    """
    hero = make_hero(
        1,
        pos=(0.0, 0.0),
        learned_skills={"power_strike"},
    )
    monster = make_goblin(2, pos=(1.0, 0.0))

    state = AuthoritativeState(
        tick=10,
        seed=42,
        entities={1: hero, 2: monster},
    )

    results = SimulationDomainLogic.execute_action(
        hero,
        {"action": "SKILL", "skill_id": "power_strike", "target_id": 2},
        current_tick=10,
        neighbor_view=[(2, monster)],
        context=state,
    )

    assert 1 in results
    hero_up = results[1]
    assert hero_up.identity is not None
    assert hero_up.identity.cooldown_updates["power_strike"] == 13

    hero_on_cooldown = make_hero(
        1,
        pos=(0.0, 0.0),
        learned_skills={"power_strike"},
        cooldowns={"power_strike": 13},
    )

    state = AuthoritativeState(
        tick=10,
        seed=42,
        entities={1: hero_on_cooldown, 2: monster},
    )

    results_fail = SimulationDomainLogic.execute_action(
        hero_on_cooldown,
        {"action": "SKILL", "skill_id": "power_strike", "target_id": 2},
        current_tick=10,
        neighbor_view=[(2, monster)],
        context=state,
    )

    hero_up_fail = results_fail[1]
    assert hero_up_fail.readiness_delta == -10.0
    assert hero_up_fail.identity is None

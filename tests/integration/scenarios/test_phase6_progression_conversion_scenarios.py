"""
tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py

Phase 6 — Scenario integration tests (Scenario 6.1 to 6.7).
"""

import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, ItemStack, EquipmentComponent, EquipSlot, PersonalityComponent
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate
from src.domains.progression.phase import ProgressionConversionPhase


def test_scenario_6_1_reward_gold_becomes_repair():
    # Damaged weapon, receives enough gold -> repair decision
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         # Cautious (bravery = 0.1, so caution = 0.9)
         .identity(personality=PersonalityComponent(bravery=0.1)))
    entity = b.build()
    
    # Low durability weapon
    entity = replace(entity,
        equipment=EquipmentComponent(
            slots={EquipSlot.MAIN_HAND: "iron_sword"},
            durability={EquipSlot.MAIN_HAND: 0.15}
        )
    )
    
    # Build ledger with gold reward
    from src.domains.progression.schema import RewardLedgerComponent, RewardEntry
    ledger = RewardLedgerComponent(entries=(
        RewardEntry(tick=1, kind="gold", subject="quest", quantity=80),
    ))
    
    entity = replace(entity, identity=replace(entity.identity, properties={"reward_ledger": ledger}))
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    
    update = StateUpdate()
    refined = ProgressionConversionPhase.execute(state, update)
    
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    
    assert ent_up.task is not None
    assert ent_up.task.work_kind_set == "BLACKSMITH_REPAIR"


def test_scenario_6_2_loot_material_kept():
    # Known iron_sword recipe, has low gold, but receives iron_ore -> keeps instead of selling
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .identity(known_recipes={"iron_sword"}, personality=PersonalityComponent(industry=0.9)))
    entity = b.build()
    
    stack = ItemStack(item_id="iron_ore", quantity=1)
    entity = replace(entity, inventory=replace(entity.inventory, items=[stack]))
    
    from src.domains.progression.possession import PossessionUnderstandingService
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    comp = PossessionUnderstandingService.evaluate(entity, state)
    
    # Ore keep priority is high
    assert comp.meanings["iron_ore"].keep_priority > comp.meanings["iron_ore"].sell_priority


def test_scenario_6_3_junk_loot_sold():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .identity(personality=PersonalityComponent(greed=0.9)))
    entity = b.build()
    
    from src.domains.progression.schema import RewardLedgerComponent, RewardEntry
    ledger = RewardLedgerComponent(entries=(
        RewardEntry(tick=1, kind="item", subject="broken_mug", quantity=5),
    ))
    entity = replace(entity, identity=replace(entity.identity, properties={"reward_ledger": ledger}))
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    update = StateUpdate()
    refined = ProgressionConversionPhase.execute(state, update)
    
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    assert len(ent_up.resource_transfers) == 1
    assert ent_up.resource_transfers[0].transfer_kind == "SELL"


def test_scenario_6_4_better_weapon_equipped():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()

    # Prepopulate the item in inventory so that possession service evaluates it
    stack = ItemStack(item_id="iron_sword", quantity=1)
    entity = replace(entity,
        inventory=replace(entity.inventory, items=[stack]),
        equipment=EquipmentComponent(slots={EquipSlot.MAIN_HAND: "rusted_sword"})
    )
    
    from src.domains.progression.schema import RewardLedgerComponent, RewardEntry
    ledger = RewardLedgerComponent(entries=(
        RewardEntry(tick=1, kind="item", subject="iron_sword", quantity=1),
    ))
    entity = replace(entity, identity=replace(entity.identity, properties={"reward_ledger": ledger}))
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    update = StateUpdate()
    refined = ProgressionConversionPhase.execute(state, update)
    
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    assert ent_up.equipment is not None
    assert ent_up.equipment.slot_updates.get(EquipSlot.MAIN_HAND) == "iron_sword"


def test_scenario_6_5_unknown_rare_item():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()
    
    from src.domains.progression.schema import RewardLedgerComponent, RewardEntry
    ledger = RewardLedgerComponent(entries=(
        RewardEntry(tick=1, kind="item", subject="ancient_fragment", quantity=1),
    ))
    entity = replace(entity, identity=replace(entity.identity, properties={"reward_ledger": ledger}))
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    update = StateUpdate()
    refined = ProgressionConversionPhase.execute(state, update)
    
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    assert ent_up.task is not None
    assert ent_up.task.work_kind_set == "ASK_INFORMATION"


def test_scenario_6_6_xp_ap_progression():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()
    
    from src.domains.progression.schema import RewardLedgerComponent, RewardEntry
    ledger = RewardLedgerComponent(entries=(
        RewardEntry(tick=1, kind="xp", subject="quest", quantity=100),
    ))
    entity = replace(entity, identity=replace(entity.identity, properties={"reward_ledger": ledger}))
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    update = StateUpdate()
    refined = ProgressionConversionPhase.execute(state, update)
    
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    assert ent_up.identity is not None
    assert ent_up.identity.unspent_ap_delta == -1


def test_scenario_6_7_personality_biases():
    # Greedy (greed=0.9, industry=0.1, caution=0.5) vs Industrious (greed=0.1, industry=0.9, caution=0.5)
    b_greedy = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .identity(personality=PersonalityComponent(greed=0.9)))
    
    b_industrious = (V2EntityBuilder(2)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .identity(personality=PersonalityComponent(industry=0.9)))
    
    ent1 = b_greedy.build()
    ent2 = b_industrious.build()
    
    from src.domains.progression.schema import RewardLedgerComponent, RewardEntry
    ledger = RewardLedgerComponent(entries=(
        RewardEntry(tick=1, kind="item", subject="iron_ore", quantity=1),
    ))
    
    stack = ItemStack(item_id="iron_ore", quantity=1)
    ent1 = replace(ent1, inventory=replace(ent1.inventory, items=[stack]))
    ent2 = replace(ent2, inventory=replace(ent2.inventory, items=[stack]))

    ent1 = replace(ent1, identity=replace(ent1.identity, known_recipes={"iron_sword"}, properties={"reward_ledger": ledger}))
    ent2 = replace(ent2, identity=replace(ent2.identity, known_recipes={"iron_sword"}, properties={"reward_ledger": ledger}))
    
    state = AuthoritativeState(entities={1: ent1, 2: ent2}, tick=1, seed=1)
    update = StateUpdate()
    refined = ProgressionConversionPhase.execute(state, update)
    
    dec1 = refined.entity_updates[1].property_updates["last_progression_decision"]
    dec2 = refined.entity_updates[2].property_updates["last_progression_decision"]
    
    # Greedy likes SAVE_FOR_LATER or SELL_LOOT
    assert dec1.selected[0].kind.value in ("SAVE_FOR_LATER", "SELL_LOOT")
    # Industrious prefers CRAFT_ITEM or keeping
    assert dec2.selected[0].kind.value == "CRAFT_ITEM"

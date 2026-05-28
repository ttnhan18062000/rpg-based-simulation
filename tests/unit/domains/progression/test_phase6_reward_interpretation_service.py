"""
tests/unit/domains/progression/test_phase6_reward_interpretation_service.py

Phase 6 — RewardInterpretationService tests.
"""

import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, ItemStack, EquipmentComponent, EquipSlot
from src.core.builder import V2EntityBuilder
from src.domains.progression.possession import PossessionUnderstandingService
from src.domains.progression.gaps import GrowthGapEvaluator
from src.domains.progression.schema import RewardLedgerComponent
from src.domains.progression.ledger import RewardLedgerService
from src.domains.progression.interpretation import RewardInterpretationService


def test_gold_reward_resolves_repair_affordability():
    # Entity with damaged weapon, low gold, receives gold
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=5))
    entity = b.build()
    
    entity = replace(entity,
        equipment=EquipmentComponent(
            slots={EquipSlot.MAIN_HAND: "iron_sword"},
            durability={EquipSlot.MAIN_HAND: 0.15}
        )
    )
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)
    
    assert report.dominant_gap == "repair_gap"
    
    # Receive 80 gold
    ledger = RewardLedgerComponent()
    ledger = RewardLedgerService.record_entry(ledger, tick=1, kind="gold", subject="quest_payment", quantity=80)
    
    interp = RewardInterpretationService.interpret(entity, ledger, possession, report, state)
    assert len(interp.meanings) == 1
    m = interp.meanings[0]
    assert m.meaning == "can_repair_weapon"
    assert m.priority == 0.9
    assert "repair" in m.suggested_conversion_tags


def test_material_reward_resolves_known_recipe_gap():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()
    
    entity = replace(entity,
        identity=replace(entity.identity, known_recipes={"iron_sword"})
    )
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)
    
    # Receives iron_ore
    ledger = RewardLedgerComponent()
    ledger = RewardLedgerService.record_entry(ledger, tick=1, kind="item", subject="iron_ore", quantity=1)
    
    # possession needs evaluating again to contain the item context
    # Let's add the item to the entity inventory first so possession understands it
    stack = ItemStack(item_id="iron_ore", quantity=1)
    entity_with_item = replace(entity, inventory=replace(entity.inventory, items=[stack]))
    possession = PossessionUnderstandingService.evaluate(entity_with_item, state)
    
    interp = RewardInterpretationService.interpret(entity_with_item, ledger, possession, report, state)
    assert len(interp.meanings) == 1
    m = interp.meanings[0]
    assert m.meaning == "recipe_material"
    assert "craft" in m.suggested_conversion_tags

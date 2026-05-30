"""
tests/unit/domains/progression/test_phase6_conversion_option_generator.py

Phase 6 — ConversionOptionGenerator tests.
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
from src.domains.progression.generator import ConversionOptionGenerator


def test_better_weapon_generates_equip_option():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()
    
    stack = ItemStack(item_id="iron_sword", quantity=1)
    entity = replace(entity,
        inventory=replace(entity.inventory, items=[stack]),
        equipment=EquipmentComponent(slots={EquipSlot.MAIN_HAND: "rusted_sword"})
    )
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)
    
    # Receive iron_sword item
    ledger = RewardLedgerComponent()
    ledger = RewardLedgerService.record_entry(ledger, tick=1, kind="item", subject="iron_sword", quantity=1)
    
    interp = RewardInterpretationService.interpret(entity, ledger, possession, report, state)
    options = ConversionOptionGenerator.generate(entity, interp, report, state)
    
    kinds = [o.kind for o in options]
    assert "EQUIP_ITEM" in kinds
    # EQUIP_ITEM should be high score
    assert options[0].kind == "EQUIP_ITEM"

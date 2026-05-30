import pytest
from src.core.builder import V2EntityBuilder
from src.core.models.inventory import ItemStack
from src.world.providers.requirements import Requirement, RequirementEvaluator


def test_has_gold_requirement():
    """Verify has_gold correctly validates and generates blockers on failure."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .inventory(gold=50)
        .build())
        
    # Test pass
    req_pass = Requirement(kind="has_gold", quantity=30)
    res_pass = RequirementEvaluator.evaluate(ent, None, req_pass)
    assert res_pass.passed
    assert res_pass.blocker_kind is None

    # Test fail
    req_fail = Requirement(kind="has_gold", quantity=100)
    res_fail = RequirementEvaluator.evaluate(ent, None, req_fail)
    assert not res_fail.passed
    assert res_fail.blocker_kind == "not_enough_gold"
    assert "gather_for_gold" in res_fail.suggested_resolution_tags


def test_has_item_requirement():
    """Verify has_item correctly validates inventory quantities and flags missing materials."""
    stack1 = ItemStack(item_id="iron_ore", quantity=1)
    stack2 = ItemStack(item_id="wood", quantity=3)
    
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .inventory(items=[stack1, stack2])
        .build())

    # Test pass (item exists with sufficient quantity)
    req_pass = Requirement(kind="has_item", subject="wood", quantity=2)
    res_pass = RequirementEvaluator.evaluate(ent, None, req_pass)
    assert res_pass.passed

    # Test fail (item exists but insufficient quantity)
    req_fail_qty = Requirement(kind="has_item", subject="iron_ore", quantity=2)
    res_fail_qty = RequirementEvaluator.evaluate(ent, None, req_fail_qty)
    assert not res_fail_qty.passed
    assert res_fail_qty.blocker_kind == "missing_material"

    # Test fail (item completely missing)
    req_fail_missing = Requirement(kind="has_item", subject="moon_resin", quantity=1)
    res_fail_missing = RequirementEvaluator.evaluate(ent, None, req_fail_missing)
    assert not res_fail_missing.passed
    assert res_fail_missing.blocker_kind == "missing_material"
    assert "ask_information" in res_fail_missing.suggested_resolution_tags

---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79
artifact_type: plan
tags: []
---

# plan - TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79

1. `MarketSystem.get_item_base_value` returns the registry item's `value` (content base_value); only an item the registry does not know gets `UNKNOWN_ITEM_BASE_VALUE`. The hardcoded table goes.
2. `MarketSystem.get_item_kind` returns the item's content kind (`ItemKind` value, OTHER when unknown); the name parsing goes. Regional and building price modifiers key on that kind.
3. Tests: `tests/unit/world/test_price_comes_from_content.py`; `test_domain_8_economy.py` declares its worked numbers (iron ore 5, iron sword 50) as content in a fixture, assertions unchanged.
4. Measure alone under audit_mode (paired, base = step 1 tip b5565796d), divergence 2.132.

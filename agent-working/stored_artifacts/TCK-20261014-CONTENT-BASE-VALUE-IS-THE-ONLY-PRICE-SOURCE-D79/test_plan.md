---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79
artifact_type: test_plan
tags: []
---

# test_plan - TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79

- Base value is the catalog value; unknown item defaults; a declared zero stays zero; kind comes from content (a name containing sword and ore is a material); price = catalog value x modifiers x 1.2/0.8; the market source names no item.
- Regression: tests/unit/resource, tests/unit/world, tests/unit/social, tests/unit/core.

## Proof Plan
- Level: unit plus paired simulation measurement.
- Proof kind: behavioural tests and paired audit_mode runs.
- Oracle source: Mechanics Bible 03 section 4 (EXCH-01) and owner ruling D79.
- Expected effect: prices equal catalog value times the existing modifiers; runs drift only where a price is read.
- Selected commands: `python -m pytest tests/unit/world/test_price_comes_from_content.py tests/unit/resource -q`.

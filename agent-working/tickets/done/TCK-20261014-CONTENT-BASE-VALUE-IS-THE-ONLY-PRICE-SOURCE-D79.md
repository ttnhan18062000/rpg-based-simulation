---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79

## Title
The catalog base value is the only price source (D79 step 2)

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Remove the market's hardcoded item price table and name-parsed kinds; price from the catalog `base_value` only.

## Scope
- `src/systems/economy_systems/market.py`, `src/content/schema.py` (required `base_value`), tests, Bible chapter 03, parity ledger TOWN-202, divergence 2.132.

## Out of Scope
- Removing the registry's built-in no-catalog fallback items (own step after v1).
- Giving grass_cover a value (content question after v1).

## Acceptance Criteria
- The market names no item and parses no name for kind; an unknown item is worth 10.
- A catalog item without `base_value` fails to compile.
- Gate-world final digests identical to base.

## Related Tickets
- TCK-20261014-EVERY-MATERIAL-ITEM-CAN-BE-SOLD-AS-SPARE-D79

## Related Docs
- docs/mechanics/03_economic_laws.md, docs/guidelines/intentional_divergences.md (2.132)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-CONTENT-BASE-VALUE-IS-THE-ONLY-PRICE-SOURCE-D79/

## Related Code Areas
- src/systems/economy_systems/market.py, src/content/schema.py

## Assumptions / Open Questions
- grass_cover value 0 is a content question after v1.

## Implementation Notes
See plan.md and divergence 2.132.

## Test Summary
test_price_comes_from_content.py (7), test_domain_8_economy (fixture only); 30-run paired measurement identical.

## Files Changed
market.py, schema.py, tests, docs.

## Completion Summary
Done; divergence 2.132.

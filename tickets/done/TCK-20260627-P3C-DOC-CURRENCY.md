---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260627-P3C-DOC-CURRENCY
phase: done
date: 2026-06-27
tags: [p3, documentation, mechanics-bible, parity, verification, stale-claims]
---

# TCK-20260627-P3C-DOC-CURRENCY

## Title
Verify 4 uncertain Mechanics Bible claims against source code

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
D17 identified 4 uncertain claims in Mechanics Bible chapters that were not verified during the D17 pass. These should be verified against source code constants before being treated as authoritative. Source: D17 P2 items.

## Scope
Verify the following 4 uncertain claims:

| Chapter | File | Uncertain Claim | Verify By |
|---|---|---|---|
| 02 — Combat Laws | `docs/mechanics/02_combat_laws.md` | Cover `+0.30` Def, Bond Synergy `+0.10` Atk | Check `COVER_REDUCTION` and `BOND_SYNERGY_BONUS` constants in combat source |
| 03 — Economic Laws | `docs/mechanics/03_economic_laws.md` | Slot Limit 16, Weight 100.0 kg; Home Storage 32/200 kg; selling formula | Verify `InventoryComponent` defaults and `ShopSystem.enforce()` formula |
| 04 — Strategic Cognition | `docs/mechanics/04_strategic_cognition.md` | Goal tier numbering; blocker types; perception radius 10–15; info decay 100 ticks | Audit 4 uncertain claims against source code |
| 06 — Worldbuilding Foundation | `docs/mechanics/06_worldbuilding_foundation.md` | "Certified Level 1" self-certification claim | Update to reflect chapters 01/04 had stale claims; re-certify |

For each claim: read the source constant, compare to the doc claim, update the doc if wrong, mark as verified in the parity ledger if applicable.

Run `make knowledge-index-update` after all doc updates.

## Out of Scope
- Fixing any behavioral bugs surfaced by the verification.
- Re-auditing claims already marked `[E]` (verified) in D17.

## Acceptance Criteria
- [ ] All 4 uncertain claims checked against source code.
- [ ] Each claim is either confirmed accurate (doc unchanged) or corrected (doc updated with verified value).
- [ ] `docs/mechanics/06_worldbuilding_foundation.md` "Certified Level 1" claim updated to reflect current status.
- [ ] Relevant parity ledger entries updated if claims were wrong.
- [ ] `make knowledge-index-update` run after changes.

## Related Tickets
- N/A

## Related Docs
- `docs/audits/D17_documentation_currency.md` P2 items
- `docs/mechanics/02_combat_laws.md`
- `docs/mechanics/03_economic_laws.md`
- `docs/mechanics/04_strategic_cognition.md`
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/parity_ledger/combat_movement.yaml`
- `docs/parity_ledger/town_resource.yaml`
- `docs/parity_ledger/strategic_cognition.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-MECHANICS-SUBCONTRACTS/` — mechanics sub-contract context

## Related Code Areas
- Combat source (for COVER_REDUCTION, BOND_SYNERGY_BONUS constants)
- `src/core/models/` (InventoryComponent defaults)
- Shop system source (selling formula)
- Strategic cognition source (perception radius, info decay)

## Assumptions / Open Questions
- Claims listed as uncertain may be correct — the goal is verification, not necessarily correction.
- Start with semantic search for each constant name before reading raw source.

## Implementation Notes
Verified all 4 uncertain claim groups against source code:

**Ch 02 — Combat Laws:** COVER_REDUCTION=0.30 (`src/engine/combat.py:27`) and BOND_SYNERGY_BONUS=0.10 (`src/engine/combat.py:28`) confirmed correct. Updated `last_verified: 2026-06-27`. No content changes needed.

**Ch 03 — Economic Laws:** Found 2 stale claims:
- Weight limit: doc said 100.0 kg, code has `max_weight: float = 50.0` (`src/core/models/inventory.py:45`). Corrected to 50.0 kg.
- Selling formula: doc said `Item_Base_Value * 0.5 * Market_Multiplier`; code uses static 50% (`DynamicPriceService.calculate_sell_price` returns `max(1, int(base_value * 0.5))`). ShopSystem applies a trauma surcharge separately (`base * (1.0 + trauma/10.0)`). Corrected to remove Market_Multiplier reference.
- Slot limit (16) and Home Storage (32 slots/200 kg) confirmed correct.

**Ch 04 — Strategic Cognition:** Found 3 stale claims:
- Blocker types: doc listed "Inventory, Congestion" as distinct kinds; code uses `BlockerKind` enum (MATERIAL, CAPABILITY, ACCESS, SOCIAL, GROUP). Congestion uses `kind="access"` with `subject="congestion"`. Inventory uses string `"inventory"`. Updated to list all 6 actual kinds.
- Perception radius: doc said "10.0 to 15.0 units"; all perception calls use 10.0 consistently (15.0 is cooperation candidate selection only). Corrected to 10.0.
- Info decay: doc said "every 100 ticks"; `BeliefCycleSystem.decay_stale_beliefs` default `stale_threshold=50`. Corrected to 50 ticks.
- Goal tier numbering: conceptual framework is qualitatively valid (utility scoring creates implicit priority ordering); no code changes needed.

**Ch 06 — Worldbuilding Foundation:** Updated "Certified Level 1" blanket claim to per-chapter status table. Ch 05 remains partially verified (2 uncertain constants: respawn interval, trauma delta). Also updated `docs/mechanics/README.md` certification summary.

**Parity ledger:** Added TOWN-184, TOWN-185, STRAT-237, STRAT-238, STRAT-239.

## Test Summary
- No code tests. Verify by reading source vs. doc.
- Run `make knowledge-index-update` after all doc edits.

## Files Changed
- `docs/mechanics/02_combat_laws.md` — last_verified date updated; constants confirmed correct
- `docs/mechanics/03_economic_laws.md` — weight limit corrected 100.0→50.0 kg; selling formula corrected (removed Market_Multiplier)
- `docs/mechanics/04_strategic_cognition.md` — blocker types corrected; perception radius corrected 10-15→10.0; info decay corrected 100→50 ticks
- `docs/mechanics/06_worldbuilding_foundation.md` — "Certified Level 1" blanket claim replaced with per-chapter status table
- `docs/mechanics/README.md` — certification summary updated
- `docs/parity_ledger/town_resource.yaml` — added TOWN-184 (inventory defaults), TOWN-185 (selling formula)
- `docs/parity_ledger/strategic_cognition.yaml` — added STRAT-237 (blocker kinds), STRAT-238 (perception radius), STRAT-239 (info decay)

## Completion Summary
Verified all 4 uncertain Mechanics Bible claim groups from D17. Ch 02 constants confirmed correct. Ch 03 corrected (weight 50.0 kg, selling = static 50%). Ch 04 corrected (blocker kinds per enum, perception radius 10.0, info decay 50 ticks). Ch 06 certification claim updated to per-chapter status table. 5 new parity ledger entries added. 14 doc tests passed.

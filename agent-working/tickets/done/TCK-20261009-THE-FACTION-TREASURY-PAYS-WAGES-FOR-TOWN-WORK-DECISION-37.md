---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261009-THE-FACTION-TREASURY-PAYS-WAGES-FOR-TOWN-WORK-DECISION-37
phase: done
date: 2026-10-10
tags: [economy, resource]
---

# TCK-20261009-THE-FACTION-TREASURY-PAYS-WAGES-FOR-TOWN-WORK-DECISION-37

## Title
A treasury pays upkeep into the building's own purse, and the building pays town work; the +10 building mint is removed

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner decisions 37 and 58: town work is the ordinary WORK shift at a building a treasury keeps; the treasury pays the building 5 gold of upkeep into its own purse, debts first, and an unpaid building is disabled and offers no work. The +10 mint and the -5 to nobody are gone.

## Scope
- `town_resolution.py` section 4: upkeep as a transfer, partial payment, debts first.

## Out of Scope
- Fiction values (rates, wages, prices): decided by the designer (memo row 58); no number is tuned here.
- The free-meal removal stack and the hunger pull.

## Acceptance Criteria
- [x] Total coin over a pinned run changes only by declared world-creation coin (tests/unit/resource/test_total_coin_is_conserved.py).
- [x] Every transfer named here has a payer and a payee, with a rejection case where the resolver can refuse.
- [x] Pinned 5-seed x 3-world measurement against main reported to rpg-planner.

## Related Tickets
- TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C, TCK-20261009-TAX-IS-A-SHARE-OF-SALES-AND-WAGES-PAID-TO-THE-PLACE-HOLDERS-TREASURY-DECISION-51, TCK-20261009-THE-FACTION-TREASURY-PAYS-WAGES-FOR-TOWN-WORK-DECISION-37, TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B (one batch, one PR)

## Related Docs
- `docs/mechanics/03_economic_laws.md` section 4.1, `docs/guidelines/intentional_divergences.md` 2.105-2.108, `docs/parity_ledger/town_resource.yaml` TOWN-205..208

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-THE-FACTION-TREASURY-PAYS-WAGES-FOR-TOWN-WORK-DECISION-37/`

## Related Code Areas
`src/engine/town_resolution.py`, `src/engine/work_shift.py`

## Assumptions / Open Questions
- Account unit is the four-value legacy bucket (debt: typed `treasuries` by catalog faction belongs with M2's ledger).

## Implementation Notes
Batch 3 of the material-economy chain, one PR on branch `batch3-treasury`.

## Test Summary
tests/unit/resource/test_tax_and_upkeep.py, tests/mechanic_scenarios/test_treasury_upkeep_pays_a_town_wage.py

## Files Changed
See the batch-3 PR.

## Completion Summary
Landed in the batch-3 PR; see its review notes for the pinned measurement and known gaps.

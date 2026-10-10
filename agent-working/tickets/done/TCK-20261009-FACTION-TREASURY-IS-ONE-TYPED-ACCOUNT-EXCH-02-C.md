---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C
phase: done
date: 2026-10-10
tags: [economy, resource]
---

# TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C

## Title
The faction treasury is one typed account; an inheritance moves goods once; a repair is charged once; coin is conserved over a run

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
The treasury was an untyped `global_resources` key written three ways, read one way and left orphaned for most catalog factions; an inheritance copied items and dropped gold; a repair charged twice; gold-sink fees, building tax, maintenance, kill gold and quest gold minted or destroyed coin. `src/core/treasury.py` gives the treasury one key scheme, a typed transfer and the total-coin invariant; the resolver gains a treasury channel, a source debit and an INHERIT transfer; coin is conserved over a pinned run.

## Scope
- `src/core/treasury.py`, one vault per region-owner bucket (sum of members' declared gold), the resolver's `treasury_update`/`SourceDebit`/INHERIT, the running per-tick treasury balance.
- `CorpseState.gold`, the dead record emptied at death, looting, escheat of a decayed body.
- Repair once / kit; gold-sink fees to the ground's owner; `RegionState.tax_share`.
- Total-coin conservation test over pinned runs; inheritance test.

## Out of Scope
- Fiction values (rates, wages, prices): decided by the designer (memo row 58); no number is tuned here.
- The free-meal removal stack and the hunger pull.

## Acceptance Criteria
- [x] Total coin over a pinned run changes only by declared world-creation coin (tests/unit/treasury/test_total_coin_is_conserved.py).
- [x] Every transfer named here has a payer and a payee, with a rejection case where the resolver can refuse.
- [x] Pinned 5-seed x 3-world measurement against main reported to rpg-planner.

## Related Tickets
- TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C, TCK-20261009-TAX-IS-A-SHARE-OF-SALES-AND-WAGES-PAID-TO-THE-PLACE-HOLDERS-TREASURY-DECISION-51, TCK-20261009-THE-FACTION-TREASURY-PAYS-WAGES-FOR-TOWN-WORK-DECISION-37, TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B (one batch, one PR)

## Related Docs
- `docs/mechanics/03_economic_laws.md` section 4.1, `docs/guidelines/intentional_divergences.md` 2.105-2.108, `docs/parity_ledger/town_resource.yaml` TOWN-205..208

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C/`

## Related Code Areas
`src/core/treasury.py`, `src/core/conservation.py`, `src/engine/economy.py`, `src/engine/pipeline.py`, `src/systems/lifecycle_systems/lifecycle.py`, `src/engine/apply_plan.py`, `src/engine/world_dynamics.py`, `src/worldbuilding/compiler.py`

## Assumptions / Open Questions
- Account unit is the four-value legacy bucket (debt: typed `treasuries` by catalog faction belongs with M2's ledger).

## Implementation Notes
Batch 3 of the material-economy chain, one PR on branch `batch3-treasury`.

## Test Summary
tests/unit/treasury/*, tests/unit/resource/test_conservation_rejection_paths.py, tests/mechanic_scenarios/test_treasury_upkeep_pays_a_town_wage.py

## Files Changed
See the batch-3 PR.

## Completion Summary
Landed in the batch-3 PR; see its review notes for the pinned measurement and known gaps.

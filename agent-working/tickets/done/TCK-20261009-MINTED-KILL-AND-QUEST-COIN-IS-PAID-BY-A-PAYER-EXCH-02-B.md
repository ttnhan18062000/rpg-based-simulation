---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B
phase: done
date: 2026-10-10
tags: [economy, resource]
---

# TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B

## Title
Kill and quest coin is paid by a payer: the body's own coin is looted, a quest reward is treasury-funded or owed

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Owner decisions 38 and 58: a kill grants experience only; the dead entity's coin moves to its body and a looter takes it; a quest reward's gold comes from a treasury, and a short treasury records a typed OwedRecord paid oldest first.

## Scope
- Remove kill gold in combat; `OwedRecord` (state, update, apply, checkpoint, presenter); reward payer; debt payment.

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
- `docs/mechanics/03_economic_laws.md` section 4.1, `docs/guidelines/intentional_divergences.md` 2.108-2.111, `docs/parity_ledger/town_resource.yaml` TOWN-206..208

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B/`

## Related Code Areas
`src/engine/combat.py`, `src/engine/quests.py`, `src/engine/pipeline_phases/quest_opportunity_rewards.py`, `src/core/state.py`, `src/core/conservation.py`

## Assumptions / Open Questions
- Account unit is the four-value legacy bucket (debt: typed `treasuries` by catalog faction belongs with M2's ledger).

## Implementation Notes
Batch 3 of the material-economy chain, one PR on branch `batch3-treasury`.

## Test Summary
tests/unit/resource/test_rewards_repair_and_fees.py, tests/unit/resource/test_corpse_gold.py

## Files Changed
See the batch-3 PR.

## Completion Summary
Landed in the batch-3 PR; see its review notes for the pinned measurement and known gaps.

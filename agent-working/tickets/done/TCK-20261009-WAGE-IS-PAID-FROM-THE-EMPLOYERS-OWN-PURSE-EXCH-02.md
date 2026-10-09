---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02
phase: done
date: 2026-10-09
tags: [economy, resource]
---

# TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02

## Title
WORK shift pays a wage from the employer's own purse

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
A WORK shift (200 ticks) pays 6 gold from the inn's own purse to the worker, one transaction per shift (a held action executes twice per tick, so the shift id is carried in the held payload). Divergence 2.102.

## Scope
- `work_shift.py`, WAGE transfer kind and its rejection cases, conservation tests.
- REPAIR leak closed (blacksmith in reach is the payee).

## Out of Scope
- Treasury-paid town wages (decision 37, batch 3).
- The double-execution engine quirk (Lane A).

## Acceptance Criteria
- [x] A shift pays exactly once per shift id even under double execution (tests/unit/world/test_work_shift_pays_a_wage_from_the_inns_purse.py).
- [x] Wage rejection cases covered; conservation holds.
- [x] Pinned paired measurement reported to rpg-planner (also the batch-2 closing measurement).

## Related Tickets
- TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02, TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02, TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02, TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3 (one batch, one PR)
- TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B (successor)

## Related Docs
- `docs/mechanics/03_economic_laws.md`, `docs/guidelines/intentional_divergences.md` (2.96-2.103), `docs/parity_ledger/town_resource.yaml` (TOWN-200..204)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/probes/` (chain_ms.py, agg.py, table4.txt)

## Related Code Areas
`src/engine/work_shift.py`, `src/core/conservation.py`, `src/engine/blacksmith.py`

## Assumptions / Open Questions
- Free meals stay on (decision 44). SELL and WORK are dormant while an inn exists.
- Region owners are legacy faction buckets (disclosed in the PR).

## Implementation Notes
Batch 2 is one commit on `batch2-on-main` (clean re-apply of the net diff on edda25490). Paired 5-seed x 3-world measurements (arm1 main, arm6 batch 2, arm7 batch 2 with profiles not applied) are in the batch-2 PR notes.

## Test Summary
tests/unit/world/test_work_shift_pays_a_wage_from_the_inns_purse.py, tests/unit/resource/test_conservation_rejection_paths.py

## Files Changed
See the batch-2 PR.

## Completion Summary
Landed in the batch-2 PR (one commit on edda25490 plus the force-full-scan and town-contract test rewrites). Pinned paired measurements (arm1 main, arm6 batch 2, arm7 batch 2 without profiles) and the starvation trace are in the PR notes and in the stored probes (arm7_trace_summary.md). Known gaps are listed in the PR.

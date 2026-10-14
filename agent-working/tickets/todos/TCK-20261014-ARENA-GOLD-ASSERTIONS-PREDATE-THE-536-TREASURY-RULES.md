---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261014-ARENA-GOLD-ASSERTIONS-PREDATE-THE-536-TREASURY-RULES
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-ARENA-GOLD-ASSERTIONS-PREDATE-THE-536-TREASURY-RULES

## Title
Three slow arena tests assert gold payouts from before #536's treasury rules (coin no longer minted). Re-state each one under the new rules, or find a real defect.

## Status
OPEN (slow-lane known red, rpg-owned, in slow_known_reds.yaml via #531)

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Found in the slow-regression dispatch 38378565537 on a branch containing main b396080cc (#536). The run before it, at ddf2297aa, was green.
- tests.arena.test_arena_quests::test_arena_quest_progression: `assert 0 >= 50`. The quest gold payout is 0.
- tests.arena.test_arena_regional_control::test_arena_regional_control: `assert 100 == 105`.
- tests.arena.test_arena_regional_control::test_arena_conquest_and_debuff: `assert 100 == 103`.
#536 changed these rules:
- a quest reward is paid by a treasury, or recorded as OWED if the treasury is short;
- kill coin is looted, not minted;
- the per-head levy is retired, and tax is a tenth of a sale or wage paid to the place holder's treasury;
- the +10 building mint is gone.

## Scope
For each test, find which #536 rule removed the expected gold, then decide:
- Under the new rules, the expected gold comes from a payer that the arena layout doesn't fund (e.g. an empty treasury). Re-stage the arena so a real payer exists (fund the treasury), and assert the conserved flow: payer -1, receiver +1, and OWED when short. Do NOT just change the number.
- The payout should happen and doesn't, even with a funded payer. That is a defect: fix it.

Also cite divergences 2.108-2.112.

## Out of Scope
Changing the treasury rules.

## Acceptance Criteria
- All three are green and assert conserved coin flows under the #536 rules.
- The slow_known_reds entry is retired.

## Related Tickets
TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B; TCK-20261009-TAX-IS-A-SHARE-OF-SALES-AND-WAGES-PAID-TO-THE-PLACE-HOLDERS-TREASURY-DECISION-51.

## Related Docs
docs/guidelines/intentional_divergences.md 2.108-2.112.

## Related Stored Artifacts
None.

## Related Code Areas
tests/arena/test_arena_quests.py; tests/arena/test_arena_regional_control.py.

## Assumptions / Open Questions
None.

## Implementation Notes
TBD

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD

---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-ENGINE-AND-BIBLE-DOC-DRIFT-AFTER-V1
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-ENGINE-AND-BIBLE-DOC-DRIFT-AFTER-V1

## Title
Doc drift found after v1: deterministic_execution.md still calls a closed ticket open, and Bible 04 names lead certainty two ways

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found by lead-planner-u24 while fact-checking (2026-10-23). Low priority; docs only.
- docs/engine/deterministic_execution.md:145 still calls TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE an "open ticket". It is in done/, and the cause was fixed by TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK (0 of 144 trials diverged after).
- The same file at :69 says "audit_mode is the current way to get a deterministic run". The 10-03 ticket called that false at the time; check whether it is true again after the 10-05 fix (v1's gate and paired runs, audit_mode plus PYTHONHASHSEED=0, reproduce byte-identically), and state the current rule, including PYTHONHASHSEED pending #593 F4.
- docs/mechanics/04_strategic_cognition.md section 3 (:114) describes lead certainty as High/Medium/Low, while section 5 (:405) uses APPROXIMATE/VAGUE/EXHAUSTED/PRECISE. Align it with the code's enum, and update the parity ledger if a Bible meaning changes.

## Scope
Fix the three passages against the code and the done tickets. Bible wording goes to rpg-designer for review.

## Out of Scope
Behaviour changes.

## Acceptance Criteria
- No doc calls a done ticket open; the :69 rule is accurate and cites its evidence; Bible 04 uses one certainty vocabulary matching the code.

## Related Tickets
TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE; TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK; TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID.

## Related Docs
docs/engine/deterministic_execution.md; docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts

## Related Code Areas
the lead-certainty enum (src/ai or src/cognition; locate at work time)

## Assumptions / Open Questions

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

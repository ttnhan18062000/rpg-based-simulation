---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260501-E5-REVIEW-HARDENING
phase: done
date: 2026-05-01
tags: [e5, review, hardening]
---

# TCK-20260501-E5-REVIEW-HARDENING

## Title
Implementation of E5 Review Findings for RPG Engine Closure

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the hardening requirements for combat rewards to achieve true logical closure of Phase E5. This involved transitioning XP and Gold rewards from legacy shadow fields in `CombatUpdate` to the authoritative `ResourceTransferIntent` flow.

## Scope
- [x] Refactor `RewardUpdate` schema in `src/core/updates.py`.
- [x] Update `src/core/conservation.py` to handle `RewardUpdate`.
- [x] Consolidate combat reward generation in `src/engine/combat.py`.
- [x] Update `AuthoritativeApplyPipeline` in `src/engine/pipeline.py` to process rewards.
- [x] Remove deprecated shadow fields from `CombatUpdate`.

## Out of Scope
- Adding new gameplay features beyond what's required for hardening.
- Modifying legacy code in `src_legacy/` or `tests_legacy/`.

## Acceptance Criteria
- [x] Combat rewards (XP/gold) are applied exactly once through clearly separated paths.
- [x] Resource resolver handles `RewardUpdate` correctly.
- [x] Authoritative pipeline merges rewards atomically.

## Related Tickets
- TCK-20260501-E5-HARDENING (preceding work)

## Related Docs
- resource_v2_e3_e4_e5_review.md
- logic_checklist_exhaustive_v2.md

## Related Stored Artifacts
- None

## Related Code Areas
- src/core/updates.py
- src/core/conservation.py
- src/engine/combat.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- None

## Implementation Notes
- Chose Option B from the review: XP for progression, Gold for resource transfers, both integrated into the intent flow.
- EvolutionSystem was updated to consume RewardUpdate.xp_gain atomically.

## Test Summary
- `tests/engine/test_combat_reward_hardening.py`: 2/2 passed.
- `tests/engine/`: Regression suite verified.

## Files Changed
- `src/core/updates.py`
- `src/core/conservation.py`
- `src/engine/combat.py`
- `src/engine/pipeline.py`
- `src/engine/domain_logic.py`
- `src/engine/evolution.py`
- `tests/engine/test_combat_reward_hardening.py`

## Completion Summary
Consolidated combat rewards into the authoritative intent-based flow. Removed all legacy shadow state updates. Verified atomic progression and resource conservation.

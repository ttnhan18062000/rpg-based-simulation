# TCK-20260427-QUEST-IDENTITY

## Title
Fixing Quest Identity Paradox and Hardening Authoritative Rewards

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The user requested a "continue" after a long conversation about a perceived "Quest Identity Paradox" where quest state appeared to revert or stay stuck in ACTIVE despite completion conditions being met.

## Scope
- Investigate the root cause of the Quest Identity Paradox.
- Verify quest progression logic in the V2 engine.
- Harden ApplyPath against identity-related bugs.
- Ensure rewards (XP/Gold) are correctly applied upon quest completion and kills.
- Fix any regressions in existing RPG tests.

## Out of Scope
- Major redesign of the Quest system.
- Full Phase 13 legacy retirement.

## Acceptance Criteria
- [x] Quest progression (ACTIVE -> COMPLETED -> REWARDED) verified in a single tick.
- [x] Kill rewards (XP/Gold) verified as correctly emitted and applied.
- [x] Legality checks (Friendly Fire) confirmed as the cause of "skipped" updates.
- [x] ApplyPath hardened against KeyErrors when entities lack specific quests.
- [x] 100% Green test suite in `tests/rpg/`.

## Related Tickets
- None

## Related Docs
- logic_checklist_exhaustive.md

## Related Stored Artifacts
- None

## Related Code Areas
- src/engine/apply.py
- src/engine/pipeline.py
- src/engine/domain_logic.py
- src/core/quests.py
- tests/rpg/test_rpg_core_recovery.py

## Assumptions / Open Questions
- Assumed `ResourceTransferIntent` was intended to be resolved in the pipeline for all sources, not just interactions.

## Implementation Notes
- Root Cause: A test setup error had a hero attacking a friendly-faction monster, causing `LegalityServiceV2` to block the attack. Since the attack was blocked, no kill occurred, and thus no quest update was generated. The hero retained their starting quest state, making it look like a "reversion" to those unaware of the block.
- Fix: Consolidated `ResourceTransferIntent` resolution into a global pipeline step in `AuthoritativeApplyPipeline.refine`.
- Cleanup: Removed extensive identity-tracking debug prints from `ApplyPath`.

## Test Summary
- `tests/rpg/test_rpg_core_recovery.py`: Added `test_quest_lifecycle` to verify full loop.
- `tests/rpg/`: All 17 tests passed.

## Files Changed
- src/engine/apply.py
- src/engine/pipeline.py
- src/engine/tactical.py
- tests/rpg/test_rpg_core_recovery.py
- tests/rpg/test_resource_conservation.py

## Completion Summary
Resolved the Quest Identity Paradox by identifying a faction-based legality block in the test harness. Hardened the V2 engine's reward application path by implementing global transaction resolution for `ResourceTransferIntent` in the refinement pipeline. Verified 100% parity and conservation laws across the RPG core logic suite.

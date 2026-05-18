# TCK-20260428-QUEST-PROGRESSION-FIX

## Title
Fix Quest Progression XP Double-Counting Regression

## Status
DONE

## Request Summary
Resolve the `AssertionError` in `tests/arena/test_arena_quests.py` where heroes received 220 XP instead of 110 XP (10 kill + 100 quest), leading to an incorrect remainder after leveling up.

## Scope
- Investigate and fix XP double-counting in `AuthoritativeApplyPipeline`.
- Sanitize worker proposals to prevent redundant reward application.
- Verify fix with `tests/arena/test_arena_quests.py`.

## Acceptance Criteria
- [x] `tests/arena/test_arena_quests.py` passes.
- [x] XP rewards are applied exactly once per authoritative re-execution.
- [x] Worker proposals are sanitized in the pipeline.

## Implementation Notes
- Discovered a redundant addition of `evolution_points_delta` in `AuthoritativeApplyPipeline._resolve_resource_transactions` (Step 9). It was being added both in a "quick path" (Line 518) and a "proper block" (Line 548). Removed the redundant Line 518.
- Added a sanitization step (Step 0) in `AuthoritativeApplyPipeline.refine` to strip calculated results from worker proposals while preserving intents.

## Test Summary
- `pytest tests/arena/test_arena_quests.py`: PASSED

## Files Changed
- `src/engine/pipeline.py`: Fixed redundant XP addition and added proposal sanitization.
- `src/engine/evolution.py`: Cleaned up diagnostic logging.

## Completion Summary
Resolved the XP double-counting bug by removing redundant logic in the resource resolution step and hardening the pipeline against noisy worker proposals.

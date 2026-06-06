# TCK-20260510-QUEST-PROGRESS-STABILIZATION

## Title

Resolving Quest Progress Double-Counting and Merging Regressions

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Identify and resolve a double-counting regression in quest progression logic. Ensure atomic, deterministic quest updates and reward delivery within the V2 authoritative pipeline.

## Scope

- Hardening `QuestUpdate.merge` to prevent duplicate IDs and correctly merge `multi_updates`.
- Hardening `_strip_untrusted_world_effects` to strip `progress_delta` from worker proposals.
- Transitioning to `QuestResolutionSystem.enforce` for robust multi-quest handling.
- Fixing `SimulationDomainLogic` to correctly handle multiple quest updates and AOE kills.

## Out of Scope

- Implementing new quest types.
- Modifying the social contract system.

## Acceptance Criteria

- `QuestUpdate.merge` deduplicates by `quest_id` and correctly flattens `multi_updates`.
- Worker-provided `progress_delta` is ignored by the authoritative pipeline.
- Multiple quests can be advanced and rewarded in a single tick without data loss.
- AOE kills correctly trigger hunt quest progression.

## Related Tickets

- None

## Related Docs

- [architecture.md](file:///home/vboxuser/Work/rpg-based-simulation/architecture.md)
- [done.md](file:///home/vboxuser/Work/rpg-based-simulation/done.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/updates.py`
- `src/engine/pipeline.py`
- `src/engine/quests.py`
- `src/engine/domain_logic.py`
- `src/engine/apply.py`

## Assumptions / Open Questions

- We assume `QuestResolutionSystem.enforce` is the intended authoritative source for reward intents.

## Implementation Notes

- Used a dictionary-based merge in `QuestUpdate.merge` to ensure ID uniqueness.
- Updated `AuthoritativeApplyPipeline` to restore missing phases (Actor Validity, Shop, Town Resolution).
- Hardened trust boundaries to prevent worker-side state injection (Law 300.2).

## Test Summary

- `tests/engine/test_hardening_e5.py` (Actor validity verification)
- `tests/engine/test_interaction_recovery.py` (Shop/Town resolution verification)
- `tests/engine/test_certification_scenarios.py` (Rejection registry compliance)
- `tests/arena/test_arena_quests.py` (End-to-end quest flow)

## Files Changed

- `src/core/updates.py`
- `src/engine/pipeline.py`
- `src/engine/domain_logic.py`

## Completion Summary

- Resolved quest merging double-counting by implementing ID-aware merging.
- Restored authoritative pipeline phases that were missing or bypassed.
- Hardened the trust boundary between workers and the simulation kernel.
- Achieved 100% pass rate on relevant regression and certification suites.

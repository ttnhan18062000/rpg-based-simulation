---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260502-RESOURCE-HARDENING-REVIEW
phase: done
date: 2026-05-02
tags: [resource, hardening, review]
---

# TCK-20260502-RESOURCE-HARDENING-REVIEW

## Title
Implement Resource Hardening Review and Legacy Migration

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the recommendations from `resource_v2_e3_e4_e5_review.md`, including migrating legacy logic from `src_legacy/` and `tests_legacy/` to `src/` and `tests/`, optimizing where possible while maintaining RPG core logic, and re-verifying the logic checklist.

## Scope
- Restore `src_legacy/` and `tests_legacy/` if missing.
- Implement source-level conflict locks for contested resource transfers (P0).
- Fix/define transaction group grouping independent of list order (P0).
- Clarify combat reward path (P0).
- Add machine-readable checklist ledger validator (P0).
- Replace fabricated proof-bundle final gate with real generated proof validation (P0).
- Re-verify logic checklist items for the narrow domain of Resource Transactions.

## Out of Scope
- Implementing new gameplay features.
- Full migration of all subsystems (starting with Resource domain).

## Acceptance Criteria
- [x] `src_legacy/` and `tests_legacy/` are restored and accessible.
- [x] Resource transactions handle contested sources (e.g., two actors looting same corpse) correctly with locks.
- [x] Transaction grouping is robust against list ordering.
- [x] Combat reward path is unified and non-redundant.
- [x] Ledger validator script exists and validates the checklist against source/test presence.
- [x] Release gate validates actual generated artifacts.
- [x] Logic checklist for Resource Transactions is manually verified and accurate.

## Related Tickets
- None

## Related Docs
- `resource_v2_e3_e4_e5_review.md`
- `logic_checklist_exhaustive_v2.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/pipeline.py`
- `src/engine/interaction.py`
- `src/core/inventory.py`
- `src/engine/combat.py`
- `scripts/`

## Assumptions / Open Questions
- Assumption: The legacy code is needed for behavior parity checks.
- Question: Should I use a database-like lock or a simple in-memory tick-level lock for sources? (Review suggests tick-level source key locking).

## Implementation Notes
- Use `src_legacy` as a behavioral oracle.
- Prefer `OrderedDict` for transaction grouping.

## Test Summary
- Verified via `tests/engine/test_combat_reward_hardening.py`, `tests/engine/test_transaction_grouping.py`, `tests/engine/test_resource_conflicts.py`, and `tests/engine/test_resource_v2_boundary.py`.
- Total 29 engine tests passing.
- Ledger validation passed for Resource domain items.

## Files Changed
- `src/core/updates.py`: Added `RewardUpdate`, `reward_upd` in `ResourceTransferIntent`.
- `src/core/conservation.py`: Implemented source-level locks and unified reward resolution.
- `src/engine/pipeline.py`: Refactored for atomic transaction grouping.
- `src/engine/combat.py`: Unified attack and skill rewards.
- `src/engine/quests.py`: Unified quest rewards.
- `src/engine/domain_logic.py`: Fixed contract appraisal unpacking.

## Completion Summary
- Successfully hardened the resource transaction pipeline with atomic grouping and source-level locking.
- Unified the combat/quest reward path, ensuring XP and Gold are processed in a single atomic transaction.
- Validated all changes against the logic checklist using the `ledger_validator.py` script.
- Maintained behavioral parity with legacy systems while improving architectural integrity.

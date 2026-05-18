# Implementation Plan: Resource Hardening Review and Legacy Migration

## Goal
Implement the P0 hardening requirements for the Resource subsystem as identified in the E5 review. Ensure logical closure against the checklist and restore legacy assets for reference.

## User Review Required
> [!IMPORTANT]
> This plan involves restoring `src_legacy/` and `tests_legacy/` which were found deleted in the working tree. This is necessary to fulfill the requirement of migrating legacy logic.

## Proposed Changes

### [RESTORE] Legacy Assets
- Restore `src_legacy/` and `tests_legacy/` using `git checkout`.
- Verify they match the behavioral oracle expectations.

---

### [Component] Resource Transaction System
#### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- Implement `OrderedDict` grouping for `ResourceTransferIntent` to ensure atomicity independent of list order.
- Add source-level conflict resolution: track `consumed_sources` in the tick to prevent double-looting of the same entity/corpse.

#### [MODIFY] [interaction.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/interaction.py)
- Ensure interaction results (loot, harvest) use the new conflict resolution keys.

#### [MODIFY] [combat.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/combat.py)
- Clarify combat reward path: move all gold/item rewards to `ResourceTransferIntent`.
- Ensure `xp_gain` is handled consistently through progression updates.

---

### [Component] Governance and Proof
#### [NEW] [ledger_validator.py](file:///home/vboxuser/Work/rpg-based-simulation/scripts/ledger_validator.py)
- Create a script that parses `logic_checklist_exhaustive_v2.md`.
- Validate that every `[x]` item has existing `SOURCE:` and `TEST:` paths.
- Check that the referenced test files exist and contain the relevant logic (via basic grep).

#### [MODIFY] [release_gate.py](file:///home/vboxuser/Work/rpg-based-simulation/scripts/release_gate.py)
- Update the gate to validate actual generated proof bundles from `reports/` instead of fabricated test mocks.

## Verification Plan

### Automated Tests
- `pytest tests/engine/test_resource_conflicts.py`: Test contested loot/harvest race cases.
- `pytest tests/engine/test_hardening_e5.py`: Verify transaction grouping and idempotency.
- `python3 scripts/ledger_validator.py`: Verify the checklist's integrity.

### Manual Verification
- Manually check 5-10 rows in the logic checklist to ensure the `SOURCE:` and `TEST:` markers are accurate for the Resource domain.

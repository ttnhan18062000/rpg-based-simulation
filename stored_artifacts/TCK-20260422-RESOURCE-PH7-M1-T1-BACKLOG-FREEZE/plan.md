# Implementation Plan: Phase 7 Backlog Freeze

## Goal

Freeze the Phase 7 replacement-ledger row set to establish the authoritative substrate backlog. This aligns the ledger with the "Substrate Closure" objective defined in the Phase 7 high-level plan.

## Proposed Changes

### Triage & Allocation

- [ ] Move semantic recovery items (141, 146, 150, 151) from Phase 7 to Phase 8/9 in `legacy_replacement_ledger.md`.
- [ ] Retain substrate-focused items (071, 139, 143) in Phase 7.
- [ ] Add explicit "Hardening" markers to existing substrate rows (001, 004, 006, 066, 068, 070, 073, 159) to signal that Phase 7 will provide the final deterministic closure for these.

### Documentation

- [ ] [NEW] `docs/engine/phase7_backlog.md`: The official backlog of Phase 7 rows.
- [ ] [MODIFY] `docs/engine/phase_allocation_map.md`: Update counts for Phase 7, 8, and 9.
- [ ] [MODIFY] `docs/engine/legacy_replacement_ledger.md`: Update "Target Phase" for the triaged rows.

## Verification Plan

### Automated Tests
- None (Documentation only task).

### Manual Verification
- [ ] Verify that the sum of rows across all phases remains 185.
- [ ] Verify that `phase7_backlog.md` contains only substrate-related logic.
- [ ] Verify that `phase_allocation_map.md` counts are consistent with the ledger.

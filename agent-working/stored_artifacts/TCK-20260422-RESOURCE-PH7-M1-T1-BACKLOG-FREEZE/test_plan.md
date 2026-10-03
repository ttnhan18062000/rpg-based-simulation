---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260422-RESOURCE-PH7-M1-T1-BACKLOG-FREEZE
artifact_type: test_plan
tags: [resource, ph7, m1, t1, backlog, freeze]
---

# Test Plan: Phase 7 Backlog Freeze

## Objective

Ensure the Phase 7 backlog is accurate, complete, and consistent with the repository's authoritative ledger.

## Verification Steps

### 1. Ledger Integrity Check
- Run `grep "| Phase 7 |" docs/engine/legacy_replacement_ledger.md` to verify the triaged row set.
- Run `grep "| Phase 8 |" docs/engine/legacy_replacement_ledger.md` to verify the moved semantic rows.
- Run `grep "| Phase 9 |" docs/engine/legacy_replacement_ledger.md` to verify the moved social rows.

### 2. Allocation Consistency Check
- Ensure the counts in `docs/engine/phase_allocation_map.md` match the results of the grep commands.
- Total item count across all phases must equal 185.

### 3. Backlog Coverage
- Verify that `docs/engine/phase7_backlog.md` includes all rows identified in the investigation as "Substrate Closure" or "Substrate Hardening".

## Success Criteria

- All substrate-related gaps are owned by Phase 7.
- All semantic recovery gaps are deferred to Phase 8 or 9.
- Documentation is bit-accurate with the ledger state.

# Implementation Plan: Audit Phase 7 Action/Update Rows

## Goal

Produce a concrete gap audit for the Phase 7 Action/Update substrate to guide the implementation of Milestone 2.

## Proposed Changes

### Research & Audit

- [ ] [AUDIT] `src/core/updates.py`:
    - Check for missing "Verb", "Reason", and "Target" fields.
    - Identify "Flat" fields that should be disaggregated into domains.
- [ ] [AUDIT] `src/engine/kernel.py`:
    - Identify "Intent Routing" logic in `_phase_resolution` that should be moved to workers.
- [ ] [AUDIT] `src/core/worker_protocol.py`:
    - Evaluate how `ActionProposal` fits into the `WorkerResult` structure.

### Documentation

- [ ] [NEW] `docs/engine/phase7_m2_gap_audit.md`:
    - Summarize the audit findings.
    - List specific rows from the master ledger that are blocked by these gaps.
    - Provide a checklist for implementation tasks 2-5.

## Verification Plan

### Manual Verification
- [ ] Cross-reference the audit findings with the `resource_phase7_milestone2.md` acceptance criteria.
- [ ] Ensure all identified gaps map back to specific ledger rows (LEG-RPG-001, 004, 006).

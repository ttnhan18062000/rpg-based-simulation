---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION
phase: open
date: 2026-08-17
tags: [documentation, engine]
---

# TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION

## Title
Fix Collection-phase concurrency contradiction in simulation_kernel_contract.md §9

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
docs/engine/kernel.md states Collection is concurrent, while docs/engine/contracts/simulation_kernel_contract.md §9 states "No concurrency or parallel execution." Both are status: active, authority: P1. The actual code (src/engine/worker_manager.py, ThreadPoolExecutor/ProcessPoolExecutor) matches kernel.md's description, not the contract's, and a third P1 doc (bounded_concurrency_contract.md) further confirms concurrency is real and intentional. simulation_kernel_contract.md §9 is the stale outlier and needs correcting to match the other two docs and the code.

## Scope
- Correct simulation_kernel_contract.md §9's "No concurrency or parallel execution" line to a narrower, accurate statement consistent with kernel.md and bounded_concurrency_contract.md (Collection/Deliberation phase concurrency via bounded worker pool is real and intentional)
- Ensure the resulting text still permits src/engine/worker_manager.py's existing ThreadPoolExecutor/ProcessPoolExecutor behavior without calling it a violation
- Update or add the relevant parity ledger entry (docs/parity_ledger/substrate.yaml or infrastructure.yaml) if applicable

## Out of Scope
- The 6-phase vs 7-phase contradiction (separate ticket: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION)
- Landing the kernel concurrency design doc or the broader docs/engine audit (separate tickets)
- Rewriting simulation_kernel_contract.md §9's other bullets ("No scheduler optimization", "No adaptive degradation", "No external event brokers") flagged as possibly-also-stale — deferred to the broader audit ticket (TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT)

## Acceptance Criteria
- [ ] simulation_kernel_contract.md §9 no longer contains "No concurrency or parallel execution" or an equivalent blanket denial
- [ ] kernel.md + simulation_kernel_contract.md + bounded_concurrency_contract.md state a mutually consistent claim: Collection/Deliberation is the sole concurrent phase via bounded worker pool
- [ ] Corrected text still permits existing src/engine/worker_manager.py behavior without calling it a violation
- [ ] Parity ledger entry (docs/parity_ledger/substrate.yaml or infrastructure.yaml) updated or added if relevant

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC

## Related Docs
- docs/engine/kernel.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/bounded_concurrency_contract.md
- docs/engine/project_lawbook_m10.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/engine/kernel.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/bounded_concurrency_contract.md
- docs/engine/project_lawbook_m10.md
- src/engine/worker_manager.py
- tests/integration/kernel/test_simulation_kernel_contract.py

## Assumptions / Open Questions
- Don't just delete the §9 line — replace with a narrower accurate statement so a real constraint isn't silently lost
- Overlaps TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION on the same two files (kernel.md, simulation_kernel_contract.md) — coordinate to avoid merge conflicts if worked concurrently; no hard ordering required between the two
- No existing test asserts on §9's literal text — this is a docs-only fix
- docs/engine/manifest.json references this file; not fully verified whether any tooling depends on exact current wording
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC depends on this ticket landing first (see SEQUENCE.md in this folder)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

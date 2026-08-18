---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION
phase: open
date: 2026-08-17
tags: [documentation, engine]
---

# TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION

## Title
Fix 6-phase vs 7-phase contradiction across architecture.md, README.md, kernel.md

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
docs/engine/architecture.md §2 describes a 6-phase loop (INIT, GOVERNANCE, SCHEDULING, PACKETIZATION, RESOLUTION, PERSISTENCE); docs/engine/kernel.md and simulation_kernel_contract.md §4 both describe a 7-phase loop (INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE) with no GOVERNANCE/PACKETIZATION. Three P1 docs disagree, and the code (src/engine/kernel.py::tick_once) proves kernel.md/simulation_kernel_contract.md correct — architecture.md and README.md carry the fabricated GOVERNANCE/PACKETIZATION phase names and need reconciliation against the real 7 _phase_* methods.

## Scope
- Correct docs/engine/architecture.md §2's phase list to match the 7 real _phase_* methods in src/engine/kernel.py::tick_once (INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE), removing the fabricated GOVERNANCE/PACKETIZATION phase names
- Correct docs/engine/README.md's 'Core Loop' bullet, which carries the identical fabricated 'Init, Governance, Scheduling, Packetization, Resolution, Persistence' text, to match the 7-phase list
- Add an explicit clarifying note reconciling docs/engine/contracts/substrate_baseline_contract.md §4's '6 authoritative phases + PERSISTENCE as non-authoritative Observational Boundary hook' framing as equivalent to (not contradicting) the 7-phase numbering elsewhere
- Do a repo-wide grep for GOVERNANCE/PACKETIZATION as phase names across docs/engine/ before closing, to confirm no third occurrence remains

## Out of Scope
- The Collection-phase concurrency contradiction (separate ticket: TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION), which touches the same two files (kernel.md, simulation_kernel_contract.md) — coordinate but no hard ordering required
- docs/systems/ai_system.md's already-archived occurrence of the same fabricated term (handled by TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT)
- Rewriting tests/integration/kernel/test_milestone_a_closure.py's '6-phase' docstring/assertions — only decide whether a clarifying note is needed, don't alter test assertions

## Acceptance Criteria
- [ ] architecture.md §2 no longer contains GOVERNANCE or PACKETIZATION as phase names; its phase list matches the 7 real _phase_* methods in kernel.py::tick_once, same order
- [ ] README.md's Core Loop bullet no longer says 'Init, Governance, Scheduling, Packetization, Resolution, Persistence'; matches the 7-phase list
- [ ] kernel.md + simulation_kernel_contract.md + corrected architecture.md/README.md all state the same 7 phases; grep for 'PACKETIZATION'/'GOVERNANCE' as phase names returns zero matches across docs/engine/
- [ ] substrate_baseline_contract.md §4 explicitly notes its 6-phase+hook framing is equivalent to (not contradicting) the 7-phase numbering elsewhere, so it is not re-flagged as a 4th conflicting count

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260619-P0-DOC-REPAIR
- TCK-20260623-FIX-KERNEL-PHASES
- TCK-20260618-AUDIT-D17-DOCS
- TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT

## Related Docs
- docs/engine/architecture.md
- docs/engine/kernel.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/substrate_baseline_contract.md
- docs/engine/README.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/engine/architecture.md
- docs/engine/kernel.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/substrate_baseline_contract.md
- docs/engine/README.md
- src/engine/kernel.py
- tests/integration/kernel/test_milestone_a_closure.py

## Assumptions / Open Questions
- README.md wasn't named in the original proposal excerpts but has the identical defect; included in scope so the contradiction doesn't just recreate itself from a different doc
- substrate_baseline_contract.md's '6 authoritative + 1 non-authoritative hook' framing is internally consistent with test_milestone_a_closure.py's own '6-phase' docstring — leaning toward documenting the convention as canonical rather than editing the test, to avoid unscoped test changes
- This is a repeat of the same contradiction class TCK-20260619-P0-DOC-REPAIR already fixed once in kernel.md; the structural fix (living test / canonical-doc convention) is scoped to TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT, not duplicated here
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC depends on this ticket landing first (see SEQUENCE.md in this folder)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

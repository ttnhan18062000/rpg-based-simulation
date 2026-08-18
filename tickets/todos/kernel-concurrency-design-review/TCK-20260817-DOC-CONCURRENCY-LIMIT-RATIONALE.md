---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE
phase: open
date: 2026-08-17
tags: [documentation, engine]
---

# TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE

## Title
Document why GovernorPolicy.from_mode()'s concurrency_limit decreases as RuntimeMode escalates

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
GovernorPolicy.from_mode() sets concurrency_limit to 1.0/1.0/0.5/0.25 across NORMAL/CONSTRAINED/DEGRADED/SURVIVAL — not self-evidently correct, since naively more pressure should mean more workers to clear backlog. The real reasoning (LOD/cadence/phase budgets already shrink the batch by the time concurrency throttles, so fewer workers on a smaller batch reduces contention) isn't written down anywhere. The author wants this recorded next to GovernorPolicy.from_mode() or in governance_logic.md.

## Scope
- Add a docstring/comment adjacent to GovernorPolicy.from_mode() in src/engine/policy.py (lines 58-148, values set at 70, 91, 112, 133) explaining that LOD/cadence/phase-budget shedding already shrinks the batch by the time concurrency throttles, so fewer workers reduces contention rather than adding scheduling noise
- Add an explicit subsection with the same rationale to docs/engine/governance_logic.md §3 Degradation Laws (or docs/engine/contracts/bounded_concurrency_contract.md §5, whichever is deemed canonical), cross-referenced from the other
- No production behavior change — concurrency_limit values (1.0/1.0/0.5/0.25) remain unchanged

## Out of Scope
- Adding the rationale to docs/engine/contracts/resource_governor_contract.md — it explicitly disclaims worker-pool/concurrency scaling as a Non-Goal, would self-contradict
- Any change to tests/unit/kernel/test_worker_adaptation.py assertions (peak_workers values) — doc-only fix

## Acceptance Criteria
- [ ] A docstring/comment adjacent to GovernorPolicy.from_mode() in src/engine/policy.py explains why concurrency_limit decreases, referencing the LOD/cadence/phase-budget shedding rationale
- [ ] governance_logic.md (or bounded_concurrency_contract.md, whichever is canonical) gets an explicit subsection on this rationale, cross-referenced from the other if split
- [ ] No production behavior change: concurrency_limit values (1.0/1.0/0.5/0.25) remain unchanged; tests/unit/kernel/test_worker_adaptation.py continues to pass unmodified
- [ ] Rationale discoverable both inline (grep/read landing on from_mode()) and via docs/REGISTRY.yaml-indexed doc

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260419-MB-TASK4-ADAPTIVE-POOL
- TCK-20260420-CPU-GOV
- TCK-20260419-MD-TASK1-FREEZE-CONCURRENCY-CONTRACT

## Related Docs
- docs/engine/governance_logic.md
- docs/engine/contracts/resource_governor_contract.md
- docs/engine/contracts/bounded_concurrency_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/policy.py
- src/core/governance.py
- src/engine/worker_manager.py
- docs/engine/governance_logic.md
- docs/engine/contracts/resource_governor_contract.md
- docs/engine/contracts/bounded_concurrency_contract.md
- tests/unit/kernel/test_worker_adaptation.py

## Assumptions / Open Questions
- Two plausible doc locations named (inline docstring vs governance_logic.md) — doing both per the acceptance criteria, rather than picking one and leaving a gap
- Pure doc/comment change with no behavior delta, but a diff-only review is warranted to ensure concurrency_limit values aren't silently altered while adding the comment

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

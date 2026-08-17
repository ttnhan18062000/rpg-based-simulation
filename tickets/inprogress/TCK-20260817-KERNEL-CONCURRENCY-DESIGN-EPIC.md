---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
phase: open
date: 2026-08-17
tags: [engine, documentation, determinism, performance]
---

# TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC

## Title
Kernel concurrency design review: land the design doc, fix documentation drift, close the benchmarking-integrity gap

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P1

## Request Summary
A system-design discussion session (2026-08-17, no code/test changes made in that session)
investigated the kernel's concurrency model in depth: why the tick loop is a synchronous
fork-join orchestrator over a bounded worker pool rather than asyncio/anyio, how race conditions
are structurally prevented, how the engine degrades gracefully under resource pressure, and what
governs performance claims. The discussion produced a complete design write-up that does not yet
exist in the repo, and surfaced several concrete, independently-verifiable gaps between what the
engine's docs claim and what the code/CI actually does — most importantly, three live
contradictions between individually-authoritative (`status: active, authority: P1`) docs
describing the same kernel, and a benchmarking-integrity gap where the CI performance gate has no
awareness of `RuntimeMode`, meaning a benchmark could silently blend cheaper degraded-mode ticks
into a reported baseline and mask a real regression. This epic scopes and tracks the child
tickets needed to investigate and resolve each finding. It does not implement any fix directly.

## Scope
- Scope-only epic: track and sequence the child tickets in `tickets/todos/kernel-concurrency-design-review/`; no direct implementation in the parent.
- Full source proposal with all findings, evidence, and file/line references: `docs/plans/kernel_concurrency_design_review_proposal.md`.
- Covers: landing the drafted kernel concurrency/design-philosophy doc into `docs/`; resolving three live documentation contradictions (concurrency framing, phase count, and a broader stale/duplicate doc audit); closing the benchmarking-integrity gap in `performance_contract.md` and `tests/perf/test_perf_regression_baseline.py`; stating the engine's implicit design-priority order explicitly; documenting the `concurrency_limit` degradation rationale; and confirming where (if anywhere) the Collection-phase worker path consumes RNG.

## Out of Scope
- Any code or behavior change to the kernel, worker pool, scheduler, or governor itself — this epic is about documentation accuracy and CI-gate integrity, not runtime behavior changes.
- Broader engine performance work beyond the specific benchmarking-integrity gap identified.
- Re-litigating the design decisions themselves (fork-join over asyncio, immutability model, etc.) — those were validated during the discussion, not questioned.

## Acceptance Criteria
- [ ] All child tickets from `docs/plans/kernel_concurrency_design_review_proposal.md` are created, reviewed, and linked below.
- [ ] Each of the three documentation contradictions (C2, C3, and the hardware-class conflict surfaced under C8) has an owning child ticket.
- [ ] The benchmarking-integrity gap (C4) has an owning child ticket with a concrete proposed fix location (`performance_contract.md` §3.1 and `tests/perf/test_perf_regression_baseline.py`).
- [ ] The epic is not closed merely because child tickets exist — each child must reach `tickets/done/` with its own evidence before this epic closes.

## Related Tickets
- TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT
- TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION
- TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE
- TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION
- TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC
- TCK-20260817-RUNTIMEMODE-BENCH-SCOPING
- TCK-20260817-STATE-DESIGN-PRIORITY-ORDER

## Related Docs
- docs/plans/kernel_concurrency_design_review_proposal.md
- docs/engine/kernel.md
- docs/engine/architecture.md
- docs/engine/project_lawbook_m10.md
- docs/engine/performance_contract.md
- docs/performance/perf_baseline_policy.md
- docs/engine/contracts/simulation_kernel_contract.md
- docs/engine/contracts/certification_contract.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/engine/kernel.py
- src/engine/executor.py
- src/engine/worker_manager.py
- src/engine/worker_logic.py
- src/engine/scheduler.py
- src/engine/governor.py
- src/engine/phase_governor.py
- src/engine/policy.py
- tests/perf/test_perf_regression_baseline.py

## Assumptions / Open Questions
- The drafted design doc content (Appendix A of the proposal) is believed accurate but was produced by reading code and docs during discussion, not through the full investigator/architecture-reviewer pipeline — the child ticket for C1 should treat it as a strong starting draft, not settled fact, particularly the C7 open question about RNG consumption in Collection.
- Which of `kernel.md` vs. `simulation_kernel_contract.md` (C2) and `architecture.md` vs. `kernel.md`/`simulation_kernel_contract.md` (C3) is the "correct" description needs a maintainer decision if investigation doesn't make it obvious from the code alone.
- Whether the reconstructed design-priority order (C5) matches actual maintainer intent needs confirmation, not just documentation.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each child ticket carries its own)

## Files Changed
(pending)

## Completion Summary
(pending)

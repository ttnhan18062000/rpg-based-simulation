---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-RESOURCE-SAFETY-EPIC
phase: done
date: 2026-06-14
tags: [resource-safety, memory, backpressure, observability, replay, architecture, epic]
---

# TCK-20260614-RESOURCE-SAFETY-EPIC

## Title
Resource Safety as a First-Class Feature — systemic governance for artifacts, workers, backpressure, and hot paths

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The certification memory investigation (`memory_issue.md`) revealed a broader pattern: the engine
has the right ideas (bounded queues, replay modes, optimization profiles, certification reports)
but resource safety was scattered rather than governed. This epic addressed the systemic layer:
explicit artifact budgets, per-subsystem resource gates, a runtime dashboard, canonical hashing
discipline, backpressure controllers for replay and observability, a worker lifecycle supervisor,
and a content hot-path guard.

## Scope
Epic tracking 8 child tickets — all implemented.

## Out of Scope
- Certification proof serialization fix (cert-memory-fix batch)
- Memray profiling mode (cert-memory-fix batch)

## Acceptance Criteria
- [x] All 8 child tickets completed and in `tickets/done/`

## Related Tickets
### Child tickets (all DONE):
- TCK-20260614-ARTIFACT-BUDGET-REG — ArtifactBudgetRegistry; 13 tests; INFRA-193
- TCK-20260614-RESOURCE-BUDGET-GATE — SubsystemBudget/PressureReport; BudgetedCanonicalHasher; 19 tests; INFRA-194/195/196
- TCK-20260614-CONTENT-HOTPATH-GUARD — ContentWarmupService + tick context guard; 10 tests
- TCK-20260614-HASH-SCHEDULER — CanonicalHashScheduler; HashMode; 19 tests; INFRA-197
- TCK-20260614-REPLAY-BACKPRESSURE — inflight tracking; replay_metrics(); 13 tests; INFRA-198
- TCK-20260614-OBS-BACKPRESSURE — ObservabilityMode controller; 28 tests; INFRA-199
- TCK-20260614-LIFECYCLE-SUPERVISOR — ShutdownReport; BehaviorWorker join; 14 tests; INFRA-200
- TCK-20260614-RESOURCE-DASHBOARD — diagnostics CLI; resource_snapshot(); 18 tests; INFRA-201

### Prerequisite batch (complete):
- TCK-20260614-CERT-SAFE-SERIAL, TCK-20260614-CERT-RECORDER-REFACTOR, TCK-20260614-CERT-EVIDENCE-LEVELS

## Related Docs
- `memory_features.md`, `memory_issue.md`
- `docs/parity_ledger/infrastructure.yaml` — INFRA-193 through INFRA-201

## Completion Summary
All 8 resource-safety child tickets implemented, tested, and committed on the
`resource-optimization` branch. 8 new test files (135 tests total). Parity ledger
updated with INFRA-193 through INFRA-201. Knowledge index and code graph updated.

---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-RESOURCE-SAFETY-EPIC
phase: open
date: 2026-06-14
tags: [resource-safety, memory, backpressure, observability, replay, architecture, epic]
---

# TCK-20260614-RESOURCE-SAFETY-EPIC

## Title
Resource Safety as a First-Class Feature — systemic governance for artifacts, workers, backpressure, and hot paths

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The certification memory investigation (`memory_issue.md`) revealed a broader pattern: the engine has the right ideas (bounded queues, replay modes, optimization profiles, certification reports) but resource safety is scattered rather than governed. The immediate certification fix (see `cert-memory-fix/` batch) addresses the acute proof-serialization issue. This epic addresses the systemic layer: explicit artifact budgets, per-subsystem resource gates, a runtime dashboard, canonical hashing discipline, backpressure controllers for replay and observability, a worker lifecycle supervisor, and a content hot-path guard.

The doc (`memory_features.md`) recommends building the top five first: EvidenceLevel (done in cert-memory-fix), Artifact Budget Registry, Runtime Resource Dashboard, Replay/Observability Backpressure, and Profiling Mode. This epic tracks all nine remaining features.

## Scope
This epic tracks child tickets only. No direct implementation.

## Out of Scope
- Certification proof serialization fix (covered by TCK-20260614-CERT-SAFE-SERIAL, TCK-20260614-CERT-RECORDER-REFACTOR, TCK-20260614-CERT-EVIDENCE-LEVELS in cert-memory-fix batch)
- Memray profiling mode (TCK-20260614-CERT-MEMRAY-BUDGET, also in cert-memory-fix batch — expanded to cover Feature 10)

## Acceptance Criteria
All child tickets completed and in `tickets/done/`.

## Related Tickets
### Child tickets (implement in SEQUENCE.md order):
- TCK-20260614-ARTIFACT-BUDGET-REG
- TCK-20260614-RESOURCE-BUDGET-GATE
- TCK-20260614-RESOURCE-DASHBOARD
- TCK-20260614-HASH-SCHEDULER
- TCK-20260614-REPLAY-BACKPRESSURE
- TCK-20260614-OBS-BACKPRESSURE
- TCK-20260614-LIFECYCLE-SUPERVISOR
- TCK-20260614-CONTENT-HOTPATH-GUARD

### Prerequisite batch (must be done first):
- TCK-20260614-CERT-SAFE-SERIAL
- TCK-20260614-CERT-RECORDER-REFACTOR
- TCK-20260614-CERT-EVIDENCE-LEVELS

## Related Docs
- `memory_features.md` (source proposal)
- `memory_issue.md` (root cause investigation)
- `docs/engine/contracts/observability_artifact_contract.md` — governs artifact writer constraints across all child tickets
- `docs/engine/contracts/replay_contract.md` — Governor owns replay degradation; child tickets must expose pressure, not auto-degrade
- `docs/engine/contracts/certification_contract_me.md` — Milestone E certification law; scoped metadata requirements
- `docs/architecture/observability_hot_path_safety_contract.md` — defines hot-path allowed/forbidden ops; primary constraint for OBS-BACKPRESSURE and LIFECYCLE-SUPERVISOR
- `docs/content/pipeline_contract.md` — WORLD-CAT-004/WORLD-CAT-005 compliance IDs; primary constraint for CONTENT-HOTPATH-GUARD
- `docs/engine/contracts/runtime_completion_contract_ma.md` — section 7: Canonical Checkpoint Law; primary constraint for HASH-SCHEDULER
- `docs/engine/performance_contract.md`
- `docs/engine/kernel.md`
- `docs/parity_ledger/infrastructure.yaml`

## Related Stored Artifacts
- `memory_issue.md`
- `memory_features.md`

## Related Code Areas
- `src/certification/` — proof artifact boundary (prerequisite batch)
- `src/engine/kernel.py` — central subsystem owner
- `src/engine/replay_manager.py` — replay backpressure
- `src/engine/checkpoint.py` — canonical hashing
- `src/observability/event_recorder.py` — observability backpressure
- `src/observability/behavior/worker.py` — worker lifecycle
- `src/config/optimization_profiles.py` — per-subsystem budgets
- `src/content_semantics/faction.py` — content hot-path
- `src/content/repository.py` — CatalogRepository YAML loading

## Assumptions / Open Questions
- None at epic level. See individual child tickets.

## Implementation Notes
N/A — epic only.

## Test Summary
N/A — epic only.

## Files Changed
N/A

## Completion Summary
_(filled when all children done)_

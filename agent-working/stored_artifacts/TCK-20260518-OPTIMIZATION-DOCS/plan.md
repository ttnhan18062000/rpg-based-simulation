---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260518-OPTIMIZATION-DOCS
artifact_type: plan
tags: [optimization, docs]
---

# Staging Plan — Optimization Documentation and Invariant Ledger

## 1. Documentation Architecture

### `docs/performance/optimization_architecture.md`
Will detail the 5-layer optimization stack:
1. **Selection & Narrowing**: `CandidateSelector`, `ScanPolicy`, `MovementCandidateSelector`, `StrategicWorkQueue`.
2. **Dirty Tracking & Invalidation**: `DirtyDependencyGraph`, downstream expansion, `CacheInvalidationPolicy`.
3. **Compaction & Plan Precomputation**: `StateUpdateCompactor`, `ApplyPlanBuilder`, `ComponentPatch`.
4. **Projection & Caching**: `ReadModelCache`, `OccupancySnapshot`, `MovementPlanCache`, `WorldIndexService`, `CacheRegistry`.
5. **Adaptive Governance**: `PhaseDependencyGraph`, `PhaseBudgetGovernor`, `OptimizationProfileResolver`.

### `docs/performance/optimization_invariants.md`
Will formalize all structural invariants ensuring bit-identical parity and safety under extreme optimization, explicitly citing unit and integration tests.

### `docs/performance/perf_baseline_policy.md`
Will document CI regression gating thresholds, hardware profiling standards, and baseline calibration procedures.

# Staging Investigation — Optimization Documentation and Invariant Ledger

## 1. Context and Hotspots
Throughout the execution of Milestones 1-20, we successfully introduced high-performance memory pooling, spatial grid indexing, dirty-set tracking, compaction, component patches, and adaptive governance. However, without centralized architectural documentation and explicit test-backed invariant ledgers, future changes risk inadvertently introducing O(N) scans or violating strict state determinism.

## 2. Invariant Discovery
Our investigation across the engine codebase confirms the following critical boundaries:
- `AuthoritativeState.dirty_set` must never be accessed directly in gameplay modules; all queries must flow through `CandidateSelector` or specific indexes.
- All 7 authoritative engine phases must support `force_full_scan` as a deterministic fallback.
- `StateUpdateCompactor` and `ComponentPatch` must preserve exact mutation ordering and detect no-op singletons.
- Caches registered in `CacheRegistry` must obey tick-based memory boundaries and eviction policies.
- `PhaseBudgetGovernor` must never throttle correctness-critical tasks (death processing, accepted transactions, inventory constraints).

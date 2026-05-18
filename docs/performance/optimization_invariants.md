# Authoritative V2 Engine Optimization Invariants

## 1. Overview and Enforcement Philosophy

To ensure that the performance hardening mechanisms in the V2 engine never compromise the bit-identical determinism of the simulation laws, all optimization features must adhere to strict architectural invariants. Violating any of these invariants constitutes an immediate test failure and blocks production deployment.

```
+-------------------------------------------------------------------------+
|                  OPT-INV-001: DIRECT DIRTYSET PROHIBITION               |
|      Prohibits direct access to AuthoritativeState.dirty_set            |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  OPT-INV-002: FORCE FULL SCAN COMPLIANCE                |
|  Guarantees O(N) deterministic fallback across all 7 core phases        |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  OPT-INV-003: COMPACTION & PATCH ORDER PROTECTION       |
|  Guarantees order-preserving mutation merging & singleton detection     |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  OPT-INV-004: CACHE INVALIDATION & MEMORY BOUNDS        |
|  Guarantees bounded RSS containment via CacheRegistry enforcement       |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  OPT-INV-005: GOVERNOR DEFERRAL SAFETY BOUNDARIES       |
|  Defines strict boundaries between deferrable and non-deferrable work   |
+-------------------------------------------------------------------------+
```

---

## 2. OPT-INV-001: Direct DirtySet Prohibition

### Rationale
In an optimized engine, allowing individual gameplay handlers or external systems to directly inspect or mutate `AuthoritativeState.dirty_set` introduces subtle race conditions and bypasses the `DirtyDependencyGraph`.

### Invariant Rules
1. Gameplay systems, AI decision trees, and action resolvers are strictly prohibited from referencing `state.dirty_set`.
2. All dirty candidate queries must flow through `CandidateSelector.select_candidates()` or specialized spatial indexes (`WorldIndexService`).
3. External state modifications must emit structured `StateUpdate` records; direct mutation of the internal dirty set is forbidden.

### Enforcement & Verification
- **Automated Verification**: Enforced statically by the architectural AST verification suite.
- **Test Citation**: `tests/integration/optimization/test_static_dirtyset_guard.py` (Proves zero direct dirty set references exist across all gameplay systems).

---

## 3. OPT-INV-002: Force Full Scan Compliance

### Rationale
Optimization heuristics (e.g., spatial bounding, dirty filtering) carry the inherent risk of missing subtle edge cases. Under chaos testing, diagnostic auditing, or `DEBUG_REFERENCE` profiling, the engine must be able to instantly bypass all narrowing filters and perform exhaustive $O(N)$ evaluations.

### Invariant Rules
1. All 7 authoritative simulation phases (`Init`, `Scheduling`, `Locomotion`, `Interaction`, `Social`, `Strategic`, `Advancement`) must check `state._force_full_scan` or `flags.get("force_full_scan")`.
2. When `force_full_scan` is active, systems must evaluate all entities in the simulation without exception, bypassing candidate selectors and phase skipping logic.
3. The resulting state hash of a full-scan run must exactly match the state hash of a correctly optimized run.

### Enforcement & Verification
- **Automated Verification**: Verified across multi-tick scenarios comparing full-scan execution against dirty-filtered execution.
- **Test Citation**: `tests/integration/optimization/test_force_full_scan_phase_compliance.py` (Verifies perfect state hash equivalence across all 7 authoritative phases).

---

## 4. OPT-INV-003: Compaction & Patch Order Protection

### Rationale
During hot-path execution, merging multiple updates targeting the same entity can cause data corruption if order-sensitive fields (e.g., equipment changes followed by derived combat stat recalculations) are applied out of sequence.

### Invariant Rules
1. `StateUpdateCompactor` must preserve the chronological sequence of order-sensitive mutations.
2. `ComponentPatch` extraction must enforce strict dependency ordering: `EquipmentPatch` -> `IdentityPatch` -> `CombatPatch` -> `TaskPatch`.
3. High-frequency no-op updates (such as empty movement or zero-delta stats) must be compacted into singletons or eliminated entirely before reaching `ApplyPath`.

### Enforcement & Verification
- **Automated Verification**: Verified by applying multiple staggered patches to mock entities and asserting bit-identical equality against legacy sequential application.
- **Test Citation**: `tests/unit/optimization/test_state_update_compactor.py` & `tests/integration/optimization/test_component_patch_apply_parity.py`.

---

## 5. OPT-INV-004: Cache Invalidation & Memory Bounds

### Rationale
To achieve high throughput, the engine caches spatial flow fields (`MovementPlanCache`), DTO projections (`ReadModelCache`), and local spatial grids (`WorldIndexService`). Without centralized lifecycle governance, these caches will accumulate stale entries and cause unbounded memory growth over long simulations.

### Invariant Rules
1. All runtime optimization caches must register their instances with `CacheRegistry` upon instantiation.
2. `CacheInvalidationPolicy` must instantly purge or invalidate cached records when corresponding domains in the `DirtySet` are flagged.
3. `CacheBudgetPolicy` must enforce maximum item thresholds. At the start of the `Cleanup` phase, caches exceeding their budget must execute deterministic FIFO or LRU eviction sweeps.

### Enforcement & Verification
- **Automated Verification**: Verified by continuous memory tracking harnesses asserting bounded RSS containment over 5,000+ ticks.
- **Test Citation**: `tests/integration/optimization/test_cache_memory_bounds.py` & `tests/certification/test_cert_long_run_stability.py`.

---

## 6. OPT-INV-005: Governor Deferral Safety Boundaries

### Rationale
When compute latency (p95) exceeds the target envelope (50ms), `PhaseBudgetGovernor` dynamically throttles candidate evaluation budgets. However, throttling correctness-critical tasks will silently corrupt the simulation state.

### Invariant Rules
1. **Allowed Deferrals**: The governor is permitted to defer routine strategic project exploration, background social gossip propagation, non-urgent movement pathfinding, and non-combat candidate scanning.
2. **Strictly Prohibited Deferrals**: The governor MUST NEVER defer:
   - Death, mortality, and heir succession processing.
   - Authoritative resolution of accepted resource transactions and quest rewards.
   - Inventory weight and capacity pressure enforcement.
   - Active combat turn evaluations.

### Enforcement & Verification
- **Automated Verification**: Verified by injecting severe compute debt into the governor and asserting that mortality, transactions, and inventory constraints resolve exactly on schedule.
- **Test Citation**: `tests/unit/optimization/test_phase_budget_governor.py` & `tests/integration/optimization/test_degraded_mode_correctness.py` (Proves flawless correctness under degraded mode throttling).

---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

Assuming the previous milestones are already implemented, the next phase should move from **optimization framework** to **deeper engine restructuring**.

The first wave gave you:

```text
central candidate selection
dirty dependency propagation
update compaction
movement candidate reduction
occupancy snapshot
world index/query layer
strategic queue
profiling modes
regression gate
```

Now continue with a second wave:

```text
reduce object churn deeper
reduce phase coupling
make scheduling adaptive
make state application more batch-oriented
improve long-run stability proof
```

---

# Milestone 13 — Post-Implementation Proof Lock

## Purpose

Before adding more optimization, lock proof that the new architecture actually helped.

## What to implement

Create a formal **Optimization Proof Report** generated from test/profiling output.

It should compare:

```text
before implementation
after implementation
```

Across:

```text
movement_1000
resource_1000
combat_1000
strategic_1000
mixed_1000
```

## Metrics to include

```text
p50 / p95 / p99 tick compute
phase cost breakdown
ApplyPath cost
movement routing cost
strategic pass cost
raw entity update count
compacted entity update count
movement candidate count
strategic candidate count
world index hit/miss rate
movement plan cache hit/miss rate
RSS trend
GC count
final state hash parity
```

## Mechanism

Create:

```text
scripts/generate_optimization_proof.py
```

It should:

```text
run pure profiling mode
run smoke benchmark mode
collect benchmark JSON
collect profiler summary
compare against baseline
write markdown report
write machine-readable JSON
```

## Tests to add

```text
tests/perf/test_optimization_proof_report.py
```

Acceptance:

```text
[x] Report includes before/after metrics.
[x] Report includes semantic parity result.
[x] Report includes phase-level breakdown.
[x] Report fails if required metrics are missing.

```

---

# Milestone 14 — ApplyPath Structural Redesign

## Purpose

The current compactor reduces update noise, but ApplyPath may still rebuild too many objects.

Now you should improve **how state updates are applied**, not only reduce input size.

## New mechanism

### `ApplyPlan`

A precomputed execution plan for applying updates.

Instead of ApplyPath repeatedly inspecting a large `StateUpdate`, build a structured plan:

```text
ApplyPlan
  entity_component_changes
  world_collection_changes
  resource_transfers
  lifecycle_changes
  transaction_trace_changes
  cache_invalidation_hints
```

## High-level behavior

Current flow:

```text
StateUpdate
  -> ApplyPath loops/checks/branches repeatedly
  -> many replace calls
```

New flow:

```text
StateUpdate
  -> StateUpdateCompactor
  -> ApplyPlanBuilder
  -> ApplyPath executes prepared plan
```

## What `ApplyPlanBuilder` should do

Group updates by type:

```text
navigation updates
combat updates
inventory updates
strategic updates
biological updates
identity updates
lifecycle updates
world-object updates
```

Precompute:

```text
which entities need replacement
which components need replacement
which collections need copying
which updates are no-op
which caches/indexes must be invalidated
```

## Why this is better

It avoids this pattern:

```text
for every entity update:
    check every possible component
    maybe replace component
    maybe replace entity
    maybe replace collection
```

And moves toward:

```text
for each changed component domain:
    apply only that domain's changes
```

## Tests to add

```text
tests/unit/optimization/test_apply_plan_builder.py
tests/integration/optimization/test_apply_plan_parity.py
tests/perf/test_apply_plan_perf.py
```

Acceptance:

```text
[x] ApplyPlan output is deterministic.
[x] ApplyPlan + ApplyPath gives same final state as old ApplyPath.
[x] Entity/component replacement count decreases.
[x] ApplyPath p95 decreases in movement/resource scenarios.
```

---

# Milestone 15 — Component-Level Patch Model

## Purpose

Move from “entity update object full of optional fields” toward **component-specific patches**.

This is a stronger long-term design than constantly checking optional fields in `EntityUpdate`.

## New mechanism

### `ComponentPatch`

Conceptually:

```text
NavigationPatch
CombatPatch
InventoryPatch
StrategicPatch
BiologicalPatch
LifecyclePatch
IdentityPatch
```

Each patch knows:

```text
target entity id
component domain
whether it is no-op
how to merge with another patch
how to apply to current component
```

## High-level behavior

Instead of:

```text
EntityUpdate(entity_id=1, combat=..., inventory=..., navigation=...)
```

Internally convert to:

```text
CombatPatch(entity_id=1, ...)
InventoryPatch(entity_id=1, ...)
NavigationPatch(entity_id=1, ...)
```

You do **not** need to expose this externally first. It can be an internal ApplyPath optimization.

## Why this matters

It allows:

```text
domain-specific merge logic
domain-specific no-op detection
batch application by component type
better metrics
easier profiling
less giant conditional logic
```

## Tests to add

```text
tests/unit/optimization/test_component_patches.py
tests/integration/optimization/test_component_patch_apply_parity.py
```

Acceptance:

```text
[x] Each patch type can detect no-op.
[x] Each patch type can merge compatible patches.
[x] Patch application equals old EntityUpdate application.
[x] Order-sensitive patches are protected.
```

---

# Milestone 16 — Phase Dependency Graph

## Purpose

The pipeline currently runs phases in a mostly fixed sequence. That is safe but can waste work.

Now that DirtySet and dependency expansion exist, phases should be scheduled based on what actually changed.

## New mechanism

### `PhaseDependencyGraph`

Represents:

```text
phase name
input dirty domains
output dirty domains
required ordering constraints
can_skip_when_no_dirty
must_run_every_tick
periodic cadence
```

Example:

```text
movement routing
  inputs: movement, strategic, interaction
  outputs: movement, occupancy

interaction routing
  inputs: movement, interaction, resource_node, corpse, ground_item
  outputs: inventory, resource_node, corpse, ground_item

lifecycle
  inputs: combat, biological, lifecycle
  outputs: lifecycle, corpse, strategic
```

## High-level behavior

Before running each phase:

```text
check expanded DirtySet
check phase policy
check cadence
decide run / skip / partial run
```

## Why this matters

It turns optimization from local phase logic into a pipeline-level decision.

## Tests to add

```text
tests/unit/optimization/test_phase_dependency_graph.py
tests/integration/optimization/test_phase_skip_parity.py
```

Acceptance:

```text
[x] Phase skip decisions are deterministic.
[x] Required phases cannot be skipped.
[x] Optional phases can skip when no relevant dirty domain exists.
[x] Skipped optimized run matches full reference run.
[x] Phase skip metrics are reported.
```

---

# Milestone 17 — Adaptive Phase Budget Governor

## Purpose

Make the engine adapt when a phase becomes too expensive.

Profiling tells you which phase is hot. The governor decides what to do about it.

## New mechanism

### `PhaseBudgetGovernor`

Input:

```text
recent phase p95
current tick cost
work debt
candidate counts
queue sizes
hardware profile
```

Output:

```text
scan policy
candidate budget
strategic budget
movement budget
background sweep interval
degraded mode decision
```

## Example decisions

```text
if strategic phase exceeds budget:
    reduce routine strategic budget
    keep urgent strategic work
    increase background sweep interval

if movement phase exceeds budget:
    process movement dirty first
    defer low-priority movement
    increase movement cadence for non-urgent entities

if apply phase exceeds budget:
    enable stronger compaction
    lower optional phase budget
```

## Important rule

The governor must not skip correctness-critical work.

It can defer:

```text
routine strategic refresh
background social updates
non-urgent movement
low-priority scanning
```

It must not defer:

```text
death/lifecycle consistency
accepted resource transactions
quest reward finalization
inventory capacity enforcement if already violated
```

## Tests to add

```text
tests/unit/optimization/test_phase_budget_governor.py
tests/integration/optimization/test_degraded_mode_correctness.py
```

Acceptance:

```text
[x] Governor lowers optional work under pressure.
[x] Urgent work still runs under pressure.
[x] Degraded mode remains deterministic.
[x] Full recovery occurs when pressure drops.
[x] No correctness-critical phase is skipped.
```

---

# Milestone 18 — Long-Run Stability Certification

## Purpose

The previous profiling report claimed long-duration stability, but you need stronger proof.

Create real long-run certification.

## New mechanism

### `LongRunStabilityHarness`

Runs:

```text
1,000 entities
5,000 ticks
multiple scenarios
pure mode
runtime mode
```

Collects:

```text
tick p50/p95/p99 trend
RSS trend
GC event count
object count trend
candidate count trend
cache hit/miss trend
phase cost trend
hash/checkpoint samples
```

## Stability checks

```text
p95 tick cost should not trend upward beyond threshold
RSS should not grow unbounded
GC count should not spike progressively
cache size should remain bounded
movement plan cache should not grow forever
world index cache should not retain stale versions
```

## Tests / certification

```text
tests/certification/test_long_run_stability.py
```

Acceptance:

```text
[x] Long-run report includes RSS and GC.
[x] Cache sizes are bounded.
[x] p95 tick cost has no uncontrolled upward trend.
[x] Final state remains deterministic for same seed.
```

---

# Milestone 19 — Cache Lifecycle and Memory Boundaries

## Purpose

After adding indexes and caches, memory risk increases. This milestone prevents cache growth bugs.

## New mechanisms

### `CacheRegistry`

Central registry of runtime caches:

```text
world indexes
movement plan cache
read model cache
strategic queue history
occupancy snapshots
```

### `CacheBudgetPolicy`

Defines max size / retention:

```text
max movement plans
max cached DTOs
max retained index versions
max profile snapshots
```

## High-level behavior

Every cache reports:

```text
current size
hit count
miss count
eviction count
last invalidation tick
```

## Tests to add

```text
tests/unit/optimization/test_cache_registry.py
tests/integration/optimization/test_cache_memory_bounds.py
```

Acceptance:

```text
[x] Every optimization cache is registered.
[x] Cache size is observable.
[x] Cache eviction is deterministic.
[x] Long-run scenario does not grow cache unbounded.
```

---

# Milestone 20 — Scenario-Specific Optimization Profiles

## Purpose

Different scenarios stress different systems. Use scenario-aware optimization profiles, not one global setting.

## New mechanism

### `OptimizationProfile`

Defines:

```text
movement budget
strategic budget
background sweep interval
indexing mode
compaction level
cache size limits
phase skip policy
```

Example profiles:

```text
COMBAT_HEAVY
MOVEMENT_HEAVY
RESOURCE_HEAVY
METROPOLIS
LOW_MEMORY
DEBUG_REFERENCE
```

## High-level behavior

Runtime profile chooses default optimization profile.

Scenario/certification can override it.

## Acceptance tests

```text
tests/unit/optimization/test_optimization_profiles.py
tests/integration/optimization/test_profile_specific_behavior.py
```

Acceptance:

```text
[x] Profiles are deterministic.
[x] Debug/reference profile disables unsafe narrowing.
[x] Low-memory profile reduces cache sizes.
[x] Movement-heavy profile prioritizes movement optimization.
[x] Resource-heavy profile prioritizes world index/resource query optimization.
```

---

# Milestone 21 — Optimization Documentation and Invariant Ledger

## Purpose

After all these mechanisms, documentation becomes mandatory.

Create:

```text
docs/performance/optimization_architecture.md
docs/performance/optimization_invariants.md
docs/performance/perf_baseline_policy.md
```

## Must document

```text
CandidateSelector contract
force_full_scan contract
DirtyDependencyGraph rules
StateUpdateCompactor safety rules
ApplyPlan behavior
MovementCandidateSelector rules
cache invalidation rules
PhaseBudgetGovernor allowed deferrals
PerfRegressionGate thresholds
```

## Acceptance

```text
[x] Every optimization mechanism has an invariant section.
[x] Every invariant references at least one test.
[x] Every perf baseline has update instructions.
```

---

# Recommended next execution order

Since the previous plan is implemented, continue like this:

```text
13. Post-Implementation Proof Lock
14. ApplyPath Structural Redesign
15. Component-Level Patch Model
16. Phase Dependency Graph
17. Adaptive Phase Budget Governor
18. Long-Run Stability Certification
19. Cache Lifecycle and Memory Boundaries
20. Scenario-Specific Optimization Profiles
21. Optimization Documentation and Invariant Ledger
```

But the next **practical slice** should be smaller:

```text
Slice 1:
- Post-Implementation Proof Report
- ApplyPlanBuilder
- ApplyPlan parity tests
- ApplyPath p95 comparison

Slice 2:
- ComponentPatch model
- patch merge/no-op tests
- patch apply parity tests

Slice 3:
- PhaseDependencyGraph
- phase skip parity tests

Slice 4:
- PhaseBudgetGovernor
- degraded-mode correctness tests
```

---

# Priority Plan

## What to do next

Start with:

```text
Milestone 13 + Milestone 14
```

Reason:

```text
You just implemented a broad optimization framework.
Now prove it, then attack the remaining largest hotspot: ApplyPath structure.
```

## What not to do next

Do not start with adaptive budget governor yet.

That is powerful but dangerous unless ApplyPath and phase dependencies are cleaner.

Do not add more caches until cache lifecycle and memory boundaries are formalized.

## Expected result after the next slice

You should be able to prove:

```text
new architecture improved measured work
ApplyPath replacement cost decreased
phase-level bottlenecks are clearer
semantic parity still holds
longer optimization work has a stable foundation
```

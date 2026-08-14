---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Candidate Selection Contract

**Source:** `src/engine/scheduler.py` (DeterministicScheduler), `src/core/dirty.py` (CandidateSelector / DirtySet), `src/engine/candidate_selector.py` (MovementCandidateSelector)
**Related docs:** [dirty_state_and_dependency.md](../core/dirty_state_and_dependency.md) (Tier 2 domain routing), [kernel.md](kernel.md) (tick pipeline context)

---

## Purpose

"Candidate selection" refers to three distinct tiers of filtering that narrow the full entity set to the subset that should receive work in a given tick or pipeline phase. All three tiers are deterministic — given the same world state and tick, each produces the same ordered result.

---

## Tier 1: Work Item Selection — `DeterministicScheduler.select_work()`

**Location:** `src/engine/scheduler.py`
**When:** the Scheduling stage of the kernel's tick loop
**Output:** Set of `WorkItem`s passed to worker threads

Decides which entities produce work this tick. Three gates:

| Gate | Rule |
|---|---|
| **Readiness** | `entity.readiness >= 100` — entities below threshold are skipped this tick |
| **LOD gating** | Level-of-detail tier (A/B/C) gates whether full or reduced processing runs; distant/low-priority entities may get simplified work items |
| **Strategic cadence** | `tick % entity.strategic_cadence == 0` — high-level strategic re-evaluation only runs every N ticks (not every tick), reducing redundant domain phase invocations |

Entities that pass all three gates receive `WorkItem`s dispatched to workers. Entities that fail any gate receive no work this tick.

---

## Tier 2: Domain Phase Routing — `CandidateSelector` on `DirtySet`

**Location:** `src/core/dirty.py` — `CandidateSelector.entities()`, `DirtySet.get_relevant_entity_ids()`
**When:** Per pipeline phase, inside `AuthoritativeApplyPipeline.refine()`
**Output:** Filtered entity subset for each domain phase to process

The 15 domain routing mappings skip entities that have no dirty state relevant to a given phase. Full documentation in [dirty_state_and_dependency.md](../core/dirty_state_and_dependency.md) — the 15 mappings, the 10 dependency expansion edges, and the force_full_scan fallback.

---

## Tier 3: Movement Candidate Selection — `MovementCandidateSelector.select()`

**Location:** `src/engine/candidate_selector.py`
**When:** Movement resolution phase
**Output:** Ordered tuple of entity IDs cleared to attempt movement this tick

The most complex of the three tiers. Runs a 6-stage filter pipeline:

### Stage 1: Liveness check
Entities that are dead, incapacitated, or in a non-movement-eligible state are rejected immediately.

### Stage 2: Already-moved guard
Entities that already moved this tick (tracked in a per-tick moved set) are excluded — prevents double-movement from processing order artefacts.

### Stage 3: Target validity
Entity's intended movement target is validated against world state. Invalid or unreachable targets produce no candidate (the movement intent itself may be voided). Before this "already at target" comparison, a stale, persisted `entity.navigation.target` (no fresh decision this tick) is live-refreshed via `MovementCandidateSelector.resolve_live_tracking_target()` when `entity.task.payload["target_id"]` names a still-alive entity — using its CURRENT position rather than the fallback's static snapshot. Without this, a pursuing entity that already "arrived" at a stale, one-time snapshot of its target's old position is permanently excluded from candidacy here, even though the target has since moved and route_movement_intent's own live-retargeting (Tier 2 downstream) would otherwise find a real, legal step toward it (`TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS`).

### Stage 4: Force-full-scan bypass
If `force_full_scan=True` is set on the dirty set for this tick (triggered by calamity events or world restructuring), all liveness-checked entities are included regardless of readiness or urgency classification.

### Stage 5: Urgency classification
Surviving entities are classified into two buckets:

| Class | Triggers |
|---|---|
| **Urgent** | Active combat, near-death (HP < 20%), critical biological need (hunger/thirst at danger threshold), active escort obligation, force_route_reevaluation flag set |
| **Normal** | All other movement intents |

### Stage 6: Scan-policy gating
- **Urgent candidates:** always included (budget-protected).
- **Normal candidates:** subject to readiness threshold and WANDER modulo throttle. `tick % wander_modulo == 0` gates opportunistic/exploration movement — entities that are only wandering do not move every tick.

### Deterministic ordering
Final result is `tuple(sorted(candidates))` — entity IDs sorted ascending. This guarantees identical ordering regardless of set operations or processing order.

---

## Budget enforcement

All three tiers respect a per-tick entity budget:
- Tier 1 budget: total WorkItems dispatched ≤ `max_concurrent_workers` × `batch_size`
- Tier 2 budget: phase-specific entity caps (see performance_contract.md for hardware class limits)
- Tier 3 budget: urgent candidates fully protected; normal candidates trimmed if total would exceed movement budget cap

---

## Determinism guarantees

Each tier produces a deterministic result:
- Tier 1: same readiness/LOD/cadence → same WorkItem set
- Tier 2: same DirtySet → same entity subset per phase (CandidateSelector is pure function of dirty flags)
- Tier 3: `tuple(sorted(...))` final output; urgency classification is deterministic (no randomness)

All tiers are covered by the broader determinism guarantee in [deterministic_execution.md](deterministic_execution.md).

---

## Regression tests

- `tests/integration/kernel/test_determinism_suite.py` — same seed → same WorkItem set across multiple runs
- `tests/unit/optimization/test_candidate_selector.py` — MovementCandidateSelector stage-by-stage filter verification
- `tests/perf/test_dirty_set_integrity.py` — CandidateSelector domain routing (15 mappings)

---

## Extension rules

1. To add a new Tier 1 gate (e.g., a new LOD tier), extend `DeterministicScheduler.select_work()` and update performance_contract.md.
2. To add a new domain routing mapping (Tier 2), follow the procedure in [dirty_state_and_dependency.md](../core/dirty_state_and_dependency.md) extension rules.
3. To add a new urgency trigger (Tier 3), add to the urgency classification logic in `MovementCandidateSelector` and add a test verifying the trigger is budget-protected.
4. Never introduce randomness into any tier — all selection must be deterministic given the same inputs.

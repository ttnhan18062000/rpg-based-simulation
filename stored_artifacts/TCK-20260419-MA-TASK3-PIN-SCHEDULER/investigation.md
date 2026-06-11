---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260419-MA-TASK3-PIN-SCHEDULER
artifact_type: investigation
tags: [ma, task3, pin, scheduler]
---

# Investigation: Deterministic Scheduler Audit

## Work Class Hierarchy

The current `DeterministicScheduler` correctly organizes work into three main buckets:
1. **CRITICAL**: Entity Actions.
2. **PERIODIC**: Subsystem Upkeep.
3. **DEFERRED**: Debt Draining.

The Milestone A Law requires exactly this order, followed by **OPPORTUNISTIC** (which is currently a placeholder).

## Tie-Break Rules

The current code implements the following tie-breaks, which match the contract:
- **Critical Entities**: Sorted by `(-readiness, owner_id)`.
- **Periodic Tasks**: Sorted by `(due_tick, owner_id)`.
- **Deferred Debt**: Sorted by `owner_id`.

## Gaps and Needed Refactors

### 1. Placeholder Removal
The `OPPORTUNISTIC` branch in `select_work` is currently a `pass` block.
```python
103:         # 4. OPPORTUNISTIC: Optional Enrichment
104:         if policy.allow_opportunistic:
105:             # Placeholder for future opportunitistic work injection
106:             pass
```
According to Milestone A "No placeholder" law, this should be explicitly gated. For the baseline runtime, we should either:
- Explicitly return that no opportunistic work is supported in Milestone A.
- Or count all potential opportunistic work as "dropped" if it were to be injected.

### 2. WorkItem Enrichment
The `WorkItem` dataclass has a `priority` field which is currently unused in the `select_work` sorting. While the contract specifies `readiness` and `due_tick`, the `priority` field exists for "Class-local priority." We should decide if this should be part of the authoritative tie-break or if it remains a non-authoritative hint. For Milestone A, we stick to the contract: `-readiness, owner_id`.

### 3. Debt Draining Stability
The `DEFERRED` logic iterates over `state.work_debt.items()`. Since `work_debt` is a `Dict`, the iteration order depends on Python's insertion order (stable in 3.7+). However, for canonical determinism, sorting by `owner_id` is correct.

## Testing Strategy
We need a "Stress Test" for the scheduler that includes:
- Entities with identical readiness.
- Periodic tasks with identical due ticks.
- Multiple debt entries.
- Verifying that the final `work_sequence` order is ALWAYS identical given the same input state.

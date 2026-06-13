---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
---

# State Update Compaction Contract

**Source:** `src/core/compactor.py` (StateUpdateCompactor), `src/core/updates.py` (StateUpdate.merge_many), `src/engine/authoritative_pipeline.py` (AuthoritativeApplyPipeline)
**Related docs:** [update_intents.md](../core/update_intents.md) (merge semantics), [authoritative_pipeline.md](authoritative_pipeline.md) (pipeline context)

---

## Purpose

State update compaction eliminates redundant or no-op update fragments before the authoritative apply pipeline commits them to durable state. Without compaction, concurrent workers produce many small fragments — some of which are identity operations that waste downstream processing.

Two distinct compaction layers exist in the pipeline. Understanding both is necessary to trace how N worker fragments become a single applied delta.

---

## Layer 1: Fragment Aggregation — `StateUpdate.merge_many()`

**Location:** `src/core/updates.py:884`
**Logic ID:** TOWN-204
**Trigger:** Called by the engine after all workers for a tick complete, before the authoritative pipeline runs.

`StateUpdate.merge_many(updates: list[StateUpdate]) -> StateUpdate` aggregates N concurrent worker output fragments into one combined `StateUpdate`. This is **not** compaction — it is union. No pruning happens here; all fragments are folded in.

**Merge semantics** (full detail in [update_intents.md](../core/update_intents.md)):

| Field type | Merge rule |
|---|---|
| Numeric delta (hp_delta, gold_delta, stamina_delta) | Sum across all fragments |
| Set/scalar (kind_set, active, new_position) | Last-write-wins (latest fragment wins) |
| List (items_add, quests_add, signals_add) | Concatenate all fragments |

After merge, one `StateUpdate` represents the combined intent of all workers for that tick.

---

## Layer 2: No-op Pruning — `StateUpdateCompactor.compact_with_metrics()`

**Location:** `src/core/compactor.py:37`
**Trigger:** First operation inside `AuthoritativeApplyPipeline.refine()` (`src/engine/pipeline.py:96`) — before any of the 17 pipeline phases.

The compactor prunes fragments that are provably no-ops given the current `AuthoritativeState`. It does NOT change semantics — only efficiency.

### What it prunes

1. **Entity updates that match current state** — if `kind_set` already equals `entity.kind`, the field is stripped. Same for `active` flag and `new_position` when entity is already at that position.
2. **No-op sub-components** — each update sub-record (EquipmentUpdate, IdentityUpdate, etc.) has an `is_noop()` method. Sub-records where all fields are no-ops are removed.
3. **Redundant entity wrappers** — if an EntityUpdate's every sub-record is stripped, the whole EntityUpdate is pruned from the StateUpdate.

### Aggressive mode

Under `AGGRESSIVE` compaction mode (configurable per-run):
- Cosmetic debug properties are stripped (they don't affect `CanonicalStateHasher` output).
- Tiny stamina deltas below the floating-point significance threshold are zeroed.

### Fingerprint equivalence invariant

**Correctness contract:** `raw_state.fingerprint() == compacted_state.fingerprint()`

Compaction must never change what the apply path commits. This invariant is verified in `tests/perf/test_apply_compaction_perf.py:76`. Any compaction optimisation that breaks this invariant is a bug, not a performance win.

---

## Pipeline position

```
Workers complete → StateUpdate.merge_many() → AuthoritativeApplyPipeline.refine()
                                                └─ Step 0: StateUpdateCompactor.compact_with_metrics()
                                                └─ Step 1–17: pipeline phases
                                                └─ Persistence
```

Compaction runs exactly once per tick, at the entry point of the authoritative pipeline.

---

## What compaction does NOT do

- It does not reorder updates.
- It does not resolve conflicts between fragments (merge_many does that with last-write-wins/sum/concat rules).
- It does not validate that a delta is legal (legality checks happen in pipeline phases 2–4).
- It does not affect the CanonicalStateHasher output for any non-no-op field.

---

## Metrics

`compact_with_metrics()` returns a `CompactionMetrics` record:
- `entities_pruned` — count of fully-pruned EntityUpdates
- `fields_stripped` — total fields removed across all updates
- `mode` — NORMAL or AGGRESSIVE

These metrics are emitted as telemetry and appear in the `TICK_END` event in the warehouse.

---

## Regression tests

- `tests/perf/test_apply_compaction_perf.py` — fingerprint invariant, compaction throughput under N-worker load
- `tests/integration/test_authoritative_pipeline.py` — end-to-end: workers produce fragments, compaction runs, pipeline applies, state matches expected

---

## Extension rules

1. To add a new no-op rule: implement `is_noop()` on the new update sub-record type. Do not add pruning logic to `compact_with_metrics()` directly — add it to the sub-record.
2. To add a new merge rule: extend `StateUpdate.merge_many()` with the new field type following the existing delta/set/list pattern.
3. Any new compaction optimisation must be verified against the fingerprint equivalence invariant test before merging.
4. AGGRESSIVE mode additions must not prune fields that appear in `CanonicalStateHasher`'s hash surface.

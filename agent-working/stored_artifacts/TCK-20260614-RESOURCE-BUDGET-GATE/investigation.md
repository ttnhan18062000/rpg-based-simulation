---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-RESOURCE-BUDGET-GATE
date: 2026-06-14
---

# TCK-20260614-RESOURCE-BUDGET-GATE — Investigation

## Current Behavior

### EventRecorder (src/observability/event_recorder.py)

- **Queue field**: `self.queue = BoundedObservabilityQueue(max_size=self.max_events)` — line 42.
- **Enqueue path**: `record()` method lines 93–133. After optional in-memory eviction, `self.queue.try_push(envelope)` is called at line 133. The queue has a hard `max_size` cap, but there is no call to `pressure_report()` and no threshold check (80%/100%) today. The queue size is readable via `self.queue.get_size()`.
- **Dropped count**: `self.queue.dropped_count` is exposed via `get_stats()` (line 143), but no structured pressure state (OK/WARN/DEGRADED) is emitted.
- **No SubsystemBudget wiring exists**: `EventRecorder.__init__` takes only `run_dir`, `max_events`, `enabled`. There is no budget injection point yet.

### ReplayManager (src/engine/replay_manager.py)

- **Chunk counter**: `self._current_chunk_id = 0` (line 53), incremented at `_rotate_chunk()` line 212. There is no `_chunks_persisted` counter; persistence success is tracked only via the manifest's `chunks` list (line 227–233 in `_execute_persistence`).
- **Inflight estimation**: No explicit `_inflight` counter exists. The approximation available is `self._current_chunk_id - len(self._manifest["chunks"])`. This requires holding `_manifest_lock` to read safely.
- **Executor**: `ThreadPoolExecutor(max_workers=1)` (line 66). The executor queue depth is not directly inspectable via the standard `concurrent.futures` API; pending submit count must be derived from `_current_chunk_id - persisted_count`.
- **Existing budget wiring**: `_rotate_chunk()` already calls `get_default_registry().check("replay_chunk", estimated_bytes)` (INFRA-193) — this is artifact-size budgeting, separate from the inflight chunk budget added here.
- **No `pressure_report()` method exists today.**

### CanonicalStateHasher (src/engine/checkpoint.py)

- **Interface**: Fully static class. `get_hash(state)` at line 17 calls `hashlib.sha256(compact_json.encode()).hexdigest()`. Every call performs a full serialization of `AuthoritativeState` (all entities, regions, tiles, etc.) — O(N) work.
- **No call counter exists today.** No window tracking, no rate limiting, no `pressure_report()`.
- **Compliance IDs in file**: INFRA-119 through INFRA-133 — all hash inclusion/exclusion parity entries.
- **Making it budget-aware requires converting from a static class to an instance** (to hold `_call_count` and `_window_start_tick`), or adding a thin wrapper/mixin. The static class design makes injecting a budget without an instance impossible.

---

## Existing Budget Patterns

### OptimizationProfile (src/config/optimization_profiles.py)

- `frozen=True, slots=True` dataclass, lines 33–48.
- Fields: `movement_budget: int`, `strategic_budget: int`, `background_sweep_interval: int`, `indexing_mode`, `compaction_level`, `phase_skip_policy`, `cache_budget_policy: CacheBudgetPolicy`.
- `SubsystemBudget` is a direct extension of this pattern. The ticket scope places `SubsystemBudget` either in `src/config/optimization_profiles.py` or a new `src/engine/resource_budget.py`.

### CacheBudgetPolicy (src/engine/cache_registry.py)

- `frozen=True, slots=True` dataclass, lines 43–53.
- Fields: `max_movement_plans`, `max_read_dtos`, `max_spatial_grid_versions`, `max_strategic_queues`, `sweep_interval_ticks` — all int, integer count caps.
- `SubsystemBudget` fields are a parallel but broader set: mix of `float | None` (MB) and `int | None` (counts/rates).

### ArtifactBudgetRegistry (src/certification/artifact_budget.py)

- `ArtifactBudget` dataclass: `artifact_type`, `max_size_mb`, `soft_limit_mb`, `retention`, `allow_full_state`, `compression`, `fail_on_budget_violation`.
- `BudgetCheckResult`: `allowed`, `action` ("allow"/"warn"/"compact"/"reject"), `reason`.
- Check method returns a result struct; never raises. Callers log violations (INFRA-060).
- This is the closest analog to `SubsystemPressureReport`. Key difference: `ArtifactBudget` is write-time/size-oriented; `SubsystemBudget` is runtime/queue-count/rate-oriented.

### Phase Budget Governor (src/engine/phase_governor.py — TCK-20260518-PHASE-BUDGET-GOVERNOR)

- Governs CPU cost (compute ms, candidate counts, scan policies). Does not govern memory/queue subsystems.
- `PhaseBudgets` propagated through `GovernorPolicy` → `ResourceGovernor`. Same advisory pattern: governor receives signals; execution decisions are centralized in the governor, not in subsystems.
- **Anti-duplication**: This ticket must not replicate governor logic inside subsystems. `pressure_report()` is an advisory read; the Governor acts on it.

---

## Best File Placement for SubsystemBudget

**Decision: `src/config/optimization_profiles.py`**

Rationale:
1. `OptimizationProfile` already owns all budget declarations for the simulation profile. Adding `subsystem_budgets: dict[str, SubsystemBudget] = field(default_factory=dict)` to it is the natural extension point (ticket scope, line 41).
2. `CacheBudgetPolicy` already lives in `src/engine/cache_registry.py` as a domain-specific peer. `SubsystemBudget` is broader (cross-domain) and belongs at the config layer, not the engine layer.
3. `src/engine/resource_budget.py` (alternative) would be a new file with no existing imports. Creating it introduces a new import seam for `SubsystemPressureReport` — every wired subsystem would need to import from the engine layer, creating potential circular imports (e.g., `src/observability/` importing `src/engine/`).
4. Both `SubsystemBudget` and `SubsystemPressureReport` can live in `src/config/optimization_profiles.py` without making the file excessively large (it currently has ~175 lines). `SubsystemPressureReport` is a pure data type with no engine dependency, matching the config layer pattern.

**If the file grows unwieldy:** extract to `src/config/resource_budget.py` (config layer, not engine layer). Do not use `src/engine/`.

---

## replay_contract.md Constraint: pressure_report() Must Be Advisory

From `docs/engine/contracts/replay_contract.md` §Sink Pressure and Quota:

> "Under pressure, the Governor will downgrade replay richness or disable capture entirely."

This confirms: **ReplayManager.pressure_report() must only describe the current state — it must not take action.** The degradation action string ("downgrade richness", "disable capture") is advisory text consumed by the Governor (TCK-20260614-RESOURCE-DASHBOARD reads it; a later epic wires the Governor to act on it). The `SubsystemPressureReport.degradation_action` field must be a `str | None` description, never a callable.

Implementation constraint for `ReplayManager.pressure_report()`:
- Must be non-blocking and read-only (ticket §Implementation Notes).
- The inflight count read (`_current_chunk_id` and `len(self._manifest["chunks"])`) requires a brief lock on `_manifest_lock`. This is acceptable as a short read-only snapshot — the lock is only ever held for dict appends (line 227) and manifest writes (line 235), making contention negligible.
- Alternative (preferred for true non-blocking): add a thread-safe `_chunks_persisted` counter incremented inside `_execute_persistence()` on success, which can be read lock-free.

---

## Parity Ledger Overlap

Scanning `docs/parity_ledger/infrastructure.yaml` for entries that directly touch EventRecorder, ReplayManager, or CanonicalStateHasher:

| Entry ID | Text summary | Relevance |
|---|---|---|
| INFRA-119–130 | Replay hash includes all gameplay domains | These are `CanonicalStateHasher` hash-coverage entries — all `verified`. Adding a rate-limiter to `get_hash()` does not change what fields are hashed, so these entries are unaffected as long as the fallback "return last known hash" path is only triggered under rate-limiting and the hash value itself is unchanged. |
| INFRA-131–133 | Replay tests (identical runs, sequential vs concurrent, save/load) | Unaffected by this ticket — no determinism change. |
| INFRA-155–157 | Replay manifest atomic write / failure preserves old manifest / finalization timeout | Unaffected. `pressure_report()` does not touch the manifest write path. |
| INFRA-170 | Shutdown flushes replay/logging within timeout | Unaffected. `pressure_report()` is advisory, not called on shutdown path. |
| INFRA-173 | Degraded mode is observable, not silent | **Relevant**: Adding `pressure_report()` with `WARN`/`DEGRADED` states directly satisfies this entry's spirit for the new subsystems. No status update needed (entry covers degraded mode being observable; this ticket makes it observable for new subsystems). |
| INFRA-193 | ArtifactBudgetRegistry enforces write-time size budgets | **Related but distinct**: INFRA-193 covers write-time artifact sizes. This ticket covers runtime queue/rate budgets. These are complementary, not overlapping. No update needed to INFRA-193. |

**New parity entries required**: Three new `INFRA-194`, `INFRA-195`, `INFRA-196` entries should be added to `infrastructure.yaml` after implementation to cover:
- INFRA-194: `EventRecorder.pressure_report()` returns WARN at ≥80% queue capacity and DEGRADED at 100%.
- INFRA-195: `ReplayManager.pressure_report()` reports chunk inflight count vs budget, advisory only.
- INFRA-196: `CanonicalStateHasher.pressure_report()` tracks full-hash call rate per 100-tick window and returns WARN when over budget.

---

## Risks and Open Questions

### Risk 1: CanonicalStateHasher static class conversion
**Current**: `CanonicalStateHasher` is a fully static class (no `__init__`, all `@staticmethod`). Adding per-instance state (`_call_count`, `_window_start_tick`, `_last_hash`) requires converting to an instance class. All call sites that use `CanonicalStateHasher.get_hash(state)` as a static call must be updated. This is a moderate scope change.
**Preferred approach**: Wrap in a `BudgetedCanonicalHasher` instance class that holds the call counter and delegates to the static `CanonicalStateHasher.get_hash()`. This avoids modifying all existing call sites and keeps parity tests green.

### Risk 2: ReplayManager pending_flushes estimation
**Option A** (ticket §Assumptions): `_current_chunk_id - len(self._manifest["chunks"])` — requires `_manifest_lock` to read safely, or may yield stale count.
**Option B** (preferred): Add `_chunks_persisted: int = 0`, increment inside `_execute_persistence()` on success, read lock-free in `pressure_report()`. Simpler, no lock needed, accurate.
**Open question for decision**: Should `_chunks_persisted` be a plain `int` (slightly racy in theory but acceptable since it's advisory) or `threading.Event`/atomic? For an advisory pressure signal, a plain `int` is sufficient.

### Risk 3: EventRecorder budget injection point
**Current `__init__`**: Takes `max_events`. The `SubsystemBudget` for observability sets `max_queue_items`. These may diverge if the budget is changed after construction. The wiring should use `budget.max_queue_items` as the source of truth for `max_events` when a budget is provided, or check against `budget.max_queue_items` independently at enqueue.
**Decision needed**: Does `SubsystemBudget.max_queue_items` replace `max_events` as the capacity, or is it an additional check? The AC says "check `max_queue_items` against queue size at enqueue" — suggesting it is checked against the queue (not the in-memory buffer), meaning it can be independent of `max_events`.

### Risk 4: DEBUG_REFERENCE profile must be unaffected
All `SubsystemBudget` fields for `DEBUG_REFERENCE` must be `None` (unlimited). The `pressure_report()` implementation must treat `None` budget fields as "no limit — always OK".

### Open Question 1: 100-tick window reset strategy for CanonicalStateHasher
The ticket proposes `(call_count, window_start_tick)` reset every 100 ticks. But `CanonicalStateHasher` currently has no tick-awareness — it is called from harness/certification paths, not from the kernel tick loop. The wiring subsystem (likely `CertificationHarness` or `V2EngineManager`) must pass the current tick to `pressure_report()` or to a `tick_advance()` call. This interface needs a decision before implementation.

### Open Question 2: "Last known hash" fallback correctness
When the hasher is over budget and returns the last known hash, the caller may assume the returned value is current. This must be clearly documented as a stale hash. The `SubsystemPressureReport.degradation_action` should state `"returning_stale_hash"` so callers can detect degraded mode.

---

## Anti-Drift Hazards

1. **`pressure_report()` must never be called on the kernel tick hot path** — each call would add a lock acquisition or counter read per tick. Wire only to the dashboard/governor polling path (explicit call, not implicit per-tick).
2. **Do not embed `SubsystemBudget` defaults inside subsystem constructors** — defaults must live in `optimization_profiles.py` profile instances so they are overridable per scenario. Subsystems receive a budget via injection (constructor arg or `Kernel` wiring), not by hardcoding defaults locally.
3. **`CanonicalStateHasher` static → instance migration must not break INFRA-119–130** — the hash value itself must remain bit-identical. Only the call-rate tracking is new behavior.
4. **`ReplayManager.pressure_report()` must not call `get_stats()`** — `get_stats()` calls `self._buffer.get_stats()` which may have internal lock implications. `pressure_report()` reads only `_current_chunk_id` and `_chunks_persisted` (or manifest chunk count), which are cheap reads.

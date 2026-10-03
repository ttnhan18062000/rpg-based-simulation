---
status: active
artifact_type: investigation
ticket_id: TCK-20260619-E31C-CHECKPOINT
date: 2026-06-21
---

# Investigation: TCK-20260619-E31C-CHECKPOINT

## 1. Current Behavior (file:line refs)

### ScenarioRuntimeService (`src/engine/scenario_runtime.py`)

- `ScenarioRuntimeService.__slots__` (L118): `("_spec","_kernel","_state","_tick","_paused","_stall_counter","_last_event_tick")`. No checkpoint slot yet.
- `_build_kernel()` (L293): constructs `Kernel(profile, state, rng, flags={"no_replay": True})` with hardcoded `AuthoritativeState(tick=0, seed=0)` and `DeterministicRNG(base_seed=0)`. This is the restore target — a fresh service must be able to bypass `_build_kernel()` and receive a pre-restored kernel instead.
- The file-level docstring (L16) explicitly calls out "E31C — checkpoint / restore" as out of scope, meaning no checkpoint code exists yet.

### CanonicalStateHasher (`src/engine/checkpoint.py:L38`)

- `to_canonical_data(state)` (L63): serializes the following fields of `AuthoritativeState` into a sortable dict: `tick`, `seed`, `world_time`, `movement_count`, `maturity`, `last_calamity_tick`, `town_center`, `entities` (via `to_canonical_dict()`), `regions`, `local_scars`, `resource_nodes`, `buildings`, `corpses`, `ground_items`, `chests`, `groups`, `home_storage`, `camps`, `global_resources`, `periodic_due_ticks`, `work_debt`, `blocked_tiles`, `town_tiles`, `building_tiles`, `rng_checkpoint`.
- `to_canonical_json()` (L52): wraps `to_canonical_data()` to produce stable JSON (sort_keys=True). This is the basis for the checkpoint file payload.

### AuthoritativeState (`src/core/state.py:L987`)

- Frozen dataclass. All mutation goes through `dataclasses.replace()` — construction from a dict requires passing field values individually to the constructor. No `from_dict()` classmethod exists.
- `__post_init__` (L1057): clears all cache fields, wraps entities in `_readonly_mapping`, auto-advances `next_entity_id` and `next_node_id` if IDs exceed current values. Any restore path must call the constructor (not bypass `__post_init__`).
- `to_readonly()` (L1105): builds a read-only view using `replace()` + `ReadOnlyDict`. Not needed for checkpoint restore — a fresh mutable state is required.

### DeterministicRNG (`src/platform/rng.py:L10`)

- `get_state()` (L40): returns `{domain.value: r.getstate() for d, r in _rng_map.items()}` — a plain Python dict mapping `int` → `tuple` (the output of `random.Random.getstate()`).
- `set_state(state)` (L43): restores domain Random instances from a saved dict. Lazily creates `random.Random()` instances for any domain not yet in `_rng_map`.

### rng_checkpoint field on AuthoritativeState (`src/core/state.py:L1043`)

- Declared `rng_checkpoint: Any = None`.
- Populated by phases during `tick_once()`: phases call `rng.get_state()` and place the result in `StateUpdate.rng_checkpoint` (see `src/core/updates.py:L862`). The apply pipeline (`src/engine/apply.py:L286`) commits it to the next AuthoritativeState via `replace()`.
- Therefore, after any completed tick, `state.rng_checkpoint` contains the full `DeterministicRNG` state dict as of the end of that tick. It is NOT stale.
- This means `CanonicalStateHasher.to_canonical_data()` already includes the RNG stream snapshot via `data["rng_checkpoint"] = state.rng_checkpoint` (L105). No separate RNG capture is needed for the checkpoint file.

### Kernel (`src/engine/kernel.py:L35`)

- `__slots__` (L40): includes `"_rng"` — the live `DeterministicRNG`. After tick 0, `kernel._rng` state diverges from `state.rng_checkpoint` only by whatever sampling occurs in the phases before the apply commit. After each completed `tick_once()`, `state.rng_checkpoint` equals the RNG state as of that tick's commit.
- `kernel.state` property (confirmed via E31A investigation at L957): returns the current `AuthoritativeState`. Safe to call between ticks.

### parity ledger (`docs/parity_ledger/infrastructure.yaml:L2419`)

- INFRA-214 (L2419): covers E31A+E31B. Status: `verified`. Lists `ScenarioRuntimeService`, `ScenarioObjectiveState`, `ObjectiveEvaluator`, `STALL_THRESHOLD`, `VictoryCondition`. No mention of checkpoint/restore.
- INFRA-215: does not exist yet. Must be added when E31C is complete.

---

## 2. Mechanics / Engine Constraints

- **Immutability law** (`docs/core/state.md`): `AuthoritativeState` is a frozen dataclass. Mutation only via `replace()`. Restore must produce a fresh `AuthoritativeState` via constructor, not by mutating an existing instance.
- **Authoritative pipeline** (`docs/engine/authoritative_pipeline.md`): All state changes flow through `AuthoritativeApplyPipeline.refine()` inside `kernel.tick_once()`. Checkpoint/restore bypasses this by constructing state externally — that is acceptable because restore precedes any ticks on the restored kernel.
- **Determinism** (`docs/engine/kernel.md`): Two kernels seeded identically and given the same RNG state must produce identical outputs. Checkpoint must capture all fields that affect future tick outcomes. The RNG state (via `state.rng_checkpoint`) and all authoritative world fields are the complete set.
- **Durable state rule** (CLAUDE.md): checkpoint is a read of state, not an authoritative mutation. The saved JSON file is an observation, not a side effect that must go through the apply pipeline.
- **No threading**: `ScenarioRuntimeService` is synchronous. Checkpoint and restore can happen between calls to `step()` or after `pause()` — no locking required.

---

## 3. Serialization Gap Analysis

### Fields covered by `CanonicalStateHasher.to_canonical_data`

All fields below are included and affect determinism:

| Field | Covered | Notes |
|---|---|---|
| `tick` | YES | scalar |
| `seed` | YES | scalar |
| `world_time` | YES | scalar |
| `movement_count` | YES | scalar |
| `maturity` | YES | scalar |
| `last_calamity_tick` | YES | scalar |
| `town_center` | YES | scalar tuple |
| `entities` | YES | via `to_canonical_dict()` |
| `regions` | YES | via `to_canonical_dict()` |
| `local_scars` | YES | via `to_canonical_dict()` |
| `resource_nodes` | YES | via `to_canonical_dict()` |
| `buildings` | YES | via `to_canonical_dict()` |
| `corpses` | YES | via `to_canonical_dict()` |
| `ground_items` | YES | via `to_canonical_dict()` |
| `chests` | YES | via `to_canonical_dict()` |
| `groups` | YES | via `to_canonical_dict()` |
| `home_storage` | YES | via `to_canonical_dict()` |
| `camps` | YES | via `to_canonical_dict()` |
| `global_resources` | YES | dict |
| `periodic_due_ticks` | YES | dict |
| `work_debt` | YES | dict |
| `blocked_tiles` | YES | set serialized as sorted list |
| `town_tiles` | YES | set serialized as sorted list |
| `building_tiles` | YES | dict |
| `rng_checkpoint` | YES | includes full DeterministicRNG stream state |

### Fields NOT covered by `to_canonical_data`

| Field | Gameplay-relevant? | Rationale |
|---|---|---|
| `terrain` | **YES** | Tile types (WALL, FOREST, etc.) affect pathfinding and combat. Must be in checkpoint. |
| `next_node_id` | **YES** | Counter for resource node IDs. Divergence causes ID collision or gaps. |
| `next_entity_id` | **YES** | Counter for entity IDs. Same risk as next_node_id. |
| `rejection_registry` | **YES** | Global counters for discarded transactions (VERIFIED v2: `rejection_registry_tracking`). Affects idempotency guards in future ticks. |
| `pressure_signals` | **MARGINAL** | `Dict[str, float]`. Affects governor behavior if it influences tick budget. Low-frequency update but non-zero risk. Include for full fidelity. |
| `current_mode` | **YES** | `RuntimeMode` enum. If `DEGRADED` or `SAFE`, phases may behave differently. |
| `processed_transaction_ids` | **YES** | Idempotency log (E5.3 Exactly-Once). If not restored, previously processed transactions could be re-applied. |
| `quest_registry` | **YES** | Active quest opportunities. Quest state drives entity behavior after restore. |
| `recent_world_events` | **LOW** | `List[WorldEvent]`. Used for narrative/observability output. Not mechanically load-bearing unless quest or pressure logic reads it. Omit unless proven needed. |
| `transaction_trace` | **NO** | Debug audit log (`List[str]`). Not load-bearing for determinism. Omit from checkpoint. |
| `town_entity_ids` | **NO** | Optimization cache — `__post_init__` rebuilds from entities. Omit. |
| `pending_information_responses` | **NO** | `repr=False, compare=False` — explicitly transient. Omit. |
| `information_source_profiles` | **NO** | `repr=False, compare=False` — transient. Omit. |
| `feature_flags` | **CONTEXTUAL** | `repr=False, compare=False`. If flags are set at construction and constant, they need not be checkpointed. If flags can change during a run, they must be included. For E31C, treat as constant (set at `_build_kernel()`). |

### Conclusion on gap

`CanonicalStateHasher.to_canonical_data` is not sufficient as-is for a restore that guarantees determinism. The checkpoint serializer for E31C must supplement it with: `terrain`, `next_node_id`, `next_entity_id`, `rejection_registry`, `pressure_signals`, `current_mode`, `processed_transaction_ids`, and `quest_registry`.

The simplest approach: the `ScenarioCheckpointer.save()` method calls `to_canonical_data()` and then appends the missing fields in a separate `"extended"` key. Restore reads both. This avoids touching `CanonicalStateHasher` (which has its own compliance IDs and must not diverge from its hash-only purpose).

---

## 4. Parity Ledger Overlap

### INFRA-214 (existing, `infrastructure.yaml:L2419`)

Status: `verified`. Covers E31A (ScenarioRuntimeService lifecycle) and E31B (ObjectiveEvaluator, stall detector). No overlap with checkpoint/restore. No modifications needed to INFRA-214.

### INFRA-215 (new, to be added in the E31C implementation session)

Proposed entry:

```yaml
- id: INFRA-215
  text: "ScenarioRuntimeService checkpoint/restore (Epic 3.1C): ScenarioCheckpointer.save(svc, path) serialises AuthoritativeState (via CanonicalStateHasher.to_canonical_data plus extended fields: terrain, next_node_id, next_entity_id, rejection_registry, pressure_signals, current_mode, processed_transaction_ids, quest_registry) and rng_checkpoint into a named JSON file. ScenarioCheckpointer.restore(path) reconstructs AuthoritativeState and DeterministicRNG, then returns a fresh ScenarioRuntimeService whose kernel is pre-seeded to that state. Determinism AC: checkpoint at tick 25, restore to fresh service, run to tick 50 produces identical events to an uninterrupted run."
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: src/engine/scenario_runtime.py::ScenarioCheckpointer
  proof_type: feature
  test_path: tests/integration/scenarios/test_scenario_runtime_service.py::TestCheckpointRestore::test_checkpoint_restore_determinism
  divergence_note: null
  support_boundary: null
```

---

## 5. Prior Work

### E31A (TCK-20260619-E31A-SCENARIO-SERVICE, stored_artifacts)

- Established `ScenarioRuntimeService` with `_build_kernel()` pattern using `AuthoritativeState(tick=0, seed=0)` and `DeterministicRNG(base_seed=0)`.
- Confirmed `kernel.state` property returns the current `AuthoritativeState` safely between ticks.
- Confirmed `Kernel._stopped` is the only halt mechanism; `pause()` is a cooperative flag on the service layer.
- Key constraint for E31C: the service's `__slots__` must be extended to include a checkpointing hook slot if needed, or `ScenarioCheckpointer` must be a standalone class that reads `svc._kernel.state` and `svc._kernel._rng` directly.

### E31B (TCK-20260619-E31B-OBJECTIVE-FSM, stored_artifacts)

- Added `ObjectiveEvaluator`, `STALL_THRESHOLD`, wired `_evaluate_after_tick()` into the loop.
- Integration test pattern: inject mock kernels via `svc._kernel = mock_kernel`. E31C's determinism test uses a real kernel (marked `@pytest.mark.slow`), so no mock-injection needed for the AC test.
- Established that `svc._kernel` is directly accessible — `ScenarioCheckpointer.save()` can read `svc._kernel.state` without a public API.

---

## 6. Risks and Open Questions

### RQ-1: rng_checkpoint field vs DeterministicRNG.get_state()

After each completed `tick_once()`, `state.rng_checkpoint` contains the domain-separated RNG state dict produced by `rng.get_state()` during that tick's apply phase. This is verified by tracing: `StateUpdate.rng_checkpoint` (updates.py:L862) → `apply.py:L286` → committed to `AuthoritativeState.rng_checkpoint`. On restore, this dict is passed to `DeterministicRNG.set_state()` to reconstruct the stream.

**Risk**: If a phase samples RNG *after* the apply commit within the same `tick_once()` call, the restored stream diverges by those samples. Investigation shows apply is the last substantive step before `tick_once()` returns (kernel.py phases: resolution → cleanup → advancement → persistence). Persistence writes telemetry, not RNG draws. Risk is LOW but should be verified by the determinism test.

### RQ-2: Restore path — frozen dataclass construction

`AuthoritativeState` has no `from_dict()` factory. Restore must call `AuthoritativeState(tick=..., seed=..., ...)` with all fields. Sub-objects (EntityState, RegionState, etc.) must be deserialized from their `to_canonical_dict()` output. Each type must have a `from_canonical_dict()` or equivalent. If any type lacks this, restore is blocked.

**Mitigation**: The AC test can use a scenario with minimal entities (or no entities at tick 25). If `to_canonical_dict()` methods exist (they're called in the canonical hasher without error), there must be a corresponding deserialize path — but it may not be named `from_canonical_dict`. Scoping the plan phase must confirm this for each collection type before committing to a full-fidelity restore strategy. Alternatively, use `pickle` or `copy.deepcopy` of the live state at checkpoint time, converting only scalars to JSON for the file format.

**Safer approach**: Use `pickle` for the in-memory checkpoint blob and JSON only for the metadata header (tick, hash). This avoids the `from_canonical_dict` gap entirely and guarantees identity-preserving round-trip. Trade-off: pickle is not human-readable and has version compatibility risk.

### RQ-3: _spec round-trip

`ScenarioRuntimeService` requires a `SimulationScenarioDefinition` spec on construction. On restore, the caller must supply the same spec (or the checkpoint file must include enough info to reconstruct it). For E31C, the checkpoint file should include the `spec.id` as a validation field; the caller provides the full spec at restore time.

### RQ-4: __slots__ extension

`ScenarioRuntimeService.__slots__` does not include a checkpoint slot. `ScenarioCheckpointer` as a standalone class (not a method on the service) avoids touching `__slots__`. This is the preferred design — it respects the service's single-responsibility boundary.

### RQ-5: tick counter divergence

The service's `self._tick` (L134) is the service-layer tick count; `kernel.state.tick` is the authoritative tick. On restore, both must be set to the checkpoint tick. If `ScenarioCheckpointer.restore()` injects the kernel directly into `svc._kernel`, it must also set `svc._tick`.

---

## 7. Anti-Drift Hazards

- **Do NOT modify `CanonicalStateHasher.to_canonical_data`** — it has 13 compliance IDs (INFRA-119 through INFRA-133) and must remain hash-identical. The checkpoint serializer wraps it, it does not replace it.
- **Do NOT bypass `AuthoritativeState.__post_init__`** — it auto-advances ID counters and clears caches. Any restore must call the constructor, not `object.__setattr__` directly on a new instance.
- **Do NOT read `kernel._rng` directly in production code** — it is a private slot. Restore the RNG via `DeterministicRNG.set_state()` on a fresh `DeterministicRNG(base_seed=0)` instance, using the value in `state.rng_checkpoint`.
- **Do NOT mark the determinism test non-slow** — it runs 50 ticks twice with a real kernel. It will be slow.
- **Do NOT add checkpoint logic into `ScenarioRuntimeService` itself** — keep it in `ScenarioCheckpointer` to avoid slot bloat and preserve E31D (REST API) clean separation.
- **Do NOT skip INFRA-215** — the parity ledger entry is a Definition-of-Done requirement for the implementation session.

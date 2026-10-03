---
status: active
artifact_type: plan
ticket_id: TCK-20260619-E31C-CHECKPOINT
date: 2026-06-21
---

# Plan: TCK-20260619-E31C-CHECKPOINT
## Epic 3.1C · Scenario Checkpoint / Restore

---

## Design Decision: deepcopy-based checkpoint (not full JSON deserialisation)

`AuthoritativeState` sub-objects (`EntityState`, `RegionState`, etc.) have no
`from_canonical_dict()` constructors. Full JSON round-trip deserialization is
out of scope for E31C and would require touching ~20 frozen dataclass types.

**Chosen approach**: The checkpoint file stores a JSON metadata header (tick,
spec_id, rng_checkpoint) plus a `pickle`-serialised blob of the live
`AuthoritativeState`. On restore, the blob is unpickled directly — this
preserves every field with zero type-mapping risk. `CanonicalStateHasher`
is not touched.

**Why this is safe**: The checkpoint file is consumed only by
`ScenarioCheckpointer.restore()` in the same Python version (same session or
same deployment). No cross-version portability is required by E31C scope.

**Trade-off documented**: Human-readability and cross-version compatibility are
sacrificed. The file header (JSON) gives human-readable metadata; the payload
is binary. This is documented in the INFRA-215 parity entry.

---

## Ordered Steps

### Step 1 — Create `src/engine/scenario_checkpoint.py`

**File**: `src/engine/scenario_checkpoint.py`

Implement `ScenarioCheckpointer` as a standalone class (no `__slots__` changes
to `ScenarioRuntimeService`):

```python
# Compliance IDs: INFRA-215
"""ScenarioCheckpointer — checkpoint/restore for ScenarioRuntimeService."""
from __future__ import annotations
import json
import pickle
import struct
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.scenario_runtime import ScenarioRuntimeService
    from src.scenarios.schema import SimulationScenarioDefinition


class ScenarioCheckpointer:
    """Save/restore ScenarioRuntimeService state across process restarts."""

    @staticmethod
    def save(svc: "ScenarioRuntimeService", path: str | Path) -> None:
        """Serialise current kernel state to checkpoint file at *path*.

        File format (binary):
          - 4-byte little-endian uint32: length of JSON header in bytes
          - JSON header bytes (UTF-8): {"tick": N, "spec_id": "...", "rng_checkpoint": ...}
          - Remainder: pickle blob of AuthoritativeState

        Raises RuntimeError if the kernel has not been started.
        """
        if svc._kernel is None:
            raise RuntimeError(
                "Cannot checkpoint: ScenarioRuntimeService has not been started."
            )
        state = svc._kernel.state
        header = {
            "tick": svc.tick,
            "spec_id": svc._spec.id,
            "rng_checkpoint": state.rng_checkpoint,
        }
        header_bytes = json.dumps(header).encode("utf-8")
        payload = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(struct.pack("<I", len(header_bytes)))
            f.write(header_bytes)
            f.write(payload)

    @staticmethod
    def restore(
        path: str | Path,
        spec: "SimulationScenarioDefinition",
    ) -> "ScenarioRuntimeService":
        """Restore a ScenarioRuntimeService from a checkpoint file.

        The restored service has its kernel pre-seeded to the checkpoint state.
        Calling .start(tick_limit=N) continues from the checkpoint tick.

        Raises:
            FileNotFoundError: if *path* does not exist.
            ValueError: if the checkpoint spec_id does not match *spec*.
        """
        from src.engine.scenario_runtime import ScenarioRuntimeService
        from src.config.profiles import RuntimeProfile, HardwareClass
        from src.platform.rng import DeterministicRNG
        from src.engine.kernel import Kernel

        path = Path(path)
        with path.open("rb") as f:
            header_len = struct.unpack("<I", f.read(4))[0]
            header = json.loads(f.read(header_len).decode("utf-8"))
            state = pickle.loads(f.read())

        if header["spec_id"] != spec.id:
            raise ValueError(
                f"Checkpoint spec_id {header['spec_id']!r} does not match "
                f"supplied spec id {spec.id!r}."
            )

        # Reconstruct RNG from the checkpoint embedded in state
        rng = DeterministicRNG(base_seed=0)
        if state.rng_checkpoint is not None:
            rng.set_state(state.rng_checkpoint)

        profile = RuntimeProfile(
            name=spec.id,
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=512,
            max_cpu_percent=100.0,
            max_worker_count=0,
            max_queue_depth=1000,
            max_replay_buffer_kb=64,
            max_observability_budget_percent=5.0,
            max_tick_budget_ms=200.0,
        )
        kernel = Kernel(profile, state, rng, flags={"no_replay": True}, run_id=f"restored_{spec.id}")

        svc = ScenarioRuntimeService(spec)
        svc._kernel = kernel
        svc._tick = header["tick"]
        return svc
```

**AC mapping**: This step satisfies all three ACs (checkpoint structure, rng_checkpoint
in file, determinism possible once step 2 tests verify it).

**Scope guards**:
- Do NOT modify `CanonicalStateHasher` (compliance IDs INFRA-119–133).
- Do NOT add `checkpoint` or `restore` methods to `ScenarioRuntimeService`.
- Do NOT touch `__slots__` of `ScenarioRuntimeService`.

---

### Step 2 — Add `# Compliance IDs: INFRA-215` to `src/engine/scenario_runtime.py`

**File**: `src/engine/scenario_runtime.py`

Add `INFRA-215` to the top compliance comment block so parity tracking is
wired to the implementation file (the service owns `ScenarioCheckpointer`
conceptually even though the class lives in a sibling file).

Add an import alias in `scenario_runtime.py` so callers can import
`ScenarioCheckpointer` from a single entry point:

```python
from src.engine.scenario_checkpoint import ScenarioCheckpointer  # E31C
```

Place this import at the bottom of the module-level imports (after the existing
`from __future__ import annotations` block and before the class definitions).

**Scope guards**:
- No changes to any existing class or function.
- Import must be inside the module body (not TYPE_CHECKING guard) so
  `from src.engine.scenario_runtime import ScenarioCheckpointer` works in tests.

---

### Step 3 — Create `tests/unit/engine/test_scenario_checkpointer.py`

**File**: `tests/unit/engine/test_scenario_checkpointer.py`

Unit tests using mock services (no real kernel). Cover:
1. `save()` raises `RuntimeError` when kernel is None.
2. `restore()` raises `ValueError` on spec_id mismatch.
3. `save()` / `restore()` round-trip preserves tick counter (real kernel, `@pytest.mark.slow`).
4. Checkpoint file contains `rng_checkpoint` in header.
5. `test_infra_215_parity_entry_exists()` — guard that INFRA-215 is in parity ledger.
6. `test_rng_checkpoint_populated_after_tick()` — guard that phases write rng_checkpoint.

---

### Step 4 — Add `TestCheckpointRestore` to integration test file

**File**: `tests/integration/scenarios/test_scenario_runtime_service.py`

Append `TestCheckpointRestore` class after `TestTerminalStateGuards`. Tests:
1. `test_checkpoint_restore_determinism` (`@pytest.mark.slow`) — checkpoint at
   tick 25, restore, run to tick 50, compare `CanonicalStateHasher.get_hash()`
   of final state between reference run and restored run. (Event recorder API
   is not available; use state hash comparison instead — the AC says "identical
   events" but the verifiable proxy is identical final state hash.)
2. `test_checkpoint_file_contains_rng_checkpoint` — verify header field.
3. `test_restore_sets_service_tick` — restored service tick matches saved tick.
4. `test_rng_checkpoint_populated_after_tick` (`@pytest.mark.slow`) — real kernel.
5. `test_save_before_start_raises` — save on unstarted service.

---

### Step 5 — Add INFRA-215 to parity ledger

**File**: `docs/parity_ledger/infrastructure.yaml`

Append after INFRA-214 (line 2428):

```yaml
- id: INFRA-215
  text: "ScenarioRuntimeService checkpoint/restore (Epic 3.1C): ScenarioCheckpointer.save(svc, path) writes a binary checkpoint file containing a JSON header (tick, spec_id, rng_checkpoint) and a pickle blob of AuthoritativeState. ScenarioCheckpointer.restore(path, spec) unpickles the state, reconstructs DeterministicRNG via set_state(rng_checkpoint), builds a fresh Kernel, and returns a pre-seeded ScenarioRuntimeService. Determinism AC: checkpoint at tick 25, restore, run to tick 50 produces CanonicalStateHasher.get_hash()-identical state to an uninterrupted run."
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: src/engine/scenario_checkpoint.py::ScenarioCheckpointer
  proof_type: feature
  test_path: tests/integration/scenarios/test_scenario_runtime_service.py::TestCheckpointRestore::test_checkpoint_restore_determinism
  divergence_note: null
  support_boundary: null
```

---

### Step 6 — Update ticket implementation notes

**File**: `tickets/inprogress/TCK-20260619-E31C-CHECKPOINT.md`

Fill `## Implementation Notes` with what was built.

---

## Dependency Map

```
Step 1 → Step 2 (import alias requires Step 1 to exist)
Step 1 → Step 3 (unit tests import ScenarioCheckpointer)
Step 1+2 → Step 4 (integration tests import from scenario_runtime)
Step 4 → Step 5 (parity entry references test path from Step 4)
All steps → Step 6 (notes filled last)
```

---

## Acceptance Criteria → Steps Mapping

| AC | Steps |
|---|---|
| Checkpoint at tick 25, restore, run to tick 50 → identical to non-checkpoint run | Step 1, Step 4 (test_checkpoint_restore_determinism) |
| `test_checkpoint_restore_determinism` passes | Step 4 |
| `state.rng_checkpoint` is included in checkpoint file | Step 1 (header), Step 3/4 (tests) |

---

## Scope Guards (global)

- Do NOT modify `CanonicalStateHasher` or any existing hasher class.
- Do NOT modify `ScenarioRuntimeService` class body, `__slots__`, or methods.
- Do NOT modify `AuthoritativeState` or any sub-object types.
- Do NOT modify `DeterministicRNG` (it already has the needed `get_state`/`set_state`).
- Do NOT add incremental checkpointing, rotation, or cleanup logic.
- Do NOT implement checkpoint-from-spec-only restore (caller always supplies spec).

---

## Deviations

**Review correction (pre-implementation)**: `Kernel()` in `restore()` must receive `run_id=f"restored_{spec.id}"` to suppress the `Domain.INIT` RNG draw in `Kernel.__init__` (line ~120 of kernel.py). Without this, the INIT-domain stream advances by 1 after `set_state()`, breaking the determinism AC. Plan updated before implementation began.

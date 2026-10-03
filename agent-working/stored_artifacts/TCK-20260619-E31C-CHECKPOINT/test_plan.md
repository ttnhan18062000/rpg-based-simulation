---
status: active
artifact_type: test_plan
ticket_id: TCK-20260619-E31C-CHECKPOINT
date: 2026-06-21
---

# Test Plan: TCK-20260619-E31C-CHECKPOINT

## 1. Regression Surface

The following existing tests must pass without modification after E31C implementation:

### Unit — scenario runtime service
```
tests/unit/engine/test_scenario_runtime_service.py
```
Tests: `TestStart`, `TestPause`, `TestResume`, `TestStep`, `TestAbort`, `TestAliveEntityCount`.
Risk: `ScenarioCheckpointer` must not alter `ScenarioRuntimeService.__slots__` or change `_build_kernel()` behavior.

### Integration — scenario runtime service (E31B)
```
tests/integration/scenarios/test_scenario_runtime_service.py
```
Classes: `TestObjectiveMet`, `TestObjectiveFailed`, `TestStallDetector`, `TestNoVictoryConditions`, `TestTerminalStateGuards`.
Risk: same as above — E31C adds a new class `TestCheckpointRestore` to this file; existing classes must remain untouched.

### Canonical state hasher
```
tests/unit/engine/test_checkpoint.py  (if it exists — check before plan phase)
```
`CanonicalStateHasher.to_canonical_data` must remain bit-identical. `ScenarioCheckpointer` may call it but must not modify it.

### RNG
```
tests/unit/platform/test_rng.py  (if it exists — check before plan phase)
```
`DeterministicRNG.get_state()` / `set_state()` round-trip must remain correct.

---

## 2. New Tests Required

### File: `tests/integration/scenarios/test_scenario_runtime_service.py`

Add class `TestCheckpointRestore` after the existing `TestTerminalStateGuards` class.

#### AC1 — Primary determinism test (must pass)

```python
class TestCheckpointRestore:

    @pytest.mark.slow
    def test_checkpoint_restore_determinism(self, tmp_path):
        """
        Checkpoint at tick 25, restore to fresh service, run to tick 50.
        Events from ticks 26-50 must be identical to ticks 26-50 of an
        uninterrupted run.

        AC: test_checkpoint_restore_determinism passes.
        AC: state.rng_checkpoint is present in checkpoint JSON.
        """
        from src.engine.scenario_runtime import ScenarioRuntimeService, ScenarioCheckpointer

        spec = _make_spec()
        checkpoint_path = tmp_path / "tick25.json"

        # --- Reference run (uninterrupted, record events 26-50) ---
        ref_svc = ScenarioRuntimeService(spec)
        ref_svc.start(tick_limit=50)
        ref_events = list(ref_svc._kernel._event_recorder.get_all())  # adjust API to actual
        ref_svc.abort()

        # --- Checkpoint run ---
        ckpt_svc = ScenarioRuntimeService(spec)
        ckpt_svc.start(tick_limit=25)
        ScenarioCheckpointer.save(ckpt_svc, checkpoint_path)

        # Validate checkpoint file structure
        import json
        blob = json.loads(checkpoint_path.read_text())
        assert blob["tick"] == 25
        assert "rng_checkpoint" in blob["state"]   # or blob["extended"] — adjust to impl
        assert blob["state"]["rng_checkpoint"] is not None

        # Restore and continue
        restored_svc = ScenarioCheckpointer.restore(checkpoint_path, spec)
        restored_svc.start(tick_limit=50)
        restored_events = list(restored_svc._kernel._event_recorder.get_all())
        restored_svc.abort()

        # Events from ticks 26-50 must match
        ref_late = [e for e in ref_events if e.tick > 25]
        res_late = [e for e in restored_events if e.tick > 25]
        assert len(ref_late) == len(res_late), (
            f"Event count mismatch: ref={len(ref_late)}, restored={len(res_late)}"
        )
        for i, (r, s) in enumerate(zip(ref_late, res_late)):
            assert r.event_type == s.event_type, f"Event type mismatch at index {i}"
            assert r.tick == s.tick, f"Tick mismatch at index {i}"
```

**Note**: The exact event recorder API (`_event_recorder.get_all()`) must be confirmed during the plan phase. If no event-list accessor exists, compare `kernel.state` hashes at tick 50 using `CanonicalStateHasher.get_hash()` with `reason="certification"` instead.

#### AC2 — rng_checkpoint field in file

```python
    def test_checkpoint_file_contains_rng_checkpoint(self, tmp_path):
        """state.rng_checkpoint is non-None in checkpoint file."""
        from src.engine.scenario_runtime import ScenarioRuntimeService, ScenarioCheckpointer
        import json

        svc = _make_service()
        svc.start(tick_limit=5)
        path = tmp_path / "ckpt.json"
        ScenarioCheckpointer.save(svc, path)
        svc.abort()

        blob = json.loads(path.read_text())
        # rng_checkpoint must be present and non-null
        rng_ckpt = blob.get("state", {}).get("rng_checkpoint") or blob.get("rng_checkpoint")
        assert rng_ckpt is not None
```

#### AC3 — Restore produces correct tick counter

```python
    def test_restore_sets_service_tick(self, tmp_path):
        """Restored service._tick matches the checkpoint tick."""
        from src.engine.scenario_runtime import ScenarioRuntimeService, ScenarioCheckpointer

        svc = _make_service()
        svc.start(tick_limit=10)
        path = tmp_path / "ckpt.json"
        ScenarioCheckpointer.save(svc, path)
        svc.abort()

        restored = ScenarioCheckpointer.restore(path, _make_spec())
        assert restored.tick == 10
```

#### AC4 — Restore from pre-tick-0 save (edge case)

```python
    def test_save_before_start_raises_or_returns_tick_zero(self, tmp_path):
        """Saving before any tick runs produces a valid tick-0 checkpoint or raises clearly."""
        from src.engine.scenario_runtime import ScenarioRuntimeService, ScenarioCheckpointer

        svc = _make_service()
        path = tmp_path / "ckpt.json"
        # Either succeeds with tick=0 or raises a documented error
        try:
            ScenarioCheckpointer.save(svc, path)
        except RuntimeError as e:
            assert "not started" in str(e).lower()
```

### File: `tests/unit/engine/test_scenario_checkpointer.py` (new file)

Unit tests for `ScenarioCheckpointer` in isolation (no real kernel, mock or minimal state).

#### Unit — save produces valid JSON

```python
def test_save_writes_json_with_expected_keys(tmp_path):
    """save() produces a JSON file with tick, spec_id, and state keys."""
    import json
    from unittest.mock import MagicMock
    from src.engine.scenario_runtime import ScenarioCheckpointer

    mock_svc = MagicMock()
    mock_svc.tick = 7
    mock_svc._spec.id = "test_scenario"
    mock_svc._kernel.state.rng_checkpoint = {"1": "dummy"}
    # Minimal state mock; to_canonical_data will be called
    # Patch CanonicalStateHasher.to_canonical_data to avoid full state walk
    with patch("src.engine.scenario_runtime.CanonicalStateHasher.to_canonical_data") as mock_canon:
        mock_canon.return_value = {"tick": 7, "rng_checkpoint": {"1": "dummy"}}
        path = tmp_path / "ckpt.json"
        ScenarioCheckpointer.save(mock_svc, path)

    blob = json.loads(path.read_text())
    assert blob["tick"] == 7
    assert blob["spec_id"] == "test_scenario"
    assert "state" in blob
```

#### Unit — restore raises on tick mismatch

```python
def test_restore_raises_on_spec_id_mismatch(tmp_path):
    """restore() raises ValueError if blob spec_id differs from supplied spec."""
    import json
    from src.engine.scenario_runtime import ScenarioCheckpointer
    from src.scenarios.schema import SimulationScenarioDefinition

    path = tmp_path / "ckpt.json"
    path.write_text(json.dumps({"tick": 5, "spec_id": "scenario_a", "state": {}}))
    spec = SimulationScenarioDefinition(
        id="scenario_b",
        world_composition="frontier_living_world",
        perspective="hero_guild_perspective",
    )
    with pytest.raises(ValueError, match="spec_id"):
        ScenarioCheckpointer.restore(path, spec)
```

#### Unit — save when kernel is None raises clearly

```python
def test_save_raises_when_kernel_none(tmp_path):
    """save() raises RuntimeError when the service has not been started."""
    from src.engine.scenario_runtime import ScenarioRuntimeService, ScenarioCheckpointer

    svc = ScenarioRuntimeService(_make_spec())
    with pytest.raises(RuntimeError, match="not started"):
        ScenarioCheckpointer.save(svc, tmp_path / "ckpt.json")
```

---

## 3. Scoped Pytest Commands

Run only the affected domain — do NOT run the full suite.

```bash
# Fast: unit tests for the new checkpointer class (no real kernel)
pytest tests/unit/engine/test_scenario_checkpointer.py -v

# Medium: existing scenario runtime unit tests (regression guard)
pytest tests/unit/engine/test_scenario_runtime_service.py -v

# Integration: E31B regression + new E31C tests (excludes slow)
pytest tests/integration/scenarios/test_scenario_runtime_service.py -v -m "not slow"

# Slow: full determinism AC test (real kernel, 50 ticks × 2)
pytest tests/integration/scenarios/test_scenario_runtime_service.py::TestCheckpointRestore::test_checkpoint_restore_determinism -v -s

# All E31C-relevant tests combined (exclude slow for CI)
pytest tests/unit/engine/test_scenario_checkpointer.py tests/unit/engine/test_scenario_runtime_service.py tests/integration/scenarios/test_scenario_runtime_service.py -v -m "not slow"
```

---

## 4. Anti-Drift Test Guards

### Guard 1 — CanonicalStateHasher output must not change

After E31C, verify:
```bash
pytest tests/unit/engine/test_checkpoint.py -v
```
If no such test file exists, add a test that calls `CanonicalStateHasher.to_canonical_data()` on a known state and asserts the returned dict keys match the expected set.

### Guard 2 — INFRA-215 parity entry must exist before merge

Add a test or CI assertion:
```python
def test_infra_215_parity_entry_exists():
    """INFRA-215 must be present in infrastructure.yaml (E31C parity requirement)."""
    import yaml
    from pathlib import Path
    ledger = yaml.safe_load(
        (Path(__file__).parents[3] / "docs/parity_ledger/infrastructure.yaml").read_text()
    )
    ids = {e["id"] for e in ledger if isinstance(e, dict)}
    assert "INFRA-215" in ids, "INFRA-215 not found in parity ledger — add it before merging E31C"
```

Place in `tests/unit/engine/test_scenario_checkpointer.py`.

### Guard 3 — rng_checkpoint non-None after any tick

This guards against phases failing to populate `StateUpdate.rng_checkpoint`:
```python
def test_rng_checkpoint_populated_after_tick():
    """After one real tick, state.rng_checkpoint must be non-None."""
    from src.engine.scenario_runtime import ScenarioRuntimeService
    svc = ScenarioRuntimeService(_make_spec())
    svc.step()
    assert svc._kernel.state.rng_checkpoint is not None, (
        "rng_checkpoint is None after tick 1 — phases are not writing StateUpdate.rng_checkpoint"
    )
    svc.abort()
```

Mark this `@pytest.mark.slow` (uses real kernel) and place it in `TestCheckpointRestore`.

### Guard 4 — Restored service cannot re-apply already-processed transactions

If `processed_transaction_ids` is excluded from checkpoint, test that the idempotency guard does not break post-restore. If included, test that a duplicate transaction after restore is silently dropped:
```python
# Placeholder — exact implementation depends on whether processed_transaction_ids
# is included in the checkpoint. Resolve during plan phase.
```

### Guard 5 — save/restore round-trip preserves tick counter identity

```python
@pytest.mark.slow
def test_restored_tick_is_identical_to_checkpoint_tick(tmp_path):
    from src.engine.scenario_runtime import ScenarioRuntimeService, ScenarioCheckpointer
    svc = _make_service()
    svc.start(tick_limit=15)
    saved_tick = svc.tick
    path = tmp_path / "ckpt.json"
    ScenarioCheckpointer.save(svc, path)
    svc.abort()

    restored = ScenarioCheckpointer.restore(path, _make_spec())
    assert restored.tick == saved_tick
    assert restored._kernel.state.tick == saved_tick
```

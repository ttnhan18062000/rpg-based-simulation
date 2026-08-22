---
status: active
layer: engine
authority: P1
audience: developer
---

# Regression & Verification: Hardening the Engine

To maintain high architectural integrity, the simulation employs a strict verification pipeline centered on **Absolute Determinism** and **Observable AI**.

---

## 1. The Headless Regression Runner

The `HeadlessRunner` (`src/testing/headless_regression_runner.py`) is the authoritative tool for verifying simulation stability. It executes the engine in an isolated, multi-threaded but deterministic environment.

### Captured Artifacts
1.  **Replay (`replay.json`)**: A tick-by-tick record of all action proposals and world state hashes.
2.  **Cognition Graphs (`cognition_e[id].json`)**: A JSON export of the "Mind Map" for tracked entities.
3.  **Manifest (`manifest.json`)**: A summary of the run duration, seed, and success status.
4.  **Renders (`renders/*.png`)**: Deterministic, hash-verified world-state snapshots produced by
    `src/rendering/render.py::render(state, out_path)`. Stored under
    `data/runs/{run_id}/renders/`. See §4 below for the render-specific determinism guarantee.

---

## 2. Using the Test Harness

The `scripts/test_harness.py` provides a CLI interface for the regression runner.

### Common Commands
```bash
# Run a basic 200-tick regression test
python scripts/test_harness.py --seed 42 --ticks 200

# Run with custom entity counts and multiple threads
python scripts/test_harness.py --seed 777 --ticks 500 --entities 20 --workers 8

# Run the specific strategic regression suite
export PYTHONPATH=.
pytest tests/e2e/strategy/test_strategic_regression.py
```

---

## 3. Log Rotation Infrastructure

Simulation runs (especially with many ticks) generate significant disk artifacts. The engine implements automatic **Log Rotation**:

- **Policy**: Only the last `N` simulation runs are preserved in `logs/regression/`.
- **Configuration**: Set `max_regression_runs` in `SimulationConfig` (Default: 10).
- **Automation**: The `HeadlessRunner` executes rotation at the start of every run, pruning the oldest directories based on creation time.

---

## 4. Determinism Check (Bors Check)

To verify that the engine remains deterministic across code changes:
1. Run a simulation with `--seed X` and capture the Replay hash.
2. Run again with `--seed X`.
3. The Replay hashes **MUST** be byte-identical.

We enforce this via `TestStrategicRegression::test_headless_run_determinism`.

**Render-specific instance**: `src/rendering/render.py::render(state, out_path)` is a pure,
read-only function of `AuthoritativeState` content — no wall-clock dependency, no reliance on
hash-randomized ordering. Three independent `render()` calls against content-equal state produce
byte-identical PNG output, verified by hashing the rendered PNG bytes directly (`state.terrain` is
excluded from both `StateFingerprinter` and `CanonicalStateHasher`, so a `state_hash`-based check
would not catch a render regression). Enforced via
`tests/unit/rendering/test_render_core.py::test_render_golden_hash_bit_identical_across_three_independent_runs`.
A `DirtySet`-incremental render (`src/rendering/incremental.py::IncrementalRenderer`) must produce
pixel-identical output to a full non-incremental `render()` of the same final state, enforced via
`tests/unit/rendering/test_render_incremental.py::test_dirty_set_incremental_render_pixel_identical_to_full_rerender`.

---

## 5. Visual Verification: Cognition Tool

For visual auditing of strategic decisions:
1. Open `tools/viz_strategy.html` in a web browser.
2. Drag and drop any `cognition_e[id].json` file from your `logs/` directory.
3. Use the **Dagre (Top-Down)** layout to see the hierarchy of Directives, Projects, and Objectives.

---

## 6. The Arena Regression Harness

The `ArenaRunner` (`src/engine/arena/runner.py`) is used for statistical verification of combat and movement behaviors. It eliminates the overhead of full world-loading and focuses on high-frequency interaction scenarios.

### Resource Boundaries & Stability
To protect the system from memory leaks and execution deadlocks, the test infrastructure implements a multi-tier watchdog system:

1.  **Virtual Memory Cap (2.0GB)**: Enforced via `resource.setrlimit` at the OS level. Prevents runaway memory allocation from locking the system.
2.  **SIGKILL Hang Watchdog**: A background daemon monitors the wall-clock duration of every test. If a test exceeds its timeout (Default: **300s**, `@pytest.mark.slow`: **600s**), the entire process is immediately terminated via `SIGKILL`.
3.  **Process Cleanup Utility**: If orphaned test workers are suspected, run the following to safely terminate them:
    ```bash
    python3 scripts/cleanup_tests.py
    ```

### Execution
```bash
# Run the full regression suite with the watchdog and aligned registries
PYTHONPATH=. pytest tests/unit/core/gameplay/test_item_contracts.py tests/unit/combat/test_ranged_combat.py
```

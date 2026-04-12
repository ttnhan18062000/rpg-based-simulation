# Regression & Verification: Hardening the Engine

To maintain high architectural integrity, the simulation employs a strict verification pipeline centered on **Absolute Determinism** and **Observable AI**.

---

## 1. The Headless Regression Runner

The `HeadlessRunner` (`src/testing/headless_regression_runner.py`) is the authoritative tool for verifying simulation stability. It executes the engine in an isolated, multi-threaded but deterministic environment.

### Captured Artifacts
1.  **Replay (`replay.json`)**: A tick-by-tick record of all action proposals and world state hashes.
2.  **Cognition Graphs (`cognition_e[id].json`)**: A JSON export of the "Mind Map" for tracked entities.
3.  **Manifest (`manifest.json`)**: A summary of the run duration, seed, and success status.

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

---

## 5. Visual Verification: Cognition Tool

For visual auditing of strategic decisions:
1. Open `tools/viz_strategy.html` in a web browser.
2. Drag and drop any `cognition_e[id].json` file from your `logs/` directory.
3. Use the **Dagre (Top-Down)** layout to see the hierarchy of Directives, Projects, and Objectives.

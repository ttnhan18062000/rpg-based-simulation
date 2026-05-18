# Certification Harness Architecture

The Certification Harness is a proof-oriented runner designed to verify the architectural integrity and logic compliance of the RPG Engine.

## Core Principles

1.  **Absolute Determinism**: Every run with the same seed must produce the exact same outcome hash.
2.  **Resource Boundaries**: Every tick must execute within a defined budget (e.g., 100ms) and memory cap.
3.  **Auditability**: Every side effect is recorded in a machine-readable "Proof Bundle".

## Implementation Details

### 1. Hardened Serialization
To prevent `RecursionError` and handle cyclical references in complex state objects (like `AuthoritativeState` with internal caches), the harness uses a custom `safe_asdict` utility.

-   **Depth-Limited**: Prevents infinite recursion by capping object traversal.
-   **Cycle Detection**: Tracks visited objects to identify and break circular references.
-   **Private Field Suppression**: Automatically skips fields starting with `_` to avoid serializing internal caches and temporary state.

### 2. Watchdog System
The harness employs a multi-tier watchdog to protect against simulation hangs:
-   **Tick Timeout**: Each tick is executed in a thread pool with a timeout based on the profile's `max_tick_budget_ms`.
-   **Fast-Tick Detection**: Monitors for "ghost" simulations where many ticks execute in <0.1ms, potentially indicating a loop logic failure.

### 3. Conformance Evaluation
After execution, the `ConformanceEvaluator` checks:
-   **Reproducibility**: Runs the scenario a second time to ensure the final state hash matches.
-   **Hardware Class**: Validates that performance metrics (RSS, compute) are consistent with the detected hardware tier.
-   **Stop Conditions**: Records whether the run finished normally, reached a timeout, or triggered a watchdog.

## Usage

```python
harness = CertificationHarness(profile, output_dir="reports/my_test")
result = harness.run_scenario(scenario_id, state, expectations, ticks=100)
assert result.conformance_passed
```

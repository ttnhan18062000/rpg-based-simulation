# Investigation - TCK-20260529-OBS-PHASE19

## Key Findings

1. **Current Mode & Config Design**:
   - `src/observability/config.py` defines `ObservabilityMode` as an Enum with values: `OFF`, `LIGHT`, `DEBUG`, `CERTIFICATION`, `LONG_RUN`.
   - The user requested presets: `OFF`, `LIGHT`, `NORMAL`, `FULL`, `RESEARCH`, `DEBUG`.
   - We need to merge them or ensure the new presets mapped are supported while preserving existing modes for backward compatibility.
   - Specifically:
     - `OFF`, `LIGHT`, `DEBUG` exist.
     - `NORMAL`, `FULL`, `RESEARCH` are new presets.
     - `CERTIFICATION` and `LONG_RUN` should map safely to flags as well.
   
2. **Hot-Path vs Post-Run Separation**:
   - The heavy analysis modules are located under `src/observability/anomaly/`, `src/observability/cognition/`, and `src/observability/reporting/` or similar.
   - Hot-path modules (such as `src/engine/observability.py`, `src/observability/event_extractor.py`, `src/observability/event_recorder.py`) must never import modules from these post-run directories.
   - We must design static analysis tests using AST parsing or simple import matching to enforce this boundary.

3. **Feature Flags Registry design**:
   - Since we want a thread-safe flat registry, we will implement methods inside `ObservabilityConfig` to query each individual flag (e.g. `ObservabilityConfig.is_runtime_profiling_enabled()`, `ObservabilityConfig.is_raw_events_enabled()`, etc.).
   - These methods will:
     - Check direct flag overrides first.
     - Check environment variables (`SIM_OBS_...` or `RPG_OBS_...`).
     - Resolve the base mode via `get_mode()`, and map the mode preset to the flag's default boolean value.

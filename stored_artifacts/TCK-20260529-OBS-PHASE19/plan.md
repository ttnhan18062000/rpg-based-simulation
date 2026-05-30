# Plan - TCK-20260529-OBS-PHASE19

## Goal
Implement Phase 19 of the Observability & Behavior Profiling roadmap. Establish architectural boundaries, feature flags, mode preset mappings, a hot-path safety contract, and corresponding unit and architecture-level tests.

## Approach
We will utilize **Approach A** (thread-safe flat registry inside `src/observability/config.py`).
This keeps the configuration lightweight, leverages the existing thread-safe lock pattern in `ObservabilityConfig`, and separates observability from optimization rollout layers cleanly.

## Step-by-Step Execution Plan

### Step 1: Write Documentation
1. Create `docs/architecture/observability_behavior_profiling_boundary.md`
   - Define: runtime profiling, raw simulation event, behavior event, behavior timeline, behavior episode, behavior metric, behavior finding, behavior insight, scorecard, run comparison.
   - Explain boundaries: hot-path (cheap timing, counters, queue appends) vs. async (normalizers, timelines) vs. post-run (episodes, scorecards, comparisons, insights).
2. Create `docs/architecture/observability_hot_path_safety_contract.md`
   - List what is allowed in hot-path and what is forbidden (JSON serialization, blocking I/O, large deepcopy, heavy analysis).

### Step 2: Update Configuration and Flags
1. Update `ObservabilityMode` in `src/observability/config.py` to include presets:
   - `OFF`, `LIGHT`, `NORMAL`, `FULL`, `RESEARCH`, `DEBUG`
   - Map existing modes to new presets or retain compatibility as needed.
2. Define the new independent configuration feature flags:
   - `OBS_RUNTIME_PROFILING`
   - `OBS_RAW_EVENTS`
   - `OBS_LIVE_STREAM`
   - `OBS_EVENT_RECORDER`
   - `OBS_ENTITY_TIMELINE`
   - `OBS_BEHAVIOR_NORMALIZATION`
   - `OBS_BEHAVIOR_TIMELINE`
   - `OBS_BEHAVIOR_EPISODES`
   - `OBS_BEHAVIOR_METRICS`
   - `OBS_BEHAVIOR_PATTERNS`
   - `OBS_BEHAVIOR_SCORECARDS`
   - `OBS_COHORT_ANALYSIS`
   - `OBS_RUN_COMPARISON`
   - `OBS_INSIGHT_GENERATION`
   - `OBS_WAREHOUSE_INGEST`
   - `OBS_DASHBOARD_EXPORT`
3. Add class methods and instance variables to `ObservabilityConfig` to manage these flags thread-safely:
   - Provide default values.
   - Support environment variable overrides (`SIM_OBS_...` or `RPG_OBS_...`).
   - Map the presets (`OFF`, `LIGHT`, `NORMAL`, `FULL`, `RESEARCH`, `DEBUG`) to flag structures dynamically.
   - Allow direct individual flag overrides.
4. Ensure flags are exported in run manifests (or config serialization).

### Step 3: Implement Verification Tests
1. Create `tests/architecture/test_phase19_observability_boundaries.py`
   - Assert `docs/architecture/observability_behavior_profiling_boundary.md` exists.
   - Verify no forbidden imports in hot-path code from heavy analyzers.
2. Create `tests/architecture/test_phase19_hot_path_safety_contract.py`
   - Assert `docs/architecture/observability_hot_path_safety_contract.md` exists.
   - Verify that hot-path packages do not import heavy post-run processing or analytical packages.
3. Create `tests/unit/config/test_phase19_observability_feature_flags.py`
   - Verify defaults.
   - Verify mode-to-flag resolution.
   - Verify programmatic overrides.
   - Verify env var overrides.

### Step 4: Run Verification and Cleanup
1. Run all fast tests: `pytest -m "not slow and not extra_slow"`.
2. Move ticket to `tickets/done/TCK-20260529-OBS-PHASE19.md`.
3. Move staging folder `staging_artifacts/TCK-20260529-OBS-PHASE19/` to `stored_artifacts/TCK-20260529-OBS-PHASE19/`.

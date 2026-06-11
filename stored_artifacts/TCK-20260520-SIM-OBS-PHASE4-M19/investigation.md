---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M19
artifact_type: investigation
tags: [sim, obs, phase4, m19]
---

# Investigation: Minimal Balance Envelope Config (Milestone 19)

## Current Architecture Analysis

1. **Baseline Comparator**:
   - Compares a single run or sweep against a baseline (`BaselineConfig`).
   - Uses hardcoded comparison rules in `BaselineComparator.compare_run` and `compare_sweep`.
   - Threshold values are pulled from `baseline.threshold_recommendations.items()`.

2. **Rules Engine**:
   - `RuleEngine` loads JSON configs via `load_config(config_path)`.
   - Evaluates a stable registration order of rules:
     - `HardLawViolationDetected`
     - `NavigationStuckBasic` (uses `tick_threshold`, default `50`)
     - `QuestStalledBasic` (uses `tick_threshold`, default `100`)
     - `ResourceProductionZero` (uses `window_threshold`, default `3`)
     - `GovernorDegradedTooLong` (uses `window_threshold`, default `3`)
   - Checks `config.scenario_types` and skips rules if they don't match the current scenario type.

3. **CLI Handlers**:
   - CLI command parsing is done in `src/cli/entry.py`.
   - `compare-run` and `compare-sweep` do not currently accept a `--envelope` option.

## Integration Proposals

### 1. Schema Definition (`balance_envelope.py`)
- We will define the `BalanceEnvelope` Pydantic models with expectations for:
  - `min`
  - `max`
  - `equals`
  - `max_multiplier_from_baseline`
  - `min_multiplier_from_baseline`
- We will support loading from JSON using `BalanceEnvelopeLoader`.

### 2. Comparator Integration
- `BaselineComparator` will accept an optional `envelope_path`.
- If provided, it will load the `BalanceEnvelope` and override baseline thresholds.
- When matching multiplier expectations (e.g. `max_multiplier_from_baseline`), we compute the override limit as:
  `override_limit = baseline_value * expectation.max_multiplier_from_baseline`
  and evaluate the actual value against this dynamic override threshold.

### 3. Rule Engine Integration
- Add `apply_envelope(self, envelope: BalanceEnvelope)` to `RuleEngine` in `src/observability/anomaly/rules_engine.py`.
- Map standard expectation keys to rule IDs and override their threshold configurations.

### 4. CLI Integration
- Add `--envelope` option to `compare-run` and `compare-sweep` commands in `src/cli/entry.py`.
- Expose envelope-name and active expectations in comparison summaries.

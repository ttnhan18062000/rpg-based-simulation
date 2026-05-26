# Implementation Plan: Minimal Balance Envelope Config

## Proposed Changes

### Component 1: Balance Envelope Definition
#### [NEW] [balance_envelope.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/balance_envelope.py)
- Define `ExpectationValue` Pydantic model with validation rules.
- Define `BalanceEnvelope` Pydantic model containing metadata and expectations mapping.
- Implement `BalanceEnvelopeLoader` to read JSON definitions with clear validation/rejection errors.

### Component 2: Comparator Enhancements
#### [MODIFY] [baseline_comparator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/baseline_comparator.py)
- Refactor `compare_run` and `compare_sweep` methods to accept an optional `envelope_path` argument.
- If provided, load the envelope and override baseline thresholds:
  - If a metric expectation has static bounds (`min`, `max`, `equals`), replace the baseline-derived target threshold.
  - If it contains `max_multiplier_from_baseline` or `min_multiplier_from_baseline`, compute the threshold relative to the baseline's value.
  - Save the comparison result containing `envelope_id` or similar metadata.

### Component 3: Rules Engine Upgrades
#### [MODIFY] [rules_engine.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/anomaly/rules_engine.py)
- Add `apply_envelope(self, envelope: BalanceEnvelope)` to overlay scenario expectations onto individual rule configs.
- Map scenario type and severity levels correctly.

### Component 4: CLI Integration
#### [MODIFY] [entry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/cli/entry.py)
- Add `--envelope` option to both `compare-run` and `compare-sweep` subcommands.
- Pass the envelope path to the comparator.
- Update output layouts to display active envelope information.

## Verification Plan

- Unit tests in `tests/unit/observability/test_balance_envelope.py`.
- Integration tests in `tests/integration/observability/test_balance_envelope_comparison.py`.

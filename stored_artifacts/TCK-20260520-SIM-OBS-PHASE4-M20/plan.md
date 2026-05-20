# Implementation Plan - Milestone 19: Minimal Balance Envelope Config

We will implement the Pydantic schemas, loaders, and comparator/rule integrations for the scenario balance envelopes.

## User Review Required

> [!IMPORTANT]
> The balance envelope configuration enables scenario-specific expectations to overlay statistical baselines. If an expectation in `balance_envelope.json` defines limits (`min`, `max`, `equals`, `max_multiplier_from_baseline`, `min_multiplier_from_baseline`), these override the baseline-derived target recommendations. If any expectation fails, it gates simulation runs by generating `FAIL` or `WARNING` results accordingly.

## Proposed Changes

### Balance Envelope Schema & Loader

#### [NEW] [balance_envelope.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/balance_envelope.py)
- **`ExpectationValue`**: Pydantic model for a single metric limit definition:
  - `min`: Optional[float]
  - `max`: Optional[float]
  - `equals`: Optional[float]
  - `max_multiplier_from_baseline`: Optional[float]
  - `min_multiplier_from_baseline`: Optional[float]
  - `severity`: str  # "PASS" | "WARNING" | "FAIL"
- **`BalanceEnvelope`**: Pydantic model for scenario expectations:
  - `scenario_name`: str
  - `scenario_type`: str
  - `expectations`: Dict[str, ExpectationValue]
  - `schema_version`: str
- **`BalanceEnvelopeLoader`**:
  - `load_from_file(path: str) -> BalanceEnvelope`: Loads and validates scenario envelopes, raising clear validation errors on syntax or boundary issues.

### Comparator Overrides

#### [MODIFY] [baseline_comparator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/baseline_comparator.py)
- Update `compare_run` and `compare_sweep` to support `envelope_path: Optional[str] = None`.
- Overlay envelope expectation limits onto the baseline comparisons:
  - Use static bounds (`min`, `max`, `equals`) if present.
  - Calculate multiplier-relative bounds (`max_multiplier_from_baseline`, `min_multiplier_from_baseline`) from the baseline metrics values.
  - Include envelope metadata (`envelope_id`) in comparison reports.

### Rules Engine Upgrades

#### [MODIFY] [rules_engine.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/anomaly/rules_engine.py)
- Add `apply_envelope(self, envelope: BalanceEnvelope) -> None` to `RuleEngine` to override registered rule severity overrides, scenario_types, and threshold parameters.

### CLI Integration

#### [MODIFY] [entry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/cli/entry.py)
- Register `--envelope <envelope.json>` option for `rpg-observe compare-run` and `compare-sweep` subcommands.
- Display the envelope scenario name and active expectations in printed summaries.

---

## Verification Plan

### Automated Tests
- **Unit Tests**: `tests/unit/observability/test_balance_envelope.py`
  - Valid envelope loading.
  - Rejection of invalid metric parameters.
  - Multiplier-relative threshold evaluation validation.
- **Integration Tests**: `tests/integration/observability/test_balance_envelope_comparison.py`
  - End-to-end CLI execution with `--envelope` options.
  - Correct exit code status reporting.

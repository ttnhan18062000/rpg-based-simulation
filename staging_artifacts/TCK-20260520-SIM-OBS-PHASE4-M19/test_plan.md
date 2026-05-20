# Test Plan: Minimal Balance Envelope Config

## Unit Verification

### `tests/unit/observability/test_balance_envelope.py`
- **Load Valid JSON Envelope**: Verify that `BalanceEnvelopeLoader.load_from_file` parses a valid configuration completely.
- **Reject Invalid Envelope**: Test that schemas with missing scenario names, scenario types, or empty expectation bounds raise clear validation exceptions.
- **Envelope Comparator Override**: Verify that the comparator successfully overrides baseline static bounds with envelope values.
- **Baseline Multiplier Calculation**: Confirm that `max_multiplier_from_baseline` scales baseline metrics correctly and triggers fails/warnings accordingly.

## Integration Verification

### `tests/integration/observability/test_balance_envelope_comparison.py`
- Run dynamic simulations producing full metric and event telemetry logs.
- Trigger `rpg-observe compare-run` with custom envelopes.
- Verify that custom threshold overrides successfully govern the CLI exit code and output results.

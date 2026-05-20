# Implementation Plan - Minimal Balance Envelope Config

## Goal
Enable dynamic, scenario-specific expectations on top of default statistical baselines via standard `balance_envelope.json` configuration overrides.

## Architectural Decisions
1. **Separation of Concerns**: Kept baseline analysis separate from scenario expectations. Balance Envelopes layer over baseline outputs as non-destructive constraints.
2. **Pydantic Validation**: Ensured type safety and robust validation of incoming JSON configurations.
3. **Pacing and severity overrides**: Multiplier-relative gating and severity promotion (e.g. promoting a WARNING to CRITICAL/FAIL if specified by envelope constraints) integrated natively inside the analysis and evaluation pipeline.

## Deliverables
- `src/observability/reporting/balance_envelope.py`: Config schemas and file loader.
- `src/observability/reporting/baseline_comparator.py`: Custom expectation checks and multiplier-relative limits.
- `src/observability/anomaly/rules_engine.py`: Dynamic config overlay supporting rule engine threshold and severity overrides.
- `src/cli/entry.py`: Registered `--envelope` flags and formatting for comparison commands.

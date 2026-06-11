---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M19
phase: done
date: 2026-05-20
tags: [sim, obs, phase4, m19]
---

# TCK-20260520-SIM-OBS-PHASE4-M19

## Title

Milestone 19 — Minimal Balance Envelope Config

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Introduce scenario-specific expectations using `balance_envelope.json` configurations without building a full designer-facing balance system. Allow these envelope definitions to override comparison thresholds in the Baseline Comparator and Rule Engine, and integrate support into the rpg-observe CLI.

## Scope

- Define Pydantic models for `BalanceEnvelope` and metric expectations.
- Implement the `BalanceEnvelopeLoader` to load and validate envelope configs from JSON files.
- Refactor `BaselineComparator` to load the optional `balance_envelope.json` and override baseline-derived limits.
- Refactor the `RuleEngine` / rule thresholds to be overridable by loaded envelopes.
- Register `--envelope <envelope.json>` CLI arguments for comparison subcommands.
- Add unit and integration tests.

## Out of Scope

- A full YAML balance profile designer system.

## Acceptance Criteria

- Load valid envelopes successfully.
- Reject invalid envelopes with clear schema validation errors.
- Ensure envelope expectations successfully override baseline comparator thresholds.
- Enable `max_multiplier_from_baseline` and `min_multiplier_from_baseline` checks.
- Add `--envelope` support to `rpg-observe compare-run` CLI.
- Run tests verifying all expectations pass correctly.

## Related Tickets

- TCK-20260520-SIM-OBS-PHASE4-M18 (Completed)

## Related Docs

- `obs_sim_phase4.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/reporting/balance_envelope.py` (NEW)
- `src/observability/reporting/baseline_comparator.py`
- `src/observability/anomaly/rules_engine.py`
- `src/cli/entry.py`
- `tests/unit/observability/test_balance_envelope.py`
- `tests/integration/observability/test_balance_envelope_comparison.py` (NEW)

## Assumptions / Open Questions

- We will focus on JSON formatted envelopes, matching CLI expectations.

## Implementation Notes

- Seamlessly integrated multiplier-relative limits directly comparing with either baseline recommendation threshold or fall back distribution mean, maintaining consistency with baseline operators.

## Test Summary

- Added unit tests in `tests/unit/observability/test_balance_envelope.py` (load validation, comparator overrides, multiplier-relative checks, rule engine overlays).
- Added integration E2E CLI comparisons test in `tests/integration/observability/test_balance_envelope_comparison.py`.
- Run full pytest suite, all 81 tests passing (100% success rate).

## Files Changed

- `src/observability/reporting/balance_envelope.py`
- `src/observability/reporting/baseline_comparator.py`
- `src/observability/anomaly/rules_engine.py`
- `src/cli/entry.py`
- `tests/unit/observability/test_balance_envelope.py`
- `tests/integration/observability/test_balance_envelope_comparison.py`

## Completion Summary

- Milestone 19 successfully completed! The BalanceEnvelope system offers a fully-validated, extensible configuration layer that overrides default statistical baselines. Features include multiplier limits, custom severity mapping, dynamic rules engine config overlay, and CLI arguments printouts, verified with robust unit and integration testing.

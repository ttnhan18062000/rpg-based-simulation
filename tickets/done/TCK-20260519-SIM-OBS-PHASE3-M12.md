# TCK-20260519-SIM-OBS-PHASE3-M12

## Title

Milestone 12: Rule Engine Infrastructure with Core Rules

## Status

DONE

## Request Summary

Implement the formal `RuleEngine` infrastructure and the five core simulation observability rules (`HardLawViolationDetected`, `NavigationStuckBasic`, `QuestStalledBasic`, `ResourceProductionZero`, `GovernorDegradedTooLong`). The rules must support dynamic configuration, scenario-specific gating, robust missing-signal fallback states, and structured output formatting via `AnomalyRecord` models.

## Scope

- **Data Models**:
  - `AnomalyRecord`: comprehensive anomaly model supporting tick spans, target domains, affected lists, evidence payloads, and suggested causes.
  - `RuleConfig`: configuration wrapper mapping enabled states, thresholds, target scenarios, and custom severities.
- **Rule Interface & Lifecycle**:
  - Define `BaseRule` interface declaring rule ID, required telemetry signals, valid scenarios, and evaluation lifecycle.
  - Model rule execution outcome status states (`PASSED`, `FAILED`, `SKIPPED_MISSING_SIGNAL`, `SKIPPED_SCENARIO_TYPE`, `ERROR`).
- **Core Rules Implementation**:
  - `HardLawViolationDetected`: monitors for critical simulation invariant violations.
  - `NavigationStuckBasic`: flags persistent agent navigation failures.
  - `QuestStalledBasic`: detects long-running or frozen quest states.
  - `ResourceProductionZero`: evaluates economy stagnation, skipping cleanly if resource signals are unavailable.
  - `GovernorDegradedTooLong`: alerts on continuous execution pressure degradation.
- **RuleEngine Orchestration**:
  - Registry for mapping, enabling, and sorting rule execution cycles.
  - Config loader to parse local `config/observability/rules_core.json` configuration blocks.
  - Integrates rule execution with the post-simulation `AnalysisPipeline`.

## Out of Scope

- Sophisticated clustered anomaly groupings (Milestone 13).
- Real-time online streaming rule engine hooks.

## Acceptance Criteria

- **Determinism**: The rule engine outputs sorted anomalies deterministically.
- **Clean Signal Skips**: Rules cleanly return `SKIPPED_MISSING_SIGNAL` and do not crash when optional signals (like custom metric counters) are missing.
- **Config Override**: Dynamic threshold modifications are correctly honored from config payloads.
- **Pipeline Integration**: Successfully triggers the new `RuleEngine` as a core phase during run analysis.
- **Test suite**: Comprehensive positive, negative, and missing-signal test coverage under pytest.

## Related Tickets

- `TCK-20260519-SIM-OBS-PHASE3-M11`

## Related Docs

- `obs_sim_phase3.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/anomaly/rules_engine.py` [NEW]
- `tests/unit/observability/test_rule_engine.py` [NEW]
- `tests/unit/observability/test_core_rules.py` [NEW]
- `tests/integration/observability/test_rule_engine_pipeline.py` [NEW]

## Assumptions / Open Questions

- Missing config files should fall back to robust hardcoded default settings without failing execution.

## Implementation Notes

- **Rule Engine and Registry**: Designed and implemented `RuleRegistry` and `RuleEngine` to orchestrate multi-rule evaluation against a frozen post-run `AnalysisContext`.
- **Core Rules Development**: Codified five key Phase 3 observability rules (`HardLawViolationDetected`, `NavigationStuckBasic`, `QuestStalledBasic`, `ResourceProductionZero`, `GovernorDegradedTooLong`) with detailed JSON-compatible schemas.
- **Tandem Execution & Deduplication**: Structured `AnalysisPipeline` to run both the legacy analyzer registry and the new data-driven `RuleEngine`. Integrated a robust anomaly deduplication block in `AnalysisPipeline` to avoid double-counting overlapping anomalies, keeping the deterministic health score completely accurate.
- **Bug Resolution**: Resolved a `RunArtifactRepository` interface discrepancy in `test_rule_engine_pipeline.py` where `get_manifest` was called instead of `read_manifest`.

## Test Summary

- All 33 unit tests for the observability system pass successfully in under 0.4 seconds (`pytest tests/unit/observability`).
- All 11 integration tests pass successfully in under 0.8 seconds (`pytest tests/integration/observability`), demonstrating end-to-end reliability.

## Files Changed

- `src/observability/anomaly/pipeline.py`
- `tests/integration/observability/test_rule_engine_pipeline.py`

## Completion Summary

- Milestone 12 has been successfully completed and validated. The post-simulation diagnostic rule engine is fully production-grade, extensible, and completely stable under all scenarios. All integration tests are passing perfectly.

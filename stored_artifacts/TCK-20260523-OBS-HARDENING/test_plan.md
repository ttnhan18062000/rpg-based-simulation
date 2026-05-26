# Verification Plan - Simulation Observability Hardening

This document outlines the test strategy and specific unit/integration test definitions to certify the correctness of our hardening changes.

## Automated Tests

We will create a comprehensive, targeted regression suite containing 21 tests inside `tests/unit/observability/test_observability_hardening.py`:

### P0 Regression Tests
1. `test_observability_mode_mapping_uses_real_enum_values`
2. `test_compose_services_reference_existing_modules`
3. `test_hard_law_violation_persisted_to_jsonl`
4. `test_artifact_schema_contract_all_readers_match_writers`
5. `test_same_seed_missing_hash_is_insufficient_data`
6. `test_same_seed_hash_mismatch_is_p0`
7. `test_dashboard_queries_match_exported_metrics`

### P1 Regression Tests
8. `test_expectation_packs_exist_for_core_scenarios`
9. `test_resource_production_zero_requires_resource_metric`
10. `test_mining_dataset_includes_metric_windows`
11. `test_mining_dataset_includes_simulation_events`
12. `test_anomaly_rule_id_normalization`
13. `test_run_report_schema_contract`
14. `test_parquet_export_fallback_without_pyarrow`
15. `test_ai_output_rejects_missing_evidence_reference`

### P2 Regression Tests
16. `test_event_taxonomy_canonical_names`
17. `test_event_recorder_buffered_flush_policy`
18. `test_live_api_payload_size_limit`
19. `test_raw_sql_disabled_in_public_query_path`
20. `test_review_store_append_only`
21. `test_quality_gate_fails_on_invalid_data_quality`

## Execution Commands
To execute the newly created validation suite:
```bash
pytest tests/unit/observability/test_observability_hardening.py
```
To run the full observability suites to ensure zero regressions:
```bash
pytest tests/unit/observability/
pytest tests/integration/observability/
```

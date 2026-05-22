# Test Plan - Milestone 13: Evidence, Triage, and Report V2

We will implement a suite of unit and integration tests to verify the correctness of the new diagnostic clustering, evidence building, and Report V2 capabilities.

## Automated Tests

### Unit Tests

#### 1. `tests/unit/observability/test_triage_engine.py`
- **TriageEngine Clustering**: Verify that 10 stuck anomalies are correctly grouped into 1 deterministic `AnomalyCluster` with entity counts and references.
- **Overlapping temporal windows**: Check that anomalies in different windows or different regions are NOT grouped together.

#### 2. `tests/unit/observability/test_evidence_builder.py`
- **Evidence Retrieval**: Mock `AnalysisContext` events/metrics and confirm `EvidenceBuilder` packages compact, valid JSON blocks for Hard Law violations and Stuck events.

### Integration Tests

#### 3. `tests/integration/observability/test_report_v2.py`
- **Report V2 generation**: Runs the pipeline and verifies that `run_report.md` contains the:
  - "Rule Execution Status" table.
  - "Anomaly Clusters" breakdown.
  - "Recommended Investigation Points".
  - "Missing Signals / Skipped Rules" section when signals are absent.

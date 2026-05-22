# Implementation Plan - Milestone 13: Evidence, Triage, and Report V2

We propose implementing the post-simulation triage, clustering, and Report V2 generation logic to turn raw lists of anomalies into highly actionable diagnostic summaries.

## Proposed Changes

### Observability Core

#### [NEW] [triage.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/anomaly/triage.py)
- **EvidenceBuilder**: Extracts relevant context segments (e.g. preceding events, metric window history, hard law breaches) and packages them into compact JSON-serializable payloads.
- **TriageEngine**: Clusters anomalies by rule ID, severity, spatial/entity/quest context, and overlapping temporal window limits. Counts affected entities/resources per cluster.
- **InvestigationHint**: Declares static checklists of recommended developer investigations mapped to rule types.

### Reporting Layer

#### [MODIFY] [run_report.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/run_report.py)
- Upgrades the markdown generator `RunReportGenerator` to produce a full Report V2 layout.
- Integrates anomaly clusters, evidence blocks, investigation suggestions, and rule status summary metrics.
- Upgrades `run_report.json` to store structured triage metadata consistently.

## Verification Plan

### Automated Tests
- `pytest tests/unit/observability/test_triage_engine.py`
- `pytest tests/unit/observability/test_evidence_builder.py`
- `pytest tests/integration/observability/test_report_v2.py`

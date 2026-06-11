---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-INVESTIGATION
artifact_type: investigation
tags: [lab, investigation]
---

# Investigation and Design Notes - Milestone 100

## 1. Output Schema Mapping

### `investigation_report.json`
```json
{
  "session_id": "string",
  "lab_run_id": "string",
  "analysis_depth": "light | standard | deep",
  "investigated_at": "string (ISO)",
  "executive_summary": "string",
  "data_quality": "string",
  "signal_coverage": "list",
  "critical_issues": "list",
  "domain_issues": "dict",
  "balance_concerns": "list",
  "liveness_concerns": "list",
  "performance_concerns": "list",
  "entity_evidence": "list",
  "missing_data": "list",
  "likely_causes_vs_facts": "list",
  "recommended_steps": "list",
  "evidence_references": "list"
}
```

---

## 2. Analysis Depth Constraints

- **Light Mode**:
  - We only load `compact_summary.json` and `issue_index.json`.
  - Process only the top 3 issues.
  - No detailed child run scans are performed.

- **Standard Mode**:
  - We load `compact_summary.json`, `issue_index.json`, `evidence_pack_index.json`, and `signal_coverage.json`.
  - Process top 10 issues.
  - Read signal coverage and flag focus domains that are not covered.

- **Deep Mode**:
  - Load all Standard Mode files.
  - If a `focus_issues` filter or specific `seeds` / `tick_range` constraints are provided in the request, selectively scan the corresponding child run scorecards (`run_report.json`) to extract full evidence tick timelines and cognition stats, keeping token weight small.

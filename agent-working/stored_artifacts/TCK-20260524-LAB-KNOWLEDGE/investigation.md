---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-KNOWLEDGE
artifact_type: investigation
tags: [lab, knowledge]
---

# Investigation and Design Notes - Milestone 102

## 1. Global Knowledge Base Schema

We will partition global simulation knowledge under `data/lab_knowledge/`:

- **Insights**:
  ```json
  {
    "insight_id": "INSIGHT-RESOURCE-0001",
    "type": "OBSERVABILITY_GAP",
    "title": "Resource target scoring is needed for resource freeze investigation",
    "source_lab_run": "manual_resource_test_001",
    "source_report": "...",
    "evidence_refs": ["investigation/missing_signals.json#resource_gap"],
    "status": "APPROVED",
    "created_at": "2026-05-24T10:00:00Z"
  }
  ```

- **Known Issues**:
  Stored under `data/lab_knowledge/known_issues/` containing rule violations and severity information.

- **Decisions**:
  Appended line-by-line in JSON Lines format:
  `data/lab_knowledge/decisions/decision_log.jsonl`
  ```json
  {"session_id": "session_01", "decision_note": "Approved...", "timestamp": "..."}
  ```

---

## 2. Approval Verification Gate

To prevent unauthorized rules or principle adjustments, the workflow checks the request or active session metadata for an explicit approval marker:
- `request.specific_inputs.get("approved_by")` or `request.specific_inputs.get("approval_recorded") == True`.
- If missing, we block updates to `rules` and `principles`, raising `ValueError`.

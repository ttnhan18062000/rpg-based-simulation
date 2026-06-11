---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-AUDIT-EVENT-SEQUENCE
artifact_type: investigation
tags: [audit, event, sequence]
---

# Investigation: TCK-20260610-AUDIT-EVENT-SEQUENCE

## Findings

Only `UpdateSimulationKnowledgeWorkflow` emitted lifecycle audit events before this ticket.
The other four workflows (Generate, Prepare, Register, Propose) had no `workflow_started`/`workflow_completed` events in the audit log. The `manual_boundary_declared` event did not exist anywhere.

`trail.read_log(sid)` returns `List[Dict]` where each entry has `event_type` and `details`.

`LabAuditTrail` is imported at module top in `workflows.py`. All workflows have `self.workspace_root`.

`UpdateSimulationKnowledgeWorkflow` emits events in this order within a single run:
`workflow_started → approval_required → (approval_recorded or blocked_action+ValueError) → ... → workflow_completed`

The E2E test runs `UpdateSimulationKnowledge` twice in the full chain: once without approval (raises ValueError), once with approval. The sequence scan handles this via gap-tolerance — it finds the correct `approval_recorded` after the first `approval_required`.

`proposals_list` was only non-empty if anomalies were CRITICAL severity. The E2E run fixture uses WARNING severity, so `proposals_list` was empty and `UpdateSimulationKnowledge` was never called in the approved path — meaning audit checkpoints 10-13 were absent.

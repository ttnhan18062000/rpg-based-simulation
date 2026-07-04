---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-LABKNOWLEDGE-REVERT
phase: open
date: 2026-07-04
tags: [lab-agent, knowledge-store, audit-trail, rollback]
---

# TCK-20260704-LABKNOWLEDGE-REVERT

## Title
Add a real revert mechanism for UpdateSimulationKnowledgeWorkflow

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/ai/workflows.md` documents `update-knowledge-store`'s output as including "Audit log JSON (what was included, excluded, approved, and how to revert)." Direct code investigation confirms this overclaims: `LabAuditTrail` (`src/lab/audit.py`) has exactly two methods, `log_event` and `read_log` — there is no revert/rollback mechanism anywhere in `src/lab/`. The audit log does capture enough information to revert manually (a `files_written` event lists every path touched by a sync), but there is no automated `how_to_revert` field or undo function. This ticket makes the existing documentation claim actually true, rather than leaving it as an aspirational description of a feature that doesn't exist.

User decision (2026-07-04): build a real revert function, not just fix the docs to stop overclaiming.

## Scope
- Add a `revert_session(session_id, sync_event_id)`-style capability (exact interface TBD by investigation/plan phase) that:
  - Reads the target `knowledge_sync_result` event and its paired `files_written` event from the session's `audit_log.jsonl`.
  - Removes or restores each written file under `data/lab_knowledge/` (`insights/`, `known_issues/`, `rules/`, `principles/`, `decisions/decision_log.jsonl` — the last is append-only, so "revert" for it likely means removing only the specific appended line(s), not truncating the whole file).
  - Appends a new `knowledge_reverted` event to the audit trail documenting what was undone and why — the revert action itself must be auditable, not a silent mutation.
- Decide and document: can a sync be reverted if a *later* sync has since touched the same insight/rule file? (Likely: reject with a clear error rather than silently clobbering newer state.)
- Update `docs/ai/workflows.md` to describe the actual revert mechanism once implemented (currently describes an aspirational one).

## Out of Scope
- Reverting `report_path` (`knowledge_update_report.md`) content — this is a generated summary, not durable knowledge state; regenerating it is cheaper than reverting it.
- A CLI/skill-level `/revert-knowledge-sync` command — this ticket scopes the underlying capability in `src/lab/`; a user-facing invocation surface can be a follow-on ticket if needed.
- Reverting partially-approved or in-flight sessions — only fully-synced (`SYNCED` status) sessions are in scope.

## Acceptance Criteria
- [ ] A revert function exists in `src/lab/` (audit.py or workflows.py) that takes a session_id and undoes a specific prior knowledge sync.
- [ ] Reverting removes exactly the files listed in that sync's `files_written` event — no more, no less.
- [ ] Reverting a sync that has been superseded by a later sync touching the same target file is rejected with a clear error, not silently applied.
- [ ] The revert action itself is logged to `audit_log.jsonl` as a new event type.
- [ ] `docs/ai/workflows.md`'s `update-knowledge-store` section accurately describes the real mechanism (update it in the same change, per this repo's parity-between-docs-and-code convention).
- [ ] New tests in `tests/integration/lab_agent/` cover: successful revert, revert-after-superseding-sync rejection, and audit trail correctness.

## Related Tickets
TCK-20260524-LAB-KNOWLEDGE (original UpdateSimulationKnowledgeWorkflow implementation)
TCK-20260704-LABKNOWLEDGE-TIMESTAMP (unrelated bug found in the same file during this investigation — fix independently)

## Related Docs
- docs/ai/workflows.md (`update-knowledge-store` section — overclaims the current capability)
- docs/ai/agent_infrastructure_audit.md (originally flagged this as "documented, not verified"; this investigation upgraded it to "documented, confirmed absent")

## Related Stored Artifacts
- `staging_artifacts/TCK-20260704-LABKNOWLEDGE-REVERT/investigation.md` — written 2026-07-04, covers current behavior (file:line), docs-vs-reality gap, existing test fixtures to reuse, and risks (superseding-sync case, append-only decision log).
- `plan.md` and `test_plan.md` intentionally not yet written — commit to concrete implementation steps, deferred until implementation actually begins per explicit user decision (ticket stays queued, not in-progress).

## Related Code Areas
- src/lab/audit.py (LabAuditTrail — add the revert capability here or a sibling class)
- src/lab/workflows.py (UpdateSimulationKnowledgeWorkflow.run — the sync logic being reverted)
- src/lab/session.py (LabSessionStore — may need to read/validate session state during revert)
- tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py
- docs/ai/workflows.md

## Assumptions / Open Questions
- Exact revert granularity (per-sync vs. per-insight) is not yet decided — left for the Investigate/Plan phase.
- Whether `decisions/decision_log.jsonl` needs a line-level revert or whether decision entries are considered permanent/non-revertible by design is an open question the plan should resolve explicitly rather than assume.

## Implementation Notes
(not yet implemented — standard tier, requires investigation and plan phases before implementation)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)

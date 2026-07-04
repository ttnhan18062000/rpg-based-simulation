---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-LABKNOWLEDGE-TIMESTAMP
phase: done
date: 2026-07-04
tags: [lab-agent, knowledge-store, bug]
---

# TCK-20260704-LABKNOWLEDGE-TIMESTAMP

## Title
Fix hardcoded fake timestamps in UpdateSimulationKnowledgeWorkflow

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`UpdateSimulationKnowledgeWorkflow.run()` in `src/lab/workflows.py` writes the literal string `"2026-05-24T10:00:00Z"` (the date this workflow was originally built, per `TCK-20260524-LAB-KNOWLEDGE`) into two places: every stored insight's `created_at` field (line 2448) and every decision log entry's `timestamp` field (line 2489). Every insight and decision ever synced through this workflow — regardless of when it actually ran — carries this same fake date. Meanwhile `LabAuditTrail.log_event` in the same call path correctly uses `datetime.now(timezone.utc).isoformat()`, so the fix pattern is already established in the same file; this is a leftover from initial development, not a design choice.

## Scope
- Replace the two hardcoded `"2026-05-24T10:00:00Z"` literals in `src/lab/workflows.py` (`created_at` on stored insight records, `timestamp` on decision log entries) with `datetime.now(timezone.utc).isoformat()`.
- Add or extend a test in `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py` asserting these fields reflect actual run time (not the literal string), e.g. parseable as ISO 8601 and within a reasonable delta of "now" at test execution.

## Out of Scope
- The `LabAuditTrail.log_event` timestamp (already correct — uses `datetime.now(timezone.utc)`).
- Retroactively correcting already-written `insights/*.json` / `decisions/decision_log.jsonl` records from past runs — those files reflect what the workflow actually wrote at the time; this ticket fixes the code going forward only.

## Acceptance Criteria
- [ ] No literal `"2026-05-24T10:00:00Z"` (or any other hardcoded date string) remains in `src/lab/workflows.py`.
- [ ] Stored insight `created_at` and decision log `timestamp` are generated via `datetime.now(timezone.utc).isoformat()` at write time.
- [ ] A test asserts these fields are dynamic (not a fixed literal) across two separate workflow runs executed at different times.
- [ ] Existing tests in `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py` and `tests/unit/lab_agent/` still pass.

## Related Tickets
TCK-20260524-LAB-KNOWLEDGE (original implementation — introduced the hardcoded literal)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- src/lab/workflows.py (lines 2448, 2489)
- src/lab/audit.py (reference pattern — LabAuditTrail.log_event already does this correctly)
- tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py

## Assumptions / Open Questions
None — the fix pattern (`datetime.now(timezone.utc).isoformat()`) is already used correctly elsewhere in the same file.

## Implementation Notes
- `src/lab/workflows.py`: added `from datetime import datetime, timezone` to the import block (line 6). Replaced the hardcoded `"2026-05-24T10:00:00Z"` literal at the stored-insight `created_at` field (was line 2448) with `datetime.now(timezone.utc).isoformat()`, and the decision-log `timestamp` field (was line 2489) with the same expression. `LabAuditTrail.log_event` in `src/lab/audit.py` was not touched (already correct, out of scope).
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`: extracted the existing `mock_workspace_for_knowledge` fixture body into a plain helper `_build_knowledge_workspace(tmp_path)` (fixture now just calls it) so a workspace can be built more than once per test. Added `test_knowledge_timestamps_are_dynamic`, which builds two independent workspaces via `tmp_path_factory`, runs `UpdateSimulationKnowledgeWorkflow` in each with a `time.sleep(0.05)` gap between them, and asserts for both the insight `created_at` and decision log `timestamp`: (a) the value is not the old literal, (b) it parses as ISO 8601 via `datetime.fromisoformat` and falls within the `before`/`after` window bracketing the `.run()` call, and (c) the two runs produce different values for both fields.

## Test Summary
- `python3 -m pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py -q` — 7 passed (6 pre-existing + 1 new).
- `python3 -m pytest tests/unit/lab_agent/ -q` — 33 passed, no regressions.

## Files Changed
- `src/lab/workflows.py`
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`

## Completion Summary
Replaced both hardcoded `"2026-05-24T10:00:00Z"` literals in `UpdateSimulationKnowledgeWorkflow.run()` with `datetime.now(timezone.utc).isoformat()`, matching the existing correct pattern in `LabAuditTrail.log_event`. Added a regression test proving the insight `created_at` and decision log `timestamp` fields are dynamic and differ across separate workflow runs. All existing integration and unit tests for the lab agent still pass.

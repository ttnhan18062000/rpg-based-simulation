---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-LABKNOWLEDGE-REVERT
phase: done
date: 2026-07-04
tags: [lab-agent, knowledge-store, audit-trail, rollback]
---

# TCK-20260704-LABKNOWLEDGE-REVERT

## Title
Add a real revert mechanism for UpdateSimulationKnowledgeWorkflow

## Status
DONE

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
- [x] A revert function exists in `src/lab/` (audit.py or workflows.py) that takes a session_id and undoes a specific prior knowledge sync. — `RevertSimulationKnowledgeWorkflow.run(session_id)` in `src/lab/workflows.py`.
- [x] Reverting removes exactly the files listed in that sync's `files_written` event — no more, no less. — required fixing `files_written` itself to include `known_issues`/`rules` paths (a genuine, verified pre-existing gap), then matching exactly against the corrected list.
- [x] Reverting a sync that has been superseded by a later sync touching the same target file is rejected with a clear error, not silently applied. — sha256 pre-flight check over all target files before any deletion; raises `LabKnowledgeRevertError`.
- [x] The revert action itself is logged to `audit_log.jsonl` as a new event type. — `knowledge_reverted` event, carrying `removed_files`.
- [x] `docs/ai/workflows.md`'s `update-knowledge-store` section accurately describes the real mechanism. — overclaim removed, replaced with an accurate Revert subsection.
- [x] New tests in `tests/integration/lab_agent/` cover: successful revert, revert-after-superseding-sync rejection, and audit trail correctness. — 11 new tests, including a legacy-audit-log guard test surfaced by architecture review (not originally anticipated by the ticket or investigation).

## Related Tickets
TCK-20260524-LAB-KNOWLEDGE (original UpdateSimulationKnowledgeWorkflow implementation)
TCK-20260704-LABKNOWLEDGE-TIMESTAMP (unrelated bug found in the same file during this investigation — fix independently)

## Related Docs
- docs/ai/workflows.md (`update-knowledge-store` section — overclaims the current capability)
- docs/ai/agent_infrastructure_audit.md (originally flagged this as "documented, not verified"; this investigation upgraded it to "documented, confirmed absent")

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-LABKNOWLEDGE-REVERT/investigation.md`, `plan.md`, `test_plan.md` — full investigate/plan/review/implement cycle completed 2026-07-04, including one architecture-review iteration (NEEDS_CHANGES → fixed → APPROVED).

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
Implemented exactly per the approved `staging_artifacts/TCK-20260704-LABKNOWLEDGE-REVERT/plan.md` (5 steps, no deviations).

- **Step 1 (write-path audit fix):** `UpdateSimulationKnowledgeWorkflow.run()`'s Step 6/7 storage loops now build each insight/known-issue/rule record's JSON string once (`json.dumps(...)`, written via `f.write` instead of `json.dump`) so the exact written bytes can be sha256-hashed. The Step 10 `files_written` event now lists `"decisions/decision_log.jsonl"` (was the bare, inconsistent `"decision_log.jsonl"`) plus every `insights/`/`known_issues/`/`rules/` path actually written, and carries a new `file_hashes: {relative_path: sha256_hex}` dict covering those three types (report_path and the decision log are excluded, per plan). The `knowledge_sync_result` event now echoes `decision_log_entry: log_entry` — the exact dict appended to `decision_log.jsonl` in Step 8 — so revert can locate that one line by full-record equality without adding an ID field to the shared JSONL file's own schema.
- **Step 2 (RevertSimulationKnowledgeWorkflow, AC1/AC2/AC4):** Added `RevertSimulationKnowledgeResult` TypedDict (`src/lab/results.py`, directly after `UpdateSimulationKnowledgeResult`) and `RevertSimulationKnowledgeWorkflow` + `LabKnowledgeRevertError` (`src/lab/workflows.py`, appended after `UpdateSimulationKnowledgeWorkflow`, same `workspace_root`/`session_store`/`knowledge_root` construction). `run(session_id)` scans the audit log in reverse for the most recent `knowledge_sync_result` + its immediately preceding `files_written` event; returns `NOTHING_TO_REVERT` if none found or the sync was `NO_INSIGHTS`; deletes the target insight/known-issue/rule files (idempotent — an already-absent file is not an error and isn't counted in `removed_files`); removes exactly the one matching `decisions/decision_log.jsonl` line via temp-file + `os.replace` (never in-place truncation); logs a new `knowledge_reverted` audit event; returns `REVERTED`.
- **Step 2b (legacy-log guard):** Before touching anything, `run()` checks `file_hashes`/`decision_log_entry` are present via `.get(...)`; if either is missing (pre-Step-1 audit log), raises `LabKnowledgeRevertError("this sync predates hash-tracking support and cannot be safely reverted")` rather than letting a bare `KeyError` propagate or attempting a partial revert.
- **Step 3 (supersede rejection, AC3):** Before deleting any file, `run()` pre-flight-checks every target path's live sha256 against `file_hashes[path]` (skipping files already absent). Any mismatch raises `LabKnowledgeRevertError` ("target file has been modified by a later operation...") before any deletion happens, so a rejected revert never partially deletes files. Uniform across insight/known-issue/rule paths, no special-casing (insights structurally can't hit this path due to the existing duplicate-write guard).
- **Step 4 (docs):** `docs/ai/workflows.md`'s `update-knowledge-store` section's output bullet no longer claims "and how to revert"; a new **Revert** subsection names `RevertSimulationKnowledgeWorkflow.run(session_id)` and describes its real behavior. `docs/ai/agent_infrastructure_audit.md` gets one pointer sentence appended at each of the two cited findings (L59 risk, L71 recommendation) noting the gap is closed by this ticket — the point-in-time audit framing itself is untouched.
- **Step 5 (parity ledger):** Added `INFRA-261` (`status: verified`, `priority: P2`) to `docs/parity_ledger/infrastructure.yaml` describing the revert capability, citing `RevertSimulationKnowledgeWorkflow`/`RevertSimulationKnowledgeResult` as `v2_evidence` and the 8 new revert tests as `test_path`. Updated `INFRA-225`'s `text` (and `v2_evidence`) from "7" to "8" lab `Workflow.run()` methods, adding `RevertSimulationKnowledge` to the enumerated flat-TypedDict list; `status`/`priority` left unchanged (count update, not re-certification). Confirmed via `grep -c "^class .*Workflow" src/lab/workflows.py` → 8.

No deviations from the approved plan — no `plan.md` Deviations section was needed.

## Test Summary
Ran (all green):
```
pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py -v       # 18 passed
pytest tests/integration/lab_agent/ tests/unit/lab_agent/ -m "not slow" -q               # 95 passed
```
All 7 pre-existing tests in `test_update_simulation_knowledge_workflow.py` pass unchanged after the Step 1 payload fix (confirms it is additive). 11 new tests added:
- `test_files_written_includes_known_issues_and_rules_with_hashes` (Step 1 payload-shape assertions)
- `test_revert_function_exists_and_is_callable` (AC1)
- `test_revert_removes_exact_files_written`, `test_revert_fixes_known_issues_and_rules_omission`, `test_revert_decision_log_removes_only_matching_line` (AC2)
- `test_revert_rejects_superseded_known_issue`, `test_revert_rejects_superseded_rule` (AC3)
- `test_revert_rejection_does_not_log_false_success`, `test_revert_logs_audit_event` (AC4)
- `test_revert_nothing_to_revert_for_no_insights_sync` (NO_INSIGHTS revert no-op path)
- `test_revert_rejects_legacy_log_missing_hash_keys` (Step 2b legacy-log guard)

Also verified YAML parses (`docs/parity_ledger/infrastructure.yaml`) and `INFRA-261` has all sibling fields (`id`/`text`/`status`/`priority`/`v2_evidence`/`test_path`).

## Files Changed
- `src/lab/workflows.py` — Step 1 `files_written`/`knowledge_sync_result` payload fix; new `RevertSimulationKnowledgeWorkflow` class + `LabKnowledgeRevertError`; new `import hashlib`.
- `src/lab/results.py` — new `RevertSimulationKnowledgeResult` TypedDict.
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py` — 11 new tests + updated imports.
- `docs/ai/workflows.md` — `update-knowledge-store` output bullet corrected + new Revert subsection.
- `docs/ai/agent_infrastructure_audit.md` — pointer sentences appended at L59/L71.
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-261` entry; `INFRA-225` text/`v2_evidence` updated (7→8).

## Completion Summary
Added `RevertSimulationKnowledgeWorkflow` (`src/lab/workflows.py`), making `docs/ai/workflows.md`'s longstanding "how to revert" claim genuinely true for the first time. Required first fixing a real, verified pre-existing bug: `UpdateSimulationKnowledgeWorkflow`'s `files_written` audit event never recorded `known_issues`/`rules` paths, which would have made revert's "no more, no less" acceptance criterion structurally unsatisfiable — fixed as necessary plumbing, not scope creep. Supersede detection uses a live sha256 content-hash pre-flight (checked over the full target set before any deletion, so a rejected revert never partially deletes files) rather than new cross-session audit-log scanning. Decision-log line removal uses temp-file + `os.replace`, never in-place truncation. Architecture review caught two real, substantive issues on first pass — a parity ledger entry (`INFRA-225`) that would go stale once an 8th workflow class landed, and a raw `KeyError` crash risk against any pre-existing audit log lacking the new hash-tracking fields — both fixed (the second via an explicit "legacy-log guard" that didn't exist in the original plan) and re-reviewed APPROVED. 95/95 `lab_agent` tests pass; `INFRA-261` (new) and `INFRA-225` (updated) both added to the parity ledger in the same session, per this repo's Authoritative Mechanics Rule. Out of scope, as the ticket specifies: reverting `knowledge_update_report.md` content, a CLI/skill-level invocation surface, and reverting in-flight (non-`SYNCED`) sessions.

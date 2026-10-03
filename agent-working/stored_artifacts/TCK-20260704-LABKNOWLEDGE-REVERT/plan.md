---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260704-LABKNOWLEDGE-REVERT
artifact_type: plan
tags: [lab-agent, knowledge-store, audit-trail, rollback]
---

# Implementation Plan — TCK-20260704-LABKNOWLEDGE-REVERT

## Summary

Add a new `RevertSimulationKnowledgeWorkflow` class in `src/lab/workflows.py` (sibling to
`UpdateSimulationKnowledgeWorkflow`, same file, same `workspace_root`/`session_store`/
`knowledge_root` construction pattern) that reverts the most recent knowledge sync for a given
`session_id`. Getting there requires first fixing `UpdateSimulationKnowledgeWorkflow.run()`'s audit
emission (`files_written` currently omits `known_issues/`/`rules/` paths and uses an inconsistent
path format; no event currently carries enough identifying detail — file hashes, decision-log
entry echo — for a later revert to safely detect supersession or locate the exact decision-log
line). That write-path fix is necessary plumbing for this ticket's own Acceptance Criteria 2 and 3,
not a separate concern, and is done first. Supersede detection uses a content-hash comparison
against the live filesystem (recorded at write time, checked at revert time) rather than scanning
every other session's audit log — this avoids new cross-session enumeration machinery and keeps
the check deterministic. No new per-entry ID field is added to `decision_log.jsonl`'s own file
schema; instead the *audit trail event* (already a free-form `details` dict, safe to extend) echoes
the exact decision-log dict written, and revert matches against that by full-record equality, never
by timestamp alone. All new logic and its own action are logged, per the append-only pattern
`LabAuditTrail.log_event` already establishes.

## Steps

### Step 1 — Fix write-path audit payloads (prerequisite plumbing for AC2/AC3)

- **Files:** `src/lab/workflows.py` (`UpdateSimulationKnowledgeWorkflow.run`, the Step 6/7 storage
  loops at ~L2436–2482 and the Step 10 audit-logging block at ~L2504–2518).
- **Change:**
  - In the Step 6 insight loop and Step 7 known-issues/rules loop, collect, for each file actually
    written: its path relative to `self.knowledge_root` (e.g. `"insights/{id}.json"`,
    `"known_issues/{id}.json"`, `"rules/{id}.json"`) and a `sha256` hex digest of the exact bytes
    written to it (compute from the same string/bytes passed to `json.dump`/`f.write`, not by
    re-reading the file afterward).
  - In the Step 10 `files_written` event: replace the literal `"decision_log.jsonl"` with
    `"decisions/decision_log.jsonl"`; append the known-issues/rules paths collected above; add a new
    `"file_hashes"` dict (`{relative_path: sha256_hex}`) covering every insight/issue/rule path
    (decision log and `report_path` excluded — decision log is matched by content-echo in Step 2,
    `report_path` stays out of scope per the ticket).
  - In the Step 10 `knowledge_sync_result` event: add `"decision_log_entry": log_entry` (the exact
    dict already built and appended to `decision_log.jsonl` in Step 8 — echo the same object, do not
    rebuild it) so revert can locate that one line by full-record equality without adding an ID field
    to the decision log file itself.
- **Do NOT touch:** approval/duplicate-guard control flow (Steps 1–5 of `run()`), the
  `decision_log.jsonl` on-disk schema (still exactly `session_id`/`decision_note`/`approved_by`/
  `timestamp`, no new field written to that file), report generation, `LabAuditTrail.log_event`'s
  signature.
- **Verify:** run `pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py -v`
  — all existing tests must stay green unchanged (confirms the fix is additive: existing assertions
  on `knowledge_sync_result`'s `status`/`synced_insights`/`synced_patches` and on stored-file
  contents are untouched, per test_plan.md's Regression Surface note that no current test inspects
  `files_written`'s exact list). Add the payload-shape assertions from
  `test_revert_fixes_known_issues_and_rules_omission` (test_plan.md, AC2 section) at this step,
  scoped to just the `files_written`/`knowledge_sync_result` shape — it will not yet call revert.

### Step 2 — Add `RevertSimulationKnowledgeWorkflow` happy path (AC1, AC2, AC4)

- **Files:** `src/lab/results.py` (new TypedDict), `src/lab/workflows.py` (new class + new
  exception).
- **Change:**
  - `src/lab/results.py`: add `RevertSimulationKnowledgeResult(TypedDict)` directly after
    `UpdateSimulationKnowledgeResult` (~L121), fields: `status: Literal["REVERTED",
    "NOTHING_TO_REVERT"]`, `session_id: str`, `removed_files: list[str]`.
  - `src/lab/workflows.py`: add `class LabKnowledgeRevertError(Exception): pass` near the new
    workflow class (module-local, following the `schema.py`/`guardrails.py` convention of a small
    exception class colocated with the logic that raises it — do not add it to a shared exceptions
    module, since none exists in `src/lab/`).
  - Add `class RevertSimulationKnowledgeWorkflow` with `__init__(self, workspace_root=None)` mirroring
    `UpdateSimulationKnowledgeWorkflow.__init__` exactly (same `workspace_root`/`session_store`/
    `knowledge_root` construction), and `run(self, session_id: str) -> RevertSimulationKnowledgeResult`:
    1. `trail = LabAuditTrail(self.workspace_root)`; `log = trail.read_log(session_id)`.
    2. Scan `log` in reverse for the most recent `knowledge_sync_result` event and its immediately
       preceding `files_written` event (both logged back-to-back in `run()`, so adjacency is a safe
       match — no new join key needed). If none found, or the most recent `knowledge_sync_result`
       has `status == "NO_INSIGHTS"`, return `{"status": "NOTHING_TO_REVERT", "session_id":
       session_id, "removed_files": []}` without touching the filesystem or logging a revert event
       (nothing was written, so there is nothing to audit as reverted).
    2b. **Legacy-log guard (required — not optional):** any `audit_log.jsonl` written before this
       ticket's Step 1 lands has `files_written`/`knowledge_sync_result` events that do NOT contain
       `file_hashes` or `decision_log_entry` — those keys did not exist yet. Before proceeding,
       check both keys are present with `.get(...)`; if either is missing, raise
       `LabKnowledgeRevertError("this sync predates hash-tracking support and cannot be safely
       reverted")` immediately — do not let a bare `KeyError` propagate, and do not attempt a
       best-effort partial revert against an under-specified legacy record.
    3. Build the target file list from `files_written.details["files"]`, excluding `report_path`
       (absolute path string, recognizable because it does not match any `self.knowledge_root`-
       relative prefix) and `"decisions/decision_log.jsonl"` (handled separately in step 5 below).
    4. For each remaining path, resolve relative to `self.knowledge_root`, delete if present; collect
       actually-removed paths into `removed_files` (a path already absent is not an error — treat as
       already-reverted/idempotent, do not count it in `removed_files`).
    5. For the decision log: read `decisions/decision_log.jsonl` line by line, parse each as JSON,
       find the line(s) whose full dict equals `knowledge_sync_result.details["decision_log_entry"]`
       exactly. If exactly one match, rewrite the file via temp-file + `os.replace` omitting that one
       line (never in-place streaming truncation) and add `"decisions/decision_log.jsonl"` to
       `removed_files`. If zero or more than one match, raise `LabKnowledgeRevertError` — ambiguous or
       already-gone decision entries must fail loudly, never guess.
    6. `trail.log_event(session_id, "knowledge_reverted", {"removed_files": removed_files})`.
    7. Return `{"status": "REVERTED", "session_id": session_id, "removed_files": removed_files}`.
- **Do NOT touch:** `UpdateSimulationKnowledgeWorkflow.run()` beyond Step 1's edits; `LabAuditTrail`
  itself (no new method added there — revert logic lives in the new workflow class, consistent with
  `audit.py` staying a thin generic log I/O + approval-gate module).
- **Verify:** `pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py -v -k
  "revert_function_exists or revert_removes_exact_files_written or revert_logs_audit_event or
  revert_decision_log_removes_only_matching_line or revert_fixes_known_issues_and_rules_omission or
  revert_rejects_legacy_log"`. Add `test_revert_rejects_legacy_log_missing_hash_keys` (new, added
  during this step, not pre-listed in test_plan.md — a direct consequence of the architecture
  review's finding): construct an `audit_log.jsonl` by hand with a `files_written`/
  `knowledge_sync_result` pair that omits `file_hashes`/`decision_log_entry` (simulating a
  pre-Step-1 session), call revert, assert `LabKnowledgeRevertError` is raised with a message
  naming the legacy-format cause, and that no file on disk is touched.

### Step 3 — Supersede detection and rejection (AC3)

- **Files:** `src/lab/workflows.py` (`RevertSimulationKnowledgeWorkflow.run`, extending step 4 of
  Step 2's logic above).
- **Change:** before deleting *any* file, pre-flight-check every insight/issue/rule path in the
  target list: if the file exists on disk, compute its current `sha256` and compare against
  `files_written.details["file_hashes"][path]`. If the file is missing entirely, skip it in the
  pre-flight check (already gone — not a supersede case, handled as idempotent no-op per Step 2).
  If the file exists and its hash differs from the recorded one, raise `LabKnowledgeRevertError`
  ("target file has been modified by a later operation and cannot be safely reverted") **before**
  deleting anything else in this sync — the check runs over the whole file set first so a rejected
  revert never partially deletes some files and leaves others. Insights can structurally never hit
  this path (duplicate-write guard at `run()` L2438–2439 means no later sync can overwrite an
  existing insight file), so in practice this only fires for `known_issues/`/`rules/` paths — no
  special-casing needed, the hash check is uniform across all three.
- **Do NOT touch:** Step 1/2 logic beyond adding this pre-flight loop; do not add cross-session
  audit-log scanning (rejected — see Anti-Drift Notes) or any change to `LabSessionStore`
  (`session.py`) to enumerate other sessions.
- **Verify:** `pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py -v -k
  "revert_rejects_superseded"`.

### Step 4 — Update `docs/ai/workflows.md` (AC5)

- **Files:** `docs/ai/workflows.md` (`update-knowledge-store` section, ~L330), `docs/ai/
  agent_infrastructure_audit.md` (L59, L71).
- **Change:** replace the "how to revert" claim in `workflows.md` with accurate prose:
  `RevertSimulationKnowledgeWorkflow.run(session_id)` reverts the most recent sync for that session;
  removes exactly the insight/known-issue/rule files recorded in that sync's `files_written` event;
  matches and removes the corresponding `decision_log.jsonl` line by exact content equality; rejects
  with `LabKnowledgeRevertError` if any target file was modified by a later sync; logs a
  `knowledge_reverted` audit event; does not regenerate or revert `knowledge_update_report.md`. In
  `agent_infrastructure_audit.md`, append one line at L59/L71 noting the gap is closed by this
  ticket (pointer only — do not rewrite that document's point-in-time audit framing).
- **Do NOT touch:** any other section of either doc.
- **Verify:** manual read-through; no automated test (doc-only, per test_plan.md AC5 note).

### Step 5 — Parity ledger entries

- **Files:** `docs/parity_ledger/infrastructure.yaml`.
- **Change:**
  - Add a new entry `INFRA-261` (next sequential ID after the confirmed current highest,
    `INFRA-260`; re-confirm at implementation time in case a concurrent ticket has since added one)
    — `status: verified`, describing the revert capability, `v2_evidence` pointing to
    `src/lab/workflows.py::RevertSimulationKnowledgeWorkflow`, `test_path` pointing to the new
    revert tests added in Steps 2–3.
  - Update `INFRA-225`'s `text` (`docs/parity_ledger/infrastructure.yaml:2683-2691`): its literal
    claim "All 7 lab Workflow.run() methods... return specific TypedDict types" becomes factually
    wrong the moment `RevertSimulationKnowledgeWorkflow` lands with its own TypedDict-returning
    `run()` — change "7" to "8" and add `RevertSimulationKnowledge` to the enumerated flat-TypedDict
    workflows list (alongside `GenerateSimulationSetup`/`UpdateSimulationKnowledge`, since it has no
    BLOCKED path either — its only branch is `REVERTED`/`NOTHING_TO_REVERT`, both terminal). Keep
    `status`/`priority` unchanged — this is a count update, not a re-certification.
- **Do NOT touch:** `INFRA-186` (remains accurate as written — verified against current text).
- **Verify:** YAML parses; new entry has all fields the sibling entries have (`id`, `text`,
  `status`, `priority`, `v2_evidence`, `test_path`); `INFRA-225`'s updated text accurately reflects
  8 workflow classes by grepping `class .*Workflow` in `src/lab/workflows.py` and counting.

## Scope Guards

- Do not implement revert by scanning every session's `audit_log.jsonl` for supersede detection —
  hash comparison against live file state is sufficient and was chosen specifically to avoid that
  complexity (see Anti-Drift Notes).
- Do not add a per-entry ID field to `decision_log.jsonl`'s own schema — matching uses the audit
  trail's own `details` dict (already free-form), not a change to the shared append-only file's
  format.
- Do not touch `report_path`/`knowledge_update_report.md` revert or regeneration — explicitly out of
  scope per the ticket.
- Do not add a CLI/skill-level `/revert-knowledge-sync` command — out of scope per the ticket; this
  plan only adds the underlying `src/lab/` capability.
- Do not modify `LabAuditTrail.log_event`/`read_log` signatures — only new event *types* and new
  `details` keys are introduced, which is backward compatible with the one other caller
  (`LabApprovalGate.record_approval`, `src/lab/audit.py:37-99`).

## Dependency Map

- Step 2 depends on Step 1 (revert reads `file_hashes` and `decision_log_entry`, which only exist
  once Step 1's emission fix lands).
- Step 3 depends on Step 2 (pre-flight hash check is inserted into the deletion loop Step 2 builds).
- Step 4 depends on Steps 1–3 being functionally complete (docs describe the real, finished
  mechanism, not an in-progress one).
- Step 5 depends on Steps 1–3 (needs final test paths and class name to cite as evidence).

## Acceptance Criteria Map

| Acceptance Criterion | Step(s) |
|---|---|
| A revert function exists in `src/lab/` taking a session_id and undoing a specific prior sync | Step 2 |
| Reverting removes exactly the files listed in `files_written` — no more, no less | Step 1, Step 2 |
| Reverting a superseded sync is rejected with a clear error | Step 3 |
| The revert action is logged to `audit_log.jsonl` as a new event type | Step 2 |
| `docs/ai/workflows.md` accurately describes the real mechanism | Step 4 |
| New tests cover successful revert, supersede rejection, audit trail correctness | Steps 2, 3 (tests run alongside each step per test_plan.md) |

## Anti-Drift Notes

- The write-path fix in Step 1 is necessary plumbing, not scope creep: Acceptance Criterion 2 is
  phrased in terms of "the files listed in that sync's `files_written` event," and today that list
  is provably incomplete for the exact target types (`known_issues/`, `rules/`) the ticket's own
  Scope section names as things revert must handle. Fixing it here, narrowly, inside the same
  function this ticket already lists as a Related Code Area, is in scope; it would only be scope
  creep if it touched unrelated behavior (it does not — no control-flow, approval, or duplicate-guard
  logic changes).
- Supersede detection deliberately uses live-file content hashing, not audit-log-wide scanning
  across sessions. Scanning every session's `audit_log.jsonl` would require new enumeration logic in
  `LabSessionStore` (`session.py`) that nothing in this ticket's scope calls for, and would still be
  racy against manual file edits outside any workflow. Hash comparison against what was actually
  written is simpler, deterministic, and catches both cases (a later sync's overwrite, or an
  out-of-band edit) uniformly.
- Do not reuse `ValueError` for the new rejection paths — use the dedicated
  `LabKnowledgeRevertError` so tests and callers can distinguish "revert was rejected" from the
  pre-existing `ValueError`s `run()` already raises for approval/duplicate-insight failures (which
  must remain unchanged).
- Do not let the decision-log rewrite (Step 2, step 5 of the method) do an in-place streaming
  overwrite — it must write to a temp file and `os.replace` it, per the investigation's explicit
  warning about corrupting concurrent appends from other sessions.
- All three of the investigation's open questions are resolved in this plan (not deferred): (1)
  location is `workflows.py`, a new sibling class, because `knowledge_root`/`session_store` already
  live on `UpdateSimulationKnowledgeWorkflow` and every existing workflow in this file follows the
  one-class-per-action pattern — `audit.py` stays a thin, domain-agnostic log/approval utility; (2)
  no per-entry ID is added to `decision_log.jsonl`'s schema — the audit event's `details` dict
  carries the exact-match key instead; (3) the `files_written` fix is done in this ticket (Step 1),
  because AC2/AC3 are unsatisfiable without it.

## Unresolved Questions

None blocking. One implementation-time detail to confirm rather than decide now: the exact next
free `INFRA-###` number in `docs/parity_ledger/infrastructure.yaml` for Step 5 (highest currently
observed is `INFRA-260`; re-check at implementation time in case a concurrent ticket has since added
one).

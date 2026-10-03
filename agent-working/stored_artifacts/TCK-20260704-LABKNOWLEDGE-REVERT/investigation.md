---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260704-LABKNOWLEDGE-REVERT
artifact_type: investigation
tags: [lab-agent, knowledge-store, audit-trail, rollback]
---

# Investigation — TCK-20260704-LABKNOWLEDGE-REVERT

## Current Behavior

`LabAuditTrail` (`src/lab/audit.py`) has exactly two public methods, unchanged by the sibling
timestamp fix:

- `log_event(session_id, event_type, details)` (`src/lab/audit.py:121-138`) — appends a structured
  JSON line (`timestamp`, `event_type`, `details`) to `data/lab_sessions/{session_id}/audit_log.jsonl`
  via `datetime.now(timezone.utc).isoformat()` (L129). Append-only, no delete/rewrite path.
- `read_log(session_id)` (`src/lab/audit.py:140-155`) — reads the full log back as a list of dicts.

There is no third method. **No revert/rollback capability exists anywhere in `src/lab/`.**

`UpdateSimulationKnowledgeWorkflow.run()` (`src/lab/workflows.py`, class declared at line 2322,
`run()` at line 2337) is the write path this ticket needs a revert for. Line numbers below are
current as of the `TCK-20260704-LABKNOWLEDGE-TIMESTAMP` merge (that fix added one `from datetime
import datetime, timezone` import line and replaced two hardcoded string literals in place — it
did not restructure the method, but it does shift every line after the import by +1 relative to
the pre-fix file. The line numbers recorded in this document are read directly from the current
file, not derived by offsetting old numbers.):

- `src/lab/workflows.py:2436-2453` — insight storage. L2438-2439 raises `ValueError` if
  `insights/{insight_id}.json` already exists (one-time-write guarantee for insights). L2441-2450
  builds `insight_record`; `created_at` (L2449) now uses `datetime.now(timezone.utc).isoformat()`
  (previously the hardcoded `"2026-05-24T10:00:00Z"` this investigation originally flagged as a
  problem — that specific defect is fixed and out of scope here per `TCK-20260704-LABKNOWLEDGE-TIMESTAMP`,
  which is DONE).
- `src/lab/workflows.py:2456-2482` — `stored_patches` handling. `KnownIssues` target type writes
  `known_issues/{patch_id}.json` (L2459-2470); `ScenarioSpec`/`WorldSpec` target types write
  `rules/{patch_id}.json` (L2471-2482). **No duplicate/one-time-write check exists for either
  branch** — unlike the insights loop, a later sync can silently overwrite an existing
  `known_issues/*.json` or `rules/*.json` file with the same `patch_id`. This is the "supersede"
  case the acceptance criteria requires revert to detect and reject.
- `src/lab/workflows.py:2485-2493` — appends one line to `data/lab_knowledge/decisions/decision_log.jsonl`
  (append-only JSONL: `session_id`, `decision_note`, `approved_by`, `timestamp`). `timestamp` (L2490)
  is also now dynamic (fixed by the same sibling ticket). No per-entry ID in the schema.
- `src/lab/workflows.py:2504-2518` — the audit trail records, in order: `files_read` (L2504-2506),
  `files_written` (L2507-2509), `knowledge_sync_result` (L2510-2514, carrying `status` /
  `synced_insights` / `synced_patches`), and `workflow_completed` (L2515-2518).

## New Finding Not in Prior Investigation Pass: `files_written` Is Incomplete and Inconsistently Formatted

Re-reading the exact `files_written` payload at `src/lab/workflows.py:2507-2509`:

```python
trail.log_event(session_id, "files_written", {
    "files": [str(report_path), "decision_log.jsonl"] + [f"insights/{i['insight_id'].lower()}.json" for i in stored_insights]
})
```

Two problems directly affect Acceptance Criterion 2 ("Reverting removes exactly the files listed
in that sync's `files_written` event — no more, no less"):

1. **`stored_patches` (the `known_issues/*.json` and `rules/*.json` files written in step 7,
   `src/lab/workflows.py:2456-2482`) are never added to the `files_written` list at all.** Only
   `report_path`, the literal string `"decision_log.jsonl"`, and per-insight paths are recorded. A
   revert built strictly off `files_written` as currently emitted would leave every known-issue and
   rule-patch file orphaned on disk after a "successful" revert — silently violating the "no more,
   no less" criterion in the direction of leaving stale state behind, not deleting too much.
   **The revert ticket's Scope explicitly lists `known_issues/`, `rules/` as things revert must
   remove — this is only possible if `files_written` is extended to include them, or if revert
   independently re-derives those paths from `stored_patches`/`approved_patches` at write time.
   This is a load-bearing gap the Plan phase must resolve, not a cosmetic one.**
2. **Path format is inconsistent across the three kinds of entries in the same list**:
   `str(report_path)` is a fully resolved absolute path; `"decision_log.jsonl"` is a bare filename
   with no directory prefix (not even `"decisions/decision_log.jsonl"`); the insight entries use a
   `"insights/{id}.json"` relative-to-`knowledge_root` prefix. A revert function that tries to
   resolve these three shapes against `self.knowledge_root` uniformly will mis-locate the decision
   log entry unless it special-cases the bare filename. This inconsistency predates this ticket and
   is not something `TCK-20260704-LABKNOWLEDGE-TIMESTAMP` touched.

## Mechanics/Engine Constraints

This subsystem is explicitly out-of-band from core simulation determinism: `docs/parity_ledger/infrastructure.yaml`
entry `INFRA-186` records "Lab state is shadow state — not in `AuthoritativeState` hash" — so this
ticket's revert mechanism does not need to satisfy the Kernel's authoritative-mutation-pipeline
contract (`docs/engine/authoritative_mutation_pipeline_contract.md`) the way a durable-world change
would. It still must satisfy this repo's general Durable State Rule (CLAUDE.md): the revert action
itself is new durable meaning and must be typed/auditable, not a bare file delete.

`INFRA-225` records that `UpdateSimulationKnowledgeWorkflow.run()` returns the
`UpdateSimulationKnowledgeResult` TypedDict (`src/lab/results.py:114-121`, fields `status: Literal["SYNCED",
"NO_INSIGHTS"]`, `report_path: str`, `synced_count: int`). A new revert function's return shape
should follow the same "typed, no raw dict[str, Any]" convention rather than returning an
untyped dict — a new TypedDict (e.g. `RevertKnowledgeSyncResult`) in `src/lab/results.py` is the
pattern-consistent choice, though the exact shape is a Plan-phase decision.

## Parity Ledger Overlap

No parity ledger entry in `docs/parity_ledger/infrastructure.yaml` (the file covering lab/audit/
observability) currently describes the audit trail's revert capability, `files_written` schema, or
`knowledge_sync_result` event semantics specifically. The two closest entries are `INFRA-186`
(general lab shadow-state description) and `INFRA-225` (typed workflow results) — neither is
`status: divergent` or otherwise flags the revert gap. **A new `INFRA-2xx` entry should be added
once revert is implemented**, referencing the new function and its test path; until then this is a
`missing` coverage area, not a `divergent` one, since there was never a code claim of revert working
that the ledger endorsed (only `docs/ai/workflows.md` made that claim, informally, outside the
ledger's authority).

## Prior Work

- `TCK-20260524-LAB-KNOWLEDGE` (DONE) — original implementation of
  `UpdateSimulationKnowledgeWorkflow` and `LabAuditTrail`/`LabApprovalGate` (Milestones 102/103).
  Establishes the append-only audit log pattern this ticket must extend, not replace.
- `TCK-20260610-KNOWLEDGE-APPROVAL-SPLIT` (DONE) — split a permissive approval assertion into three
  explicit status-path tests in the same test file this ticket will extend
  (`tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`). No revert content;
  relevant only as evidence of this test file's established per-status-path test style
  (`test_approved_with_no_insights_returns_no_insights`, `test_approved_with_insights_not_blocked`).
- `TCK-20260704-LABKNOWLEDGE-TIMESTAMP` (DONE, merged as commit `2edfc418`) — fixed the two
  hardcoded `"2026-05-24T10:00:00Z"` literals flagged by the original pass of this investigation.
  Added `test_knowledge_timestamps_are_dynamic` (`tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py:316-364`)
  which runs the workflow twice via `tmp_path_factory` against independently built workspaces and
  asserts both timestamp fields are live and differ across runs — a useful template for any new
  revert test that needs two independent sync events to test supersede-rejection.
- `docs/ai/agent_infrastructure_audit.md:59,71` — an infrastructure review that independently
  flagged this exact gap ("Rollback path for knowledge-store writes is described, not verified" /
  "Exercise the knowledge-store revert path once, for real") before this ticket was opened. No
  code changes resulted from that review; this ticket is the first to act on it.
- Grep for `revert`/`rollback`/`knowledge_reverted` across `src/lab/` and `docs/REGISTRY.yaml`
  found no other related ticket or code beyond the three above and the unrelated
  `TCK-20260424-PH12-M1-READINESS`/`M4-CUTOVER-VALIDATION` tickets, which cover deployment-cutover
  rollback (a different subsystem — Phase 12 runtime cutover, not the lab knowledge store) and are
  not relevant prior art for this ticket's scope.

## Existing Test Fixtures to Reuse

`tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py` (365 lines currently):

- `_build_knowledge_workspace(tmp_path)` (L16-107) — the actual workspace-building logic: creates a
  session, a completed lab run with one CRITICAL anomaly, and runs Compact → Investigate → Propose
  workflows in sequence so the session lands with staged insight candidates and a proposed patch
  ready for `UpdateSimulationKnowledgeWorkflow` to consume.
- `mock_workspace_for_knowledge` (`@pytest.fixture`, L110-112) — thin fixture wrapper calling
  `_build_knowledge_workspace(tmp_path)`. **Correction to prior investigation pass: this is a
  fixture at L110-112, not a bare function at L15** — the L15 reference in the earlier draft was
  inaccurate independent of the timestamp fix (there is no line 15 content resembling this; L15 is
  a blank line after the imports block, which ends at L14).
  `_build_knowledge_workspace` was previously mislabeled with this fixture's name.
  Any revert test should call `UpdateSimulationKnowledgeWorkflow(...).run(...)` against this fixture
  first to produce a real, completed sync to revert.
- `mock_workspace_empty_insights` (`@pytest.fixture`, depends on `mock_workspace_for_knowledge`,
  L239-252) — same workspace but with insight candidates and proposed patches cleared, producing a
  `NO_INSIGHTS` sync. **Correction: L233 in the prior pass was wrong; the fixture is at L239-252.**
  Useful for a revert test asserting that reverting a `NO_INSIGHTS` sync either no-ops cleanly or
  is rejected as "nothing to revert" (Plan phase should decide which).
- `test_approved_with_no_insights_returns_no_insights` (L255-282) and
  `test_approved_with_insights_not_blocked` (L285-313) — **corrections: prior pass cited L248 and
  L278 respectively; both are off by ~7-27 lines.** Both already read back
  `trail.read_log(session_id)` and filter by `event_type` — the exact pattern a new
  `test_revert_logs_audit_event`-style test should follow.
- `test_knowledge_timestamps_are_dynamic` (L316-364, added by the sibling TIMESTAMP ticket, not
  present when the original investigation pass was written) — demonstrates running the workflow
  twice against two independently built `tmp_path_factory` workspaces; a revert test that needs
  "sync A, then sync B supersedes A's target file, then attempt to revert A" can follow this
  two-workspace-run pattern but within a *single* workspace (two sequential `.run()` calls against
  the same `mock_workspace_for_knowledge`, not two separate workspaces) to actually exercise the
  supersede-conflict path.

## Risks and Open Questions

- **Supersede risk differs by target type.** Insights (`insights/*.json`) already have a hard
  duplicate-write guard (`src/lab/workflows.py:2438-2439`), so a same-`insight_id` supersede is
  structurally prevented today — revert of an insight sync can never conflict with a later sync of
  the same insight. `known_issues/*.json` and `rules/*.json` (via `stored_patches`, L2456-2482) have
  **no such guard** — a later sync with the same `patch_id` silently overwrites. This is the real
  case Acceptance Criterion 3 ("revert of a superseded sync is rejected") must guard against, and it
  can only be detected by comparing file mtime/content-hash against what the audit log recorded at
  write time, or by scanning later `audit_log.jsonl` events for a `files_written` entry touching the
  same path — the exact detection mechanism is a Plan-phase decision.
- **`files_written` omits `known_issues/`/`rules/` paths entirely** (see "New Finding" section
  above) — this must be fixed as part of this ticket's implementation, not deferred, since
  Acceptance Criterion 2 is written in terms of "the files listed in that sync's `files_written`
  event," and today that list is incomplete for exactly the target types revert must be able to
  restore/remove.
- **`decision_log.jsonl` is append-only with no per-entry ID** — reverting "the decision logged in
  session X" means locating and removing one specific line from a file shared across all sessions,
  keyed only by `session_id` (+ now a real `timestamp`, post-`TIMESTAMP`-fix, which at least makes
  the match key practically unique in ways it wasn't when the timestamp was a shared hardcoded
  literal). The Plan phase should decide whether a per-entry ID needs to be added at write time
  before revert can target a specific decision-log line unambiguously, given a session could in
  principle sync more than once (nothing in the code prevents calling `.run()` twice for the same
  `session_id`, since there is no session-level "already synced" guard beyond the file-level
  duplicate check).
- **Report regeneration is out of scope** (ticket explicitly excludes `report_path` /
  `knowledge_update_report.md` from revert) — confirmed consistent with current code: the report is
  a derived artifact (`_format_knowledge_report_md`, `src/lab/workflows.py:2526+`), not source-of-truth
  knowledge state.

## Anti-Drift Hazards

- Do not build revert as "delete every file under `data/lab_knowledge/` and re-run" — that would
  discard writes from other sessions synced in between, which is exactly the silent-data-loss
  pattern Acceptance Criterion 3 is meant to prevent.
- Do not implement revert against the `files_written` event as currently emitted without first
  fixing the omission of `known_issues/`/`rules/` paths — doing so would make revert *appear* to
  work in the existing insight-only integration tests while silently failing to clean up known-issue
  or rule-patch writes, which is worse than an obviously-missing feature because it looks tested.
- The revert action itself must be logged via `trail.log_event(session_id, "knowledge_reverted",
  {...})` (or an equivalently named new event type), never a bare file delete with no audit trail
  entry — an unaudited revert defeats the purpose of this being an audited knowledge store, and is
  explicitly called out as a requirement in Acceptance Criterion 4.
- Do not silently truncate or rewrite `decision_log.jsonl` wholesale when reverting one entry — it
  is shared, append-only, multi-session state; only the specific line(s) matching the target
  session/sync should ever be removed, and the removal mechanism should itself be careful not to
  corrupt concurrent appends from other sessions (file-level locking/atomic rewrite discipline, not
  in-place line deletion via streaming overwrite without a temp-file swap).

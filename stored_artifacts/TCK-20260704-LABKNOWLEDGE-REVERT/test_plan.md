---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260704-LABKNOWLEDGE-REVERT
artifact_type: test_plan
tags: [lab-agent, knowledge-store, audit-trail, rollback]
---

# Test Plan — TCK-20260704-LABKNOWLEDGE-REVERT

## Regression Surface

Files touched by implementation will be `src/lab/audit.py` and/or `src/lab/workflows.py`
(wherever the revert capability lands — see investigation.md's note that the exact class/module
is a Plan-phase decision) and `src/lab/results.py` (if a typed revert result is added). Because
`UpdateSimulationKnowledgeWorkflow.run()` itself must change (to fix the `files_written` omission
of `known_issues/`/`rules/` paths — see investigation.md "New Finding"), every existing test in
`tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py` that inspects
`files_written` payload shape is regression surface, even though none currently assert on it
directly (`grep` of that file shows no existing test reads the `files_written` event's `details`
field — only `knowledge_sync_result` is asserted on, e.g. L279-282, L310-313). Confirm this remains
true after the fix; if any test is later added that snapshots the exact `files_written.files` list,
it must be updated to include `known_issues/*.json` / `rules/*.json` entries.

Also in scope as regression surface:
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py::test_knowledge_update_success`
  (asserts on stored insight/issue/decision file contents but not `files_written` shape) — must
  still pass unchanged.
- `tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py::test_knowledge_timestamps_are_dynamic`
  — must still pass; revert must not touch the dynamic-timestamp code path fixed by the sibling
  ticket.
- Any other consumer of `LabAuditTrail.read_log()` or `.log_event()` signatures — a broader grep
  turned up no other call sites outside `src/lab/workflows.py`'s workflow classes and
  `src/lab/session.py`'s `LabApprovalGate` (which uses `log_event` only, at
  `src/lab/session.py`... note: `LabApprovalGate` actually lives in `src/lab/audit.py:28-109`, not
  `session.py` — `record_approval` at `audit.py:37-99` calls `trail.log_event(session_id,
  "approval_recorded", ...)` at L92-97). Adding a new event type must not break this or any other
  existing `log_event` caller since `log_event`'s signature is unchanged by this ticket.
- `tests/unit/lab_agent/test_audit_trail.py` — direct unit tests of `LabAuditTrail`; must continue
  to pass unmodified unless the revert capability is added as a new method on that class, in which
  case new unit tests belong there too (see below).

## New Tests Required (per Acceptance Criterion)

**AC1 — a revert function exists that takes a session_id and undoes a specific prior knowledge
sync.**
- `test_revert_function_exists_and_is_callable` (or fold into the success test below) —
  smoke-level: import the revert entrypoint (exact name TBD by Plan phase, e.g.
  `LabAuditTrail.revert_sync(session_id, sync_event_id)` or a new
  `RevertSimulationKnowledgeWorkflow.run(...)`), call it against a real prior sync, assert it
  returns without raising.

**AC2 — reverting removes exactly the files listed in that sync's `files_written` event — no more,
no less.**
- `test_revert_removes_exact_files_written` — run `UpdateSimulationKnowledgeWorkflow` once against
  `mock_workspace_for_knowledge` to produce a `SYNCED` result; capture the `files_written` event via
  `LabAuditTrail(...).read_log(session_id)`; call revert; assert every path in that event's
  `details["files"]` no longer exists (or, for `decision_log.jsonl`, that only the specific
  appended line is gone, not the whole file — see AC-specific test below); assert no *other* file
  under `data/lab_knowledge/` was touched (e.g. write an unrelated sentinel file into
  `data/lab_knowledge/insights/` before revert and assert it survives).
- `test_revert_fixes_known_issues_and_rules_omission` — this is the regression test for the
  investigation's "New Finding": run a sync that produces both a `KnownIssues`-target patch and a
  `ScenarioSpec`/`WorldSpec`-target patch (mutate a proposed patch's `target_type` the same way
  `test_knowledge_anti_misdirection_rules` does at L224-231 of the existing test file, but with
  `approved_by` set so the sync actually succeeds), assert `files_written`'s `details["files"]`
  post-fix now includes the `known_issues/{id}.json` and `rules/{id}.json` paths, then assert revert
  actually deletes those files too (not just the insight file). This test would fail against the
  current, unfixed `files_written` payload and must pass after the ticket's implementation.
- `test_revert_decision_log_removes_only_matching_line` — build a workspace, sync twice against
  *different* sessions (or twice against the same session if that's not blocked — confirm via
  Plan-phase decision on whether a session can sync more than once) so `decision_log.jsonl` has
  two+ lines; revert one sync; assert exactly the one matching line is gone and the other survives
  verbatim (byte-for-byte on the remaining line, to catch any wholesale-rewrite corruption of the
  shared append-only file).

**AC3 — reverting a sync that has been superseded by a later sync touching the same target file is
rejected with a clear error.**
- `test_revert_rejects_superseded_known_issue` — sync session A with a `KnownIssues` patch
  `patch_id=X`; sync session B with a different proposed-patch payload but the same `patch_id=X`
  (exploiting the confirmed lack of a duplicate guard on `known_issues/*.json`,
  investigation.md's "Risks" section, `src/lab/workflows.py:2456-2482`) so B's write silently
  overwrites A's; attempt to revert A's sync; assert a clear, typed error is raised (not a silent
  no-op, not an uncaught exception) and that B's file content is unchanged after the attempt.
  Mirror the same test for a `ScenarioSpec`/`WorldSpec`-target `rules/*.json` supersede.
- `test_revert_insight_supersede_is_structurally_impossible` (documentation-style regression test,
  not a new behavior test) — assert that attempting to sync a duplicate `insight_id` still raises
  `ValueError("Duplicate insight registration detected...")` per the existing
  `test_knowledge_duplicate_insight_rejected` (L182-210) — confirming the investigation's claim that
  insights can never be superseded, so a revert-rejection test for insights is unnecessary/moot.
  This isn't a new test so much as flagging in a comment that the existing duplicate test already
  covers why AC3 doesn't need an insight-specific supersede case.

**AC4 — the revert action itself is logged to `audit_log.jsonl` as a new event type.**
- `test_revert_logs_audit_event` — after a successful revert, call
  `LabAuditTrail(workspace_root).read_log(session_id)` (same pattern as
  `test_approved_with_no_insights_returns_no_insights` L276-282) and assert an event with the new
  `event_type` (e.g. `"knowledge_reverted"` — exact name is a Plan-phase decision, but must be
  distinct from all four existing event types: `workflow_started`, `approval_required`,
  `blocked_action`, `approval_recorded`, `files_read`, `files_written`, `knowledge_sync_result`,
  `workflow_completed`) is present, with `details` identifying the reverted sync (at minimum the
  original `sync_event_id`/timestamp and the list of files actually removed).
- `test_revert_rejection_does_not_log_false_success` — for the AC3 rejection case, assert the
  rejected revert attempt either logs a `blocked_action`-style event (matching the existing pattern
  at `src/lab/workflows.py:2362-2366`) or raises before any audit event is written — but never logs
  a `knowledge_reverted` success event when the revert was actually rejected.

**AC5 — `docs/ai/workflows.md`'s `update-knowledge-store` section accurately describes the real
mechanism.**
- No pytest coverage (doc-only). Verification is manual: confirm the "Audit log JSON (what was
  included, excluded, approved, and how to revert)" line (`docs/ai/workflows.md:330`) is replaced
  with prose naming the actual function/entrypoint and its supersede-rejection behavior, per this
  repo's parity-between-docs-and-code convention (CLAUDE.md "Authoritative Mechanics Rule").
  Cross-check `docs/ai/agent_infrastructure_audit.md:59,71` — those two "unverified"/"exercise
  once" lines should also be revisited (not necessarily edited, since that doc is a point-in-time
  audit snapshot, but the Plan/Implementation phase should note whether a follow-up note is
  warranted).

## Scoped Pytest Commands

```bash
# Full existing suite for this workflow (must stay green throughout implementation)
pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py -v

# New revert-specific tests, once added (adjust node IDs to match actual test names chosen)
pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py -v -k "revert"

# Unit-level audit trail tests (if revert lands on LabAuditTrail)
pytest tests/unit/lab_agent/test_audit_trail.py -v

# Broader lab_agent domain sanity check (matches prior sibling ticket's "84/84 lab_agent tests
# pass" scope note in commit 2edfc418 — use as a baseline count to diff against)
pytest tests/integration/lab_agent/ tests/unit/lab_agent/ -v

# Do NOT run the full suite per CLAUDE.md Testing Rule; if a slow-marker sweep is needed:
pytest tests/integration/lab_agent/ tests/unit/lab_agent/ -m "not slow"
```

## Anti-Drift Test Guards

- Any new test that builds a second sync to test supersede-rejection (AC3) must reuse
  `_build_knowledge_workspace`/`mock_workspace_for_knowledge` rather than hand-rolling a second
  ad hoc workspace — consistency with the existing fixture style keeps the supersede tests directly
  comparable to `test_knowledge_duplicate_insight_rejected` (L182-210), which already demonstrates
  the "pre-seed a conflicting file, then assert rejection" pattern this ticket's AC3 tests should
  follow structurally.
- Tests must assert on the *typed* return/exception shape, not just "no exception raised" — per
  CLAUDE.md's "Do not expose raw domain models... typed records" rule, a revert result should be
  asserted against its concrete fields (e.g. `result["reverted_files"]`), not just truthiness.
- No test should assert against the old hardcoded timestamp literal `"2026-05-24T10:00:00Z"` for
  any matching/lookup logic — that literal is dead now (fixed by the sibling TIMESTAMP ticket) and
  any revert logic that happened to key off it would be silently broken; `test_knowledge_timestamps_are_dynamic`
  already guards against reintroduction of the literal itself, but a new anti-drift assertion in the
  revert tests should confirm revert matches by `session_id` (+ event identity), never by
  timestamp-string equality.
- Do not test revert by asserting `data/lab_knowledge/` directory is empty afterward — always
  assert on the specific expected-remaining and expected-removed file sets, so a future change that
  adds a new knowledge-store subdirectory doesn't make an overly broad "is empty" assertion pass or
  fail for the wrong reason.

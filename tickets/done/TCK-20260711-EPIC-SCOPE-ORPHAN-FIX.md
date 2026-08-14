---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260711-EPIC-SCOPE-ORPHAN-FIX
phase: done
date: 2026-07-11
tags: []
---

# TCK-20260711-EPIC-SCOPE-ORPHAN-FIX

## Title
Fix Scope phase to move (not copy) todos-originated tickets and detect/sweep pre-existing epic orphans

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
When implement-ticket.js runs the Scope phase on an epic-tier ticket that originated under tickets/todos/**/, the ticket-scoper prompt's Step 1c unconditionally copies the ticket to tickets/inprogress/{tid}.md before the tier is known to the orchestrator. For hotfix/standard tickets this copy is later reconciled by Finalize (moved to tickets/done/ or deliberately left as a live working copy). But epic-tier tickets return EPIC_SCOPED immediately after Scope and never reach Finalize by design, so nothing ever cleans up or reconciles the tickets/inprogress/ copy -- it becomes a permanent byte-identical duplicate of the tickets/todos/ original. Confirmed live on TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC. Violates the repo's Definition of Done ("Repo state is consistent").

## Scope
- Change implement-ticket.js's Step 1c (lines 55-87) so the todos->inprogress transfer for epic-tier tickets is a move (copy-then-delete-original), not a copy-only, eliminating dual on-disk presence while preserving the single-copy-in-tickets/inprogress/ semantics that hotfix/standard Finalize (lines 1040-1043) and epic_staleness_check.py's epic_id-mode discovery (lines 119-163) already depend on.
- Relocate this cp/rm decision out of the ticket-scoper prompt's LLM-interpreted text and into deterministic orchestrator-side bash(), consistent with the pattern already established in TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC of moving prompt-text bookkeeping into orchestrator bash() calls.
- Add a new static self-check (mirroring done_checker_static.py's check_ticket_location (status, evidence) tuple shape at lines 214-220) that scans tickets/inprogress/*.md and flags any epic-tier file whose corresponding tickets/todos/ original still exists on disk -- the actual orphan signature (dual presence), not merely "epic ticket resting in inprogress/" (which is legitimate per docs/ai/ticket-lifecycle.md line 440).
- Because Step 1a checks tickets/inprogress/{ticketId}.md first and returns immediately if found (an existing orphan is never re-touched by re-running Scope), include a one-time detection/sweep against the currently-existing orphan pattern in the live repo in addition to the prevention fix -- prevention alone does not remediate what already exists.

## Out of Scope
- Adding dedupe logic to tools/agent-monitoring/epic_staleness_check.py's discover_candidate_epics() double-discovery across its epic_id-mode and folder-mode scan loops -- tracked separately in TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK since it is a distinct fix in a distinct file with its own test file.
- Any change to the request-mode branch of implement-ticket.js (lines 88-132), confirmed unaffected since only one copy ever exists for freshly-created tickets.
- Redesigning tickets/inprogress/ as a resting place for epic_id-mode epics -- that placement is correct per docs/ai/ticket-lifecycle.md and must be preserved, not removed.

## Acceptance Criteria
- [ ] Running Scope on an epic-tier ticket originating under tickets/todos/** results in exactly one on-disk copy after EPIC_SCOPED returns (in tickets/inprogress/, matching epic_staleness_check.py's expected epic_id-mode location) -- never both simultaneously.
- [ ] Running Scope on hotfix/standard tier tickets is unaffected -- existing copy-then-Finalize-reconciliation behavior and its current test coverage continue to pass.
- [ ] A new static self-check (mirroring check_ticket_location's (status, evidence) tuple shape) scanning tickets/inprogress/*.md flags any epic-tier file whose corresponding tickets/todos/ original still exists (the actual orphan signature -- dual presence, not just "is an epic ticket resting in inprogress/", since that alone is legitimate per ticket-lifecycle.md).
- [ ] Running this new check against the live repo post-fix returns zero orphans.

## Related Tickets
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC
- TCK-20260710-EPIC-STALENESS-CHECK
- TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK (sibling, distinct file/fix, created in parallel)

## Related Docs
- docs/ai/ticket-lifecycle.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/gate_checks/done_checker_static.py
- docs/ai/ticket-lifecycle.md

## Assumptions / Open Questions
- Assumes "move not copy" is the correct fix framing (superseding the original proposal's literal "skip the copy for epic tier" framing, which investigation confirmed would be wrong -- it would leave todos-originated epics permanently absent from tickets/inprogress/, breaking epic_staleness_check.py's epic_id-mode discovery).
- Assumes the one-time sweep for the already-existing orphan (TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC, already manually cleaned this session) is a no-op by the time this ticket is implemented, but the sweep logic itself must still be built and verified against a synthetic fixture, not skipped just because the one known live instance is already gone.

## Implementation Notes

- Built `resolve_and_relocate_ticket()` in new `tools/agent-monitoring/scope_ticket_relocate.py`: a
  pure Python function performing the same `tickets/inprogress -> tickets/done -> tickets/todos/**`
  search the ticket-scoper prompt used to do in agent-interpreted text, reusing
  `epic_staleness_check.py::_section_body()` for `## Tier` parsing. When a ticket is found under
  `tickets/todos/`, it is copied to `tickets/inprogress/{id}.md`; the todos original is then
  deleted only when `## Tier` is `epic` (a move), left in place otherwise (copy-only, preserving
  existing Finalize-reconciliation for hotfix/standard). Returns a dict with a fixed `action` enum:
  `already_in_inprogress` / `already_in_done` / `not_found` / `moved_from_todos` /
  `copied_from_todos`. Ships a `MARKER:`-prefixed CLI entrypoint.
- Wired a new orchestrator helper `resolveScopeTicketLocation()` into
  `.claude/workflows/implement-ticket.js`, defined alongside `captureTs` (~line 198) and invoked
  one statement *before* `const scopeTs = await captureTs()` (never between it and
  `const ticketInfo = await agent(`), preserving the exact literal adjacency
  `tests/tools/test_step0_ts_orchestrator.py` asserts. Result stored in `scopeOrphanInfo`.
- Rewrote the ticketId-branch prompt's old Step 1 (locate + unconditionally copy) and Step 2
  (read tier) into a single stated-facts block using `scopeOrphanInfo.ticket_path` /
  `.tier` / `.todos_source_path` (snake_case, matching this file's existing `ticketInfo.*`
  convention — see plan.md Deviations), plus a not-found fallback that surfaces as a Scope
  conflict instead of silently trying to read an empty path. Steps 3/3a/3b (tag→skill mapping,
  tags echo, mistag warning) are untouched, including their literal numbering.
- Built the standalone `scan_epic_scope_orphans()` sweep in new
  `tools/agent-monitoring/epic_scope_orphan_check.py`, with `check_single_epic_orphan()`
  mirroring `done_checker_static.py::check_ticket_location`'s `(status, evidence)` shape. Flags
  only the actual orphan signature (epic-tier ticket in `tickets/inprogress/` with a
  `tickets/todos/**` original still present) — never epic-resting-alone, never non-epic dual
  presence. Not wired into any workflow phase or into `done_checker_static.py`'s aggregates, per
  the `workflow_meta_conformance.py` precedent this mirrors.
- Verified the live-repo AC #4 check: `scan_epic_scope_orphans()` against the real
  `tickets/inprogress/`/`tickets/todos/` directories returns zero `FAIL` entries today.
- No deviations from architecture constraints; no mechanics/parity impact (pure agent-infra
  tooling). See `staging_artifacts/TCK-20260711-EPIC-SCOPE-ORPHAN-FIX/plan.md`'s new "Deviations"
  section for the two minor, non-behavioral naming/numbering deviations from the plan's
  illustrative pseudocode.

## Test Summary

New tests, all passing:
- `tests/tools/test_scope_orphan_fix.py` (7 tests): placement guard
  (`test_step1c_orphan_bash_precedes_capturets`), epic move
  (`test_epic_tier_move_deletes_todos_original`), standard/hotfix copy-only
  (`test_standard_hotfix_tier_still_copy_only`), already-in-inprogress/already-in-done/not-found
  branch coverage, and the removed-unconditional-copy prompt-text guard
  (`test_ticket_scoper_prompt_no_longer_unconditionally_copies`).
- `tests/tools/test_epic_scope_orphan_check.py` (6 tests): flags dual presence, passes when todos
  original absent, does not flag legitimate epic-resting-in-inprogress, ignores non-epic dual
  presence, live-repo AC #4 zero-findings check, and `done_checker_static.py` signature/shape
  guard.

Full scoped regression pass (per test_plan.md's post-implementation command):
```
pytest tests/tools/test_step0_ts_orchestrator.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_done_checker_static.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_epic_staleness_check.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_scope_orphan_fix.py tests/tools/test_epic_scope_orphan_check.py -v
```
Result: 117 passed, 1 xfailed (pre-existing, unrelated xfail in `test_workflow_meta_conformance.py`). Zero regressions.

Also manually confirmed: `node --check .claude/workflows/implement-ticket.js` passes (syntax valid);
both new modules' `MARKER:`-prefixed CLI entrypoints run cleanly standalone.

## Files Changed

- `tools/agent-monitoring/scope_ticket_relocate.py` (new)
- `tools/agent-monitoring/epic_scope_orphan_check.py` (new)
- `.claude/workflows/implement-ticket.js` (modified — Scope phase orchestrator wiring + prompt text)
- `tests/tools/test_scope_orphan_fix.py` (new)
- `tests/tools/test_epic_scope_orphan_check.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (modified — added INFRA-265)
- `docs/ai/workflows.md` (modified — Scope-phase table row updated to document the new `resolveScopeTicketLocation()` orchestrator step, per DoD Verify finding)

## Completion Summary

Fixed the Scope-phase epic-tier orphan defect by moving the todos->inprogress ticket-location
decision out of agent-prompt text into a deterministic orchestrator-side Python module
(`scope_ticket_relocate.py`), which moves (rather than copies) a todos-originated ticket file only
when its tier is epic — eliminating the permanent duplicate that previously occurred because epic
tier never reaches Finalize's cleanup step. Added a standalone, unwired static sweep
(`epic_scope_orphan_check.py`) that detects the actual dual-presence orphan signature against the
live repo, confirmed to return zero findings today. All four acceptance criteria are met; the two
highest-risk pre-existing regression tests
(`test_step0_ts_orchestrator.py`, `test_current_run_sidecar_orchestrator.py`) pass unmodified,
confirming the new orchestrator `bash()` call was placed correctly relative to `captureTs()`/
`agent()`.

Mid-Verify correction: the first Verify pass flagged that `docs/ai/workflows.md`'s Scope-phase
table row still described only the old prompt-driven copy behavior and did not mention the new
`resolveScopeTicketLocation()` orchestrator step. `docs/ai/workflows.md` was updated in the same
session to document the corrected Scope-phase flow, and a second Verify pass confirmed doc/code
parity before Finalize.

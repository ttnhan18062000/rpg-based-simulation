---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261003-IMPLEMENT-TICKET-JS-USE-BEFORE-DEFINE
phase: done
date: 2026-10-03
tags: [ai, process-improvement]
---

# TCK-20261003-IMPLEMENT-TICKET-JS-USE-BEFORE-DEFINE

## Title
`.claude/workflows/implement-ticket.js` calls two `const` helpers before their definitions, so every native `Workflow` run fails at the Scope phase with a ReferenceError

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary

A native `Workflow` run of `implement-ticket` (the attempt to verify AC 9 of `TCK-20261003-AGENT-WORKING-ROOT-MOVE`)
fails immediately with `ReferenceError: Cannot access 'captureTs' before initialization`. Verified on
`origin/main` (e85db0a2f) by reading the script; the same ordering exists at `243e798ad^`, so the agent-working
move did not cause it, and `const captureTs = async` was last introduced by a bulk commit on 2026-08-14.
Native runs have been unexercised since (the native-port epic proved behaviour with Agent subagents, not the
runtime).

Two top-level `const` arrow functions are called before their definition lines (a top-level `await` runs in
order, so the temporal dead zone throws):

| Helper | First use | Defined | Notes |
|---|---|---|---|
| `captureTs` | line 178 (`const scopeTs = await captureTs()`) | line 427 | unconditional: fails every run |
| `resolveScopeTicketLocation` | line 176 (`ticketId ? await resolveScopeTicketLocation(ticketId) : null`) | line 452 | only when a `ticket_id` is passed, so it would be the **next** failure after `captureTs` is fixed |

A scan of the other top-level `const name = (async) (...) =>` helpers found no further use-before-define (a
regex scan, not a runtime run; the fix must prove it by a run). Both fixes stay within `implement-ticket.js`.

## Scope

- Reorder so each helper is defined before its first use: move the `captureTs` / `captureEpochMs` block and
  `resolveScopeTicketLocation` (with any helper it calls that is itself defined later) above line 176. Keep
  `workflowStartMs` after `captureEpochMs`. Do not change behaviour or prompts.
- Add a static order test: a Python test over `.claude/workflows/*.js` that, for every top-level
  `const name = (async) (...) =>`, fails if the name is called on an earlier non-comment line. Positive control: a
  fixture script with a seeded use-before-define fails; the real script passes after the fix.
- Re-run the tests that pin this file's layout before and after: `tests/tools/test_current_run_sidecar_orchestrator.py`
  (writeSidecar-to-agent() adjacency strings, named in the script's own comment) and
  `tests/agent_orchestration_claude_adapter/test_no_forbidden_calls_against_implement_ticket_js.py`; check any other
  test that pins a line number or adjacency in `implement-ticket.js`.
- A **native run** is a separate verification, needs the owner's explicit `Workflow` opt-in, and is NOT part of
  this ticket's acceptance. This ticket makes it possible and records it as not run.

## Out of Scope

- Any behaviour change, prompt change, phase change or new gate in `implement-ticket.js`.
- Other workflow scripts (none showed the pattern).
- Running the native Workflow (owner opt-in); closing `TCK-20261003-AGENT-WORKING-ROOT-MOVE` AC 9 (that ticket's decision).

## Acceptance Criteria

1. In `implement-ticket.js`, `captureTs`, `captureEpochMs` and `resolveScopeTicketLocation` are defined before their first use.
2. The order test passes on the fixed script and fails on the seeded fixture.
3. The sidecar-adjacency and no-forbidden-calls tests still pass; any other test pinning this file is named and passes.
4. The ticket records that a native run was NOT performed and what it would need (owner opt-in).

## Related Tickets

- `TCK-20261003-AGENT-WORKING-ROOT-MOVE` (AC 9 depends on a runnable native workflow).
- `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT` (epic; deferred children need the native runtime).
- `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH` (introduced `captureTs`).

## Related Docs
`docs/guides/delivery_process.md`; `.claude/skills/implement-ticket/SKILL.md` and its `.agents/` mirror (no change expected).

## Related Stored Artifacts
(None.)

## Related Code Areas
`.claude/workflows/implement-ticket.js`; `tests/tools/test_current_run_sidecar_orchestrator.py`;
`tests/agent_orchestration_claude_adapter/`.

## Assumptions / Open Questions

- Assumed the runtime keeps the script's top level in program order (the failure the implementer saw confirms
  `captureTs`). Whether `resolveScopeTicketLocation` also throws is expected from the same rule and is not run.
- Whether to also add a runtime smoke test with a stubbed `agent()` is left to the implementer; the static test is
  the minimum.

## Implementation Notes
Hotfix tier: no staging artifacts. Moved the `captureTs` / `captureEpochMs` definitions and `resolveScopeTicketLocation` (with their comments, unchanged) to just above `const scopeOrphanInfo`. `const workflowStartMs = await captureEpochMs()` and its comment stay where they were, so its execution point (after the Scope agent) is unchanged. No prompt, phase or gate text changed.

The new test `tests/tools/test_workflow_helper_definition_order.py` has two guards. A static check over every `.claude/workflows/*.js` flags a call on an unindented non-comment line above a top-level `const name = (async) (...) =>` definition; it flags both helpers on the pre-fix script and passes on all eleven scripts now. A node `vm` smoke runs `implement-ticket.js` with every dispatch stubbed to `null`, once without and once with a `ticket_id`; the pre-fix script throws `ReferenceError: Cannot access 'captureTs' before initialization` and, with a `ticket_id`, `... 'resolveScopeTicketLocation' ...`; the fixed script runs to its Scope-failure return. The smoke skips when `node` is absent.

A native `Workflow` run was NOT performed (needs the owner's explicit `Workflow` opt-in). The vm smoke covers the Scope phase only; later phases are covered by the static order check.

## Test Summary
46 files that name `implement-ticket.js`, plus `tests/agent_orchestration_claude_adapter` and the new order test: all pass, 579 passed, 10 skipped, 1 xfailed (baseline before the edit: 531 passed, 10 skipped, 1 xfailed). Two existing tests pinned the old, buggy layout (`captureTs` after `writeSidecar`; `workflowStartMs` before `resolveScopeTicketLocation`) and were updated to the corrected layout. Seeded controls: pre-fix script fails both the static check and the smoke.

## Files Changed
- .claude/workflows/implement-ticket.js (definition order only)
- tests/tools/test_workflow_helper_definition_order.py (new)
- tests/tools/test_step0_ts_orchestrator.py (the pin that put `captureTs` after `writeSidecar` now only requires it before `classifyChecklistFailure`; test renamed)
- tests/tools/test_shadow_reviewer_call_site.py (the pin on `workflowStartMs` now follows `resolveScopeTicketLocation`, matching the unchanged execution point)

## Completion Summary
The two helpers the Scope phase calls first are now defined before use, so the Scope phase no longer throws a ReferenceError under a stubbed run. A new static and node-vm test pins the ordering. The native `Workflow` run itself is not verified here and needs the owner's opt-in.

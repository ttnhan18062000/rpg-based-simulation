---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT
phase: done
date: 2026-09-30
tags: [ai, agent-monitoring]
---

# TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT

## Title
Port `implement-epic.js` to run on the native `Workflow` tool

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The `create-tickets` pilot (`TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT`) recommended GO for
porting `implement-epic.js` next: it already parses cleanly, and its `bash()` sites are
bookkeeping-shaped, so the bounded `runCommand()` tax measured in the pilot should repeat. Apply
the same pattern here.

## Scope
1. Replace the 11 `bash()` sites (timestamps at L34/L87/L279/L305, sidecar/monitoring writes at
   L37/L125/L283/L286/L310/L313, discovery at L148) with `args.start_ts` plus the pilot's narrow
   `runCommand()` helper. Preserve every fail-open WARNING path.
2. Classify each site as bookkeeping or gate before routing it. Any site whose result decides
   pass/fail stays orchestrator-side or is parsed from `{exit_code, stdout}` markers by the script,
   never reported by the agent.
3. Resolve the nested `workflow('implement-ticket', ticketArgs)` call (L347): measure whether the
   native runtime exposes `workflow()` to a script. If not, record the finding and the smallest
   viable fallback (children dispatched by the top-level session) rather than guessing.
4. Write `execution_mode:"workflow"` for native runs. Update `implement-epic` SKILL.md and
   `docs/ai/skills.md` to say what is ported.
5. One real native `/implement-epic` run on a small epic, with a short measurement note in
   `staging_artifacts/` that is then stored.

## Out of Scope
- `implement-ticket.js` (needs its own gate-vs-bookkeeping classification ticket first).
- Any other workflow script, and the Agent SDK path (`TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME`).

## Acceptance Criteria
1. `implement-epic.js` parses under acorn with the runtime's options, pinned by the existing
   `tests/tools/test_workflow_runtime_acorn_parse.py` pattern.
2. No `bash(`, `Date.now(`, `Math.random(` or argless `new Date(` remains; a test pins this.
3. Existing implement-epic tests are updated, not deleted; fail-open paths still covered.
4. Missing `args.start_ts` returns a structured `INVALID_ARGS` result.
5. The nested-workflow question is answered with a measurement and recorded in the ticket.
6. One native run completed; cost-proxy attribution for the epic child rows checked (ties to
   `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION`, now merged).

## Related Tickets
- TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT (done; pattern and go/no-go)
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (backlog parent)
- TCK-20260904-COST-PROXY-EPIC-TICKETS (done; sidecar semantics that must survive)

## Related Docs
- `docs/ai/skills.md`, `docs/agent-monitoring/schema.md`
- `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/pilot_measurement.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/`

## Related Code Areas
- `.claude/workflows/implement-epic.js`, `.claude/skills/implement-epic/SKILL.md`
- `tests/tools/test_*epic*`, `tests/tools/test_workflow_runtime_acorn_parse.py`

## Assumptions / Open Questions
- Open: does the native runtime support `workflow()` inside a script? Measure; don't assume.
- Assumes the pilot's `runCommand()` tax (see measurement note) is acceptable for bookkeeping sites.

## Implementation Notes
**Classification first (scope 2):** all 11 `bash()` sites are bookkeeping (4 timestamps, 5 monitoring record writes, 1 sidecar write, 1 sidecar clear); none decides pass/fail, so the plain `runCommand` route is safe. Table in `investigation.md`.

**Port (scope 1, 4):** `args.start_ts` is required (structured `INVALID_ARGS` with no record, since no truthful timestamp exists); `runCommand()` copied from create-tickets.js; `runMonitoringCommand()` is the fail-open wrapper (exit marker, WARNING, never throws); `writeSidecar`/`clearSidecar` keep their markers and warnings; the two early-exit paths and the INVALID_ARGS-with-args path write records via `runMonitoringCommand` with `start_ts` as both timestamps (no elapsed time is tracked there). `"execution_mode":"workflow"` in every run record. The raw backticks at line 247 (parse blocker added after the pilot) are escaped, and the same one-line defect in create-tickets.js line 855 (added by #267, same class) is fixed so the acorn baseline test passes.

**Nested workflow (scope 3, measured):** `workflow()` nests one level and throws inside a child. implement-epic may call `workflow('implement-ticket', ...)`, but implement-ticket still has 38 `bash(` sites and fails to parse, so the child call cannot succeed today. Smallest fallback, implemented: `WORKFLOW_ERROR` with an instruction to dispatch children from the top-level session, and the SKILL keeps hand-translation as the primary path for epics with pending children until `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`.

**Docs (scope 4):** `.claude/skills/implement-epic/SKILL.md` and `docs/ai/skills.md` say exactly what is ported and what is not.

**Real native run (scope 5, user opt-in 2026-10-01):** `wf_18d6fbaa-844`, NOTHING_TO_DO path on a scratch folder: 5 agents, 234,551 subagent tokens, 50.7 s; records carry `execution_mode:"workflow"`; 9 Discover tool calls attributed at seq -1 under the orchestrating session's id. It found a false zero on the seq-1 early-exit event row (Discover's calls are at seq -1); fixed by widening the omit-when-unattributed rule to any positive-seq implement-epic row. Not exercised: the child loop and the cleanup/close/tracking-doc agents.

## Test Summary
`tests/tools/test_implement_epic_native_port.py` (new, 9): no `bash(` sites, no Date.now/Math.random/argless new Date in code, parses under the runtime's acorn options, structured INVALID_ARGS before any work, run start from `args.start_ts`, monitoring writes fail-open and labelled `workflow`, sidecar helpers via runCommand with markers, runMonitoringCommand labels are record-writes only, unavailable-child fallback. Updated, not deleted: `test_epic_create_tickets_sidecar_orchestrator.py` (2), `test_run_execution_mode_field_wiring.py` (2), `test_step0_ts_orchestrator.py`, `test_record_events.py` (early-exit and collision pins now expect null), the acorn baseline now passes. `pytest tests/tools` and `tests/unit/tools`: see the PR.

## Files Changed
- `.claude/workflows/implement-epic.js`, `.claude/workflows/create-tickets.js` (one-line backtick escape), `.claude/skills/implement-epic/SKILL.md`, `docs/ai/skills.md`, `docs/agent-monitoring/schema.md`
- `tools/agent-monitoring/record_events.py`
- tests: `test_implement_epic_native_port.py` (new), `test_epic_create_tickets_sidecar_orchestrator.py`, `test_run_execution_mode_field_wiring.py`, `test_step0_ts_orchestrator.py`, `test_record_events.py`
- `stored_artifacts/<this ticket>/`; this ticket

## Completion Summary
Done, with one stated limit: the child loop cannot complete natively until implement-ticket.js is ported. AC1: parses under acorn, pinned. AC2: no `bash(`, `Date.now(`, `Math.random(` or argless `new Date(` in code, pinned. AC3: existing tests updated, fail-open paths still covered. AC4: missing `start_ts` returns structured INVALID_ARGS. AC5: nested-workflow question answered by measurement. AC6: one real native run completed (NOTHING_TO_DO path); cost-proxy attribution checked, and the epic early-exit false zero it exposed is fixed.

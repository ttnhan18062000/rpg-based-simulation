---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT
phase: open
date: 2026-09-30
tags: [ai, agent-monitoring]
---

# TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT

## Title
Port `implement-epic.js` to run on the native `Workflow` tool

## Status
OPEN

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
Draft by agent-working-design; the implementer commits it.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.

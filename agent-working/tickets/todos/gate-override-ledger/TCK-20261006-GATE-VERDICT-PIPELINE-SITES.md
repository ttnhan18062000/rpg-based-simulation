---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-PIPELINE-SITES
phase: open
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-VERDICT-PIPELINE-SITES

## Title
Every implement-ticket.js gate writes a gate_verdicts row on pass and on fail

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 2 of `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER`. The formal pipeline keeps a gate's verdict only when it
blocks. A pass is event status `ok`, and the APPROVED text and done-checker checklist are dropped. A false pass
cannot be found if passes are never recorded. This is P3 because the formal pipeline runs rarely: 1 of 37 W41 runs.

## Scope
- In `.claude/workflows/implement-ticket.js`, after each gate listed in `gate-policy.yaml`, write one
  `gate_verdicts` row through child 1's writer, invoked like the existing `pushEvent` monitoring writes. The gates
  are:
  - Scope conflicts and tag check
  - plan gate
  - Review
  - arch static checks
  - Architecture-Verify
  - doc_staleness
  - test_scope_coverage and Test
  - data_runs_cleanup and parity
  - Security-Review
  - Verify / done-checker
  - finalize_selfcheck
- `run_id` and `execution_mode` come from the run. An agent-verdict gate stores the agent's enum. A gate behind
  `shAttested` stores the attestation's `stdout_sha` in `inputs_ref`.
- Add a conformance test: every `gate-policy.yaml` entry has an emit site. Model it on
  `workflow_meta_conformance.py`.

## Out of Scope
- Changing any gate's logic, or the order of gates.
- Outcomes and adjudication (child 3).

## Acceptance Criteria
1. A pipeline dry-run/fixture run that passes all gates writes one row per gate reached, each with `blocking: false`
   and the raw verdict.
2. A fixture run blocked at Review writes the Review row with `verdict: NEEDS_CHANGES, blocking: true`, and writes
   no rows for gates it never reached.
3. The conformance test fails when a `gate-policy.yaml` gate has no emit site, and passes on the result.
4. A ledger write failure does not change `final_status` or the event stream.
5. The workflow tests and the gate-policy conformance tests are green.

## Related Tickets
- `TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES` (depends on it)
- `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST` (where gate-policy.yaml comes from)

## Related Docs
- `agent-working/agent-orchestration/gate-policy.yaml`, `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- None.

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (gates at about :723-2094, `pushEvent` at :561, `shAttested` at :149)
- `tools/gate_checks/workflow_meta_conformance.py`

## Assumptions / Open Questions
- The new writes go through the same monitoring call path the workflow already uses, so they need no new
  permission and no new process.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

## Test Summary

## Files Changed

## Completion Summary

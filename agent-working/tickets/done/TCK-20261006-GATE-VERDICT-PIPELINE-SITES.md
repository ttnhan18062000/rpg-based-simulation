---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-PIPELINE-SITES
phase: done
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-VERDICT-PIPELINE-SITES

## Title
Every implement-ticket.js gate writes a gate_verdicts row on pass and on fail

## Status
DONE

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
`tests/tools/test_gate_verdict_pipeline_sites.py` (33 pass): 13 gate-policy entries each have an emit site and their site precedes the stop; removing a site fails the conformance check; `record_batch` writes one non-blocking row per reached gate, a Review block writes `NEEDS_CHANGES, blocking: true` and nothing later, one bad row does not stop the others, and the CLI exits 0 on bad JSON. Related workflow, conformance and native-refusal tests stay green (142 pass in the selected sweep).

## Files Changed
- `.claude/workflows/implement-ticket.js`, `tools/agent-monitoring/gate_verdicts.py`
- `tests/tools/test_gate_verdict_pipeline_sites.py` (new)
- `docs/agent-monitoring/schema.md`

## Completion Summary
Closed 2026-10-06. AC3, AC4 and AC5 met; AC1 and AC2 are proven at source and function level, not by a live pipeline run (the script cannot run in a test), so the first real pipeline run is their live check. Observed, not changed: on the native runtime a static gate's row carries the attestation's own gate name, not the `gate-policy.yaml` id, so the two spellings do not join in the ledger. Not done: any gate's logic or order (out of scope).

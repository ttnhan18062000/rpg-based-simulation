---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER
phase: open
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER

## Title
Gate override ledger: record every gate verdict, what happened next, and whether it was right

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The direction doc's row "Gate override ledger (verdict, inputs, human stop)" was an idea. On 2026-10-06 the owner
chose it as the item after the hand-closure cost epic, which resolves the direction doc's pending decision.

Today a gate's verdict is kept only when it blocks, as the run's `final_status` plus a coarse `reason_code`. A pass
leaves only status `ok`. The CLIs that hand closures use (`done_checker_static.py`, `post_native_run_check.py`,
`attest_gate.py`) print to stdout only. Nothing records an override, a re-run, or how one of the 27
NEEDS_HUMAN_INPUT rows was resolved. Human overrides show up only in retro prose (W35, AFFECTION-CONTRACT-GATE).
As a result, gate precision is learned only when a person notices. Examples are
`TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS`, `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED` and
`TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE`.

## Scope
Four children (see `SEQUENCE.md`):
1. `TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES`: a `gate_verdicts` shard family, its writer and schema, and
   emitting from the gate CLIs that hand closures run. Hand closures are 36 of the 37 W41 runs that carry
   `execution_mode`, so this site comes first.
2. `TCK-20261006-GATE-VERDICT-PIPELINE-SITES`: every gate in `implement-ticket.js` writes a row on pass and on
   fail, keyed by `gate-policy.yaml`.
3. `TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION`: what followed each blocking verdict (fixed and re-run,
   overridden, stopped, re-run with no change), plus adjudication (true block, false block, false pass, unknown).
4. `TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO`: a report-only precision reading over adjudicated rows, plus a
   retro section.

## Out of Scope
- Ingesting CI jobs and the code-health ratchet (GitHub check runs, rows added to the
  `code_health_exceptions.jsonl` registry). The direction doc gets this as a new idea row; it is the CI-side
  analogue of `TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT`.
- Changing any gate's predicate, threshold or blocking behaviour. The ledger observes and never decides.
- Automatic adjudication. Model-versus-model agreement (shadow reviewer) is not ground truth.

## Acceptance Criteria
1. All four children are DONE.
2. After the first full ISO week following the merge, the retro shows, per `gate_id`: verdict counts, blocking
   count, outcome mix, and adjudicated-row count. Precision is shown only where adjudicated rows exist; elsewhere it
   reads "not adjudicated" and never 100% or 0%
   (`ai_first_hardening_epics/agent_evaluation_foundation_experiment.md:92`).
3. The direction doc row moves from `idea` to `shipped (code)`. Its pending decision about the next item is struck
   through as resolved on 2026-10-06, and a CI-ingest idea row is added.

## Related Tickets
- `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST` (same hand-closure recording path)
- `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN` (the orchestrator re-run backstop; a disagreement there is
  a false-pass signal)
- `TCK-20260915-DUPLICATE-RUN-RECORDS`, `TCK-20260904-SHADOW-REVIEWER-LOGGING`,
  `TCK-20260706-MONITORING-REASON-CODE`, `TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT`

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md` (rows at :54 and :89)
- `docs/agent-monitoring/schema.md`
- `agent-working/agent-orchestration/gate-policy.yaml` (the `gate_id` source)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md`

## Related Code Areas
- `tools/agent-monitoring/` (writer, shard paths, `run_dedup.py`, `generate_retro.py`,
  `record_hand_orchestrated_closure.py`)
- `tools/gate_checks/` (`done_checker_static.py`, `post_native_run_check.py`, `attest_gate.py`,
  `plan_gate_static.py`, `doc_staleness_check.py`)
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- A ledger write failure must never fail a gate or a workflow. This is the same rule as monitoring.
- Adjudication is by a person or a named session. Precision readings will be sparse at first. That is accepted:
  sparse and honest beats full and invented.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06 from a read-only investigation of `origin/main` @ `c41446c86`.

## Test Summary

## Files Changed

## Completion Summary

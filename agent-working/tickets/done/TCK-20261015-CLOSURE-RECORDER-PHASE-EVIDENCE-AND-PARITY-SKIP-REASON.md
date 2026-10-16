---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON
phase: done
date: 2026-10-15
tags: [agent-monitoring, data-quality, workflows]
---

# TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON

## Title
Hand-closure records which phases really ran from artifact evidence, needs a structured Parity skip reason when src/ changed, and the retro counts ledger blocks as gate failures

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Source: RETRO-2026-W41 final note (PR #605), W41/W42 deep investigation 2026-10-15, findings 2 and 5. 330 of 337 W41 + W42 runs were hand-closed, and 246 of 278 W41 runs carry the fixed
6-event template. The Paths section reports Investigate/Plan/Review/Architecture-Verify "omitted" on 125 W41 standard
closures, but 189 of 194 have full staging artifacts. The real gaps (9 standard tickets without artifacts) are buried.
Parity was skipped on 22 W41 and 4 W42 runs whose Files Changed lists `src/`, with only free-text reasons. The W42 Run
Summary says "Gate failures 0" while the Gates section shows 22 blocking Finalize verdicts, because the line counts run
final_status only.

## Scope
1. `record_hand_orchestrated_closure.py` derives the standard-tier phases that ran from evidence: staging/stored
   artifacts present means Investigate/Plan ran (recorded as such, with the artifact path in the summary). It only records
   omitted when the evidence is absent.
2. When the ticket's diff touches `src/` and Parity is skipped, a structured `skip_reason` from the enum is required (no
   free text alone). The recorder refuses otherwise, with a clear message, like its existing guards.
3. `generate_retro.py` Run Summary: show ledger blocking verdicts next to run gate failures (two labelled numbers), so
   "0" no longer hides blocks.

## Out of Scope
- Changing tiers or routing (the Paths routing candidates are the owner's next direction).
- Re-recording historical runs.

## Acceptance Criteria
- Tests: a standard ticket with stored artifacts records Investigate/Plan as ran; one without records them omitted; a
  src/ diff with Parity skipped and no enum reason is refused.
- W42's regenerated Run Summary shows 22 ledger blocks beside 0 run gate failures.

## Related Tickets
- TCK-20261006-EPIC-TICKET-PATH-RECORD
- TCK-20261009-HAND-CLOSURE-TEMPLATED-EVENTS-GUARD

## Related Docs
- docs/guides/agent_monitoring.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
- agent-working/agent-monitoring/retro/RETRO-2026-W41.md (final note, runs=281)

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py, tools/agent-monitoring/generate_retro.py, tools/agent-monitoring/path_report.py

## Assumptions / Open Questions
- Assumption: the stored_artifacts path for a ticket is stable at closure time (staging moved before the recorder runs). Verify the order.

## Implementation Notes
`record_hand_orchestrated_closure.py`: `evidence_phase_events()` adds an Investigate and/or Plan event (status ok, summary naming the artifact path and saying the recorder derived it) for a standard/epic closure whose `investigation.md` / `plan.md` exists under stored_artifacts or staging_artifacts and whose phase the closer did not give; they are placed right after Scope; with no artifact the phase stays absent, so `phases_omitted` names the real gaps. `parity_skipped_without_enum_reason()` refuses (before anything is written, like the other guards) a Parity event skipped without a `skip_reason` from the enum, or with `unstated`, when the ticket's own diff touches `src/`; an out-of-vocabulary reason is refused with the valid list. `generate_retro.py`: the Run Summary adds `Blocking gate verdicts (ledger)` (blocking of verdicts, and how many have no recorded outcome) beside the unchanged `Gate failures` line, and a `Reset-boundary declarations` row for weeks from 2026-W42 (item 8). Measured on W42's ledger: 22 blocking of 81 verdicts, 1 without an outcome, next to run Gate failures 0. The recorder docstring is updated. This ticket's own closure is the first use of the evidence rule: its stored artifacts exist, so Investigate and Plan are recorded as ran.

## Test Summary
`tests/tools/test_closure_recorder_phase_evidence.py` (new, 13: artifacts give Investigate and Plan, no artifacts none, staging counts, no duplication and hotfix derives nothing, phases_omitted loses them, the Parity refusal cases, the run-summary rows) and `test_record_hand_orchestrated_closure.py`, `test_retro_provenance.py`, `test_generate_retro.py` pass.

## Files Changed
tools/agent-monitoring/record_hand_orchestrated_closure.py, tools/agent-monitoring/generate_retro.py, tests/tools/test_closure_recorder_phase_evidence.py

## Completion Summary
Hand closures record the phases their artifacts prove, refuse an unstructured Parity skip on a src/ change, and the retro shows ledger blocks beside run gate failures (W42: 22 beside 0).

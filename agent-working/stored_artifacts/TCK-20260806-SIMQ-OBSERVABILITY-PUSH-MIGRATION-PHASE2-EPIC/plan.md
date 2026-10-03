---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC
artifact_type: plan
tags: [observability, engine, simulation-quality, performance, progression]
---

# plan.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC

## Steps

1. File 8 child tickets into `tickets/todos/simq-observability-push-migration-phase2/`, with
   `SEQUENCE.md` establishing the build (1-6, independent of each other) -> validate (7) ->
   cutover (8) order.
2. Hand-orchestrate each child ticket's full `implement-ticket.js` pipeline, sequentially,
   stopping on the first non-DONE result (none occurred — all 8 completed DONE in order).
3. Once child 7 (shadow validation) reaches a GO verdict, proceed to child 8 (cutover) — the one
   irreversible step.
4. Once all 8 children are DONE, close this epic ticket with a full completion summary, event
   coverage accounting, and `docs/audits/D20_simq_quality_status_review.md` update.

## Scope guard

The epic ticket itself makes no `src/`/`tests/` changes — all implementation happened in child
tickets' own Implement phases, each independently reviewed and verified.

## Acceptance-criteria map

| Epic AC | Satisfied by |
|---|---|
| 8 child tickets filed with SEQUENCE.md | Step 1 |
| Child 1 (perf gate) lands before any shaper-build child | SEQUENCE.md's explicit ordering |
| Children 2-5 independently SHADOW-validated before child 7 | Each child's own Verify gate |
| Child 6 closes all 3 of Phase 1's remaining named deferrals | Child 6's own Completion Summary |
| Child 7 DONE with divergence investigated before child 8 begins | Child 7's own GO verdict |
| Child 8 completes: old diffing code flag-gated, live queue fed by the new path | Child 8's own Completion Summary |
| Every one of the 51 audited events accounted for by name | investigation.md's coverage accounting |
| D20 updated with this epic's outcome | Child 8's own Docs Requiring Update + this epic's own closure |

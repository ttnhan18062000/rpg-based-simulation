---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC
artifact_type: plan
tags: [observability, engine, combat, simulation-quality, performance]
---

# plan.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC

## Unresolved Questions

None at the epic level — the architecture question is already resolved
(`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE`, DONE). Each child ticket carries its
own Investigate/Plan phases for its own narrower scope; this epic plan only fixes the sequencing
and gating structure.

## Steps

1. Remove the superseded flat implementation ticket
   (`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-EMISSION-PHASE1-COMBAT-ECONOMY-FACTION`) from
   `tickets/todos/simq-pillar-lifecycle-depth/` — no implementation had started on it.
2. Move `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` from
   `tickets/todos/simq-pillar-lifecycle-depth/` into this epic's folder
   (`tickets/todos/simq-observability-push-migration/`) as child 1.
3. File 4 new child tickets (2 through 5, per this epic's Scope) into the same folder.
4. Write `SEQUENCE.md` for the new folder with the strict build → validate → cutover order,
   explicit about the hard gate before cutover.
5. Update `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s blocking-dependency note to
   reference this epic instead of the removed flat ticket.
6. Update `tickets/todos/simq-pillar-lifecycle-depth/SEQUENCE.md` to reflect the removal/move and
   point to the new epic folder.
7. Once child tickets are filed, this epic ticket's own Scope phase is complete — hand-orchestrate
   each child ticket's full `implement-ticket.js` pipeline in order, starting with child 1.

## Scope guard

The epic ticket itself makes no `src/`/`tests/` changes — all implementation happens in child
tickets' own Implement phases, each independently reviewed and verified.

## Acceptance-criteria map

| Epic AC | Satisfied by |
|---|---|
| 5 child tickets filed with SEQUENCE.md | Plan steps 2-4 |
| Step 1 lands before step 4 begins | SEQUENCE.md's explicit ordering |
| Step 2 proves pattern before step 3 | SEQUENCE.md's explicit ordering |
| Step 4 gates step 5 | SEQUENCE.md's explicit ordering + child 5's own blocking-dependency note |
| Step 5 completes the cutover | Child 5's own acceptance criteria |
| D20 updated on completion | Deferred to epic Finalize, once all children DONE |
| PROGRESSION ticket updated | Plan step 5 |

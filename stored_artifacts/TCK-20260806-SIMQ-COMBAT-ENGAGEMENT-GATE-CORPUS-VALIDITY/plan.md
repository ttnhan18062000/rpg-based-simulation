---
status: active
layer: simulation
authority: P0
audience: agent
ticket_id: TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY
artifact_type: plan
tags: [simulation-quality, combat, progression, feature-flags, observability]
---

# Plan: TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY

## Unresolved Questions

None — investigation.md and its two addenda reached a complete, evidence-backed conclusion
(Findings 1-5, both addenda, Recommendation). What started as "is the flag an unexamined gap"
escalated twice: first to a confirmed exact bug (missing `outcome_kind` check), then to a
materially larger architecture question (the entire observability pipeline is diff-based, not
push-based). Both escalations are filed as their own precisely-scoped tickets rather than expanding
this ticket's scope further.

## Steps

1. **Correct `D20_simq_quality_status_review.md`'s Full Pillar Health table** — COMBAT's "Healthy,
   archetype-correct spread" note gets a qualifier noting the confirmed hazard-misclassification
   bug and pointing at its fix ticket, rather than an unqualified "Healthy."
2. **File three tickets** in `tickets/todos/simq-pillar-lifecycle-depth/` (two already filed live
   during Investigate, per the addenda; documented here for the record):
   - `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` (hotfix) — confirmed bug,
     known fix.
   - `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE` (standard, investigation-first) —
     the generalized push-vs-diff architecture question.
   - `TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE` (standard, investigation-first) — still
     needed, unrelated to the above two; not yet filed, do it in Implement.
3. **Update `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`** — change its blocking-dependency
   note from this ticket to the two combat-relevant follow-ups
   (`EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` and `OBSERVABILITY-PUSH-BASED-ARCHITECTURE`),
   since real growth data can't be assessed until the corpus's combat event stream is trustworthy.
4. **Rewrite `SEQUENCE.md`** to reflect this ticket's DONE status and all 4 remaining open tickets'
   dependency graph.
5. Run `make knowledge-index-update` (D20 doc touched).

## Scope guard

No `src/` or `tests/` files are touched by this ticket itself — confirmed by investigation.md's own
Recommendation. The confirmed bug fix and the architecture question both get their own tickets with
their own Implement phases, not bundled into this one's Implement step.

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| Identify source of observed combat-like events despite gate being off | investigation.md Finding 3 + Addendum 1 (now a confirmed exact bug, not a hypothesis) |
| State whether flag default is a ruling or unexamined gap | investigation.md Finding 1 |
| Concrete recommendation with reasoning | investigation.md Recommendation + both addenda |
| Quest-reward gap traced to a specific cause | investigation.md Finding 5 (plausible pacing explanation; follow-up ticket to confirm) |
| D20 Full Pillar Health corrected if needed | Plan step 1 |
| PROGRESSION ticket updated | Plan step 3 |

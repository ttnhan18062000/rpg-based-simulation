---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-XP-LEVELING-EVOLUTION-IDENTITY-INVESTIGATION
phase: done
date: 2026-09-20
tags: [architecture, schema]
---

# TCK-20260920-MECHANISM-XP-LEVELING-EVOLUTION-IDENTITY-INVESTIGATION

## Title
`xp_leveling` / `evolution` — applying the identity rule's own Merge test deliberately, the rule's
first live application

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION` (batch 1) found `xp_leveling`'s own
positive-control scenario is identical to `evolution`'s own already-bound verified block, and left
it unbound rather than double-attribute one implementation to two ids — flagged as an identity
question, explicitly deferred to its own deliberate investigation rather than decided in passing
during a binding sweep. This ticket is that investigation: the identity rule
(`docs/plans/mechanism_identity_and_change_taxonomy.md` §1)'s first real, deliberate application to
a live Merge candidate.

## Scope
Determine whether `xp_leveling` and `evolution` are the same mechanism under two names, applying
§1's own operational test directly rather than by inference, and record the outcome against the
rule per peer's explicit request — not settle it in passing during an unrelated batch.

## Out of Scope
- Executing any registry restructuring (removing a row, redirecting citations) — a merge's own
  blast radius needs real review, same restraint as this session's own `commitment_betrayal`
  non-merge (opposite finding direction, same discipline).
- Fixing the underlying corpus-volume shortfall that makes both mechanisms' own real behavior hard
  to observe — that's the shared root cause the `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN`
  epic already tracks, not reopened here.

## Acceptance Criteria
1. The identity rule's own Merge test applied directly to the real code both ids point at, not
   assumed from the ids' own names.
2. A clear, deliberate verdict recorded — Merge, Split, or Leave-as-two — with the reasoning that
   produced it, not left as "genuinely ambiguous" a second time.
3. The verdict recorded in both the identity taxonomy doc (as a real case study, since this is the
   rule's first live test) and on `xp_leveling`'s own registry entry.
4. No structural registry change executed without further review.

## Related Tickets
- `TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION` — where the identity question was
  first found and deliberately deferred to this ticket.
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — tracks the shared root cause (low real combat
  volume) both mechanisms' own real-play behavior traces back to; not reopened here.

## Related Docs
- `docs/plans/mechanism_identity_and_change_taxonomy.md` §8 — the new case study this ticket wrote.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-XP-LEVELING-EVOLUTION-IDENTITY-INVESTIGATION/`.

## Related Code Areas
- `src/engine/evolution.py` (`EvolutionSystem.evaluate()`)
- `registries/mechanisms.yaml` (`xp_leveling`, `evolution` entries)

## Assumptions / Open Questions
None open for this investigation's own scope — the verdict is recorded as deliberate, not
provisional. Whether to actually execute the merge remains open, explicitly deferred to review.

## Implementation Notes
Read `EvolutionSystem.evaluate()`'s own full body directly (not inferred from either entry's own
prose). Found it does two structurally distinct things in one undivided pass: (1) XP consolidation,
level-threshold crossing, and stat/AP/skill growth on any `levels_gained > 0` — what `xp_leveling`'s
own entry claims; (2) species-kind transformation and equipment upgrade, gated specifically on
`old_level < threshold <= new_level` for `threshold in (10, 25, 50)` — what `evolution`'s own name
most naturally implies. `evolution`'s own cited positive control (level 1 → 2) never approaches
threshold 10, so it demonstrates behavior (1), not behavior (2) — the entry's own name and its own
evidence don't currently match.

Applying §1's Merge test ("if two declared ids share one implementation and cannot independently
succeed or fail, they are one mechanism"): behavior (2) structurally requires behavior (1) to have
already fired repeatedly (reaching level 10 requires first reaching every level below it), and no
evidence from either entry shows the two currently diverging in real corpus play — both are starved
by the identical real-world volume shortfall the entity-layer batch's own note already measured
(max 50 XP accumulated against a 100-XP threshold in any tested world; level 10 is further still).

**Verdict: Merge, `xp_leveling` into `evolution`.** Recorded in
`docs/plans/mechanism_identity_and_change_taxonomy.md` §8 and on `xp_leveling`'s own registry entry.
Not executed — a real registry restructuring needs review before landing, the same restraint this
session already applied once in the opposite direction (`commitment_betrayal`, where the merge
premise turned out false; here it turns out true, and the ticket still declines to act on it
unilaterally).

## Test Summary
No test changes — a documentation/registry-note-only investigation, no binding or state changed.
`registry.py::validate()`: clean, 93 mechanisms (unchanged count, no row removed).

## Files Changed
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — new §8 case study.
- `registries/mechanisms.yaml` — `xp_leveling`'s own note updated with the deliberate verdict.

## Completion Summary
**Done.** The identity rule's own Merge test applied deliberately for the first time: `xp_leveling`
and `evolution` share one undivided implementation and no evidence shows them currently able to
succeed or fail independently — verdict is Merge, recorded in both the identity taxonomy doc and
the registry entry itself, not executed pending review. This closes the identity question batch 1
deliberately deferred rather than guessed at.

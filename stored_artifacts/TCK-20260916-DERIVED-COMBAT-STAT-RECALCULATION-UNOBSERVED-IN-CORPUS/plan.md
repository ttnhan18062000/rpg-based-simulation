---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS
artifact_type: plan
tags: [progression, simulation-quality, testing]
---

# Plan — TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS

This ticket's own scope is investigation and measurement only ("Out of Scope: Repairing
anything — this ticket is filed per explicit 'verify, don't repair in the same pass' instruction").
No code changes are made here. The plan is a measurement plan, not an implementation plan.

## Steps

1. Run the proposed discriminating measurement (accumulated XP vs. level-up threshold at tick
   1000, across the same three real corpus worlds the original ticket used) by instrumenting
   `CombatRewardClassificationService.classify_defeated_target` with a call counter and reading
   final `identity.evolution_points`/`evolution_level` from real `Kernel`-driven state.
2. Interpret the result against the ticket's own explicit discrimination rule (meaningful-but-below
   threshold XP → pacing; zero/near-zero XP despite confirmed combat damage → wiring). Do not
   assume either direction before measuring.
3. Trace in whichever direction the measurement points, per peer's instruction — expect a naming
   trap or data precondition rather than missing code, per this arc's own track record.
4. Validate any "the code doesn't work" reading with a real positive control *before* reporting it
   — and validate the positive control itself runs through the same real code path the corpus
   measurement does (a lesson this exact investigation had to relearn mid-pass, see
   investigation.md's "false lead" section).
5. Record the final verdict, with evidence, in both the ticket body and the mechanism registry
   (`xp_leveling`, `evolution`, and any other mechanism the trace directly touches) — propagated to
   every consumer artifact the registry's own convention requires (atlas badge, capabilities page).
6. If a real, separately-scoped follow-up is warranted (tuning, further root-causing), file it as a
   new ticket rather than fixing anything in this one's own pass.
7. Close this ticket once its own five Acceptance Criteria are satisfied by the investigation
   itself, not by a code fix — this ticket's own definition of done never included a repair.

## Explicit non-goals for this ticket

- No change to XP reward values, level thresholds, or corpus world composition — those are for the
  follow-up ticket, if pursued.
- No re-investigation of why cross-faction combat volume is generally low — that is
  `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own scope.
- No deep verification of `attributes_biology` — out of this investigation's actual reach; left
  unverified rather than force-fit.

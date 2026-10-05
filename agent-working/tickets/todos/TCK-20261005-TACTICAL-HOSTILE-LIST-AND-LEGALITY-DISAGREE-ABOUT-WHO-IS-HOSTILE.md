---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE
phase: open
date: 2026-10-05
tags: [engine, combat, investigation]
---

# TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE

## Title
751 `FRIENDLY_FIRE_ILLEGAL` verdicts appeared once the decision path became reachable: tactics selects
a target with one hostility predicate while legality gates on a *different* predicate chosen by
whether clean faction data happens to exist — three hostility call sites, no single authority

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Reported by `rpg-implementer` (Lane A) as "751 `FRIENDLY_FIRE_ILLEGAL` verdicts appearing after the
dispatch change, single run, unexamined", with the honest note that it may be residue from Lane A's own
`TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` (#333). Filed by the planner with the code read
done, so the lane starts from a located divergence rather than a count.

**The 751 verdicts are a symptom of exposure, not of a new defect.** More brain calls after fix (A)
means more attacks reach legality; the disagreement was always there. That matters for priority: this
is not a regression from fix (A), and the attack-path ticket should not be held for it.

**The divergence, located.** There are three hostility decisions on the path from "who do I fight" to
"may I hit them", and they do not share a predicate:

1. `src/engine/tactical.py:75` — the **appraisal** neighbour scan uses `are_entities_hostile(...)` with
   a `RelationContext`.
2. `src/engine/tactical.py:249` — the **hostile list that drives target selection** uses
   `semantics_service.is_hostile_compat(src_faction_id, tgt_faction_id, context)`, **unconditionally**.
3. `src/engine/legality.py:252-272` — the **legality gate** first probes the semantics repo for "clean"
   data (any perspective whose `chosen_faction` or `id` matches the attacker, or any
   `faction_relationships` edge source→target). **Only if `has_clean` is true** does it consult
   `is_hostile_compat`. If not, it falls back to raw `attacker.identity.faction ==
   target.identity.faction` equality.

So for any pair with no clean perspective and no matching relationship edge, **tactics decides
hostility semantically and legality decides it by raw faction-string equality.** Those can disagree in
both directions: two entities of the same raw faction that semantics treats as hostile (a schism,
a perspective-driven split) are selected by tactics and refused by legality as friendly fire; and the
`has_clean` probe itself is asymmetric — it matches relationship edges source→target only, so A→B may
be "clean" while B→A is not, giving the two directions of the same pair different gates.

**Why this is a bug and not tuning.** The question is not where a threshold sits; it is that one
subsystem's answer to "is X hostile to Y" depends on whether a lookup table happens to be populated.
That makes combat legality a function of content-authoring completeness rather than of the fiction. It
is also the second time this family has bitten: #333 swept raw legacy faction enums out of hostility
checks, and `legality.py`'s fallback is exactly such a raw check, still in place.

## Scope
1. **Investigation first — this ticket does not start with a fix.** On post-#344 `main`, instrument the
   three call sites and record, over the corpus worlds, every attacker/target pair where the predicates
   disagree, with: the pair's raw factions, whether `has_clean` was true in each direction, which
   predicate each site returned, and the resulting verdict. Report the **count of disagreeing pairs**,
   not only the count of verdicts — 751 verdicts may be a handful of pairs re-trying.
2. **Re-measure the 751.** It is a single run on a pre-#344 tree. State the post-#344 figure, per world,
   as a sample or a value according to how it was taken.
3. **Determine whether `has_clean` is ever false on corpus content.** If it is never false, the raw
   fallback is dead code on this corpus and the whole defect is latent rather than firing — say so
   plainly, and the fix shrinks to deleting a dead branch plus a test that pins it. If it is sometimes
   false, report which worlds and which factions.
4. **Report, do not decide, the semantic question.** Which predicate is authoritative is a **rule
   question**, and the Mechanics Bible's hostility definition is the authority. Bring the planner: the
   measured disagreement, what the Bible says (or that it is silent), and a recommendation. If the Bible
   is silent, this needs an owner/rule-owner ruling before any unification — exactly the mistake the
   trauma ticket is parked on, and we are not repeating it.
5. **Only then**, and in a separate pass the planner approves: unify on the ratified predicate, with a
   disabling-control test per direction of the asymmetry.

## Out of Scope
- Changing `are_entities_hostile` or `is_hostile_compat` semantics themselves in the investigation pass.
- `src/content_semantics/faction.py` — **held by Lane B** (`rpg-implementer-2`). If the fix needs it,
  come back for a hold; do not take it.
- Re-opening #333. Its sweep is not being reverted; this is a site it did not reach.
- The flee gate (P0, blocked on ratification) and the `OUT_OF_RANGE` sticky task (its own ticket).

## Acceptance Criteria
- [ ] The three call sites' predicates are recorded with the disagreeing pairs, counted as **pairs** and
      as verdicts, on post-#344 `main`.
- [ ] Whether `has_clean` is ever false on corpus content is answered with evidence, per world.
- [ ] The asymmetry of the `has_clean` relationship probe (source→target only) is confirmed or refuted
      by measurement, not by reading alone.
- [ ] The 751 figure is re-taken and labelled sample or value.
- [ ] A recommendation on the authoritative predicate reaches the planner **with** what the Bible says
      or an explicit statement that it is silent. **No unification lands before ratification.**
- [ ] If the fallback is dead on this corpus, that is stated and a test pins it.

## Related Tickets
- `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` (#333) — the earlier sweep; this is a site it
  did not cover. Check whether its ticket claimed completeness it did not have.
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` — made the path
  reachable and so exposed this. **Not a regression from it; do not hold that PR for this.**
- `TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES` — same run.
- `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` — the planner owes a re-read of its
  framing; same "two subsystems, two answers" shape, worth comparing.

## Related Docs
- The Mechanics Bible's hostility / faction-relationship definition — **the authority this ticket must
  cite or declare silent.**
- `docs/engine/` combat legality contract.

## Related Code Areas
- `src/engine/tactical.py:70-80` (appraisal predicate), `:207-251` (hostile list and
  `hostile_identity_sources`).
- `src/engine/legality.py:252-272` — the `has_clean` probe and the raw-equality fallback.
- `src/content_semantics/faction.py:186` — `is_hostile_compat`. **Lane B's hold; read only.**

## Assumptions / Open Questions
- **Lane.** Lane A for `tactical.py` and `legality.py`. `faction.py` is Lane B's — read-only here.
- `hostile_identity_sources` (tactical.py:251) already records which identity source decided each
  hostile. **Check whether it alone answers scope 1** before building new instrumentation; it looks
  like it was added for exactly this question.
- Open: whether `RelationContext` at :75 and the `context` at :249 are the same object. If they differ,
  there are three predicates and not two, and the appraisal/selection split is a second defect.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)

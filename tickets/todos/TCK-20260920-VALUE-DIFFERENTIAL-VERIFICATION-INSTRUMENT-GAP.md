---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP
phase: open
date: 2026-09-20
tags: [simulation-quality, testing, cognition]
---

# TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP

## Title
The differential scenario harness proves a mechanism *executes*, not that it *matters* — three
distinct failure-to-matter shapes it cannot currently detect, named with real instances each

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Found while pre-screening `personality` for `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-
RUNTIME-VERIFICATION`'s batch 2, filed rather than forced into that batch, per direct peer
instruction: `personality` doesn't fit the harness's own reachability-differential shape at all.

`PersonalityComponent` (greed/bravery/sociability/industry) is a pure data component, always
present on every entity, read unconditionally at ~8 real call sites (`src/engine/tactical.py`,
`src/engine/movement.py`, `src/engine/cognition.py`, `src/ai/goals/scorers.py`,
`src/systems/social_systems/clan_lifecycle.py`, `src/systems/social_systems/party_lifecycle.py`).
"Is it reachable" is not the interesting question for it — it always is, trivially, since it's a
required field on every entity, not an optional phase behind a gate. The real question is: **do
different personality values actually produce different observable behavior** — does a high-bravery
entity make a different combat-vs-flee decision than a low-bravery one, given the same situation?
That's a *value* differential, not the *presence/absence* differential every scenario in this
program so far has built.

**Named as its own gap, per peer framing, and widened from one shape to three (2026-09-20,
`adventure_routing`'s own investigation)**: this harness currently proves a mechanism *executes*,
never that it *matters* — a dormancy of a different kind from the ones this program has been finding
(`perception`, unreached; `temporal_pressure`, gated) and, for RPG mechanics specifically, arguably
the more common one. Stats, traits, modifiers, and scorers don't usually fail by not running; they
fail by not mattering. Three distinct shapes, each with a real, named instance, not hypothetical:

1. **Value** — the mechanism runs, but its own inputs never change the outcome. `personality`
   (greed/bravery/sociability/industry), read unconditionally at ~8 real call sites
   (`src/engine/tactical.py`, `src/engine/movement.py`, `src/engine/cognition.py`,
   `src/ai/goals/scorers.py`, `src/systems/social_systems/clan_lifecycle.py`,
   `src/systems/social_systems/party_lifecycle.py`) — nobody has checked whether varying `bravery`
   actually changes `scorers.py`'s own output, only that the field is read.
2. **Arbitration** — the mechanism runs, produces a real, non-default output, and never wins.
   `adventure_routing` (`AdventureGoalScorer.score()` -> `AdventureDecisionService.decide()`,
   `src/ai/goals/adventure_scorer.py:165`): registered as one candidate among many in
   `StrategicIntelligenceSystem.evaluate_strategic_intent()`'s own real tier-5 goal-scoring
   arbitration, not a direct write. A scorer that genuinely computes a real score and always loses
   the competition is dormant in effect while passing every check this harness currently has — any
   candidate-scoring mechanism in a tier arbitration has this shape, which in this codebase is a
   real number of mechanisms, not just this one. A legitimate, narrower fallback verdict exists for
   this shape even without solving full arbitration-tracing: "the scorer is called and produces a
   real non-default `GoalScore`" is a weaker, distinct claim from "changes a selection" — worth
   stating as its own acceptable outcome, not treated as a lesser failure to fix later.
3. **Reachability** (already solved, listed for contrast) — the mechanism never runs at all. This is
   the one shape `mechanic_verification_scenarios_proposal.md`'s existing differential harness
   already handles (`perception`, `temporal_pressure`, and most of this program's own findings).

**A fourth, adjacent constraint, not a fourth shape**: `adventure_routing`'s own investigation also
surfaced that a single shared scenario world can only ever verify the mechanisms that world
exercises. `mechanic_scenario_combat_judgement_withdrawal` (the one world every scenario in
`TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` has reused) has only
monster-kind entities, none with a cognition profile supporting adventure routing — testing shape 2
for `adventure_routing` needs a real hero entity, a different world. A small set of purpose-built
scenario worlds is real infrastructure work belonging with the value/arbitration instrument itself,
not something to bolt onto a batch that was deliberately built around reusing one world.

## Scope
Not scoped here — this ticket names the instrument gap and the concrete cases found so far, per
explicit instruction ("don't build it now... leave [it] unverified rather than giving it a verdict
the instrument can't support"). A future ticket/program would need to:
1. Design a value-differential assertion shape (shape 1, distinct from the present/absent shape
   `docs/plans/mechanic_verification_scenarios_proposal.md` §3.3/§5 already codifies) — likely:
   stage two entities identical except for one real value (e.g. `bravery`), same real precondition,
   assert their real, observable outputs differ in the direction the value's own documented meaning
   predicts.
2. Design an arbitration assertion shape (shape 2) — likely two tiers: the narrower "produces a
   real non-default score" claim (cheap, always available), and the fuller "wins against a real
   staged rival, changing the actual selection" claim (needs the arbitration's own real competing
   candidates staged, not synthetic ones).
3. Decide whether purpose-built scenario worlds (the adjacent constraint above) are built as part of
   this same program or as their own infrastructure ticket first.
4. Apply to `personality` and `adventure_routing` first (the two concrete cases found here), then
   assess how many other registered `done` mechanisms are actually stats/traits/modifiers/scorers
   with one of these two shapes (not scoped here — a sizing question for whoever picks this up, same
   discipline as `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`).
5. Decide whether `personality`'s and `adventure_routing`'s own registry entries should get a
   `verified` block at all under either new instrument, or whether "unverified, this instrument
   doesn't exist yet" is itself the honest, recorded state in the meantime.

## Out of Scope
- Any code change to `personality`, `adventure_routing`, or their consumers.
- Any other mechanism in `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`'s own
  batch — this is explicitly a separate, later program, not folded into the current one.

## Acceptance Criteria
(none yet — gap-naming ticket; criteria belong to whichever future ticket picks this up)

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — where this gap was found
  (batch 2's own pre-screen)

## Related Docs
- `docs/plans/mechanic_verification_scenarios_proposal.md` — the existing (presence/absence-shaped)
  differential harness this gap sits alongside, not inside

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/core/state.py::PersonalityComponent`
- `src/ai/goals/scorers.py` (the plausible first real value-differential candidate — combat-vs-flee
  scoring)
- `src/ai/goals/adventure_scorer.py::AdventureGoalScorer`,
  `src/domains/adventure/service.py::AdventureDecisionService` (the arbitration-shape instance)
- `src/systems/strategic_systems/intelligence.py::StrategicIntelligenceSystem::evaluate_strategic_intent`
  (the real tier-5 arbitration `adventure_routing`'s score competes inside)

## Assumptions / Open Questions
Whether `personality`'s own values actually change any real output, and whether `adventure_routing`'s
own scored candidate ever wins its real arbitration, are both genuinely unverified, not assumed
either way — that's exactly the gap this ticket exists to name, not to prejudge.

## Implementation Notes
(none yet — not started)

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)

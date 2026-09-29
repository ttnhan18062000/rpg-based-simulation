---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED
phase: open
date: 2026-09-20
tags: [simulation-quality, cognition]
---

# TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED

## Title
Design decision needed: which of three perception-shaped things in this codebase is meant to be
the real one? (Not a wiring bug — a scope-of-concept question for the roadmap session.)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found by `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`'s differential
runtime scenario, not fixed there per that program's explicit governing constraint (record the
contradiction, do not fix the code to make an old claim true in the same pass), and explicitly
reframed here per peer review before it could ossify into a "just wire it up" bug ticket: **this
codebase currently has three real, distinct, perception-shaped things, and nothing declares which
one is meant to be the entity's actual perception.**

1. **A designed abstraction nothing consumes**: `src/domains/perception/filter.py::
   PerceptionFilterService` + `src/domains/perception/phase.py::PerceptionUpdatePhase`. Real,
   correct code — scores candidate signals, budget-clamps them into a ranked `PerceptionModel`
   (`perceived_entities`/`perceived_threats`/`perceived_resources`/`perceived_services`/
   `perceived_opportunities`). But `PerceptionUpdatePhase` is never instantiated anywhere in `src/`
   outside its own file (confirmed by full-tree grep and a real differential Kernel-run scenario,
   `tests/mechanic_scenarios/test_perception_pipeline_wiring.py`: zero real `.filter()` calls and
   an empty `perceived_entities` across 5 real ticks against a world with an adjacent, perceivable
   entity; a positive control proves the code itself works when called directly). And even if it
   were wired in, **nothing downstream reads its output either** — zero real code anywhere in
   `src/` reads any `PerceptionModel` field outside this dead chain itself, independently confirmed
   while investigating why `perception` has zero registry `depends_on` dependents.
2. **A direct bypass strategic cognition actually uses instead**: `goal_hierarchy`'s own verified
   note documents `StrategicIntelligenceSystem` sourcing situational awareness through a direct
   `SpatialQueryService.nearby_entities()` spatial query — real, wired, load-bearing, but a
   completely different mechanism from the `PerceptionModel` abstraction above, with no budget
   clamp, no salience ranking, no "what does the entity consciously notice" concept at all.
3. **A live, unregistered gate doing raw sense-detection**: `src/world/perception/gate.py::
   PerceptionGate`, real and wired (`src/engine/tactical.py:181,199`, initialized via
   `src/content/warmup.py`), but scoped narrowly to "can this entity detect that specific neighbor
   at all" (vision/hearing/smell/etc. against a target's emitted signals) for `TacticalDecisionSystem`'s
   own targeting — upstream of a decision, not itself a notice-and-remember abstraction.

The registry's own `perception` entry (state `done` → `orphan`, verdict → `contradicted`) has
already been corrected to reflect that thing #1 specifically is dead. This ticket is not "fix thing
#1" — a fix there would leave things #2 and #3 exactly as unresolved as they are now, and might not
even be the right thing to fix. **This is a design question about which of the three is meant to be
canonical**, or whether they're meant to coexist with distinct, non-overlapping scopes that just
need to be declared as such.

## Scope
For the roadmap/planning session to decide, not to implement here:
1. Is `PerceptionModel` (thing #1) meant to be the real strategic-cognition-facing perception layer,
   with `goal_hierarchy`'s direct spatial-query bypass (thing #2) meant to be replaced or folded
   into it? Or was the direct bypass always the intended design, making thing #1 a superseded,
   removable abstraction?
2. Should `PerceptionGate` (thing #3) be registered as its own mechanism (its scope — raw
   detection capability — is real and narrower than either of the above), and if so, does it
   belong under `cognition` or a different system?
3. Whichever direction is chosen, what should happen to the other(s): remove, repurpose, or
   explicitly scope them apart with a registry note (the same "declare the boundary, don't erase
   the history" treatment `tactical_decision`'s own entry now gives `PerceptionGate`)?

## Out of Scope
- Implementing any of the above — this ticket exists to get a decision, not to make one
  unilaterally.
- Re-verifying the finding itself — already confirmed by a real differential scenario and a direct
  full-tree grep for consumers, not to be re-litigated here without new evidence.
- Any other `cognition` mechanism, or the broader registry-completeness scope-gap question this
  investigation also surfaced (tracked separately:
  `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`).

## Acceptance Criteria
1. A real design decision from the roadmap session on which perception-shaped thing (or
   combination) is canonical.
2. Once decided: either a real implementation ticket scoped to that decision, or an explicit
   "coexist, here's why" registry note update — never a silent code change made to match a guess
   at what the decision would have been.

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — found this, did not fix it
- `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP` — the broader "how much other live code
  isn't in the registry" question `PerceptionGate` surfaced, tracked separately

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/perception/phase.py::PerceptionUpdatePhase`
- `src/domains/perception/filter.py::PerceptionFilterService`
- `src/domains/perception/salience.py::WorldSignal`
- `src/systems/strategic_systems/intelligence.py` (the `SpatialQueryService.nearby_entities()` bypass)
- `src/world/perception/gate.py::PerceptionGate`
- `src/engine/pipeline.py`
- `src/engine/tactical.py`

## Assumptions / Open Questions
None outstanding on the investigation side — the three things and their real/dead/scope status are
all directly confirmed, not assumed. The open question is purely the design call in Scope above.

## Implementation Notes
(none yet — not started; awaiting the design decision this ticket exists to request)

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)

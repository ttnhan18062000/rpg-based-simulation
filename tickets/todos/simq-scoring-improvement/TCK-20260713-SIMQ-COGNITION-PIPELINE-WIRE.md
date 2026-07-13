---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE
phase: open
date: 2026-07-13
tags: [simulation-quality, cognition]
---

# TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE

## Title
Wire `ActionIntentAdapter.execute()` into the production tick pipeline for COGNITION self-model
query-routing

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Self-model query-routing (Branch B of `InformationBeliefPhase` — "what don't I know, who might
know it") is verified mechanically correct
(`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`, direct test-harness invocation via
`test_ask_information_intent_execution_closes_the_loop`) but has zero live-gameplay reach.
Confirmed directly (`grep -rn "ActionIntentAdapter" src/`): the execution entry point
(`ActionIntentAdapter.execute()`, `src/engine/intent/action_intent.py:32`) has no production call
site anywhere in `src/` — it exists only as a class definition and a docstring mention
(`src/domains/adventure/resolver.py:20`). Every other gated phase in `src/engine/pipeline.py`
(`cooperation` at line ~158, `information_belief` at line ~152, `adventure_decision` at line ~230)
is wired via a `run_phase(...)` call; no equivalent line exists for intent execution.

This is the specific, named blocker the archived `docs/plans/archive/simq_development_roadmap.md`'s
Phase 5 gate identified and explicitly deferred as "a distinct future initiative if gameplay ever
actually needs live self-model query-routing" — this ticket picks up exactly that thread, not a
re-opening of any closed roadmap question.

## Scope
- Investigation-tier first: scope the exact merge point in `src/engine/pipeline.py` relative to
  the existing `information_belief` and `cooperation` phases (ordering matters — the routed
  `ActionIntent` comes from `InformationBeliefPhase` Branch B, which must run before intent
  execution can act on its output), and confirm whether a new `FeatureMode` flag is needed
  (near-certain yes, to keep this off by default in every shipped profile, matching how
  `ENABLE_SOCIAL_COOPERATION`/`ENABLE_BELIEF_ASSIMILATION` gate their phases today).
- Add a new gated phase to `src/engine/pipeline.py`, matching the existing `run_phase(...)`
  pattern, that takes the `ActionIntent` routed by `InformationBeliefPhase` Branch B and calls
  `ActionIntentAdapter.execute()` on it, merging the resulting `EntityUpdate` back into the tick's
  update set.
- Extend or add a test proving the call actually fires through the real tick pipeline (not just
  direct test-harness invocation of `ActionIntentAdapter.execute()` in isolation, which
  `test_ask_information_intent_execution_closes_the_loop` already covers) — a probe-profile-style
  calibration run (mirroring `urban_political_selfmodel_probe`'s existing pattern) with the new
  flag deliberately turned on is the natural verification vehicle.

## Out of Scope
- Turning the new flag on in any shipped world profile — this ticket wires the mechanism, it does
  not activate it for live gameplay anywhere.
- Any change to `InformationBeliefPhase`'s routing logic itself (already correct, per
  `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) or to `ActionIntentAdapter.execute()`'s
  internals — this ticket only adds the missing call site.
- Re-opening any FACTION/SOCIAL/AGENCY/materialization-half-of-COGNITION question — all
  independently closed by the archived roadmap's Phase 5 gate.

## Acceptance Criteria
- [ ] A new gated phase exists in `src/engine/pipeline.py` calling
      `ActionIntentAdapter.execute()`, off by default (flag-gated).
- [ ] A calibration run with the new flag deliberately enabled (probe-profile style) shows at
      least one `ActionIntentAdapter.execute()` call firing through the real
      `Kernel.tick_once()` loop — not just via direct test-harness invocation.
- [ ] `test_ask_information_intent_execution_closes_the_loop` and the existing Branch A/B
      regression suite (`tests/integration/domains/information/`,
      `tests/unit/domains/information/`) continue to pass unmodified.
- [ ] 0 regressions on a full `evaluate_simq.py` sweep with the new flag left off (default state).

## Related Tickets
- `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` (done) — the routing/execution logic this ticket
  wires into the pipeline, already verified correct in isolation.
- `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` (done) — established that self-model
  materialization generalizes cleanly; this ticket addresses the other half (query-routing).
- `TCK-20260713-SIMQ-COVERAGE-DECISION-GATE` (done) — the Phase 5 ruling that explicitly deferred
  this exact work as a future initiative.

## Related Docs
- `docs/simulation_quality/current_state.md` — the COGNITION per-pillar read and Recommendation 3.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 3, this ticket's source.
- `docs/plans/archive/simq_development_roadmap.md` — Phase 5 section, the original deferral.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/intent/action_intent.py:32` (`ActionIntentAdapter`)
- `src/engine/pipeline.py` (the `run_phase(...)` wiring pattern — `cooperation`,
  `information_belief`, `adventure_decision` phases)
- `src/domains/information/phase.py` (`InformationBeliefPhase` Branch B, where the `ActionIntent`
  is routed)
- `src/domains/optimization/feature_flags.py` (`FeatureMode` — naming convention for the new flag)
- `tests/integration/domains/information/test_phase5_information_belief_phase.py`
  (`test_ask_information_intent_execution_closes_the_loop`, the existing direct-invocation test)

## Assumptions / Open Questions
- The exact merge point and phase ordering relative to `information_belief`/`cooperation` is not
  yet scoped — first investigation task.
- Whether a new flag name should follow the `ENABLE_*` convention exactly (e.g.
  `ENABLE_INFORMATION_INTENT_EXECUTION` or similar) is left to the implementer, informed by
  `feature_flags.py`'s existing naming patterns.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

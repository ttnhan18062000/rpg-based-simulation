---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION
artifact_type: plan
tags: [simulation-quality, testing, cognition]
---

# Plan — TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION

## Scope guard
This is the harness-proving batch — 3 mechanisms, not the remaining 17 `cognition` mechanisms.
Report the harness design to the peer session before scaling; do not proceed to the rest of
`cognition` in this same ticket.

## Steps

1. `tests/mechanic_scenarios/test_belief_cycle_lead_staleness.py` (new). Reuse an existing compiled
   world (pick one with at least one active, alive entity and no conflicting staged
   `strategic.leads` — confirm directly, don't assume). Stage a `LeadState` via `replace()` the same
   way the readiness-gate test staged `combat.readiness`. Two conditions:
   - present: `state.tick` such that `tick - discovered_tick >= 50` → assert certainty becomes
     `VAGUE`.
   - absent: `tick - discovered_tick < 50` → assert certainty stays `APPROXIMATE`.
   Real `Kernel.tick_once()` dispatch both times, not a direct call to `resolve_lead_staleness`.

2. `tests/mechanic_scenarios/test_perception_pipeline_wiring.py` (new). Stage a real compiled world
   with two entities close enough that a naive salience/range check would perceive one from the
   other (need to confirm what `SignalSalienceEvaluator`/candidate-signal sourcing would need —
   investigate directly whether anything in the real pipeline ever constructs `WorldSignal`s at
   all, since `PerceptionUpdatePhase.run()` takes `world_signals` as a direct argument and nothing
   calls `.run()` in the first place). Run several real ticks. Assert
   `entity.cognition.subjective.perception.perceived_entities` stays empty across all of them, and
   a call-counter wrap on `PerceptionFilterService.filter` records zero real (non-test) calls.
   Record the contradiction in `mechanisms.yaml` — do not wire the phase in to make it pass.

3. `tests/mechanic_scenarios/test_quest_generation_sourcing_orphan_calibration.py` (new). Stage a
   real compiled world with one region forced to `trauma_score=0.9`. Run several real ticks with a
   call-counter wrap on all 3 `QuestGenerationSystem` methods — assert zero calls. Positive control:
   call `QuestGenerationSystem.generate_from_scar()` directly against the same region and assert it
   returns a real `QuestTemplate` (proving the code itself works, the absence is purely "never
   invoked"). Record `instrument: scenario` (upgrading the existing `code_trace` verdict, verdict
   stays `contradicted`) — no code fix.

4. Update `registries/mechanisms.yaml`: `belief_cycle` (`verified.instrument: scenario, verdict:
   observed`), `perception` (`state` correction if the runtime result confirms the dead chain —
   likely `done` → `orphan`, and `verified.instrument: scenario, verdict: contradicted`),
   `quest_generation_sourcing` (`verified.instrument: scenario`, verdict unchanged `contradicted`,
   now runtime-backed not just code_trace).

5. File a follow-up ticket for `perception`'s real defect if runtime testing confirms the dead
   chain — do not fix `PerceptionUpdatePhase`'s wiring in this ticket.

6. Regenerate `docs/brainstorm/mechanism_verification_view.md`,
   `mechanism_system_rollup_view.md`, `mechanism_registry.html` (`make mechanism-verification-view
   mechanism-system-rollup-view mechanism-registry-html`).

7. Run `tests/mechanic_scenarios/ tests/unit/tools/` scoped suite. Finalize, PR — batch 1 only.

## Explicitly out of scope
- The remaining 17 `cognition` mechanisms (batch 2+, pending peer sign-off on the harness design).
- Fixing `perception`'s wiring gap if confirmed (a separate ticket).
- `goal_hierarchy` (not selected this batch — see investigation.md's rationale).

---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES
phase: open
date: 2026-09-21
tags: [strategy, cognition]
---

# TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES

## Title
Design decision needed: is cognitive-capacity enforcement meant to be opportunistic
(piggybacking on other phases' updates) or unconditional? Currently the former, undocumented as a
design choice.

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found while closing `cognition_capacity_fatigue`'s own runtime-verification scenario
(`TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`), and explicitly reframed
here per peer review before it could sit as a buried staging detail: **`CapacityEnforcementPhase.
enforce()` (`src/engine/pipeline_phases/capacity_enforcement.py`) only evaluates an entity that
already has a real `StrategicUpdate` proposed by some OTHER phase that same tick**
(`if not ent_upd or not ent_upd.strategic: continue`). An entity genuinely over its own
`profile.max_leads`/`max_concerns` cap, with nothing else proposing anything for it that tick, is
silently skipped rather than trimmed — it stays over cap indefinitely, not just for one tick.

Read from the code's own side, this looks like a staging inconvenience (which is how it was
originally described while building the verification scenario). Read from the simulation's own
side, it's a real behavioral question: **capacity enforcement doesn't enforce unless something
unrelated happened to the entity first.** The phase is called unconditionally every tick
(`src/engine/pipeline.py:427`, `must_run_every_tick=True` in `phase_graph.py`, no feature flag) —
but the phase running unconditionally and the phase actually acting on an over-cap entity are two
different claims, and only the first is true unconditionally.

A real differential scenario confirmed the mechanism works correctly WHEN it runs
(`tests/mechanic_scenarios/test_cognition_capacity_fatigue_lead_trim.py`, staged by chaining
`belief_cycle`'s own real staleness-decay to give the entity the real precondition
`enforce()` needs) — that verdict stands, `cognition_capacity_fatigue`'s own registry entry is
`observed`/`scenario`. What's undecided is whether the entity needing an unrelated update that
same tick is the intended design or a real gap.

## Scope
For the roadmap/planning session to decide, not to implement here:
1. Is opportunistic enforcement (only re-evaluate capacity when something else already touched the
   entity's strategic state that tick) the intended design — e.g. as a real performance/cost
   optimization (avoiding a full capacity check on every entity every tick when nothing changed)?
2. Or is it a real gap — should an entity sitting quietly over cap eventually get enforced even
   with no other phase proposing anything for it?
3. If it's a gap: what's the right fix shape — should `enforce()` itself independently check
   `len(entity.strategic.leads) > profile.max_leads` regardless of `ent_upd.strategic`, or should
   some other mechanism (a periodic sweep, a dirty-set entry) ensure an over-cap entity eventually
   gets a `StrategicUpdate` proposed for it?
4. How common is "over cap with nothing else proposed" in real corpus play? Not measured here —
   would need a real corpus run checking `len(entity.strategic.leads) > profile.max_leads` against
   whether `ent_upd.strategic` was populated that tick, across a real world/seed.

## Out of Scope
- Any code change — this ticket exists to get a decision, not to make one unilaterally, matching
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`'s own framing for a comparable
  design-question ticket.
- Re-verifying `cognition_capacity_fatigue`'s own scenario — already confirmed real and correct
  for the case it stages; not re-litigated here without new evidence.

## Acceptance Criteria
1. A real design decision from the roadmap session on whether opportunistic enforcement is
   intended or a gap.
2. Once decided: either a real implementation ticket scoped to the fix (if a gap), or an explicit
   registry-note/doc update recording the design choice (if intended), never a silent code change
   made to match a guess at what the decision would have been.

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — where this was found
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — the comparable "design decision, not
  a bug report" framing this ticket follows

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/pipeline_phases/capacity_enforcement.py::CapacityEnforcementPhase`
- `src/strategy/capacity.py::CapacityService`

## Assumptions / Open Questions
Whether "over cap with nothing else proposed that tick" is common or rare in real corpus play is
genuinely unmeasured, not assumed either way — that's exactly what Scope item 4 asks for if this
ticket is picked up.

## Implementation Notes
(none yet — not started; awaiting the design decision this ticket exists to request)

### 2026-09-30 — classified via `TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD` (epic `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`, child `T03`): verdict `UNDECLARED`

**This is not a "never fires" mechanism, and the title's "dead guard" framing does not fit it.** Branch tip
`3dbdff48a`, no commit to `capacity_enforcement.py` since filing (2026-09-21):
- The guard the ticket describes is real (`capacity_enforcement.py:34-35`,
  `if not ent_upd or not ent_upd.strategic: continue`), and the mechanism fires when its precondition holds:
  `tests/mechanic_scenarios/test_cognition_capacity_fatigue_lead_trim.py` — 3 passed.
- **The ticket's claim that the opportunistic behaviour is "undocumented as a design choice" is partly wrong.**
  The phase's own header declares it: `# Milestone 5 Optimization: Only enforce on strategic-dirty entities`,
  `Logic ID: PERF-007 (O(Dirty) enforcement)` (`capacity_enforcement.py:23-24`), introduced in `562116889`
  (2026-05-18). What is undeclared is the *consequence* — an entity pushed over cap by something other than a
  same-tick strategic update (e.g. a cap that shrinks under fatigue) stays over cap until the next update — and
  nothing states whether that consequence is accepted.
- **Measured, not assumed.** A real 1,500-tick `V2EngineManager` run (`frontier_living_world`, seed 42,
  `PROD_LARGE`, 25 requested entities) checked every living entity at the end of every tick against its own
  `profile.max_leads / max_concerns / max_active_projects`: **10,916 entity-checks, 0 over-cap
  observations, 0 ticks with any over-cap entity.** One world, one seed, one horizon — enough to say the gap is
  not observable there, not enough to say it never occurs.

**Verdict `UNDECLARED`**: the operative test (a design decision is needed before any code change) is exactly
what the ticket asks for, and the decision is half-declared (PERF-007) rather than absent. A measurable effect
was not found in the corpus run, which bears on the ticket's `P1` but is not this pass's call.

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)

**Verdict as of 2026-09-30: `UNDECLARED`** — behaviour is declared as PERF-007 in code but its consequence is not adjudicated; 0 over-cap observations in a measured run; see Implementation Notes. Still `OPEN`.

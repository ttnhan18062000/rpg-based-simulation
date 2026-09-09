---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION
phase: open
date: 2026-09-09
tags: [architecture, strategy]
---

# TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION

## Title
Two live mechanisms enforce `max_leads` with different pending-update awareness — the cruder one runs first and preempts the more correct one

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while writing `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`'s own real-pipeline test
for `CapacityEnforcementPhase`'s lead-pruning behavior. This is **not** the "tested but
unreachable" pattern the rest of this session's batch has repeatedly found (see
`TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`) — both mechanisms here are live, reachable, and
run every relevant tick. The defect is different: they are not equivalent implementations of the
same rule, and the one with worse information runs first.

- `DetourSuggestionSystem.enforce_bandwidth()` (`src/systems/strategic_systems/detour.py:146-172`)
  is called from inside `StrategicIntelligenceSystem.fused_strategic_pass()` (much earlier in
  `src/engine/pipeline.py`'s own phase sequence — the `strategic_intelligence` phase). It sorts
  `entity.strategic.leads.values()` (the **current, pre-tick state only**) by `_certainty_score`
  and drops the excess past `profile.max_leads`. It has **no awareness of leads arriving this
  same tick** — not this tick's own new leads, not this tick's own decay/contradiction demotions.
- `CapacityEnforcementPhase.enforce()` (`src/engine/pipeline_phases/capacity_enforcement.py:44-57`)
  is the dedicated phase, running much later (after `lead_contradiction`, `lifecycle`, `groups`,
  etc.). Its own trigger is `len(entity.strategic.leads) + len(strat_upd.leads_add_or_update) >
  profile.max_leads` — it correctly accounts for this tick's own pending lead updates before
  deciding whether/what to prune.

**The consequence, confirmed via direct tracing (not assumed)**: because `enforce_bandwidth()` runs
first and only sees the pre-tick state, it can — and in a real reproduction did — prune an entity's
leads down to `max_leads` *before* `capacity_enforcement.py`'s own dedicated phase ever runs. By
the time the dedicated, pending-update-aware phase evaluates the entity, it is often already at or
under capacity from the cruder mechanism's own earlier action, so its own more correct logic never
gets to fire. The more correct implementation may rarely or never be the one that actually decides
what gets dropped — the same "real, tested code whose behavior is preempted rather than absent"
shape as this session's other findings, just at the level of which live mechanism's decision wins,
not whether either runs at all.

**Direct evidence this is real, not theoretical**: `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-
METHOD-CLEANUP`'s own capacity-interaction test
(`tests/unit/strategic/test_belief_staleness_decay_pipeline.py::
test_capacity_enforcement_prunes_newly_decayed_lead_over_fresh_ones`) could not be run against the
real, full `AuthoritativeApplyPipeline.refine()` — a 9-pre-existing-lead entity got pruned by
`enforce_bandwidth()` during `strategic_intelligence`, before `capacity_enforcement.py`'s own
dedicated phase ever saw it, contaminating the specific interaction that test needed to isolate.
The test had to call `CapacityEnforcementPhase.enforce()` directly, bypassing the earlier phase
entirely, to test the mechanism this AC actually cared about. Needing to route around a live phase
to exercise another live phase's own real logic is itself evidence of the preemption.

## Scope
- Confirm the preemption's real frequency/impact: under what real conditions does an entity
  actually reach `>max_leads` before `strategic_intelligence`'s own `enforce_bandwidth()` call,
  and how often does `capacity_enforcement.py`'s own dedicated logic get a chance to run at all
  for leads specifically once `enforce_bandwidth()` has already acted.
- Determine the real design intent: was `enforce_bandwidth()` meant to be superseded by
  `capacity_enforcement.py`'s later, more careful mechanism (i.e. a migration that never removed
  the old call site), or are the two intentionally layered for a reason not yet identified (e.g.
  `enforce_bandwidth()` as a cheap early guard, `capacity_enforcement.py` as the authoritative
  final pass)?
- **This is a real design decision — do not resolve which one should win, or unify them,
  without a decision.** Get a design decision (peer-routed, per this repo's standing convention)
  before implementing any fix.

## Out of Scope
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`'s own decay-staleness wiring — already
  closed; this ticket is a sibling finding from that ticket's own test-writing process, not a
  reopening of it.
- `enforce_bandwidth()`'s/`capacity_enforcement.py`'s own handling of concerns, hypotheses,
  projects, or candidate zones — this ticket is scoped to the `leads`/`max_leads` divergence found;
  if Investigate finds the same asymmetry for other capacity-bounded collections, record it here
  rather than silently expanding scope.
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`'s own scope (unreferenced code) — both
  mechanisms here are live and reachable; this finding does not belong in that audit.

## Acceptance Criteria
- [ ] Real evidence (not assumption) establishes how often, and under what conditions,
      `enforce_bandwidth()`'s own pruning actually preempts `capacity_enforcement.py`'s dedicated
      lead logic in practice.
- [ ] Real evidence establishes the design intent (superseded-but-never-removed vs. intentionally
      layered) — git history, related tickets, or design docs, not guessed.
- [ ] A design decision on the fix approach (unify into one mechanism, remove the redundant one,
      or document the layering as intentional) is obtained via peer review before any
      implementation.
- [ ] If a fix is implemented: real test evidence that the correct, pending-update-aware logic is
      the one that actually decides what gets pruned, not merely that "some" pruning still occurs.

## Related Tickets
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` (origin of this finding)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (a related but distinct class of finding —
  unreferenced code, not preempted-but-reachable code; explicitly out of that audit's own scope)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/systems/strategic_systems/detour.py` (`DetourSuggestionSystem.enforce_bandwidth()`)
- `src/engine/pipeline_phases/capacity_enforcement.py` (`CapacityEnforcementPhase.enforce()`)
- `src/systems/strategic_systems/intelligence.py` (`fused_strategic_pass()`, the call site that
  invokes `enforce_bandwidth()` early)
- `src/engine/pipeline.py` (the phase ordering itself)

## Assumptions / Open Questions
- Which mechanism should be authoritative (or whether both should be, in a coordinated way) is the
  central, deliberately-unresolved design question this ticket exists to raise, not answer here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_

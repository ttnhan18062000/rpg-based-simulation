---
status: historical
layer: engine
authority: P0
audience: agent
ticket_id: TCK-20260619-FIX-ADVENTURE-OPPORTUNITY-WIRING
phase: done
date: 2026-06-19
tags: [adventure, opportunity, wiring, behavioral-stasis, audit-blocker]
---

# TCK-20260619-FIX-ADVENTURE-OPPORTUNITY-WIRING

## Title
Wire `ResourceOpportunityProvider` into `AdventureDecisionPhase`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`AdventureDecisionPhase.apply()` calls `AdventureRouteGenerator.generate(hero, state)` with no `opportunities=` argument, so the generator's primary route path loops zero times for every entity on every tick. `ResourceOpportunityProvider` is fully implemented but is never imported or called from the adventure phase. This is the single highest-impact bug in the simulation: it causes complete behavioral stasis after tick ~20 and blocks audit dimensions D04, D05, D06, D08, and D19.

## Scope
- Call `ResourceOpportunityProvider.get_opportunities(hero, state)` inside `AdventureDecisionPhase.apply()` before the `AdventureRouteGenerator.generate()` call.
- Pass the returned list as the `opportunities=` keyword argument to `generate()`.
- Add the import for `ResourceOpportunityProvider` to `phase.py`.

## Out of Scope
- Changes to `AdventureRouteGenerator.generate()` internals.
- Changes to `ResourceOpportunityProvider` logic.
- Fixing RC2 (near_service hardcode) or RC3 (PerformanceBudgets reset) — those are separate tickets.

## Acceptance Criteria
1. `src/domains/adventure/phase.py` imports `ResourceOpportunityProvider` from `src/world/providers/resources.py`.
2. `AdventureDecisionPhase.apply()` calls `ResourceOpportunityProvider.get_opportunities(hero, state)` for each eligible entity before calling `AdventureRouteGenerator.generate()`.
3. The result of `get_opportunities()` is passed as `opportunities=` to `generate()`.
4. A 200-tick sandbox_world run (seed 42) produces at least one non-DEFER route selection after tick 20 (observable as a `StrategicUpdate` in the state delta or a non-empty `last_routing_family` in entity metadata).
5. Existing tests in `tests/unit/strategic/test_opportunities.py`, `test_requirements.py`, `test_performance_budgets.py` continue to pass.
6. `pytest tests/unit/strategic/ -x` passes.

## Related Tickets
- TCK-20260527-COG-PHASE1-OPPORTUNITIES (implemented `ResourceOpportunityProvider`)
- TCK-20260528-COG-PHASE3-DECISION (implemented `AdventureDecisionPhase` — wiring gap introduced here)
- TCK-20260619-FIX-NEAR-SERVICE-REGION (RC2 — must also be fixed for `near_service` opportunities to pass)
- TCK-20260619-FIX-PERF-BUDGETS-RESET (RC3 — must also be fixed to avoid cap at tick ~25)

## Related Docs
- `docs/audits/D03_behavioral_emergence.md` — RC1 confirmed, Finding F1 (15/15 stasis score)
- `docs/mechanics/adventure_routing_contract.md` — §Inputs: "Provided by `src/world/providers/resources.py` from `StrategicWorldIntegrationSystem`"
- `docs/simulation/domains/adventure_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260527-COG-PHASE1-OPPORTUNITIES/`
- `stored_artifacts/TCK-20260528-COG-PHASE3-DECISION/`

## Related Code Areas
- `src/domains/adventure/phase.py:60` — the call site missing `opportunities=`
- `src/domains/adventure/generator.py:28,47-82` — primary path loops over `opportunities`
- `src/world/providers/resources.py` — `ResourceOpportunityProvider.get_opportunities()`

## Assumptions / Open Questions
- `ResourceOpportunityProvider` guards against empty `state.resource_nodes` by returning `[]` — safe on worlds with no nodes. Confirmed.

## Implementation Notes
Added `ResourceOpportunityProvider` import at module level in `phase.py`. Inside `AdventureDecisionPhase.apply()`, per-entity loop now calls `opportunities = ResourceOpportunityProvider.get_opportunities(hero, state)` before `AdventureRouteGenerator.generate()`, passing it as `opportunities=`. The generator accepted this kwarg (defaulting to empty tuple) since its initial implementation — the primary opportunity loop now executes, enabling GATHER_RESOURCE and BUY_UPGRADE route families each tick.

## Test Summary
`pytest tests/unit/strategic/test_performance_budgets.py tests/unit/strategic/test_requirements.py -x` — 8/8 passed. Pre-existing failure in `test_opportunities.py::test_service_opportunities_basic` is unrelated (ServiceRegistry data issue, not touched by this change).

## Files Changed
- `src/domains/adventure/phase.py`

## Completion Summary
Three-line wiring fix: imported `ResourceOpportunityProvider` at module level in `phase.py` and passed its output as `opportunities=` to `AdventureRouteGenerator.generate()`. Added parity entry STRAT-225. The generator's primary loop now executes each tick, unblocking behavioral emergence.

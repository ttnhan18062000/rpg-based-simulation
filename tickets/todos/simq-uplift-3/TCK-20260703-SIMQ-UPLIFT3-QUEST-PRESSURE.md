---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE
phase: open
date: 2026-07-03
tags: [quests, strategy, world-evolution, backlog]
---

# TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE

## Title
Pressure-driven quest generation: extend QuestGenerator to select templates from world-state signals, not just hero level

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Carried over from `docs/plans/audit_fix_plan.md` P1-D (confirmed still open 2026-07-03).
`QuestGenerator` (`src/quests/generator.py`) selects from a static `TEMPLATES` list keyed only by
hero level (`QuestTemplate("q_slime_cull", "Clear the Slimes", QuestKind.HUNT, 1, 5, ...)`, etc.).
It does not read resource scarcity, regional threat level, or regional trauma score — signals the
`ResourceOpportunityProvider` already generates from world state for a different subsystem. Quest
content is therefore static and level-gated rather than emergent from the world's actual pressure
history, which caps NARRATIVE/PROGRESSION richness independent of any SimQ scoring-infrastructure
gap.

## Scope
1. Re-verify `QuestGenerator`'s current template-selection logic against `src/` (this ticket may be
   picked up well after 2026-07-03 — confirm the static-template characterization is still
   accurate before planning around it).
2. Identify the world-state pressure signals already available for reuse: resource scarcity by
   region, regional threat level, regional trauma score (see `docs/mechanics/05_world_evolution.md`
   §trauma and `docs/mechanics/03_economic_laws.md` §resource pressure for the driving formulas).
3. Extend `QuestGenerator` to accept these signals and select/weight quest templates that match the
   current pressure profile (e.g. a scarcity-driven region favors GATHER templates, a
   high-trauma region favors HUNT/defense templates).
4. Ensure hero-level gating is preserved alongside the new pressure-driven selection — this is an
   addition to the existing level-based filter, not a replacement.
5. Add tests: quest selection responds to a changed pressure profile in a controlled scenario;
   existing level-gating behavior is unchanged for scenarios with flat/neutral pressure.

## Out of Scope
- Changing `QuestTemplate`'s reward/requirement structure
- The broader quest activation precondition chain (`P1-B`, already resolved separately)
- Any change to `ResourceOpportunityProvider` itself (only consume its existing signals)

## Acceptance Criteria
- [ ] `QuestGenerator` accepts world-state pressure signals (scarcity, threat, trauma) as selection
      inputs, not just hero level
- [ ] Quest template selection demonstrably shifts when pressure signals change, in a test scenario
- [ ] Existing hero-level gating behavior unchanged for neutral-pressure scenarios (regression test)
- [ ] `docs/mechanics/05_world_evolution.md` / `03_economic_laws.md` cross-referenced correctly for
      the signal formulas actually used

## Related Tickets
- None currently open covering this — carried over fresh from `docs/plans/audit_fix_plan.md` P1-D

## Related Docs
- `docs/plans/audit_fix_plan.md` P1-D — original finding, source of this ticket
- `docs/mechanics/05_world_evolution.md` §trauma
- `docs/mechanics/03_economic_laws.md` §resource pressure

## Related Stored Artifacts
- None yet

## Related Code Areas
- `src/quests/generator.py` — `QuestGenerator`, `TEMPLATES`
- `src/systems/strategic_systems/intelligence.py` — quest-to-project activation chain (already
  fixed for P1-B, do not re-touch that logic)

## Assumptions / Open Questions
- UQ-1: Should pressure-driven selection be probabilistic (weighted random among matching
  templates) or deterministic (highest-pressure-match wins)? This affects determinism/replay
  guarantees — resolve during planning with reference to `docs/engine/architecture.md`'s
  determinism requirements, not left as an implementation-time guess.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)

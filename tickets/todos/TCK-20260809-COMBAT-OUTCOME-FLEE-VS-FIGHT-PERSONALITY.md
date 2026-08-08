---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY

## Title
Investigate real combat-outcome diversity: does race/personality currently drive flee-vs-fight
behavior, and does a "escape isn't guaranteed" pursuit-prevents-escape penalty already exist (user
recalls this logic existing) — richer `combat_started`/`combat_ended` events may be needed to see it

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Per the user's own explicit direction (raised while `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-
FALSE-INVESTIGATION`'s own real combat-legality bottleneck was being traced): if/once real combat
actually resolves more often, the user wants combat *outcomes* to be diverse and
personality/race-driven — e.g. a wolf should realistically fight to the death rather than flee,
while other creatures/entities might flee when losing, and a fleeing entity should not always
successfully escape (a real "the winner can prevent the loser from fleeing" penalty mechanic the
user recalls already existing somewhere in this codebase, not yet re-confirmed this session).

The user also suggested introducing richer combat-outcome observability
(`combat_started`/`combat_ended` events with result/winner/loser/escape info) — both because it's
a real, valuable observability gap on its own, and because it would make investigations like this
one (and the sibling legality-gate investigation) much easier to trace directly from event data
rather than requiring hand-instrumented probes each time.

## Scope
1. **Investigate** (mandatory before Plan):
   - Search the real codebase for any existing flee/retreat-vs-fight decision logic tied to
     race/personality/`ActionStyle` (this session's own earlier reading of `tactical.py` already
     found `ActionStyle.AGGRESSIVE`/`EVASIVE` biasing kiting/range behavior for `SKIRMISHER` role
     specifically — confirm whether this generalizes to a broader "should this entity flee" decision,
     or is narrowly role-scoped).
   - Search for the "pursuit prevents escape" mechanic the user recalls — check
     `CombatRetreatScorer`, `MovementMode.RETREAT`/`PURSUE` interaction, and the opportunity-attack
     mechanic itself (which already effectively penalizes retreating-while-adjacent — confirm
     whether this IS the mechanic the user is recalling, or whether a separate, more explicit
     "pursuit roll" mechanic exists elsewhere).
   - Confirm real per-race/archetype personality data (`bravery`, etc.) actually varies
     meaningfully across the content corpus (not all entities defaulting to the same values) —
     check `data/content/entities/entity_archetypes.yaml`'s own personality fields.
   - Assess the real event-coverage gap: do `combat_started`/`combat_ended`-equivalent events
     exist today (real trigger, real payload with result/winner/loser), or would this be new
     observability work — cross-reference `docs/simulation_quality/quality_scoring_contract.md`'s
     own COMBAT section and `docs/event_ledger/entity.yaml`.
2. **Plan**: once Investigate confirms what's real vs. missing, scope the real gap — likely some
   combination of (a) new/richer combat-outcome events, (b) confirming or building the flee-vs-fight
   personality decision, (c) confirming or building the pursuit-prevents-escape mechanic.
3. **Implement**: only the real, confirmed, minimal gap-closing work.

## Out of Scope
- The sibling `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`'s own real
  bottleneck (why combat rarely resolves at all) — this ticket assumes that gets fixed
  independently and focuses on outcome *diversity* once combat does resolve, not the resolution
  rate itself.
- Building an entirely new combat AI/decision framework — this ticket investigates and extends
  what's real and already there first.

## Acceptance Criteria
- [ ] investigation.md confirms what flee-vs-fight/pursuit-prevents-escape logic already exists
      (not assumed from the user's own recollection alone)
- [ ] investigation.md confirms the real combat-outcome event coverage gap, if any
- [ ] Real gap-closing work lands (scope determined by Investigate/Plan), re-verified against real
      corpus data
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION (sibling — the real
  combat-resolution-rate bottleneck this ticket's own outcome-diversity work depends on being
  fixed to be meaningfully observable)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` (COMBAT pillar section)
- `docs/event_ledger/entity.yaml`
- `docs/mechanics/02_combat_laws.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/tactical.py` (existing `ActionStyle`/kiting/role-based combat decision logic)
- `src/ai/goals/scorers.py` (`CombatRetreatScorer`)
- `src/observability/event_extractor.py` / `event_shapers.py` (real combat event coverage)
- `data/content/entities/entity_archetypes.yaml` (real personality data per archetype)

## Assumptions / Open Questions
- Whether the "pursuit prevents escape" mechanic the user recalls is the existing opportunity-attack
  mechanic (already real) or a separate, not-yet-found/not-yet-built mechanic — not assumed.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)

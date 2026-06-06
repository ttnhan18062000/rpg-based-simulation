# TCK-20260322-INDIVIDUAL_SPIRIT

## Title
Milestone 10: The Individual Spirit (AI Personality)

## Description
Implement persistent AI personality traits including grudges, mood-driven combat decisions, and locational memory aversion.

## Scope
- `src/core/aspects/mind.py`: Added `grudges`, `mood`, `memory_locations`.
- `src/actions/combat.py`: Damage increases grudge, kills record regional trauma.
- `src/ai/states.py`: Nemesis prioritization and mood-sensitive `should_flee`.
- `src/ai/perception.py`: Locational memory bias in exploration.

## Acceptance Criteria
- [x] Entities track damage from specific attackers as "grudges".
- [x] AI prioritizes "Nemeses" (high grudge) in combat.
- [x] HP threshold for fleeing shifts based on `mood`.
- [x] Regional deaths are recorded as negative memories.
- [x] Frontier exploration avoids regions with negative memories.
- [x] 5 unit tests covering all features must pass.

## Related Tickets
- TCK-20260322-RPG_REFINEMENT (General system improvements)

**Tier:** standard
**Type:** chore
**Priority:** P1

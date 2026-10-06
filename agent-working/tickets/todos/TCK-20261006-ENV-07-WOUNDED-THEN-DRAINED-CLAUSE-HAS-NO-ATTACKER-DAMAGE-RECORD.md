---
status: active
layer: world
authority: P3
audience: agent
ticket_id: TCK-20261006-ENV-07-WOUNDED-THEN-DRAINED-CLAUSE-HAS-NO-ATTACKER-DAMAGE-RECORD
phase: open
date: 2026-10-06
tags: [world, combat]
---

# TCK-20261006-ENV-07-WOUNDED-THEN-DRAINED-CLAUSE-HAS-NO-ATTACKER-DAMAGE-RECORD

## Title
`ENV-07` ratifies that "a wounded-then-drained death still counts", but the engine keeps no authoritative record
of recent attacker damage, so the implementation counts only deaths whose lethal update is `KILL`/`DEFEAT`.
Accepted as a documented gap because it is a measured no-op; implement it when the trigger fires.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Owner decision 15 (`ENV-07`, ratified, on `main` via #349) says regional trauma counts deaths with a **violent
cause**, and states explicitly: *"A wounded-then-drained death still counts."*

`rpg-implementer-2`'s implementation (`src/core/violent_cause.py`, DEV-011) judges a death by the cause recorded on
its **lethal update**: `KILL`/`DEFEAT` count. So a death where combat wounded the entity and hazard drain then
finished it is recorded `HAZARD` and **does not count**, which contradicts that clause.

**Why it isn't implemented now:** the engine keeps **no authoritative record of recent attacker damage**. Nothing
on `CombatComponent` or entity state carries it; only observability tracks it. Implementing the clause needs new
**durable** state (a typed "last attacker damage" record with a lifecycle), i.e. a change touching
`src/core/state.py` (ask-first) and a window length from the rule owner.

**Why the gap is accepted (planner ruling, 2026-10-06, owner may override):**
- **It is a measured no-op.** `rpg-designer`'s refutation test for `ENV-07` found **0 of 2,112** corpus `HAZARD`
  deaths had **any** earlier attacker damage, at windows of 50, 200 and unlimited, on two bases.
- Adding durable engine state for zero current effect would be premature.
- Rewording the clause to match the implementation would **change the meaning of an owner decision**, which the
  planner may not do (the row-12 lesson).

The gap is recorded in four places on Branch 1 (`boss-inert-and-violent-trauma-main`): Bible 05 §2, DEV-011,
`violent_cause.py`'s docstring, and the `regional_trauma` registry note — each marking **this clause only** as
"decided, not yet implemented".

## Trigger — when this must be implemented
Re-run the wounded-within-window measurement (attacker damage within 50 ticks before a `HAZARD` death) whenever
combat lethality changes materially — in particular after
`TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER`,
`TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION`, and the
trauma→panic mapping ticket land. **If any corpus `HAZARD` death had earlier attacker damage, the clause is no
longer a no-op and this ticket becomes P1.**

## Scope (when triggered)
1. Get the window length from the rule owner (`world-rule-catalog-design`), with what would refute it.
2. Add a typed, durable attacker-damage record per the Durable State Rule: typed model, stable location, defined
   lifecycle, inspection visibility, tests. Needs the planner's go for `src/core/state.py`.
3. Count a `HAZARD` death as violent when the record falls inside the window.
4. Remove the four "not yet implemented" markers; record the divergence.

## Out of Scope
- Rewording `ENV-07`. The ratified sentence stands.

## Acceptance Criteria
- [ ] Trigger measurement re-run after each listed ticket lands; result recorded here.
- [ ] If triggered: window ruled, typed record added, clause implemented, four markers removed.

## Related Tickets
- `TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING` (P0, closed) —
  where `ENV-07` and its refutation test came from.

## Related Docs
- `docs/world_rules/space-environment/environment.md` — `ENV-07`. `docs/mechanics/05_world_evolution.md` §2.

## Related Stored Artifacts
- The P0's `investigation.md`: the wounded-within-window measurement (0 of 2,112).

## Related Code Areas
- `src/core/violent_cause.py`; `src/core/state.py` (ask-first); `CombatComponent`.

## Assumptions / Open Questions
- **Lane.** Lane B when triggered.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)

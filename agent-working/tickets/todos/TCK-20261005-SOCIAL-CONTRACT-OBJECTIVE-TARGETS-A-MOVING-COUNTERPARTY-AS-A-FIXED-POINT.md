---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT
phase: open
date: 2026-10-05
tags: [strategy, cognition]
---

# TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT

## Title
`SocialContractScorer` targets a cooperation counterparty by entity id and freezes that entity's
position at goal-win time — the second and last live instance of the entity-as-fixed-point shape

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by `rpg-implementer` during the Scope 4 scorer audit of
`TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES`, and filed
separately on the planner's ruling rather than folded in — a different scorer, different semantics,
and different termination conditions.

`SocialContractScorer` (`src/ai/goals/social_contract_scorer.py:68-70`) sets
`target_id=str(contract.source_id)` — the **entity** id of the cooperation counterparty — and
`target_pos=source_entity.navigation.position`, that entity's position read **once**, at the moment
the goal wins.

**This is not an oversight, and the ticket should not be written as if it were.** The scorer's own
comment at `:55-59` ("Design Decision #8") states the constraint explicitly and documents the
position capture as the deliberate workaround for it:

> the counterparty's real position, so the materialized objective is tactically resolvable
> (`TacticalDecisionSystem._resolve_target_position()` only resolves int-castable targets against
> `state.resource_nodes`/`state.buildings`, never `state.entities` — a stringified entity id alone,
> as `accept_contract()`'s ORIGINAL `ObjectiveState` used, was never resolvable).

So the author knew the pursuit path cannot resolve an entity and compensated by capturing a
coordinate. That made the objective *resolvable*; it did not make it *correct for a target that
moves*. The counterparty walks away and the entity navigates to where they stood.

**Why it is worth a ticket despite the workaround being deliberate.** Cooperation contracts are live
in corpus runs, so this is not dormant. And the workaround is strictly worse than the mechanism that
`TCK-20261002` is now adding: a typed `target_entity_id` on `ObjectiveState` makes the entity target
resolvable *as an entity*, which is the thing Design Decision #8 wanted and could not have.

**The scorer audit that bounds this.** All `target_id=` sites in `src/ai/goals/` were swept. Exactly
two put an entity id there: `CombatEngageScorer` (owned by `TCK-20261002`) and this one.
`CombatRetreatScorer` uses `"town_center"`; every other site is a resource-node, building, region or
blocker id, or an `"adventure:<family>"` string. **This is a complete sweep with a negative result,
not a spot check** — there is no third case to find in that package.

## Scope
1. Move `SocialContractScorer`'s counterparty target onto the typed `target_entity_id` that
   `TCK-20261002` adds to `ObjectiveState`, so the pursuit path resolves the counterparty's current
   position instead of a captured coordinate.
2. Retire Design Decision #8's position-capture workaround **and its comment**, replacing the comment
   with one that records why the capture existed and what superseded it. Do not delete the reasoning;
   a future reader needs to know the capture was deliberate.
3. Give the social-contract objective its own termination conditions. They are **not** the combat
   ones: a cooperation contract's objective should terminate on the contract being fulfilled,
   cancelled or expired, and on the counterparty becoming unreachable — not on "target dead", which
   is the combat case. Enumerate them against the contract lifecycle in `investigation.md` before
   implementing, and if the contract lifecycle has no cancellation or expiry concept, say so rather
   than inventing one.
4. Measure, on a corpus world where cooperation contracts actually form, how often the captured point
   differs from the counterparty's live position, and how often a social-contract objective is still
   `ACTIVE` after its contract is no longer current. Report both whatever they are — including if
   they turn out to be near zero.

## Out of Scope
- Adding `target_entity_id` to `ObjectiveState`. `TCK-20261002` owns that; this ticket consumes it.
  **This ticket is sequenced after `TCK-20261002` lands** and must not race it.
- `CombatEngageScorer` and the combat objective's termination — `TCK-20261002`.
- The contract scoring, the reduction rule, or the tie-break at `:40-44`. Determinism-sensitive and
  not what this is about.
- Changing when contracts are offered or accepted. Only how an accepted contract's objective resolves
  its target.
- The lazy-import pattern at `:46-53`. Documented and deliberate; leave it.

## Acceptance Criteria
- [ ] A social-contract objective navigates toward the counterparty's **current** position, asserted
      end-to-end through a real `Kernel.tick_once()` loop with a counterparty that moves after the
      objective is created.
- [ ] Design Decision #8's workaround is removed and the superseding reason is recorded in the code,
      not only in this ticket.
- [ ] Every termination condition enumerated under Scope 3 has a test, and the enumeration itself is
      justified against the contract lifecycle rather than copied from the combat case.
- [ ] Scope 4's two measurements are reported with the world, seed and tick count, whatever the
      numbers are.
- [ ] Determinism: canonical/replay/fingerprint sweep green. Any recorded-hash fixture that moves is
      explained, not regenerated.
- [ ] The `accept_contract()` path mentioned at `:58` is checked — the comment says its *original*
      `ObjectiveState` used a bare stringified entity id. Confirm whether that path still constructs
      objectives and, if so, whether it has the same defect. A negative result is a valid answer.

## Related Tickets
- `TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES` — **the
  prerequisite.** Adds the typed `target_entity_id` this ticket consumes; its Scope 4 audit found
  this case. Sequence after it.
- `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` — the same family (a pursuit target
  that is not where the entity should go), different mechanism.
- `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG` — introduced the `target_position` fallback that
  Design Decision #8 was written around; its own cases must keep working.
- `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` (done, #291) — changed which
  objective kinds are materialized, so any pre-#291 measurement of this path is suspect.

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` — goal hierarchy and objective lifecycle
- `docs/engine/contracts/tactical_contract.md` §7 — objective target resolution

## Related Stored Artifacts
_(none yet — Scope 4's measurement will produce the first)_

## Related Code Areas
- `src/ai/goals/social_contract_scorer.py:55-70` — the capture and the decision comment
- `src/core/strategic.py::ObjectiveState` — where `target_entity_id` arrives from `TCK-20261002`
- `src/engine/tactical.py::_resolve_target_position` — the path that could not resolve an entity

## Assumptions / Open Questions
- **Whether the contract lifecycle has cancellation and expiry at all is open** and is Scope 3's
  first question. If it does not, the honest termination set may be smaller than the combat case's,
  and that is a finding rather than a gap to fill by inventing a lifecycle.
- Line numbers are at `9bf34765b`. `TCK-20261002` edits `src/core/strategic.py` and
  `src/engine/tactical.py`, so **re-derive them** at the commit this ticket starts from.
- How often cooperation contracts form in corpus runs is not quantified here. If Scope 4 finds the
  path is rare rather than live, the priority should be revisited rather than the ticket forced
  through — report it to the planner.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_

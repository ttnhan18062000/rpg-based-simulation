---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY
phase: open
date: 2026-08-09
tags: [combat, observability, simulation-quality]
---

# TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY

## Title
Real, high-level combat-engagement data (why an engagement started, who was involved and their
real state at the time, and how it ended — kill, successful escape, caught-while-fleeing, or
pursuit abandoned) is computed throughout `combat.py`/`tactical.py`/`movement.py` but almost
entirely discarded before reaching any observable event — build the missing high-level
observability layer first (per-attack tactical-modifier detail deferred, see Out of Scope) so
combat scenarios can be judged for reasonableness later

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Direct follow-up to this session's own combat-behavior work (attack-legality fix, personality/
`ActionStyle` wiring, readiness/movement decoupling). The user asked what combat "status" —
winner, outcome, statistics — is currently recorded, and the honest answer was: almost nothing.
Individual hit/kill events (`combat_damage`, `combat_initiated`, `entity_killed`) carry only
`attacker_id`/`killer_id`; there is no `combat_ended`-style summary event, no win/loss semantics,
no statistics anywhere, and no way to correlate outcomes with the personality/`ActionStyle` work
already shipped.

The user then asked for **initiation reason** ("why did combat happen") and clarified that
"combat dodged" means **avoiding combat entirely — fleeing, escaping** (not a to-hit miss/evasion
roll — confirmed via direct investigation that no such roll exists: `CombatComponent.evasion` is
a real field but is completely unused anywhere in `calculate_damage()`/`resolve_attack()`; every
legal attack always lands. Building a real evasion/miss mechanic is explicitly out of this
ticket's own scope — a separate, bigger design question, not bundled in here per the user's own
direction to think about "avoid the combat, fleeing... not dodge/evasion in combat").

Traced the full real combat lifecycle end-to-end (source-code-verified, not assumed) to scope
this properly:

**Initiation (why combat starts)** — two real, architecturally distinct causes, currently
indistinguishable in any event:
1. **Deliberate**: `GoalKind.COMBAT_ENGAGE` wins the real goal competition →
   `tactical.py`'s own `ATTACK`/`SKILL` emission branch (reached only when none of the
   retreat/reposition/hold branches below fired first — the deliberate-engage path is
   structurally distinct from every other branch by construction).
2. **Forced/reactive**: an opportunity attack triggered by a *hostile's own* disengagement
   (`movement.py`, `CombatUpdate.is_opportunity_attack=True`) — the attacker didn't choose this
   fight, the target's own retreat triggered it.

**During (what happens on a single attack) — explicitly deferred, per direct user direction
("let in-combat mechanism later, we investigate high-level of combat first")**: a real, already-
computed tactical-modifier trace (`CombatUpdate.trace`: `HIGH_GROUND`, `FLANKING`, `SURROUNDED`,
`COVER_REDUCTION`, `SHATTER`, `EXHAUSTION`, `STAMINA_EXHAUSTION`, `BOND_SYNERGY`,
`FINAL_ATK_MULT`/`FINAL_DEF_MULT`, `REWARD_SOURCE`/`REWARD_CATEGORY`, `WOUND_INFLICTED`) is
computed on every single `resolve_attack()` call and discarded before reaching any event — real,
valuable, but explicitly **not this ticket's own scope** (see Out of Scope). Documented here only
so the finding isn't lost; a future, dedicated in-combat-mechanism ticket should pick it up.

**Entity information at engagement time (real requirement of this ticket)**: to let a later
investigation judge whether a given combat scenario was *reasonable* — e.g. a low-level civilian
killed by a high-level predator, or a low-bravery entity that should have fled forced into a fight
— both `combat_engagement_started` and `combat_engagement_ended` must carry a real snapshot of
each involved entity's own state at that moment, not just bare IDs. Real, already-available
fields: `identity.evolution_level` (power/level), `combat.hp`/`combat.max_hp` (health state),
`combat.atk`/`combat.def_stat` (raw combat stats), `identity.role` and `identity.properties`'s own
`faction_id`/`race_id`/`archetype_id` (who/what they are), `identity.personality.bravery` and
`combat.action_style` (this session's own new personality-driven signals — lets a later analysis
directly ask "did an EVASIVE-styled, low-bravery entity get denied its own escape chance").

**End without a kill (real, currently 100% invisible)** — traced 4 distinct real real outcomes:
1. **Successful escape**: `MovementMode.RETREAT` + `ActionStyle.EVASIVE` → `skip_oa=True`
   (`movement.py:184-186`) — the opportunity attack is skipped entirely, zero damage, zero event
   of any kind today. (Only reachable at real, non-trivial volume as of this session's own
   `TCK-20260809-COMBAT-ACTIONSTYLE-WIRING` — before that fix, no entity ever had `ActionStyle
   .EVASIVE`, so this path was itself dormant.)
2. **Caught while fleeing**: `MovementMode.RETREAT` without `EVASIVE` (or hostiles still engaged)
   → the real opportunity attack fires (`is_opportunity_attack=True`, `is_lethal=False` by
   default) — may or may not be lethal depending on damage; currently only visible as a bare
   `combat_damage`/`entity_killed` event indistinguishable from a normal, deliberate attack.
3. **Pursuit abandoned by the attacker**: `tactical.py`'s own real `LEASH_RETURN`
   (`LeashService.is_beyond_leash`/`should_give_up_chase`) or `STALEMATE_BREAK`
   (`stale_ticks > 10`) reason codes — the chase simply stops, no resolution event at all.
4. **Entity chose to flee in the first place**: `PANIC_RETREAT`
   (`AppraisalSystem.is_fleeing`) or `SAFETY_PRESSURE_RETREAT` — real, already-computed reason
   codes living only in `TaskUpdate.payload_set`, never surfaced as an observable event.

All of `tactical.py`'s own real tactical-decision reason codes (`PANIC_RETREAT`, `LEASH_RETURN`,
`SAFETY_PRESSURE_RETREAT`, `STALEMATE_BREAK`, `SEEK_COVER`, `KITING`, `PURSUIT_BLOCKED_KITE`,
`BRACKETING`, `GUARDING_ALLY`, `INTERCEPTING`, `HOLD_CHOKEPOINT`, `REGROUP`,
`CONTRACT_OBLIGATION_GUARD`) are confirmed real and currently invisible outside internal task
state — none reach `event_shapers.py`.

## Scope
1. **Investigate**: confirm the above findings against the current source (re-verify line numbers/
   exact conditions, since this session's own prior tickets touched several of these files); check
   `docs/simulation_quality/event_type_coverage.md`/`docs/simulation_quality/quality_scoring_contract.md`
   for the real registration requirements for new event types; check whether any new event types
   should be scored by the COMBAT pillar or marked `unscored_intentional` (matching this session's
   own precedent for new-but-not-yet-pillar-integrated events); confirm the real, minimal set of
   per-entity fields to snapshot (evolution_level, hp/max_hp, atk/def_stat, role, faction_id/
   race_id/archetype_id, personality.bravery, action_style) against live `EntityState` structure.
2. **Plan**: design the real, high-level event-type additions — a `combat_engagement_started`
   (real `trigger_reason`: `GOAL_ENGAGE` | `OPPORTUNITY_ATTACK`, plus a real entity snapshot for
   both participants) and a `combat_engagement_ended` (real `outcome`: `KILL` | `ESCAPED` |
   `CAUGHT_FLEEING` | `PURSUIT_ABANDONED`, plus attacker/defender IDs and each participant's own
   real end-state snapshot, e.g. final HP, so a later analysis can see both the starting and
   ending state of a scenario). Decide the real `SimulationEvent`/`event_shapers.py` wiring shape,
   matching this session's own established push-based event patterns.
3. **Implement**: the real, minimal event additions — reusing already-computed data
   (`is_opportunity_attack`, `tactical.py`'s own existing reason strings, real `EntityState`
   fields for the snapshot), not inventing new game logic and not surfacing the per-attack
   `CombatUpdate.trace` (deferred, see Out of Scope).

## Out of Scope
- **Per-attack tactical-modifier detail** (`CombatUpdate.trace`: high ground, flanking, cover,
  exhaustion, bond synergy, etc.) — explicitly deferred per direct user direction ("let in-combat
  mechanism later, we investigate high-level of combat first"). This ticket covers
  engagement-level start/end only, not individual attack resolution detail. Documented in this
  ticket's own Request Summary so the finding isn't lost for that future ticket.
- Building a real evasion/miss/to-hit-roll mechanic — `CombatComponent.evasion` remains unused;
  the user explicitly clarified this ticket is about avoiding combat (fleeing), not a per-attack
  dodge roll. If a real to-hit mechanic is ever wanted, that's a separate, bigger design decision
  (a new combat law, not observability) — not bundled here.
- Statistical aggregation/reporting tooling (win-rate dashboards, per-faction/per-`ActionStyle`
  outcome correlation reports) — this ticket produces the real, raw event data (including the
  entity-snapshot fields needed for reasonableness analysis); building aggregation/analysis
  tooling on top of it is a natural, real follow-up once the events exist, not this ticket's own
  scope.
- Any change to real combat resolution logic itself (`calculate_damage`, `resolve_attack`,
  legality checks) — purely additive observability on top of already-computed data.

## Acceptance Criteria
- [ ] investigation.md re-confirms the real, current combat-lifecycle architecture (initiation and
      all 4+ end-without-kill paths) against live source, not assumed from this ticket's own
      request-summary alone
- [ ] Real, new high-level event type(s) land covering: initiation reason (deliberate vs.
      opportunity-forced) and all real end-without-a-kill outcomes (successful escape,
      caught-while-fleeing, pursuit-abandoned) — per-attack tactical trace explicitly deferred
- [ ] Both new event types carry a real, honest snapshot of each involved entity's own state
      (level, hp/max_hp, atk/def_stat, role/faction/race, bravery, action_style) sufficient to
      later judge whether a given combat scenario was reasonable
- [ ] New event types registered in `docs/simulation_quality/event_type_coverage.md` and, if
      pillar-scored, `docs/simulation_quality/quality_scoring_contract.md`
- [ ] Real corpus re-verification: a live run against `dungeon_crawl`/`urban_political` shows the
      new events firing at real, non-zero, honestly-reported volume, with real, sensible-looking
      entity-snapshot data — not assumed from unit tests alone (matching this session's own
      established discipline)
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION,
  TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (DONE, same session — made real combat
  resolve often enough for this observability data to actually matter)
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION, TCK-20260809-COMBAT-ACTIONSTYLE-WIRING (DONE,
  same session — the successful-escape path this ticket observes only became reachable at real
  volume because of the `ActionStyle` wiring fix)
- TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY (DONE, same session — first confirmed the
  real opportunity-attack/`EVASIVE` mechanics this ticket now proposes making observable; also
  disclosed the same richer-events gap as its own out-of-scope finding)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md`, `docs/simulation_quality/quality_scoring_contract.md`
- `docs/mechanics/02_combat_laws.md` (the real, Certified Level 1 combat-laws doc — confirmed to
  NOT claim any evasion/miss mechanic, consistent with this investigation's own findings)
- `docs/engine/contracts/combat_contract.md` §4 (Opportunity Attacks)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/tactical.py` (all real reason codes, the deliberate-engage `ATTACK`/`SKILL` branch)
- `src/engine/movement.py` (opportunity-attack trigger, `skip_oa` real escape condition)
- `src/core/state.py` (`EntityState`/`IdentityComponent`/`CombatComponent`/`PersonalityComponent`
  — the real fields the entity snapshot draws from)
- `src/observability/event_shapers.py`, `src/observability/event_extractor.py` (where the new
  event types need real wiring)
- `src/engine/combat.py` (`CombatResolutionSystem.resolve_attack`, the real `trace` dict) —
  reference only, not touched by this ticket (see Out of Scope)

## Assumptions / Open Questions
- Whether `combat_engagement_started`/`combat_engagement_ended` should be scored by the COMBAT
  pillar directly, or land as `unscored_intentional` initially (matching this session's own
  precedent for new events not yet integrated into scoring) — a real Plan-phase decision, not
  pre-decided here.
- Exact shape of the entity snapshot (a flat dict on the event payload vs. a typed sub-structure)
  — a real Plan-phase decision, matching whatever pattern is most consistent with this repo's own
  existing `SimulationEvent`/payload conventions.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)

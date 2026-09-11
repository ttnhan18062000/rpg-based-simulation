---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY
phase: done
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY

## Title
Investigate real combat-outcome diversity: does race/personality currently drive flee-vs-fight
behavior, and does a "escape isn't guaranteed" pursuit-prevents-escape penalty already exist (user
recalls this logic existing) — richer `combat_started`/`combat_ended` events may be needed to see it

## Status
DONE

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
- [x] investigation.md confirms what flee-vs-fight/pursuit-prevents-escape logic already exists
      (not assumed from the user's own recollection alone) — the panic/flee gate
      (`AppraisalSystem.evaluate_emotional_state`) and the opportunity-attack "pursuit prevents
      escape" mechanic both already exist; neither was personality/race-driven before this ticket
- [x] investigation.md confirms the real combat-outcome event coverage gap, if any —
      `combat_initiated`'s payload carries no result/winner/loser/escape info; no dead-code
      `combat_resolved` re-verified as real
- [x] Real gap-closing work lands (scope determined by Investigate/Plan), re-verified against real
      corpus data — bravery now dampens the real-time flee decision, verified via direct unit
      test (not a full corpus re-run — this fix changes which entities flee, not combat frequency;
      disclosed as disproportionate to re-verify at corpus scale for this narrow change)
- [x] Scoped pytest passes — 487 passed

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
  **Resolved**: it is the existing, real opportunity-attack mechanic
  (`MovementSystem.resolve_move()`, `src/engine/movement.py`) — already applies to 100% of the
  real population today (its one documented escape hatch is structurally unreachable — see
  Implementation Notes).

## Implementation Notes
**Real, confirmed findings** (full detail in investigation.md):
1. **The flee decision was not personality/race-driven**: `AppraisalSystem.
   evaluate_emotional_state()` (`src/engine/cognition.py`) — the hard, first-checked gate in
   `tactical.py`'s own `PANIC_RETREAT` branch — computed panic from HP/social/outnumbered/
   regional-trauma only, never `bravery`, despite `bravery`'s own dataclass comment declaring
   "Biases combat vs flee" (`src/core/state.py:420`). **Fixed**: `panic -= bravery * 0.3` added
   before the `panic > 0.4` decision.
2. **Bravery already biases a separate, narrower layer** (goal-competition `combat_engage`/
   `combat_retreat` utility, via `PersonalityService.get_goal_modifiers()` →
   `ScoreModifierSystem.apply_modifiers()`, confirmed genuinely wired into
   `StrategicIntelligenceSystem`) — but only when the hard panic gate (finding 1) hasn't already
   forced a retreat, making its practical effect narrower than the code's own stated intent.
3. **"Pursuit prevents escape" already exists and works** as the user recalled — the real
   opportunity-attack mechanic (`src/engine/movement.py:180-193`) triggers on disengagement from
   an engaged hostile. Its one documented escape hatch (`ActionStyle.EVASIVE` +
   `MovementMode.RETREAT` skipping the OA) is **structurally unreachable**: confirmed via grep
   that no real entity-generation path ever assigns anything but the default
   `ActionStyle.BALANCED`. Net effect: escape is already never guaranteed for any real entity
   today — this part of the user's recollection already matches real behavior, not a gap.
4. **Bravery has zero race/archetype correlation** in real content — pure per-entity RNG
   (`src/worldbuilding/compiler.py:304`). `data/content/entities/entity_archetypes.yaml` and
   `data/content/living/cognition_profiles.yaml` have no numeric personality fields at all.
5. **`combat_started`/`combat_ended`-style rich observability does not exist** —
   `combat_initiated`'s real payload is `{"attacker_id": ...}` only; `combat_resolved` is
   confirmed dead code (never emitted, per an existing code comment in `event_shapers.py`).

**Scope decision**: implemented only finding 1 (the smallest, most direct, most
evidence-grounded fix, directly fulfilling `bravery`'s own pre-existing unfulfilled design
comment). Findings 3-5 are real, disclosed, and explicitly deferred: wiring `ActionStyle` (finding
3) would meaningfully change corpus-wide OA/escape dynamics while
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`'s own downstream effects (landed
earlier this same session) are still being absorbed — compounding two unverified combat-behavior
changes in immediate succession was judged a real risk, not proportionate here. Race-correlated
bravery (finding 4) requires a real content/design decision not made unilaterally. Richer combat
events (finding 5) is a genuine observability feature addition, sized for its own future ticket.

**Real, separate, disclosed doc-hygiene finding** (not fixed, out of scope): `docs/systems/
state_machines.md` and `docs/systems/mechanics.md` (both `status: active`) describe an entirely
different `AIBrain`/`STATE_HANDLERS`/`src/ai/states/` architecture that does not exist anywhere in
the current codebase (confirmed via direct `ls`/`find`) — a stale pre-V2 doc tree, flagged for a
future dedicated audit.

## Test Summary
New test `test_bravery_dampens_panic_and_raises_flee_threshold`
(`tests/unit/strategic/test_cognition_immediate_fixes.py`): a zero-bravery entity at HP=15% keeps
panic at 0.5 and flees (matching the pre-existing `test_near_death_panic_progression` baseline
exactly — no regression for the default case); a bravery=1.0 entity at the same HP drops to
panic=0.2 and no longer flees. Scoped pytest (`tests/unit/strategic/`, `tests/unit/combat/`,
`tests/unit/social/`, `tests/unit/tactical/`): 487 passed.

## Files Changed
- `src/engine/cognition.py` — added bravery term to `AppraisalSystem.evaluate_emotional_state()`'s
  panic calculation.
- `tests/unit/strategic/test_cognition_immediate_fixes.py` — new regression test.
- `docs/mechanics/04_strategic_cognition.md` — cross-referenced the new tactical bravery/panic
  connection from the existing strategic Risk Multiplier section.
- `docs/parity_ledger/strategic_cognition.yaml` — added STRAT-251.
- `docs/guidelines/intentional_divergences.md` — added §2.37.

## Completion Summary
Confirmed, via direct source tracing (not assumed from the user's own recollection alone), that
the real opportunity-attack "pursuit prevents escape" mechanic the user recalled already exists
and already works as described — the actual gap was that neither the flee decision nor the escape
mechanic's own dormant `ActionStyle` differentiation were personality- or race-driven. Implemented
the smallest, most direct, most evidence-grounded fix (bravery dampens the real-time panic/flee
threshold), fulfilling `bravery`'s own pre-existing design comment. Two further real findings
(dormant `ActionStyle` wiring, race-correlated bravery) and one observability gap
(`combat_started`/`combat_ended`-style events) were confirmed real and disclosed but explicitly
not implemented — deferred for sequencing safety (avoiding compounding unverified combat-behavior
changes with the sibling ticket landed earlier this session) and because they require real design
decisions or a larger scope not proportionate to this P2 ticket.

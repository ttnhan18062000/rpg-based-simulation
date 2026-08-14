---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY

## Context search (mandatory step)
`search_docs` for "flee retreat combat outcome personality bravery pursuit escape opportunity
attack CombatRetreatScorer" surfaced `docs/systems/state_machines.md` (a 23-state
`AIBrain`/`STATE_HANDLERS` FSM with a documented `FLEE` state) and
`docs/engine/contracts/tactical_contract.md` §4 "Retreat & Disengage Rules". **Cross-checked
before trusting either**: `docs/systems/state_machines.md` (and its sibling
`docs/systems/mechanics.md`) describe `src/ai/states/` and `src/ai/brain.py` — **neither exists
in the current codebase** (confirmed via direct `ls`/`find`) — this doc tree is stale, describing
a fully superseded pre-V2 architecture despite `status: active`. Disclosed as a real doc-hygiene
finding (see Docs Requiring Update) but not otherwise treated as authoritative. By contrast,
`docs/engine/contracts/tactical_contract.md` matches the real, live `TacticalDecisionSystem`
exactly (confirmed via direct source read) and was trusted.

## Finding 1 (the real, primary gap): the flee decision is not personality- or race-driven
`src/engine/tactical.py`'s own hard, first-checked flee gate: `if emotion.is_fleeing: ... return
...PANIC_RETREAT`. `emotion` comes from `AppraisalSystem.evaluate_emotional_state()`
(`src/engine/cognition.py`), which computes `panic` from: regional dread (world trauma),
nemesis/grudge social history, **HP percentage** (thresholds at 10%/20%/40%), and
outnumbered-ratio (hostiles > 2x allies). `is_fleeing = panic > 0.4`.

**This function never referenced `subject.identity.personality.bravery` anywhere**, despite
`bravery`'s own dataclass field carrying an explicit comment declaring the intended design:
`bravery: float = 0.0  # Biases combat vs flee` (`src/core/state.py:420`). Confirmed real,
non-trivial per-entity variance exists — `bravery` is RNG-assigned per entity at generation
(`src/worldbuilding/compiler.py:304`, `rng.get_float(Domain.WORLD, 0, entity_id, sub_id=11)`,
range `[0.0, 1.0)`) — the comment's intent was simply never wired into this specific, dominant
flee-decision function. Since this hard gate is checked *before* any goal-competition layer runs,
it overrides everything else regardless of how brave an entity's personality is: **a maximally
brave entity and a maximally cowardly entity flee at the exact same HP/context thresholds today.**

## Finding 2: bravery *does* already bias a separate, narrower layer — but only when Finding 1's gate doesn't already force a retreat
`PersonalityService.get_goal_modifiers()` (`src/ai/personality.py:24-28`) returns real utility
modifiers keyed by `GoalKind` value: `combat_engage: bravery*0.5`, `combat_retreat:
-bravery*0.5`. This *is* genuinely wired: `ScoreModifierSystem.apply_modifiers()`
(`src/ai/score_modifiers.py`) is called from `StrategicIntelligenceSystem`
(`src/systems/strategic_systems/intelligence.py:1280-1293`) on the real output of
`GoalRegistry.get_all_scores()` — confirmed real, not dead code (unlike several other
`personality_mods` keys in the same dict, `"combat"`/`"flee"` bare strings, which don't match any
currently-registered `GoalKind` and are dead weight). So bravery *does* real work biasing whether
an entity's strategic goal competition favors `COMBAT_ENGAGE` over `COMBAT_RETREAT` — but this
layer only gets consulted when Finding 1's hard panic gate hasn't already forced a
`PANIC_RETREAT` first. In practice this makes the *user-visible* effect of bravery on
combat-vs-flee much narrower than the code's own stated intent.

## Finding 3: the "pursuit prevents escape" mechanic already exists and is real — but currently applies uniformly (not personality/race-driven), and the escape-hatch is structurally dead
The user's own recollection matches real code: `MovementSystem.resolve_move()`
(`src/engine/movement.py:180-193`) triggers a real opportunity attack
(`CombatResolutionSystem.resolve_multi_attack(..., is_opportunity_attack=True, ...)`) whenever an
entity disengages while adjacent to an *engaged* hostile — this already is "the winner can
prevent the loser from fleeing," and is the corpus's own dominant real kill mechanism (confirmed
by prior session findings, `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`).

**The one documented escape hatch — `skip_oa = True` when `MovementMode.RETREAT` and
`entity.combat.action_style == ActionStyle.EVASIVE`
(`src/engine/movement.py:185-186`) — is structurally unreachable in real gameplay**: grepped
every real entity-construction site (`src/systems/world_systems/generator.py`,
`src/worldbuilding/compiler.py`) and confirmed `action_style` is never explicitly set anywhere —
every real entity keeps `CombatComponent.action_style`'s own default, `0` (`ActionStyle.BALANCED`).
The `ActionStyle` enum (`BALANCED`/`AGGRESSIVE`/`EVASIVE`) has real code hooks (this OA-skip, and
a kiting-bias branch at `tactical.py:437`) but no real producer ever assigns anything but the
default — the same "real hook, no real producer" class of finding as several sibling tickets this
session (`EquipmentService.auto_equip()`, `trait_expressed`).

**Net effect, disclosed honestly**: today, escape from an engaged hostile via disengagement is
*already* never guaranteed for any real entity (100% of the population always risks the OA, since
none ever get the EVASIVE-retreat free pass) — this part of the user's own recollection already
matches real, working behavior, not a gap. What's *missing* is the personality/race-driven
*variation* in that risk — a wolf and a citizen currently face identical OA risk on disengagement,
and the dormant `ActionStyle` system that could have differentiated them (an aggressive-styled
predator perhaps *never* attempting evasive retreat at all, versus a low-bravery archetype
reliably getting the safe exit) is unimplemented.

## Finding 4: real personality data variance is confirmed, but not race/archetype-correlated
`data/content/entities/entity_archetypes.yaml` and `data/content/living/cognition_profiles.yaml`
have **zero** `bravery` (or any numeric personality trait) fields anywhere (confirmed via grep) —
`cognition_profile`s (`instinctive_animal`, `opportunistic_humanoid`, etc.) carry only qualitative
planning/reasoning descriptors (`planning_depth`, `risk_modeling`, etc.), not personality trait
values, and are not traced further here (a separate strategic-cognition-depth concern, out of
this ticket's own scope). Real `bravery` variance exists (confirmed Finding 1) but is **pure
per-entity RNG**, uncorrelated with race, archetype, or faction — a "wolf" archetype gets exactly
the same bravery distribution as any other entity. This means the user's own specific example ("a
wolf would fight to the death... depend on race") is not yet possible even with Finding 1's fix
alone — closing it fully would require either race-correlated bravery ranges at generation time
(a real content/design decision, not decided here) or race-specific overrides, both explicitly out
of this ticket's own proportionate scope (would require new content schema/authoring decisions).

## Finding 5: `combat_started`/`combat_ended`-style rich observability does not exist
`combat_initiated` is a real, emitted event (`src/observability/event_shapers.py:121-127`) but its
payload is minimal (`{"attacker_id": ...}` only — no result/winner/loser/escape info).
`combat_resolved`/`attrition_threshold_crossed` are confirmed dead code (a code comment in
`event_shapers.py:63` already says so directly: "dead code, never emitted by any path"). No event
anywhere marks "attempted flee, succeeded" vs. "attempted flee, caught by opportunity attack" —
confirmed via direct read of `event_shapers.py`'s full COMBAT-domain shaper. Real, confirmed gap;
not implemented here (see Scope decision below).

## Scope decision: what's implemented vs. disclosed-only
Per this ticket's own "real, minimal gap-closing work" mandate, implemented **only Finding 1**
(bravery dampens panic in `AppraisalSystem.evaluate_emotional_state`) — it is the smallest, most
direct, most evidence-grounded fix that closes the primary gap the user named ("personality should
affect flee vs fight"), and directly fulfills `bravery`'s own pre-existing, unfulfilled design
comment. Findings 3-5 are real and disclosed but **not implemented**:
- Finding 3's `ActionStyle` wiring would meaningfully change corpus-wide combat/kill dynamics
  (session context: `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION` just landed
  in this same session, itself still only partially resolving the corpus's own low combat-legal
  rate) — changing OA-escape odds now, before that fix's own real downstream effects are
  understood at scale, is a real risk of compounding unverified changes. Proportionate to defer.
- Finding 4 (race-correlated bravery) requires a real content/design decision not made here.
- Finding 5 (richer combat events) is a genuine observability feature, not a bug fix — sizable
  enough (new event type, event_type_coverage.md, tag registry, possible SimQ scoring
  implications) to warrant its own future ticket rather than folding into this one.

## Docs Requiring Update
- `docs/mechanics/04_strategic_cognition.md`: note the real, now-partially-closed bravery/panic
  connection (cross-reference from the existing Risk Multiplier section, §6.3).
- Flag (not fixed): `docs/systems/state_machines.md` and `docs/systems/mechanics.md` describe a
  non-existent `src/ai/states/`/`src/ai/brain.py` architecture despite `status: active` — a real,
  separate doc-hygiene gap, out of this ticket's own scope to fully audit/fix.

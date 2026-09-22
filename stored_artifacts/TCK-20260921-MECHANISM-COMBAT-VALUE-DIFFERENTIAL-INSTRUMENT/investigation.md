# Investigation — TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT

## Re-scoped mid-investigation, by explicit peer instruction

This ticket originally scoped an 8-mechanism `combat` sweep (shape-triaged below, kept for record —
the triage itself is real and was done before the re-scope). Peer re-scoped it to a single,
narrower question before any batch-1 test beyond the shape triage was committed: **within a real
fight, does an entity's own combat attributes have measurable purchase on the outcome, or not?**
Rationale given: combat costs more per mechanism than progression did (RNG is live throughout, so
every scenario needs the draw-order question settled first) and yields fewer real candidates
(target selection and action choice are arbitration-shaped and out of scope by name) — a full sweep
is most of the cost for a fraction of the decision value, and the narrow question is the one the
`stats_dirty` P0 finding actually needs answered. One or two scenarios, recorded only against the
mechanism entries the scenario genuinely evidences, then stop — no further combat waves, no
arbitration instrument, `#232` closes after this.

A `trauma` test (`WoundService` wound-penalty functions) had been drafted under the original
broader scope; deleted, unrun, uncommitted, per explicit peer instruction to leave unbuilt work
unbuilt rather than finish it for tidiness once the scope narrowed.

## §5.1 shape triage, all 8 `combat` mechanisms (done before the re-scope, kept for the record —
## NOT the active scope of this ticket's own batch 1 below)

| id | current instrument/verdict | shape | disposition |
|---|---|---|---|
| `combat_resolution` | `corpus_run`/`observed` (reachability) | pure formula, same-tick (`calculate_damage()`) | Narrow re-scope's own target |
| `trauma` | `code_trace`/`observed` | pure formula, same-tick (wound-penalty sums) | Drafted, deleted per re-scope; not this ticket's scope |
| `tactical_decision` | `corpus_run`/`contradicted` (reachability) | decision among competing neighbors/goals, emotional appraisal, goal hysteresis | Arbitration-shaped, out of scope by name |
| `combat_engagement` | `scenario`/`observed` (reachability) | risk-scored gate decision (posture vs threshold) | Arbitration-adjacent, out of scope by name |
| `action_pacing_readiness` | `scenario`/`observed` | threshold gate | Already effectively value-tested by its own existing scenario; not re-verified |
| `movement` | `code_trace`/`observed` | pathing + congestion ladder | Needs more investigation; not attempted |
| `skill_unlocks` | `code_trace`/`partial` | static level->skill-list lookup | Catalog-lookup shaped, presumptively out of scope |
| `status_effects` | `code_trace`/`orphan` | zero real producers | Out of scope, no producer |

## The narrow question, investigated and answered

**Which real attributes feed combat resolution, and through what chain**: re-read
`LevelingService.recalculate_combat_stats()` (`src/progression/leveling.py:76-105`, already fully
investigated in the progression program) in full: `attributes.strength` -> `atk`,
`attributes.vitality`+`endurance` -> `max_hp`, `attributes.vitality` -> `def_stat`,
`attributes.agility` -> `evasion`/`readiness_speed`. `attributes.charisma`/`intelligence`/`wisdom`/
`spirit`/`perception` feed none of these outputs — confirmed by re-reading the function's full body,
not assumed. `CombatResolutionSystem.calculate_damage()` (`src/engine/combat.py:31-46`, also
already investigated) reads only `attacker.combat.atk`/`defender.combat.def_stat`.

**Real apply-path sequencing rules out a naive same-tick test**: `apply.py`'s `stats_dirty`
recalculation runs as part of the SAME tick's final apply step, using entity updates already
collected during that tick — a real attribute-change dispatched in the same tick as a forced
attack would not have its derived `atk` recalculated in time to affect that same tick's combat
resolution (the attack reads the CURRENT, pre-recalculation `combat.atk`). A same-tick "change
attribute then attack" scenario would therefore silently test nothing, or worse, look like a
negative result for the wrong reason (the change hadn't taken effect yet, not that attributes don't
matter) — exactly the vacuous-negative-arm shape this program's own §5 item 5 / §5.1 rules exist to
catch. Resolved by calling `LevelingService.recalculate_combat_stats()` directly with two real
attribute presets (the same function the real pipeline calls, not a shortcut or synthetic
replacement) to get the derived `atk` a real recalculation WOULD produce, then staging that result
directly and dispatching a real fight — tests the same real formula without the misleading
same-tick race.

**Determinism trap, resolved by code trace before staging anything** (re-confirmed, same
conclusion this program already reached for `evolution`/`xp_leveling`): neither
`recalculate_combat_stats()` nor `calculate_damage()` contains an RNG call. Varying the attacker's
attributes changes only the derived `atk` value fed into `calculate_damage()`, never the fight's
own RNG surface (there is none in this code path at all). Confirmed empirically too: both arms
resolve the same real one-hit shape (a single dispatched attack, no retries, no branching).

## Scenarios built (2, both against `combat_resolution` only)

1. `tests/mechanic_scenarios/test_combat_resolution_damage_value_differential.py` — direct
   `combat.atk`/`combat.def_stat` differential (the mechanism's own most immediate real inputs).
   Positive control: varying `combat.atk` directly moves damage by exactly the documented formula.
   Negative control: `identity.evolution_level` (already proven irrelevant to combat resolution in
   the progression program) leaves damage unchanged.
2. `tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py` —
   the narrow question's own direct answer, chaining both real formulas end-to-end through a real
   dispatched fight. Positive control: real strength 5 -> 20 (via the real derivation function)
   deals more real damage. Negative control: `charisma` (confirmed unread by the derivation
   function) leaves the real fight's outcome unchanged.

Both scenarios reuse `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` (goblin vs orc,
already proven a legal forced-attack pairing). No new world needed.

## The one-sentence answer

**Yes — within a real, dispatched fight, an entity's own combat attributes (strength, via the real
derivation chain into `atk`) have measurable, formula-exact purchase on the fight's outcome.**
Recorded against `combat_resolution` only — the mechanism these two scenarios actually dispatch and
observe, not stretched across `derived_stats` (already independently value-tested in the
progression program) or any other entry.

**What this means for `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS`**: the
`stats_dirty` bug is severe for the first, worse reason peer named — it is destroying something
that demonstrably matters. An entity's combat attributes have real, exact, formula-governed
purchase on how its fights resolve; a recalculation that silently discards a species' own base
stats in favor of generic defaults is not a cosmetic drift, it is erasing a real determinant of
real combat outcomes. This finding is added to that ticket's own Request Summary as the direct
answer to the open question it left for the roadmap session, not left as a separate implication for
someone else to connect.

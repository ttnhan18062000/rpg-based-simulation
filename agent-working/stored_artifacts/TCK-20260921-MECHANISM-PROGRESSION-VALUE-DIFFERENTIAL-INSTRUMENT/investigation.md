# Investigation — TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT

## Context scan
- `mcp__knowledge-search__search_docs` / `graphify query` run for "progression value differential",
  "readiness_speed_scaling", "xp_leveling evolution" at the start of this program (pre-summary).
  Confirmed no existing value-differential instrument anywhere in the repo — only the reachability
  harness from Program A (`docs/plans/mechanic_verification_scenarios_proposal.md`).
- Full `registries/mechanisms.yaml` pulled for `systems: [progression]`: 15 mechanisms total, 3
  already `instrument: scenario` (`readiness_speed_scaling`, `evolution`, `xp_leveling` — all
  reachability-shaped, not value-differential-shaped; `readiness_speed_scaling`'s own scenario is
  corpus-reachability instrumentation, not "does varying agility change readiness_speed").

## Candidate mechanisms considered
| id | state | why chosen / rejected |
|---|---|---|
| `readiness_speed_scaling` | partial, contradicted | **chosen** — pure, RNG-free formula, ideal calibration mechanism |
| `derived_stats` | done, code_trace | **chosen** — same function as above (`recalculate_combat_stats`), free second mechanism from the same harness |
| `evolution`/`xp_leveling` | done/partial, scenario | **chosen** — structurally distinct code path (combat kill → conservation → EvolutionSystem), proves the instrument isn't just re-testing one function |
| `breakthrough_bonuses` | partial, contradicted | rejected — acquisition side has zero real producers (confirmed prior investigation); no real input to vary in play |
| `class_assignment` | partial, code_trace | rejected — `resolve_role_defaults()` is a static catalog lookup by role_id, not an ongoing per-tick mechanism; a differential here would test the resolver's dict lookup, not simulation behavior |
| `genetics_aptitude` | gated | rejected — flag off by default (`ENABLE_REPRODUCTION_HUMANOID_PATH`); reachability question, not value |
| `progression_conversion` | gated | rejected — flag off by default (`ENABLE_PROGRESSION_EVOLUTION`); reachability question, not value |
| `attributes_biology`, `race_archetype`, `personality`, `aging_death`, `succession`, `entity_role`, `build_diversity` | various | not investigated this batch — batch is capped at 3 mechanisms per peer instruction ("prove it small before scaling") |

## Determinism/seed-sensitivity trap — resolved by direct code reading, not assumption
Peer named this trap explicitly: varying an input might also perturb RNG draw order, producing a
downstream difference unrelated to the mechanism itself.

**For `readiness_speed_scaling`/`derived_stats`**: `LevelingService.recalculate_combat_stats()`
(`src/progression/leveling.py:76-180`) is a pure function of `AttributeComponent` fields
(`strength`/`vitality`/`endurance`/`agility`), equipment, learned skills, and traits — no RNG call
anywhere in the function body (read in full). Varying one attribute field while holding the others
fixed cannot touch any other output field through a hidden RNG path, because there is no RNG path
at all.

**For `evolution`/`xp_leveling`**: the concern was specifically whether varying the *defender's*
`identity.evolution_level` (the lever `xp_reward = defender.identity.evolution_level * 10` reads,
`src/engine/combat.py:510`) could also change the defender's own derived combat stats, altering how
many rounds/RNG draws a forced combat kill consumes before resolving — the value-differential
analogue of the cadence trap peer warned about. Resolved by direct trace, in order:
1. `CombatResolutionSystem.calculate_damage()` (`src/engine/combat.py:31-46`) — the entire damage
   formula reads only `attacker.combat.atk` and `defender.combat.def_stat`. No RNG call in the
   function. `is_kill = new_hp <= 0` (`combat.py:486`) is fully deterministic given those two
   fields.
2. `LevelingService.recalculate_combat_stats()` — confirmed above — never reads
   `identity.evolution_level`, only `AttributeComponent` fields. So `combat.atk`/`def_stat`
   (and therefore `calculate_damage`'s result) cannot change when only `identity.evolution_level`
   varies.
3. `src/domains/combat_engagement/power.py:49` and `perception.py:51` both state explicitly, in
   their own code comments, that `evolution_level` is "deliberately excluded, not merely
   unweighted" from `true_power()`/combat-power comparisons — independent, in-code confirmation
   that the codebase itself treats `evolution_level` as decoupled from combat power.
4. Full repo grep of every `evolution_level` read site (`grep -rn "evolution_level" src/`) — the
   only sites inside `combat.py` are the `xp_reward`/`gold_delta` construction lines
   (177/178/282/283/394/395/510/516/575/581), all AFTER the kill/damage decision, never inputs to
   it.

Conclusion: staging `defender.combat.hp` low enough to guarantee a one-hit kill (a legitimate,
already-used technique — same shape as Program A's `emotion_near_death_hardening` low-HP staging)
and varying only `defender.identity.evolution_level` between arms produces byte-identical combat
resolution (same `calculate_damage` inputs, same RNG draws if any) in both arms — only the
post-kill `xp_reward` value differs. No forced route: the kill itself is real, dispatched through
the real `CombatResolutionSystem`/`EvolutionSystem` pipeline, exactly as `evolution`'s own existing
positive control does.

**Negative control choice for `evolution`/`xp_leveling`**: needed a defender field that (a) is real
and legitimate to vary, (b) provably does not feed `xp_reward`'s formula, and (c) does not itself
perturb the fight (ruling out `attributes.*`, which WOULD change `combat.atk`/`def_stat` and
therefore the fight's own resolution — a bad negative control, since a value differential must
change only the target field, not two things at once). Chosen: `identity.evolution_points` (same
component as `evolution_level`, a different field) — `xp_reward`'s formula reads only
`evolution_level`, never `evolution_points`; `recalculate_combat_stats` reads no `identity` fields
at all. Symmetric, clean, provably inert on both axes.

## Purpose-built-worlds check
`readiness_speed_scaling`/`derived_stats`: no new world needed — a single entity's own
`AttributeComponent` is mutated directly on an already-compiled state (matches Program A's own
`_stage_leads`-style direct-state-mutation pattern), reusing any existing compiled world.

`evolution`/`xp_leveling`: reused the existing `data/worlds/mechanic_scenario_combat_judgement_
withdrawal/` world (goblin id=1 vs orc id=2, real catalog-driven content, already used by
`test_combat_judgement_withdrawal.py`) rather than authoring a new one — it already has two
combat-capable entities of different factions at adjacent positions, staged via a forced ATTACK
task exactly as that existing test does. No forced route: attacking is a real, legal action for
this pairing (already proven legal by the existing test in this same world). Defender's `combat.hp`
staged low to guarantee the kill deterministically, same shape as `emotion_near_death_hardening`'s
low-HP staging in Program A.

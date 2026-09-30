---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS
phase: open
date: 2026-09-21
tags: [simulation-quality, progression]
---

# TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS

## Title
World-integrity bug living in the progression path: `stats_dirty` recalculation silently
converges every entity's species-specific base combat stats toward generic defaults, and has
been doing so throughout every prior balance measurement of this simulation

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
**Read this as a world-integrity finding, not a progression-subsystem defect that happens to
live in progression's code path — per explicit peer review before this ticket was filed further:
this is the most consequential finding of the batch it came from.** Found incidentally while
building the value-differential calibration instrument for
`TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT` (not deliberately hunted — a
zero-delta sanity check against a real compiled entity failed unexpectedly, which is what
surfaced this).

`src/engine/apply.py:616-624`'s `stats_dirty` call site invokes
`SkillScalingService.get_effective_stats(new_att, new_eq, wounds=..., scars=..., learned_skills=...,
traits=..., current_role=..., active_breakthroughs=..., class_id=...)` **without ever passing
`base_hp`/`base_atk`/`base_def`/`base_evasion`**. Both `get_effective_stats()`
(`src/engine/rpg_depth.py:342-356`) and the `recalculate_combat_stats()` it calls
(`src/progression/leveling.py:76-105`) default these to generic values (`base_hp=100,
base_atk=10, base_def=5, base_evasion=0.05`) when not supplied.

Confirmed directly: a `goblin_scout` from `data/worlds/mechanic_scenario_combat_judgement_
withdrawal/` spawns at `combat.max_hp=35` (a real, content/species-specific base). The moment
`stats_dirty` fires for ANY reason (an attribute change, an equipment change, a learned skill, a
trait add/remove, a wound, or `evolution_level` increasing — see `apply.py:595-608`'s own
`stats_dirty` condition), `max_hp` recalculates to `112` — the generic default (`100 + vitality*2 +
endurance*0.5` with `vitality=endurance=5`), silently discarding the entity's own spawned base
entirely, not just adjusting it by the delta. The same applies to `atk`/`def_stat`/`evasion`.

**Why this is world-integrity severity, not a progression-scoped defect**: `stats_dirty`'s own
trigger list is broad and routine — any attribute change, equipment change, learned skill, trait
add/remove, wound, or evolution-level increase fires it, for every entity, across every species,
role, and faction in the simulation. This means every entity's species/content-driven combat-stat
differentiation degrades toward one shared generic baseline (100/10/5/0.05) as soon as it takes
any of those ordinary actions, and keeps degrading further the more it acts. **This silently
invalidates every combat-balance observation anyone has ever measured against this simulation
before today, not just future ones** — any SimQ run, any manual balance pass, any tuning decision
made by watching real corpus play was watching species differentiation erode over the course of
that same run without anyone knowing it was happening. It is filed under `progression` because
the erosion is triggered by progression-adjacent events, but the actual defect and its blast
radius belong to the simulation's own world-model integrity, not to the progression subsystem's
own scope.

**Direct answer to this ticket's own open question, added 2026-09-21**
(`TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT`, a narrow, single-question follow-on
to the value-differential program): does entity identity actually matter to combat outcomes, or is
this erosion cosmetic? **Answer: it matters, exactly and measurably.** A real, dispatched fight
(`tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py`)
confirms that an entity's own `strength` attribute, run through the real
`LevelingService.recalculate_combat_stats()` derivation into `combat.atk`, has real,
formula-exact purchase on how much damage that entity deals in a real fight
(`CombatResolutionSystem.calculate_damage()`, also confirmed RNG-free and formula-exact via its own
differential). This `stats_dirty` bug is therefore severe for the worse of the two reasons this
ticket's own Request Summary named: it is not silently drifting something decorative, it is
silently destroying a real, demonstrated determinant of real combat outcomes every time it fires.

## Scope
For whoever picks this up:
1. Confirm whether `EntityState`/`IdentityComponent`/content schema carries a real, addressable
   per-entity base_hp/base_atk/base_def/base_evasion value anywhere (spawn-time content
   resolution likely sets `combat.max_hp` etc. directly rather than storing a separate "base"
   field — need to check `src/core/builder.py`/`src/content/resolver.py`'s spawn path to see if a
   recoverable base value exists to pass through).
2. If a real base value exists: wire it through `apply.py`'s `stats_dirty` call site so
   recalculation preserves the entity's own base instead of substituting the generic default.
3. If no such value is currently tracked as durable per-entity state: this is a genuine durable-
   state gap (per this repo's own Durable State Rule — a species/content-derived base that
   "survives beyond the current tick" needs a typed, stable location) and the fix needs to add one,
   not just thread a value through that doesn't exist yet.
4. Measure real corpus impact: how often does `stats_dirty` actually fire per entity per tick in
   real corpus play, and for how many entities does the resulting base_hp/atk/def diverge
   meaningfully from their spawned value? Not measured here.

## Out of Scope
- Fixing the value-differential instrument's own test suite — both new test files
  (`test_readiness_and_derived_stats_value_differential.py`,
  `test_evolution_xp_reward_value_differential.py`) already account for this by comparing
  arm-to-arm deltas (both arms undergo the identical default-base substitution), not absolute
  values against a raw spawn baseline — their own verdicts are unaffected by this bug and do not
  need to be revisited once this is fixed.

## Acceptance Criteria
1. A real decision + fix (or explicit documented divergence, if this turns out to be intended
   behavior) for whether `stats_dirty` recalculation should preserve an entity's spawned base
   stats.
2. If fixed: a real differential test confirming a `stats_dirty` trigger no longer silently
   inflates/deflates a species-specific entity's base stats toward the generic default.
3. Real corpus measurement (Scope item 4) recorded, even if the fix itself is deferred further.

## Related Tickets
- `TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT` — where this was found
- `TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT` — direct answer to this ticket's
  own "does this matter" question: yes, exactly and measurably
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — prior investigation into
  the same `stats_dirty`/`recalculate_combat_stats` code path, from the reachability angle
- `TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES` — companion finding from
  the same program: this ticket shows species differentiation eroding after spawn, that one shows
  biological pressure was never differentiated by entity identity in the first place. Worth reading
  together for the roadmap session's own "how much does entity identity influence the simulation"
  question, per peer instruction — not merged, each stands on its own evidence.

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/apply.py:593-624` (`stats_dirty` trigger + call site)
- `src/engine/rpg_depth.py::SkillScalingService.get_effective_stats`
- `src/progression/leveling.py::LevelingService.recalculate_combat_stats`
- `src/core/builder.py` / `src/content/resolver.py` (spawn-time base-stat assignment, not yet read
  for this ticket)

## Assumptions / Open Questions
Whether a real, addressable per-entity "base" value exists anywhere in durable state today is
genuinely unknown — not assumed either way. That's Scope item 1's own first task.

## Implementation Notes

### 2026-09-30 — Premise re-verified against current code, and Scope 1 answered

Re-verified before scoping, per the standing rule that today's sample produced two false premises
and one duplicate. **The premise holds exactly, unchanged, at `01ac88f56`:**

- `src/engine/apply.py:616-623` calls `SkillScalingService.get_effective_stats(new_att, new_eq,
  wounds=…, scars=…, learned_skills=…, traits=…, current_role=…, active_breakthroughs=…,
  class_id=…)` — **no `base_hp`, `base_atk`, `base_def` or `base_evasion` argument.**
- `src/engine/rpg_depth.py:349-352` declares those four as keyword defaults
  `base_hp: int = 100, base_atk: int = 10, base_def: int = 5, base_evasion: float = 0.05`.
- So every `stats_dirty` recalculation rebuilds combat stats from the generic baseline and
  discards the entity's spawned species values. Confirmed by reading both sites, not inferred.

### Scope 1 — "does a recoverable per-entity base value exist?" — YES, with a caveat

**The base values exist as real content.** `data/content/entities/stat_profiles.yaml` defines
per-archetype profiles named `<archetype>_base` — e.g. `goblin_scout_base` at lines 55-59 with
`hp: 35, max_hp: 35, atk: 8, def: 2`, matching the ticket's observed spawn value of 35 exactly.
Others present: `hero_base`, `commoner_base`, `monster_base`, `wolf_predator_base`,
`goblin_raider_base`, `goblin_archer_base`, `cave_spider_base`. This is a first-class content
family, not ad-hoc data — `src/content/repository.py:117` registers it as
`ContentFamilySpec("entities.stat_profiles", …, StatsProfileDefinition, "stats_profiles")` and
`src/content/reference_graph.py:23` gives it the reference type `stat_profile`.

**The caveat, and the real design question: the entity does not carry a pointer back to its
profile.** Neither `EntityState` nor `IdentityComponent` has an `archetype_id`, `stat_profile_id`
or `species` field — verified by reading the full field list of both. So at `stats_dirty` time the
recalculation has no declared way to ask "which profile were these stats derived from?"

`EntityState.kind: str` **is** present and is in scope at the `apply.py` call site, which makes it
the obvious candidate link. **Whether `kind` actually resolves to a `stat_profiles.yaml` id has
NOT been confirmed** — that is the first thing to check, and it decides which of two fixes applies.

### Two fix shapes, and which one applies depends on that check

**A — lookup, if `entity.kind` resolves to a profile id.** Resolve the profile at recalc time and
pass its four values through. No new durable state. **Blocker to check first:** does the
`apply.py` path have access to a catalog/registry at all? There is direct precedent for it not
having one — `WorldCompiler.compile()` has no `catalog_repo` parameter and had to be handed
`context.legacy_roles`/`legacy_faction` for exactly this reason
(`src/worldbuilding/repository.py:89-114`'s docstring, `TCK-20260808-MONSTER-ROLE-MISTAGGING-
INVESTIGATION`). If `apply.py` is likewise catalog-free, A needs the same kind of context
threading and is not the cheap option it looks like.

**B — typed durable base-stat field, if no reliable link exists.** Store the resolved base values
(or the profile id) on the entity at spawn. This is **durable state** and the Durable State Rule
applies in full: typed model, stable location in entity state, defined lifecycle, inspection/debug
visibility, and tests. **Do not** put it in `identity.properties` — CLAUDE.md forbids durable
meaning in free-form metadata, and that dict is exactly that.

Either way this is **not** a parameter pass-through, which is how the ticket's Scope step 2 reads
("wire it through"). Both shapes need a real decision first, and B is an architecture change.

### 2026-09-30 — RUNTIME MEASUREMENT: the erosion never fires. Severity is wrong.

The ticket's central severity claim — that this "silently invalidates every combat-balance
observation anyone has ever measured" — was a reasoned inference from the code path. **Measured, it
is false.**

Probe: production loader (`WorldRepository.load_world_with_context`, the path real runs use — not
the content-catalog path, per `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION`), real
`Kernel` ticks under `PROD_SMALL`, seed 42, counting every `SkillScalingService.
get_effective_stats` call.

| world | ticks | entities | **`stats_dirty` firings** | deaths | entities whose stats moved |
|---|---|---|---|---|---|
| `frontier_living_world` | 600 | 49 | **0** | 21 | 8 |
| `crowded_frontier` | 400 | 38 | **0** | 13 | 10 |
| `quest_dense_frontier` | 400 | 6 | **0** | 6 | 6 |

**Zero firings in all three worlds, across 40 deaths.** So the generic-baseline substitution at
`apply.py:616-623` is real in code but **unreached at ordinary corpus run lengths**. No entity's
species stats were eroded, because the recalc never ran.

**The zero is trustworthy** — a monkeypatch returning zero is meaningless without a positive
control, so the probe asserts one: it calls through `apply.py`'s own resolved name
(`apply_mod.SkillScalingService is rpg_depth.SkillScalingService`, then invokes it) and requires
the counter to increment by exactly 1 before the run starts. It did. Combat also genuinely
occurred (40 deaths), so this is not "nothing happened".

**Why stats still moved: there is a second, additive writer, and it is the one actually in use.**
`CombatUpdate.max_hp_delta` (`src/core/updates.py:111`, merged additively at `:145`) plus
`LevelingService`'s own `max_hp += …` at `leveling.py:123,147`. Observed increments were
`+5/+10/+15/+20` on `max_hp` only, with `atk`/`def` never moving — consistent with level-up HP
grants, not with a full recalc.

**This is the architecturally important finding.** The codebase already has a delta path for
combat stats that **preserves species bases by construction**, running alongside a full-recalc
path that **destroys them**. The live path is the safe one. So the question is less "how do we
feed the recalc a correct base" and more "should this recalc path exist at all, given a working
additive path already carries the load."

**Consequences for the decision:**
- **No SimQ re-baseline is implied** — not because the fix is conservative, but because the code
  being fixed does not execute. This resolves the open question raised in review; it was the right
  question and the answer is empirical, not assumed.
- **The `commoner_base` behaviour change does not arise in practice.** Village Workers keep
  `100/10/0` today because the recalc never runs on them. Worth declaring anyway, but it is not a
  live regression risk.
- **P0 is the wrong severity.** This is a latent defect in an unreached path — the same
  "unreachable mechanism" shape as the corpus this session has been working through all day. It
  should be re-rated and re-sequenced against defects that do execute.

**Bounds, stated plainly:** three worlds, one seed, 400–600 ticks. It does **not** prove the path
is unreachable in principle — only that nothing in an ordinary corpus run triggers it. A longer
run, an equipment-heavy scenario, or any future code that sets `update.attributes` /
`update.equipment` / `wound_update` would reach it immediately. The defect should still be fixed;
it should not be fixed *first*, and it should not be described as having corrupted past
measurements.

### Sequencing note

The ticket's own claim that this invalidates prior combat-balance observations is plausible and
important, but **do not restate it as established without a runtime measurement** — it is
currently a reasoned inference from the code path. If a before/after measurement is wanted, note
`TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR` (the corpus runs at ~10 entities and
could not detect a real 58% combat-volume change), so SimQ may not be the right instrument for
demonstrating the improvement.
(none yet — not started)

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)

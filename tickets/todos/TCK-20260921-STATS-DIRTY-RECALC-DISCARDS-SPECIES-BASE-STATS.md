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
`stats_dirty` recalculation silently replaces an entity's spawned/species-specific base combat
stats with `get_effective_stats()`'s generic defaults, every time it fires

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found incidentally while building the value-differential calibration instrument for
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

This means any entity whose content definition set a non-default base HP/ATK/DEF (species,
role, or other content-driven base) loses that base the first time it takes ANY action that marks
`stats_dirty` — not a rare edge case; `stats_dirty`'s own trigger list is broad (any attribute or
equipment change is exactly what's expected to happen routinely in real play).

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
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — prior investigation into
  the same `stats_dirty`/`recalculate_combat_stats` code path, from the reachability angle

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
(none yet — not started)

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)

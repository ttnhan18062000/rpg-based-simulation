---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME
phase: open
date: 2026-09-17
tags: [progression, simulation-quality, testing]
---

# TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME

## Title
No entity in any tested corpus world accumulates enough combat-kill XP to cross a single level-up
threshold within 1000 ticks — a content-composition/pacing gap, not a code defect

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Follow-up to `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS`, closed with a
root-caused, measured verdict: the combat-XP-to-level-up chain
(`src/engine/combat.py` → `conservation.py`'s COMBAT branch →
`src/engine/evolution.py::EvolutionSystem.evaluate()` → `LevelingService._execute_level_up()`) is
directly confirmed correct and reachable via a real Kernel-tick positive control (a goblin staged
at `evolution_points=95` who then kills an orc worth 10 XP correctly reaches
`evolution_level=2, evolution_points=5`, matching
`docs/mechanics/attribute_progression_contract.md`'s own formula exactly). The code is not broken.

The problem is volume. Instrumented across the same three real, compiled, catalog-driven corpus
worlds (`crowded_frontier`, `quest_dense_frontier`, `hero_guild_routing`; seed 42; 1000 ticks each,
via a real `Kernel` tick loop):

| World | Entities | Kills | Total XP granted | Busiest single entity |
|---|---|---|---|---|
| `crowded_frontier` | 42 | 10 | 100 | 5 kills, 50 XP |
| `quest_dense_frontier` | 9 | 0 | 0 | — |
| `hero_guild_routing` | 35 | 3 | 30 | 2 kills, 20 XP |

The level-2 threshold is `int(100 * 1**1.5) = 100` XP, and a typical kill (a level-1 monster,
`HOSTILE_CREATURE` classification, `xp_multiplier=10`) grants 10 XP — about 10 kills needed for one
level-up. The busiest single entity across all three worlds reached half of that, in the entire
1000-tick window. No entity present at world-compile time changed `evolution_level` at all in any
of the three runs.

This matches the `camp` family exactly
(`docs/plans/world_composition_precondition_gap_finding.md`): correct, wired code, defeated by
real-world data/volume rather than a defect in the mechanism itself.

## Scope
1. Determine whether the low kill volume is itself explained by
   `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own already-evidenced lead
   (region-name resolution gap suppressing cross-faction proximity in at least one corpus world) —
   check whether fixing that investigation's own finding, if and when it lands, changes the kill
   count materially before independently retuning anything here.
2. If kill volume alone doesn't explain the gap even after accounting for (1), evaluate whether the
   XP-per-kill values (`defender.identity.evolution_level * 10` for a hostile creature,
   `* 20` for a hero) or the level-threshold formula (`int(100 * level**1.5)`) are realistic for
   the actual combat cadence these corpus worlds produce — a tuning question, not a wiring one.
3. Re-run this ticket's own discriminating measurement at a longer tick count (this investigation
   used 1000, matching the original ticket's own window; `COMB-318`'s own 9500-tick run found the
   same early-cessation pattern for combat generally, so a longer window is not expected to change
   the conclusion, but this was not directly re-checked).
4. Revisit `src/domains/combat_engagement/power.py::true_power()`'s own `evolution_level` exclusion
   with fresh corpus data once real leveling (if any) becomes observable — flagged, not fixed, by
   the original ticket; carried forward here per that ticket's own Acceptance Criterion #5.

## Out of Scope
- Re-investigating cross-faction combat rarity from scratch — that is
  `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own scope; this ticket only checks
  whether its resolution would materially change this finding.
- Any change to `LevelingService`, `EvolutionSystem`, or the combat reward-construction code
  without first confirming (via scope items 1–2) that a code-level tuning change — as opposed to a
  world-composition fix — is actually the right lever.
- Verifying `attributes_biology` — out of reach of the investigation that produced this ticket; not
  picked up here either.

## Acceptance Criteria
1. The relationship between this finding and `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`
   is resolved with evidence (either "fixing that ticket would materially raise kill volume" or "it
   would not, and the gap is independent").
2. If a real tuning change (XP values, threshold formula, or corpus composition) is warranted, it
   is scoped with real measured evidence of the new resulting kill-to-level-up ratio, not a guess.
3. `true_power()`'s own `evolution_level` exclusion is revisited with fresh data, or explicitly
   re-flagged forward again if leveling still doesn't occur in the corpus.

## Related Tickets
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — closed; this ticket's own
  more precise successor, per that ticket's Acceptance Criterion #4.
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — the most likely upstream root cause of
  the low kill volume this ticket measured; check before independently retuning.
- `TCK-20260831-READINESS-SPEED-FORMULA` — a separate mechanism (`readiness_speed`) whose own
  agility-scaling recalculation is gated on the same `stats_dirty` trigger this ticket's own
  finding shows almost never fires from combat.

## Related Docs
- `docs/mechanics/attribute_progression_contract.md` — XP threshold formula, level-up execution
  order; the code this ticket's own positive control confirmed matches exactly.
- `docs/plans/world_composition_precondition_gap_finding.md` — the `camp`-family pattern this
  finding matches.
- `docs/parity_ledger/combat_movement.yaml` (`COMB-318`) — the original, narrower related finding.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS/investigation.md`
  — the full measurement and root-cause trace, including a false wiring-gap lead caught and
  corrected before being reported.

## Related Code Areas
- `src/engine/combat.py` (kill-reward construction, `xp_gain` computation)
- `src/engine/evolution.py::EvolutionSystem.evaluate()` (real, unconditional pipeline phase that
  consolidates XP and evaluates the level-up threshold)
- `src/progression/leveling.py::LevelingService` (threshold formula, `_execute_level_up`)
- `src/domains/combat_engagement/power.py::true_power()` — downstream dependency on the frozen
  `evolution_level == 1` corpus data this finding explains; flag, don't fix here without fresh data

## Assumptions / Open Questions
- Whether the measurement holds at tick counts beyond 1000 (not directly re-checked; `COMB-318`'s
  own 9500-tick run suggests it would, but that ran a different world set).
- Whether the `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` fix (if pursued) alone
  raises kill volume enough to matter, or whether XP-per-kill/threshold values also need
  independent tuning.

## Implementation Notes
Not yet started.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed after `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` was closed
with a root-caused, measured content-composition/pacing verdict (not a wiring defect), per that
ticket's own explicit "verify, don't repair in the same pass" scope and its Acceptance Criterion #4
(a real defect, if confirmed, gets filed with the correct scope rather than fixed as part of the
investigation).

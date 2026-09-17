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
BLOCKED — on `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (see Scope item 1 and the
2026-09-17 peer-review note below). Not a soft dependency: retuning the threshold before that
ticket lands would be masking a starved-system signal, not fixing anything — see the note.

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

**The complete causal chain, per peer review 2026-09-17, is now fully measured, not assumed at any
link**: cross-faction combat is rare (`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`
measured it at zero in 3 of 4 corpus worlds) → few kills (this ticket's own 0–10 kills per world) →
XP never accumulates past a fraction of one threshold → no level-ups fire → `stats_dirty` never
sets → agility never reaches `readiness_speed`'s own recalculation
(`TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS`'s original finding). This
retires several previously-separate open threads at once and fully explains
`action_pacing_readiness`'s own agility-scaling half without any code being broken anywhere in the
chain.

## Scope
1. **Blocking, not merely "check first."** Wait for
   `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` to land (or be explicitly deprioritized
   by the user) before touching the threshold, XP-per-kill values, or corpus composition. Per peer
   review 2026-09-17: lowering the threshold to fit today's 0–10 kills-per-1000-ticks is the same
   failure shape as lowering the attribution ratchet to fit a low score — it silences a real signal
   (entities barely fight) instead of fixing the thing the signal is reporting on. If combat becomes
   less rare after that ticket lands, re-run this ticket's own discriminating measurement fresh
   against the new kill volume before concluding anything about whether XP values or the threshold
   formula also need tuning.
2. Only after (1) is resolved: if kill volume alone doesn't close the gap even with realistic
   cross-faction combat, evaluate whether the XP-per-kill values
   (`defender.identity.evolution_level * 10` for a hostile creature, `* 20` for a hero) or the
   level-threshold formula (`int(100 * level**1.5)`) are realistic for the actual combat cadence —
   a genuine tuning question at that point, not a stand-in for the rarity fix.
3. Re-run this ticket's own discriminating measurement at a longer tick count (this investigation
   used 1000, matching the original ticket's own window; `COMB-318`'s own 9500-tick run found the
   same early-cessation pattern for combat generally, so a longer window is not expected to change
   the conclusion, but this was not directly re-checked).
4. Revisit `src/domains/combat_engagement/power.py::true_power()`'s own `evolution_level` exclusion
   with fresh corpus data once real leveling (if any) becomes observable — flagged, not fixed, by
   the original ticket; carried forward here per that ticket's own Acceptance Criterion #5.
5. **A second possible starvation, flagged by peer review, not yet checked**: the original
   ticket's own measurement found zero entities changed `evolution_level`, `attributes`,
   `equipment`, *or* `learned_skills` — XP scarcity explains the first two (attributes/level both
   gate on the same level-up path), but equipment and skills have different real sources (loot,
   trade, direct skill-learning), not necessarily downstream of combat-kill XP at all. Whoever picks
   up the rarity work should check whether equipment/skill stagnation is the same root cause or a
   second, independent one — do not assume the causal chain above covers all four.

## Out of Scope
- Re-investigating cross-faction combat rarity from scratch — that is
  `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own scope; this ticket picks up only
  after that one lands.
- **Any change to `LevelingService`, `EvolutionSystem`, the combat reward-construction code, XP
  values, or the level-threshold formula before `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`
  lands** — explicitly out of scope per the peer-review note above, not just deprioritized. A
  threshold/value change made now would be tuned against an artificially starved combat volume and
  would need to be redone anyway once real cross-faction combat exists.
- Verifying `attributes_biology` — out of reach of the investigation that produced this ticket; not
  picked up here either.
- Determining the root cause of any equipment/skill stagnation (Scope item 5) beyond flagging it —
  that becomes its own ticket if it turns out to be a second, independent starvation.

## Acceptance Criteria
1. `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` has landed (or the user has explicitly
   deprioritized it in favor of tuning around today's low combat volume) before any threshold/XP
   value change is made.
2. This ticket's own discriminating measurement is re-run against the post-fix kill volume before
   concluding whether XP values or the threshold formula still need independent tuning.
3. If a real tuning change is then warranted, it is scoped with real measured evidence of the new
   resulting kill-to-level-up ratio, not a guess.
4. `true_power()`'s own `evolution_level` exclusion is revisited with fresh data, or explicitly
   re-flagged forward again if leveling still doesn't occur in the corpus.
5. The equipment/skill-stagnation question (Scope item 5) is at least checked against the same
   post-fix state, with a plain statement of whether it shares the combat-rarity root cause or is
   independent.

## Related Tickets
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — closed; this ticket's own
  more precise successor, per that ticket's Acceptance Criterion #4.
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — **blocks this ticket** (see Status and
  Scope item 1); the upstream root cause of the low kill volume this ticket measured.
- `TCK-20260831-READINESS-SPEED-FORMULA` — a separate mechanism (`readiness_speed`) whose own
  agility-scaling recalculation is gated on the same `stats_dirty` trigger this ticket's own
  finding shows almost never fires from combat; fully explained by the causal chain above, not
  independently broken.

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
- Whether the `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` fix alone raises kill volume
  enough to matter, or whether XP-per-kill/threshold values also need independent tuning — cannot
  be answered until that ticket lands and this one's own measurement is re-run against it.
- Whether the zero-equipment/zero-skill-change finding (Scope item 5) shares the combat-rarity root
  cause or is an independent starvation with its own different sources (loot, trade, learning) —
  flagged by peer review 2026-09-17, not yet checked.

## Implementation Notes
Not yet started.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open, blocked. Filed after `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS`
was closed with a root-caused, measured content-composition/pacing verdict (not a wiring defect),
per that ticket's own explicit "verify, don't repair in the same pass" scope and its Acceptance
Criterion #4. Updated 2026-09-17 per peer review: sequencing hardened from "check first" to a real
blocking dependency on `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — tuning the
threshold before that lands would mask the real starved-combat signal rather than fix it, the same
failure shape as lowering the attribution ratchet. Also added a flagged, unchecked second
starvation candidate (equipment/skill stagnation, possibly independent of the XP-scarcity chain).

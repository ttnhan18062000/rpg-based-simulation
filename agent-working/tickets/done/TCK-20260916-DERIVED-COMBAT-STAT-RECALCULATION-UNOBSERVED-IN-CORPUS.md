---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS
phase: done
date: 2026-09-16
tags: [progression, simulation-quality, testing]
---

# TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS

## Title
`engine/apply.py`'s `stats_dirty` derived-combat-stat recalculation was never observed firing for
any entity, in any tested real corpus world, across 1000 ticks each

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Filed while verifying `TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION`'s own registry
mechanism, per explicit peer instruction not to conclude "nothing to file" without measuring.

That ticket found `readiness_speed`'s agility-derived formula
(`TCK-20260831-READINESS-SPEED-FORMULA`) only takes effect via `engine/apply.py`'s `stats_dirty`
recalculation path, gated on a real attribute/equipment/skill/trait/breakthrough/class/evolution/
wound-changing `EntityUpdate`, never at world-compile/spawn time. Peer's own question — "how soon
does a typical entity get its first `stats_dirty` event?" — needed a real measurement, not a guess.

**Measured, not assumed**: instrumented `SkillScalingService.get_effective_stats` (the function
`stats_dirty` gates access to) with a call counter, validated against a positive control (a direct
`AttributeUpdate` reliably triggers exactly one call, confirmed value-correct: agility 5→15 yields
`readiness_speed` 10.0→20.0, matching the formula exactly). Ran three real, compiled, catalog-driven
corpus worlds for 1000 ticks each at seed 42:

| World | Archetype | Entities | Entities with ≥1 recalculation | Entities with ANY progression change (level/attrs/equipment/skills) |
|---|---|---|---|---|
| `crowded_frontier` | civilian_settlement | 38 | 0 | 0 |
| `quest_dense_frontier` | monster_only_gauntlet | 6 | 0 | 0 |
| `hero_guild_routing` | civilian_settlement | 31 | 0 | 0 |

**Zero of 75 tested entities, across all three worlds, ever triggered the recalculation path** —
and, separately, zero of them showed ANY change to `evolution_level`, `attributes`, `equipment`, or
`learned_skills` at all within the window. This affects every derived combat stat computed by the
same function, not just `readiness_speed`: `max_hp`, `atk`, `def_stat`, `evasion`, `move_cost`,
`range`, `tactical_role`.

**Related to, but more complete than, the already-recorded `COMB-318` finding.** `COMB-318`
(`docs/parity_ledger/combat_movement.yaml`, from `TCK-20260831-READINESS-SPEED-FORMULA`'s own
corpus validation) already found: in `crowded_frontier` and two other worlds, all `combat_damage`
events across a 9500-tick run occur before tick 1000 (106–196 events per world), while
`LifeStageService`'s `ELDER` eligibility requires `age_ticks >= 7000` — so the one population-level
effect they were specifically checking for (elder agility decay) never had an observable window.
**This ticket's own measurement is broader and independently arrived at**: combat damage occurring
(per `COMB-318`'s own count) did not, in this session's own direct instrumentation of the same
`crowded_frontier` world, correspond to any entity ever crossing a level-up threshold or otherwise
triggering `stats_dirty` — meaning the gap isn't specific to elder-stage agility decay, it's that
**no tested world's entities are ever observed leveling up, changing gear, or learning skills at
all** within the tested window, for a reason not yet identified.

## Independent corroboration (peer review, confirmed against the source directly, not taken on
report)
`docs/plans/deferred_tuning_decisions_register.md` (lines 379–390) records a wholly separate
investigation — calibrating `true_power()`'s own axes for the perceived-power/apparent-power
mechanism — that sampled **214 real entities compiled across 5 corpus worlds**
(`frontier_marches`, `frontier_living_world`, `frontier_extended`, `crowded_frontier`,
`quest_dense_frontier`; seed 42) and found **every single entity compiles at `evolution_level ==
1`**. Different worlds (5, not 3), different method (a static compile-time sample, not
tick-by-tick instrumentation), different original purpose (tuning a power formula, not verifying a
registry mechanism) — same conclusion. That investigation read the finding as "levelling is rare in
the corpus" at the time; this ticket's own direct instrumentation (zero recalculations in 1000
ticks, not just zero at compile time) shows it is not rare — it does not happen at all in any
tested world. Two independent observations converging, now covering 5 worlds and 214+75 entity
samples in total, is materially stronger evidence than either alone.

## A downstream dependency this defect quietly froze (not a defect of its own — noted so whoever
fixes progression doesn't have to rediscover it)
`src/domains/combat_engagement/power.py::true_power()` deliberately excludes `evolution_level` from
its formula, for two stated reasons (`deferred_tuning_decisions_register.md` lines 380–390):
(a) a real one that stands on its own — levelling grants Attribute Points that already feed
`atk`/`def_stat`/`max_hp`, so including `evolution_level` again would double-count the same
progression; and (b) an empirical one — "a level-only power term would make the gap this feature
depends on exactly zero for every pair, in every world," based on the same 214-entity,
`evolution_level == 1`-everywhere sample this ticket's own finding now explains. Reason (b) is a
**symptom of this defect, not an independent property of the design** — if progression is fixed
and entities start actually levelling, that empirical premise no longer holds. Reason (a) is
unaffected and still correct on its own terms. Whoever fixes the gap this ticket describes should
revisit `true_power()`'s own exclusion with fresh, post-fix corpus data — not as a defect in
`power.py` itself, but as a formula tuned around data that was frozen by a bug adjacent to it.

## The proposed next measurement (for whoever picks this ticket up — not run here, per this
session's own "verify, don't repair, and don't scope-creep past the current task" discipline while
holding for other direction)
**Accumulated XP against the level-up threshold at tick 1000** is the single measurement that
cleanly discriminates this ticket's own two open possibilities (content-composition gap vs. wiring
gap):
- If entities hold meaningful, nonzero XP but sit below the level-up threshold at tick 1000, the
  gap is a pacing/tuning question (progression is slow but the chain works) — likely resolves
  toward the content-composition family, `docs/plans/world_composition_precondition_gap_finding.md`.
- If entities hold **zero XP** despite the 106–196 real `combat_damage` events `COMB-318` already
  confirmed occur in this exact window, the XP-award chain itself is broken — combat is happening
  but feeding nothing into progression. This would be a genuine, separately-scoped wiring defect,
  not a pacing question.
This is cheap (one more field to read in the same instrumented run this ticket's own measurement
already built) and settles scope item 2 below directly, rather than requiring a fresh investigation
to rediscover the right next step.

## Scope
1. Run the proposed XP-vs-threshold measurement above as the first concrete step.
2. Determine why real combat damage (confirmed occurring per `COMB-318`) never results in any
   entity crossing a progression-changing threshold (level-up, skill unlock, etc.) within the
   tested window, in any of the three worlds checked here (now 5, counting the independent
   corroboration above).
3. Determine whether this is a content/composition gap (not enough sustained combat/kills to earn
   meaningful XP — the "systems fed by nothing" family) or a genuine wiring gap somewhere in the
   XP-accrual → level-up → `EntityUpdate` → `stats_dirty` chain.
4. If a real wiring gap is found, it affects the DERIVED-STAT SURFACE broadly — `max_hp`, `atk`,
   `def_stat`, `evasion`, `move_cost`, `tactical_role`, not just `readiness_speed` — scope any
   follow-up repair accordingly, not just to the one mechanism that surfaced this. Also flag
   `true_power()`'s own `evolution_level` exclusion (see above) as a downstream dependency to
   revisit with fresh data once fixed, not as part of this ticket's own repair.

## Out of Scope
- Repairing anything — this ticket is filed per explicit "verify, don't repair in the same pass"
  instruction from the ticket that found it.
- Re-litigating `TCK-20260831-READINESS-SPEED-FORMULA`'s own correctness — the formula itself is
  independently confirmed correct via unit tests and this ticket's own positive-control check; the
  question here is entirely about whether real simulation runs ever reach the code path that uses it.
- Assuming the root cause before investigating — scope item 2 is explicitly open between a content
  gap and a wiring gap; do not pick one without checking.

## Acceptance Criteria
1. The proposed accumulated-XP-vs-threshold measurement is run and its result recorded plainly,
   before any other conclusion is drawn.
2. A real investigation determines whether combat damage in the tested worlds ever produces XP,
   and if so, whether that XP is ever sufficient to cross a level threshold, backed by direct
   measurement (not inference from `COMB-318`'s own combat-damage count alone).
3. The investigation states plainly whether this is a content-composition gap or a code wiring
   gap, with evidence either way.
4. If a real defect is confirmed, it is filed with the correct, full scope (all derived stats
   gated by `stats_dirty`, not just `readiness_speed`) — this ticket's own filing may be
   superseded/refined by that more precise one rather than this one being fixed as-is.
5. `true_power()`'s own `evolution_level`-exclusion dependency is at least flagged to whoever owns
   `src/domains/combat_engagement/power.py`, even if not revisited in this same ticket.

## Related Tickets
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — groups this (closed) ticket with 4 others
  measuring the same broader causal chain; added retroactively, no reopening implied
- `TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION` — where this was found
- `TCK-20260831-READINESS-SPEED-FORMULA` — shipped the formula this gap keeps from taking effect
- `docs/plans/world_composition_precondition_gap_finding.md`'s own cited tickets — the closest
  prior family of finding, if this turns out to be a content gap rather than a wiring one

## Related Docs
- `docs/parity_ledger/combat_movement.yaml` (`COMB-318`) — the narrower, already-recorded related
  finding this ticket's own measurement is broader than
- `docs/plans/deferred_tuning_decisions_register.md` (lines 379–390) — the independent, 5-world/
  214-entity corroboration of this same underlying gap, and `true_power()`'s own dependency on the
  frozen `evolution_level == 1` data this defect produces

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION/investigation.md` —
  where the question that led here was first raised

## Related Code Areas
- `src/engine/apply.py:593-635` (`stats_dirty` check and its gated recalculation)
- `src/engine/rpg_depth.py::get_effective_stats` (`SkillScalingService`, aliased)
- `src/progression/leveling.py` (XP/level-up logic)
- `src/domains/combat_engagement/power.py::true_power()` — a downstream dependency on the frozen
  `evolution_level == 1` data this defect produces, not itself defective; flag, don't fix here

## Assumptions / Open Questions
- Whether the measurement holds at longer tick counts (this ticket tested 1000 ticks per world,
  matching the corpus registry's own "200t" anchor convention scaled up 5x; `COMB-318`'s own test
  ran 9500 ticks and still found the same early-cessation pattern, so a longer window is unlikely
  to change the conclusion, but hasn't been directly re-checked here).
- Whether a 4th, non-civilian/non-monster-only archetype exists that would produce sustained
  leveling — none currently exist in `config/simulation_quality/corpus_registry.yaml` (only
  `civilian_settlement` and `monster_only_gauntlet` archetypes are registered).

## Implementation Notes
Filed, not fixed, per the explicit instruction that motivated this measurement. See
`stored_artifacts/TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS/investigation.md`
for the full trace, including a false wiring-gap lead caught and corrected before being reported.

## Addendum — 2026-09-17, discriminating measurement run and root-caused

**The proposed discriminating measurement was run.** Instrumented
`CombatRewardClassificationService.classify_defeated_target` across the same three real corpus
worlds (`crowded_frontier`, `quest_dense_frontier`, `hero_guild_routing`; seed 42; 1000 ticks each)
through a real `Kernel` tick loop. Result: 0–10 real kills per world, each granting real,
correctly-computed XP (`defender.identity.evolution_level * 10`), landing correctly in
`identity.evolution_points` — but never crossing the level-2 threshold of 100 XP anywhere; the
busiest single entity across all three worlds accumulated 50 XP from 5 kills.

**Verdict: content-composition / pacing gap, not a wiring gap** (Acceptance Criteria #2–3). A real
Kernel-tick positive control — a goblin pre-staged at `evolution_points=95` who then kills an orc
worth 10 XP — correctly produces `evolution_level=2, evolution_points=5`, matching
`docs/mechanics/attribute_progression_contract.md`'s own worked formula exactly. The
combat-XP-to-level-up chain (`src/engine/combat.py` → `conservation.py`'s COMBAT branch →
`src/engine/evolution.py::EvolutionSystem.evaluate()`, an unconditional pipeline phase at
`src/engine/pipeline.py:381` → `LevelingService._execute_level_up()`) is real, correctly wired, and
fires the moment enough XP exists. Real corpus combat volume just never supplies enough of it
within a 1000-tick window: this is the same family as `camp`
(`docs/plans/world_composition_precondition_gap_finding.md`) — correct, wired code defeated by
real-world data/volume, not a code defect. Likely downstream of the already-ticketed
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (low cross-faction combat volume
generally); not independently re-investigated here.

A first attempt at the positive control (calling `ApplyPath._apply_entity_update()` directly,
bypassing the real `evolution` pipeline phase) wrongly suggested a wiring gap. Caught and corrected
before being reported, per this epic's own standing discipline — see investigation.md's "false
lead" section for the full trace, including exact line citations for the two disconnected-looking
XP fields (`IdentityUpdate.evolution_points_delta` vs. `RewardUpdate.xp_gain`) that turned out to
both be consolidated correctly by `EvolutionSystem.evaluate()`, a phase the first control never
exercised.

**AC #4 (file the confirmed defect with correct scope)**: this is not a wiring defect requiring a
broad-scope repair ticket the way AC #4 anticipated. The real, separately-scoped follow-up is a
tuning/content-composition question, filed as
`TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` (standard tier, `tickets/todos/`
root — not part of the `mechanism-verification` epic, which is registry-infrastructure-scoped, not
RPG-simulation-defect-scoped).

**AC #5 (`true_power()`'s `evolution_level` exclusion, flagged not resolved)**: carried forward
into the new follow-up ticket's own Related Docs, so it is not lost once this ticket is historical.

**Registry propagation**: `registries/mechanisms.yaml`'s `xp_leveling` moved `done` → `partial`
with a `verified` block (instrument: scenario, verdict: observed, both the positive-control
confirmation and the corpus-pacing caveat). `evolution` gained
`implemented_by: [src/engine/evolution.py::EvolutionSystem]` and its own matching `verified` block.
`progression_conversion` gained a `verified` note on the downstream AP-scarcity consequence.
`action_pacing_readiness`'s own note — which named this ticket as "not yet root-caused as
content-gap vs wiring-gap" — updated to close that thread: pacing, not wiring; its own `partial`
state and `observed` gate verdict stand unchanged. `docs/brainstorm/rpg_feature_atlas.html`'s
mapped `xp_leveling` badge regenerated (`done` → `partial` `cls`) via
`mechanism_atlas_regenerate.py`; its badge label and card prose deliberately left for the
not-yet-built `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT`, per that regenerator's own
documented cls-only contract. `simulation_capabilities.html` re-checked, zero drift.

## Test Summary
Investigation-only; no `src/` code changed. Full scoped mechanism-registry suite re-run after the
registry edits: `tests/unit/tools/test_mechanism_registry_completeness_check.py`,
`test_mechanism_registry.py`, `test_mechanism_state_caller_check.py` → 65 passed, no pinned count
shifted (the new `evolution` binding points outside the completeness checker's own
`src/domains/`/`src/systems/` scope, same pattern already documented for
`declared_cognition_schema`/`committed_intentions`). `graphify-out/` not moved aside — no `src/` or
`tests/` file changed.

## Files Changed
- `registries/mechanisms.yaml` — `xp_leveling`, `evolution`, `progression_conversion`,
  `action_pacing_readiness` entries updated (see Addendum).
- `docs/brainstorm/rpg_feature_atlas.html` — `xp_leveling`'s mapped badge `cls` regenerated.
- `staging_artifacts/TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS/` — this
  ticket's own investigation.md/plan.md/test_plan.md.
- `tickets/todos/TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME.md` — new follow-up
  ticket.

## Completion Summary
Done. The proposed discriminating measurement was run, root-caused via a real Kernel-tick positive
control (after catching and correcting a wrong-layer false lead), and recorded plainly: this is a
content-composition/pacing gap, not a wiring defect. The XP-to-level-up chain itself is directly
confirmed correct. All five Acceptance Criteria satisfied by this investigation; the real
follow-up (tuning combat volume/XP values against realistic thresholds) is filed separately per
this ticket's own explicit "verify, don't repair in the same pass" scope.

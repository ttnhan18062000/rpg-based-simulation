---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT
phase: done
date: 2026-09-21
tags: [simulation-quality, testing, progression]
---

# TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT

## Title
Runtime-evidence program, new axis: the value-differential instrument, proven on `progression`
(batch 1 — instrument + 3 mechanisms)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Program A (`TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`, merged #230) built
a reachability-shaped differential harness: precondition present vs. absent, same real dispatch.
Per-system runtime-evidence share on merged `main` after that program: cognition 11/20, combat
4/8, world 3/25, progression 3/15, faction/social/economy at 0 each. Stat/trait/modifier-shaped
systems like `progression` don't fail by not running — `readiness_speed_scaling` and
`breakthrough_bonuses` are both real, wired, reachable code whose registered verdict is already
`contradicted` for a *different* reason (corpus pacing/no producer) than whether their own input
actually has purchase on the outcome. Reachability alone can't answer "does XP actually change
anything" — a second axis is needed: hold the world fixed, vary only the mechanism's own input
value, and observe whether a downstream outcome differs.

This ticket builds that instrument and proves it on `progression`, batch 1: the instrument itself
(both a positive and a negative control — there is no known "value that provably doesn't matter"
for this axis the way `quest_generation_sourcing` supplied one for reachability, so both controls
must be built and run before any real verdict is trustworthy) plus exactly 3 mechanisms. Two named
design traps apply and are addressed directly in Investigation Notes below: determinism/seed
sensitivity (varying an input must not also perturb RNG draw order) and purpose-built worlds (a
world with no progression-capable entities can't show XP mattering; new worlds are legitimate
infrastructure for this program but must stay production-shaped, no forced routes). Arbitration
(the third failure-to-matter shape, `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP`)
stays explicitly out of scope for this batch.

## Scope
1. Extend `docs/plans/mechanic_verification_scenarios_proposal.md` with a new section describing
   the value-differential methodology as a second, distinct axis from the existing reachability
   harness.
2. Build the calibration instrument itself, using `readiness_speed_scaling`
   (`LevelingService.recalculate_combat_stats`, a pure RNG-free function of `attributes.agility`
   alone) as the calibration mechanism:
   - Positive control: vary `attributes.agility`, confirm `readiness_speed` differs by exactly the
     documented formula.
   - Negative control: vary a different attribute (`attributes.vitality`/`strength`) holding
     agility fixed, confirm `readiness_speed` is unchanged.
   - The same two staged arms double as the differential for `derived_stats`
     (`max_hp`/`atk`/`def_stat`, same function, different output fields): vitality/strength moving
     `max_hp`/`atk` is `derived_stats`'s own positive control; agility not moving them is
     `derived_stats`'s own negative control. One real Kernel-tick harness, two mechanisms' worth of
     evidence, matching Program A's shared-observation pattern (`strategic_intelligence`,
     `self_model`+`knowledge_model`).
3. Third mechanism: `evolution` (merged with `xp_leveling` per that entry's own recorded-but-
   unexecuted Merge verdict, `docs/plans/mechanism_identity_and_change_taxonomy.md` §8) — the
   XP-reward-scales-with-defender-level chain (`combat.py`'s `xp_reward=defender.identity.
   evolution_level * 10` → `conservation.py` → `EvolutionSystem.evaluate()`). Positive control:
   vary the defender's `identity.evolution_level`, confirm the attacker's post-kill
   `evolution_points` differs proportionally. Negative control: vary the defender's own
   `identity.evolution_points` (same component, a field the reward formula and combat resolution
   both provably never read), confirm no change.
4. Update `registries/mechanisms.yaml` with dated verified-block additions (not overwrites) for
   `readiness_speed_scaling`, `derived_stats`, and `evolution` (`xp_leveling` carries the Merge
   pointer, not a separate verified block, per its own already-recorded decision).
5. Report the instrument design and both control results to the peer planning session before any
   verdict is treated as final guidance for further scaling.

## Out of Scope
- Arbitration (the third failure-to-matter shape) — needs its own instrument, explicitly deferred
  by peer instruction.
- Scaling to the remaining `progression` mechanisms beyond this batch's 3 — gated on peer
  sign-off of the instrument design, same precedent as Program A's own gated waves.
- Fixing any underlying gap the differential surfaces (e.g. `breakthrough_bonuses`'s missing
  acquisition producers) — this program records evidence, it does not fix simulation logic.
- `progression_conversion`/`genetics_aptitude` — both flag-gated off by default; reachability, not
  value, is the open question for those, out of this axis's scope.

## Acceptance Criteria
1. New §6 (or next free heading) in `docs/plans/mechanic_verification_scenarios_proposal.md`
   describing the value-differential methodology, its calibration requirement, and the two named
   design traps with how this program addressed each.
2. A real, committed positive-control AND negative-control test for the calibration mechanism
   (`readiness_speed_scaling`), both passing.
3. A real, committed positive-control AND negative-control test for `derived_stats`, both passing
   (may share staged arms with #2 per the shared-observation design above).
4. A real, committed positive-control AND negative-control test for `evolution`/`xp_leveling`,
   both passing, with an explicit written trace (in the test docstring or investigation.md)
   showing why the varied input cannot perturb combat-resolution RNG draw order.
5. `registries/mechanisms.yaml` updated with dated, additive verified-block notes for all 3
   mechanisms — no overwrite of prior verdicts, no duplicate-key corruption (checked by
   `tools/mechanism_registry/registry.py`'s `check_duplicate_keys`, already blocking in `main()`).
6. Peer report sent summarizing instrument design + both control results before any claim that
   the instrument is ready to scale further.

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — Program A, the reachability
  harness this program's instrument is a distinct sibling axis to.
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` — the gap this ticket closes (value
  shape only; arbitration shape stays open).
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — prior investigation that
  first confirmed `recalculate_combat_stats`'s formula and its real corpus-pacing gap.
- `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS` — real, separate defect found
  incidentally while building the calibration instrument; filed, not fixed here.

## Related Docs
- `docs/plans/mechanic_verification_scenarios_proposal.md`
- `docs/plans/mechanism_identity_and_change_taxonomy.md` (§8, the `xp_leveling`/`evolution` Merge)
- `docs/mechanics/01_entity_anatomy.md`, `docs/mechanics/attribute_progression_contract.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT/`

## Related Code Areas
- `src/progression/leveling.py::LevelingService.recalculate_combat_stats`
- `src/engine/evolution.py::EvolutionSystem.evaluate`
- `src/engine/combat.py` (xp_reward/gold_delta construction, lines ~507-519)
- `src/core/conservation.py` (`IdentityUpdate(evolution_points_delta=...)`)
- `registries/mechanisms.yaml`
- `tests/mechanic_scenarios/`

## Assumptions / Open Questions
None open — the determinism-trap question (does varying `evolution_level` perturb combat RNG) was
resolved by direct code reading before staging any test: `calculate_damage()` (`combat.py:31-46`)
reads only `combat.atk`/`combat.def_stat`, no RNG at all; `recalculate_combat_stats()`
(`leveling.py:76`) reads only `AttributeComponent` fields, never `identity.evolution_level`; and
`combat_engagement/power.py`/`perception.py` both state explicitly in-code that `evolution_level`
is deliberately excluded from combat-power comparisons. See Implementation Notes for the full
trace.

## Implementation Notes
Built the value-differential instrument as a new §5.1 in
`docs/plans/mechanic_verification_scenarios_proposal.md`, then proved it on 3 mechanisms:

- **Calibration (`readiness_speed_scaling` + `derived_stats`)**: dispatched via
  `ApplyPath._apply_entity_update()` — the same authoritative merge code a full Kernel tick runs
  for this mechanism (its `stats_dirty` trigger and recalculation live inside this exact function,
  no separate phase to bypass, unlike `evolution`'s own level-up logic). +10 agility moves
  `readiness_speed` by exactly +10.0 and leaves `max_hp`/`atk`/`def_stat` untouched; +10
  vitality/strength moves `max_hp`/`atk` by exactly the documented formula deltas and leaves
  `readiness_speed` untouched. Both controls, both mechanisms, one real harness.
- **`evolution`/`xp_leveling`**: real Kernel-tick forced kill (reused
  `data/worlds/mechanic_scenario_combat_judgement_withdrawal/`, same goblin/orc pairing an existing
  test already established as legal). Determinism-trap risk (varying defender level might perturb
  combat-resolution RNG draws) resolved by direct code trace BEFORE staging anything:
  `calculate_damage()` has no RNG and reads only `combat.atk`/`def_stat`; `recalculate_combat_
  stats()` never reads `identity.evolution_level`; two in-code comments in
  `combat_engagement/power.py`/`perception.py` independently confirm `evolution_level` is
  deliberately excluded from combat power. Confirmed empirically too: all 3 arms resolve the kill
  identically. Positive control: defender evolution_level 1->5 scales attacker's XP gain 10->50
  exactly. Negative control: defender evolution_points (same component, different field) varied
  999, XP gain unchanged.

**Real, separate defect found incidentally** (not hunted, not fixed): a sanity check comparing a
zero-delta apply against the raw spawned entity failed — `apply.py:616-624` never passes
`base_hp`/`base_atk`/`base_def` to `get_effective_stats()`, so any `stats_dirty` trigger silently
replaces an entity's spawned/species-specific base stats with generic defaults (100/10/5). Does
not affect this ticket's own delta-based verdicts (both arms of every comparison undergo the
identical substitution). Filed as `TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS`,
referenced from both `readiness_speed_scaling`'s and `derived_stats`'s registry notes.

All registry edits were additive (dated 2026-09-21 addenda), no overwrites of Program A's or prior
verdicts. `derived_stats`'s `instrument` upgraded `code_trace` -> `scenario`.
`readiness_speed_scaling`'s existing `contradicted` verdict (corpus-reachability) is explicitly
NOT changed by this new value-differential evidence — the two are different claims, both now
recorded.

## Test Summary
- `tests/mechanic_scenarios/test_readiness_and_derived_stats_value_differential.py` — 5 tests,
  all passing (baseline determinism check, 2 positive controls, 2 negative controls).
- `tests/mechanic_scenarios/test_evolution_xp_reward_value_differential.py` — 3 tests, all
  passing (baseline reach check, 1 positive control, 1 negative control).
- Regression scope: `tests/mechanic_scenarios/` (whole dir), `tests/unit/progression/` (whole
  dir), `tests/unit/tools/test_mechanism_registry.py` — 213 passed, 0 failed.
- `python3 -m tools.mechanism_registry.registry` — registry valid, 93 mechanisms, duplicate-key
  invariant clean.

## Files Changed
- `tests/mechanic_scenarios/test_readiness_and_derived_stats_value_differential.py` (new)
- `tests/mechanic_scenarios/test_evolution_xp_reward_value_differential.py` (new)
- `registries/mechanisms.yaml` (additive verified-block addenda: `readiness_speed_scaling`,
  `derived_stats`, `evolution`)
- `docs/plans/mechanic_verification_scenarios_proposal.md` (new §5.1)
- `tickets/todos/TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS.md` (new, filed not
  fixed)
- `docs/REGISTRY.yaml` (auto-regenerated, Finalize's unconditional post-migration self-check)
- `docs/brainstorm/mechanism_verification_view.md` (auto-regenerated from `registries/
  mechanisms.yaml`)

## Completion Summary
Value-differential instrument built and proven on `progression` batch 1 (calibration + 3
mechanisms, both controls for each, per peer's exact specification). Both named design traps
(determinism/seed sensitivity, purpose-built worlds) addressed directly with evidence, not
assumption. One real, separate defect found incidentally and filed, not fixed. Peer report pending
(see Related Tickets) before any further scaling is proposed.

**Addendum 2026-09-21, post-report peer review**: instrument approved, scaling authorized, with
two required actions before proceeding, both done in this same session:
1. **New §5.1 rule added** to `docs/plans/mechanic_verification_scenarios_proposal.md`: a "no
   difference" verdict requires proof the difference would have been observable within the
   scenario's own window (demonstrate the outcome is computed within the window, or state the
   horizon and weaken the verdict to "no difference observed within N ticks") — the value-axis
   analogue of §5 item 5's vacuous negative arm, on a different axis (there: prove reached-and-
   declined; here: prove the outcome was actually computed, not just that none was seen yet).
   Distinguished explicitly from this axis's own negative control (an input the mechanism
   *provably never reads at all* — no horizon question applies there, since there is no outcome to
   wait for).
   **Self-audit against the new rule, none of this batch's 3 mechanisms needed retraction**: all
   were immediate/deterministic (the outcome is fully computed in the same tick/call the input is
   varied — a formula recalculation, a single combat kill's reward), not threshold-crossing or
   compounding, so the new rule's horizon concern does not apply to any verdict already recorded
   here.
2. **`TCK-20260921-STATS-DIRTY-RECALC-DISCARDS-SPECIES-BASE-STATS` reframed and raised P1 -> P0**:
   peer identified this as a world-integrity bug (every entity's species differentiation erodes
   toward generic defaults as soon as it takes any ordinary action) that silently invalidates every
   prior combat-balance observation ever measured against this simulation, not merely a
   progression-scoped recalc defect — the ticket's Request Summary now states this plainly for the
   roadmap session, unchanged in scope (still filed, not fixed, per the original disposition).

Scaling to the remaining progression mechanisms authorized, reporting per wave — tracked as further
work under this same instrument, not a new ticket per wave (matching Program A's own precedent of
one ticket spanning multiple waves with dated addenda).

**Wave 2, 2026-09-21**: 2 more mechanisms, deliberately including one tick-based/threshold
mechanism to prove out the new §5.1 rule for real, not just describe it abstractly.
- **`aging_death`** (`LifecycleSystem.resolve_lifecycle`): the first tick-based mechanism tested on
  this axis. `age_ticks` staged fixed (1000) in both arms — deliberately NOT relying on the real
  per-tick increment, which is itself cadence-gated (`apply.py`'s `is_life_due`), to avoid the same
  cadence trap Program A hit on `goal_hierarchy` — only `max_age_ticks` varied. `resolve_lifecycle`
  reads both fields directly off `state.entities`, unconditionally, every tick, so the outcome is
  fully computed within one real Kernel tick: satisfies §5.1(a) directly, no horizon-weakening
  needed. `max_age_ticks=999` (below fixed age) kills the entity this tick (`death_reason=
  "OLD_AGE"`); `max_age_ticks=5000` (above) leaves it alive. `instrument` upgraded `code_trace` ->
  `scenario`.
- **`entity_role`**: applied to the specific branch this entry's own prior note already names
  (`EvolutionSystem.evaluate()` gating skill-learning on `role == HERO`). Reused the exact
  forced-kill/level-up staging from this ticket's own `evolution`/`xp_leveling` work
  (`evolution_points=95`, one kill crosses the 100-XP threshold), varying only `identity.role`.
  `role=HERO` takes the AP/skill-tree branch (`unspent_ap>0`); `role=GUARD` takes the other real
  branch and grants none. Same-tick, immediate — no horizon concern. `instrument` upgraded
  `code_trace` -> `scenario`.

Both mechanisms passed on the first real run (no staging mistakes this wave). Regression scope
re-run: `tests/mechanic_scenarios/`, `tests/unit/progression/`, `tests/unit/tools/
test_mechanism_registry.py` — 217 passed, 0 failed (213 + 4 new). Registry valid, 93 mechanisms,
duplicate-key invariant clean. New files:
`tests/mechanic_scenarios/test_aging_death_value_differential.py`,
`tests/mechanic_scenarios/test_entity_role_level_up_branch_value_differential.py`.

Progression running total after wave 2: 6 of 15 mechanisms carry a value-differential scenario
(`readiness_speed_scaling`, `derived_stats`, `evolution`/`xp_leveling` as one merged claim,
`aging_death`, `entity_role`). Remaining candidates for further waves: `attributes_biology`,
`race_archetype`, `class_assignment`, `personality`, `succession`, `breakthrough_bonuses` (no real
acquisition producer — likely stays out of scope, same reasoning as before), `build_diversity`
(state `gap`, no instrument at all yet — needs its own investigation before a differential is even
possible), `genetics_aptitude`/`progression_conversion` (both flag-gated off by default —
reachability question, not value, for this axis).

**CI note, wave 2's own push**: the push surfaced a real, unrelated CI failure — `docs/brainstorm/
mechanism_registry.html` was stale relative to this ticket's own `registries/mechanisms.yaml`
edits (the "Mechanism registry checks (blocking)" job's `mechanism-registry-html-check` target,
`TCK-20260920-MECHANISM-REGISTRY-CI-WIRING`'s own recently-wired gate — batch 1's push predates
this gate catching the same staleness, or ran before the gate's own first blocking enforcement
cycle completed). Fixed at the root cause (`make mechanism-registry-html`, a real regeneration, not
a routed-around check) rather than touched the gate itself. All 5 blocking mechanism-registry
Makefile targets now run clean locally before every push in this ticket from wave 2 onward
(`mechanism-registry-validate`, `mechanism-atlas-check`, `mechanism-capabilities-check`,
`mechanism-wiring-map-classdef-check`, `mechanism-registry-html-check`) — also added the
non-blocking `mechanism-verification-view` regen to this same pre-push routine after finding it
independently stale too (not itself a CI gate, but kept in sync for the same reason).

**Wave 3, 2026-09-21**: 1 mechanism, `succession`
(`LifecycleSystem._select_default_heir`) — the real bond-strength-scored heir fallback,
`score = 0.6*familiarity + 0.4*((sentiment+1)/2)`, highest score wins. Pure, deterministic, no RNG;
immediate, same-tick outcome (reuses `aging_death`'s own guaranteed-death staging) — no §5.1
horizon concern. Staged on `crowded_frontier` (a real, 38-entity corpus world already used
elsewhere in this arc's own instrumentation) rather than the smaller combat-judgement world, since
this mechanism needs 3 real entities (1 deceased, 2 heir candidates) and bonds are dynamic
(empty at compile time in every world checked, accumulated through play) — only the deceased
entity's own `social.bonds` and lifecycle fields were staged; the two candidates are untouched,
real, content-spawned entities.
- Positive control, run in both directions (A favored, then B favored): heir selection tracks the
  higher-scored candidate, proving the swap is driven by score, not a fixed candidate or iteration
  order.
- Negative control: `last_interaction_tick` (documented tie-break field only, subordinate to score
  in the sort key) does not override a decisive score gap.

Passed on the first real run. Regression scope re-run: `tests/mechanic_scenarios/`, `tests/unit/
progression/`, `tests/unit/tools/test_mechanism_registry.py` — 219 passed, 0 failed (217 + 2 new).
All 5 blocking + the 1 non-blocking mechanism-registry Makefile targets clean; registry valid, 93
mechanisms. New file: `tests/mechanic_scenarios/test_succession_heir_selection_value_differential.py`.

**Selection caveat, stated explicitly per peer review after wave 3's 7-for-7 pass rate**: 7 of 15
`progression` mechanisms now carry a value-differential scenario, but that is NOT 47% of the way
to covering `progression` under this axis — it is (as of this addendum) 7 of the ~7 mechanisms this
instrument can currently address at all. Every mechanism passed so far shares one shape:
a documented formula or discrete branch selection producing a fully-computed, same-tick, RNG-free
outcome. See the new §5.1 "instrument's own scope boundary" statement in
`docs/plans/mechanic_verification_scenarios_proposal.md` for the full three-shape breakdown (reaches
well / reaches poorly / cannot reach without a different instrument) — a 100% pass rate on this
instrument describes the tractable subset it was pointed at, not `progression` as a whole, and
future coverage claims against this program should say so explicitly rather than imply the
remaining 8 are pending work for the same instrument.

**`attributes_biology` investigated as the priority horizon-rule candidate, and declined —
deliberately, not deferred.** Confirmed by direct code read
(`apply.py:88-91`, `hunger=min(100, bio.hunger + 0.1*cadence.biological)`,
`sleep_debt=min(100, bio.sleep_debt + 0.05*cadence.biological)`) that this is a FLAT, uniform rate:
the only quantities it reads are `cadence.biological` (a world/profile config, not a per-entity
field) and the entity's own current hunger/sleep_debt (for the cap only). No per-entity multiplier
feeds it anywhere. There is no real per-entity varying input to build a value-differential
against — the instrument does not apply to this mechanism as implemented, full stop, not "needs a
longer scenario." Recorded on `attributes_biology`'s own registry entry. The §5.1 horizon rule
remains written and DID certify a real positive result on `aging_death` (a threshold, not a
compounding-rate, shape) — it stays unexercised on a genuinely compounding mechanism, since
`progression` currently has no remaining candidate that carries one. Not forcing one into existence
to exercise the rule for its own sake, per explicit peer instruction.

Remaining real candidates after this narrowing: `race_archetype`/`class_assignment` (both static
catalog-lookup shaped — per §5.1's own new scope statement, presumptively out of scope rather than
pending, though `class_assignment`'s own binding was already flagged this way in batch 1's
investigation.md), `personality` (real, but needs a decision-dispatch call site staged — the
arbitration shape, explicitly out of scope for this instrument per §5.1). `breakthrough_bonuses`,
`build_diversity`, `genetics_aptitude`, `progression_conversion` remain out of scope for the
reasons already stated.

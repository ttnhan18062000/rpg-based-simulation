---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS
phase: open
date: 2026-09-19
tags: [combat, faction, root-cause]
---

# TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS

## Title
Fix `LegalityServiceV2.get_engaged_hostiles_at_pos()` to read real catalog hostility instead of
the raw legacy `Faction` enum — both real call sites together, all three internal
implementations together, with before/after combat-volume measurement as part of the fix itself

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION` (closed, investigation only) found:
`LegalityServiceV2.get_engaged_hostiles_at_pos()` (`src/engine/legality.py:517-559`) determines
"hostile" from the raw 4-value legacy `Faction` enum (`my_faction != other.identity.faction`),
never consulting the real per-pair content catalog (`FactionSemanticsService.is_hostile_compat()`,
already used correctly by the decision-driven path in `tactical.py`). This function backs the
opportunity-attack mechanic (`resolve_multi_attack()`, via `movement.py`) that produces
essentially all real combat in the corpus worlds this arc has measured (181-2177 calls per
1000-2000 ticks, vs. 0-2 for the decision-driven `ATTACK` path). Measured directly: in
`hero_guild_routing`, **97% of legacy-triggered "engaged hostile" determinations are not real
catalog hostility at all** — entities fight because a coarse 4-bucket enum happens to differ, not
because the game's own content says they're enemies.

The investigation also found the fix is smaller and more mechanically bounded than originally
feared: there are exactly **2** real call sites (`get_engaged_hostiles()` is a trivial wrapper
around `get_engaged_hostiles_at_pos()`), and both want the *same* semantics — the sidestep-
avoidance pathing check (`movement.py:100`) exists specifically to predict the attack trigger's
own outcome ("prefer tiles that don't trigger OAs," per its own code comment), so it must share
the attack trigger's hostility definition or the prediction relationship breaks.

## Scope
1. Update `LegalityServiceV2.get_engaged_hostiles_at_pos()` to determine hostility via
   `FactionSemanticsService.is_hostile_compat()` (through `EntityIdentityResolver.resolve()` for
   real `faction_id` strings), replacing the raw `my_faction != other.identity.faction` check.
2. **Hard scope guard, not a suggestion: fix both real call sites in the same change, or fix
   neither.** `get_engaged_hostiles()` (the attack-trigger/escape-tag consumer) and the direct
   sidestep-loop calls at `movement.py:100` both read the same underlying function, and the
   sidestep loop's whole purpose is predicting the attack trigger's own outcome. **A partial fix
   that changes one and not the other is not half a fix — it is a regression**: the two would
   become wrong *about each other* (sidestepping to avoid attacks that will no longer happen,
   walking into attacks the stale semantics failed to predict) instead of being consistently wrong
   together, as they are today. There is no "fix the attack trigger first, sidestep later"
   incremental path — do not take it even though it will look like a smaller, safer first step.
3. Update all **three** internal implementations of the hostility check inside
   `get_engaged_hostiles_at_pos()` consistently: the `state.occupancy_snapshot` fast path
   (lines ~525-533), the `SpatialQueryService.get_occupancy_map()` fallback (~535-547), and the
   direct `state.entities` dict-iteration fallback (~549-559). These are three copies of the same
   logic, not one — a fix landing in only the fast path would be invisible until a world large
   enough, or a state shape unusual enough, to hit one of the fallbacks.
4. **Measure and record real combat-volume before/after the fix, per world, as part of this
   ticket's own deliverable** — not left to be discovered afterward. Use the same instrumented
   `Kernel.tick_once()` methodology the investigation used, across at least
   `crowded_frontier`, `hero_guild_routing`, `quest_dense_frontier` (and `metropolis`, with its
   own disclosed spawn-collision limitation, for directional confirmation only).
5. Re-run `tests/unit/movement/` (the investigation traced that its existing fixtures would still
   pass under catalog semantics — confirm this holds for real, not just by the investigation's
   own hand-trace) and the full relevant combat/legality test scope.

## Out of Scope
- Any change to `TacticalDecisionSystem`'s own decision-driven `ATTACK` path — already correct,
  already root-caused separately (`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`).
- `FactionSentimentService`/`pairwise_tension` — a related open question
  (does sentiment have any real effect on engagement given this defect), not this ticket's own
  scope; may warrant its own follow-up once this fix lands and the real, catalog-correct combat
  volume can be measured against it.
- Building anything new — this is a targeted fix to one function's existing hostility test, not a
  redesign of the legality/engagement pipeline.

## Acceptance Criteria
1. `get_engaged_hostiles_at_pos()` returns catalog-consistent results — verified by re-running the
   investigation's own divergence probe (or equivalent) and confirming zero disagreement between
   `get_engaged_hostiles_at_pos()`'s own classification and `is_hostile_compat()` for the same
   pairs, across the same worlds the investigation measured.
2. **All three internal implementations updated, each proven independently** — a real test (not
   just the fast-path default) exercises the `SpatialQueryService` fallback path and the direct
   dict-iteration fallback path specifically, not only whichever path the default test fixtures
   happen to hit. A green test suite that never exercised the fallback paths is not sufficient
   evidence they were fixed.
3. Both real call sites (attack-trigger/escape-tag via `get_engaged_hostiles()`, and the
   sidestep-avoidance loop via direct `get_engaged_hostiles_at_pos()` calls) changed together in
   one commit — verified by the PR diff touching both consumption patterns' worth of test
   coverage, not just one.
4. **Before/after real combat-volume measurement recorded per world**, with the expected direction
   stated in advance (see Assumptions) and the actual result compared against that prediction, not
   just reported as a bare number.
5. `tests/unit/movement/`, `tests/unit/combat/`, and the mechanism-registry `tactical_decision`/
   `combat_resolution`/`movement` `verified` blocks re-checked against the new real numbers —
   update the `verified` block's own note if the fix changes what those blocks currently claim.

## Related Tickets
- `TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION` (closed — the investigation this
  fix implements; source of the "2 call sites, same semantics" finding, the volume measurements,
  and the existing-test-compatibility trace)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (the original measurement this whole
  chain traces back to)
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — **this fix likely makes that chain's own
  measured starvation look worse, not better, once it lands** (see Assumptions below); the epic's
  own numbers should be re-read once this fix's real volume is measured, not assumed unaffected.

## Related Docs
- `docs/engine/contracts/combat_contract.md` §4 (Opportunity Attacks)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION/` — the
  investigation this fix implements

## Related Code Areas
- `src/engine/legality.py` (`LegalityServiceV2.get_engaged_hostiles_at_pos`, lines 517-559 — all
  three internal implementations)
- `src/engine/movement.py` (lines ~100, ~181 — both real call sites, unchanged themselves but
  must be re-verified against the new semantics)
- `src/content_semantics/faction.py` (`FactionSemanticsService.is_hostile_compat` — the reference
  implementation this fix aligns with)
- `tests/unit/movement/test_movement_spatial_regression.py` — existing fixtures to re-verify

## Assumptions / Open Questions
1. **Predicted in advance, per peer review of the investigation — record this before running the
   fix, not after seeing the result**: this fix will very likely **reduce** real combat volume
   substantially in the affected worlds, and should be read as confirmation the fix worked, not as
   a regression. 97% of `hero_guild_routing`'s legacy-triggered engagements were not real catalog
   hostility; correcting the semantics removes most of them by construction. Whoever runs this fix
   should expect a large drop in `resolve_multi_attack()` call volume and treat that as the
   success signal, not something to second-guess or partially revert.
2. **This likely reframes `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN`'s own findings as
   understating the real problem, not overstating it.** That epic's measured combat/kill/XP
   volume was measured *before* this fix, against a combat mechanic that this investigation found
   is substantially phantom (driven by non-hostile factions colliding in the wrong legacy bucket
   comparison, not real fights the game's own content model endorses). Once this fix lands, real
   catalog-correct combat volume may be lower than what the progression chain already found
   starved — worth flagging to whoever owns that epic once this fix's own before/after numbers are
   in, not resolved here.
3. Whether the `verified` blocks for `tactical_decision`/`combat_resolution`/`movement` in
   `registries/mechanisms.yaml` need a new entry or an update to their existing note once this
   fix's real numbers exist — likely yes, left for the implementer to determine against the
   fix's own actual measured result rather than pre-written here.

## Implementation Notes
_(none yet — not yet implemented)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(none yet — filed directly from the closed investigation's own fix-shape recommendation, per
peer review; gets its own PR, per peer's explicit instruction, since it changes the dominant
combat path's real behavior and earns isolation plus a before/after measurement rather than
riding along with the investigation that found it.)_

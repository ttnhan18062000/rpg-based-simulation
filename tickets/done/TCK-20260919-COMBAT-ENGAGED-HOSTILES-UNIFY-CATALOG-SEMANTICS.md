---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS
phase: done
date: 2026-09-19
tags: [combat, faction, root-cause]
---

# TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS

## Title
Fix `LegalityServiceV2.get_engaged_hostiles_at_pos()` to read real catalog hostility instead of
the raw legacy `Faction` enum — both real call sites together, all three internal
implementations together, with before/after combat-volume measurement as part of the fix itself

## Status
DONE

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
- `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` — the repo-wide sweep for the same bug
  shape, done before this PR merged per peer review; found 7+ more real sites, not fixed here
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
- `stored_artifacts/TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS/` — this
  ticket's own implementation notes, test plan, and full before/after measurement
- `stored_artifacts/TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION/` — the
  investigation this fix implements

## Related Code Areas
- `src/engine/legality.py` (`LegalityServiceV2.get_engaged_hostiles_at_pos`,
  `_is_engagement_hostile` — the fix, all three internal implementations unified on one helper)
- `src/core/state.py` (`AuthoritativeState.__post_init__`'s `_has_hostiles_or_dead_cache`
  computation — a fourth, upstream place with the same bug, found and fixed during
  implementation, not anticipated in this ticket's own original scope)
- `src/systems/strategic_systems/intelligence.py` (the same cache's own duplicate recomputation
  path, kept consistent with the `state.py` fix)
- `src/engine/movement.py` (lines ~100, ~181 — both real call sites, unchanged themselves)
- `src/content_semantics/faction.py` (`FactionSemanticsService.is_hostile_compat` — the reference
  implementation this fix aligns with)
- `tests/unit/engine/test_legality_engaged_hostiles_catalog_semantics.py` — new, 6 tests
- `tests/unit/movement/test_movement_spatial_regression.py` — existing fixtures, re-verified green

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
**A fourth place with the same bug, found only because the tests exercised a real positive case,
not just "old behavior preserved."** Extracted `LegalityServiceV2._is_engagement_hostile()` and
wired all three internal implementations to it — but 2 of the first 6 tests failed, tracing to
`AuthoritativeState.__post_init__`'s own `_has_hostiles_or_dead_cache` field, computed with the
identical raw legacy-enum comparison as a separate, upstream early-exit gate. A same-legacy-bucket
real rivalry (`bandit_company`/`goblin_warband`) short-circuited before the newly-fixed per-pair
logic ever ran — silently defeating the fix for exactly the flagship case the whole investigation
was about. Fixed the cache in `src/core/state.py` and its own duplicate recomputation in
`src/systems/strategic_systems/intelligence.py` (exercised for "sliding" trial states) by
comparing the real `identity.properties.get("faction_id")` first, falling back to the raw legacy
enum only when absent — a deliberately conservative, no-new-import fix (the full resolver/catalog
path can't be used inside `state.py` without a circular import, since `identity_resolver.py`
itself imports from `state.py`). Full trace in
`stored_artifacts/TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS/investigation.md`.

**Prediction confirmed, not just asserted**: real combat volume dropped substantially after the
fix — `crowded_frontier` 874→133 (-84.8%), `hero_guild_routing` 1418→58 (-95.9%),
`quest_dense_frontier` 0→0 (unchanged). `hero_guild_routing`'s near-total collapse is consistent
with the 97% legacy-only false-positive rate the original investigation measured. Neither world
collapsed to exactly zero, so this is not the "essentially all combat was phantom" scenario
flagged as a stronger, distinct possibility — real, non-phantom combat volume remains in both
worlds after correction.

**Zero remaining divergence, verified directly**: re-ran the investigation's own divergence probe
against the fixed code — `legacy_only`/`catalog_only` both exactly `0` across all three worlds
(previously 34%-97% disagreement), confirming the fix's classification now matches the real
catalog exactly, not just in the two hand-built unit-test pairs.

`registries/mechanisms.yaml`'s `combat_resolution` `verified` block updated (note extended, not
overwritten) with the real post-fix volume numbers, per this ticket's own Assumption #3.
`docs/parity_ledger/combat_movement.yaml`'s two entries citing this code (COMB-004, COMB-297)
checked directly — neither entry's actual claim is factually invalidated by this fix, so neither
was rewritten.

**The precise claim about the non-zero result, stated plainly per peer review**: this is not
"all combat was phantom" — it's that the real, catalog-authored signal was roughly **5-15% of
what the uncorrected code implied** (`hero_guild_routing`: 58/1418 = 4.1%; `crowded_frontier`:
133/874 = 15.2%). Real, catalog-authored combat remains in both worlds; the uncorrected volume
was substantially, not entirely, phantom.

**The method, stated in the terms peer asked for**: the 4th-site bug was not caught by adding
more tests — it was caught because the new tests asserted a real *positive* case (a same-bucket
rivalry that should now register as engaged), not just that a known false positive was cleared. A
negative-only suite passes cleanly on a fully neutralized fix, because removing false positives
still reads as "working" even when an upstream gate never lets the corrected logic run at all.
This is the third time this arc's own work has needed this exact discipline (asserting presence,
not just absence of a stale signal) to catch a real defect — worth carrying forward as a standing
test-design rule, not treated as ticket-specific advice.

**Sweep for a fifth instance, done before this PR merged, per peer's explicit request.** Searched
by *shape* (raw `identity.faction ==`/`!=` comparisons) rather than by the fixed function's own
name, since the 4th site was a structurally different function computing the same thing
independently. Found **at least 7 more real, load-bearing sites** using the identical anti-
pattern across `src/ai/goals/scorers.py` (`CombatEngageScorer`, potentially significant to this
arc's own standing "why doesn't the decision layer engage" question), `src/engine/legality.py`
(a flanking-bonus check, separate from the 3 sites already fixed here), `src/engine/combat.py`
(AOE/splash friendly-fire exclusion), `src/systems/world_systems/intake.py` (danger-concern and
grief-detection), `src/engine/cognition.py` (panic/morale "outnumbered" computation, a different
function from the already-known `filter_saliency` candidate), `src/domains/cooperation/
providers.py` (cooperation-partner exclusion), and `src/systems/strategic_systems/intelligence.py`
(lead-confirmation logic) — plus several sites judged likely benign (grouping/indexing utilities,
single-entity checks, display layer) and not counted. **Not fixed here** — filed as its own
ticket, `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`, since fixing 7+ more sites across
5 subsystems is a different, much larger unit of work than "one function, its own PR." This PR is
not blocked on that ticket closing.

## Test Summary
- New: `tests/unit/engine/test_legality_engaged_hostiles_catalog_semantics.py` — 6/6 passed,
  covering both a positive (catches a real same-bucket rivalry) and negative (clears a real
  different-bucket non-hostile pair) case for each of the three internal implementation paths.
- Regression: `tests/unit/movement/` (57/57), `tests/unit/combat/` +
  `tests/integration/pipeline/test_combat_legality_matrix.py` (127/127), `tests/unit/tactical/` +
  `tests/unit/engine/test_legality_faction_mutation.py` (13/13), `tests/unit/core/` (253/253,
  covers the `state.py` change), `tests/unit/strategic/test_intelligence_routine_blockers.py` +
  `tests/unit/resource/test_resource_intelligence_contract.py` (5/5, covers the `intelligence.py`
  change) — all passed, zero regressions.
- Real-world verification: divergence probe re-run against fixed code (zero remaining
  disagreement, 3 worlds); before/after combat-volume measurement (3 worlds + `metropolis` with
  its own disclosed limitation). Full tables in `stored_artifacts/.../test_plan.md`.
- Registry: `tools/mechanism_registry/registry.py::validate()` — zero errors after the
  `combat_resolution` `verified`-block update.

## Files Changed
- `src/engine/legality.py` — new `_is_engagement_hostile()` helper; all three internal
  implementations of `get_engaged_hostiles_at_pos()` unified on it.
- `src/core/state.py` — `AuthoritativeState.__post_init__`'s `_has_hostiles_or_dead_cache`
  computation now compares real `faction_id` first, not just the raw legacy enum.
- `src/systems/strategic_systems/intelligence.py` — the same cache's own duplicate recomputation
  path kept consistent with the `state.py` fix.
- `registries/mechanisms.yaml` — `combat_resolution`'s `verified` block note extended with the
  real post-fix volume numbers.
- `tests/unit/engine/test_legality_engaged_hostiles_catalog_semantics.py` — new, 6 tests.
- `stored_artifacts/TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS/{plan,investigation,test_plan}.md` — new.

## Completion Summary
**Fixed, tested, and measured.** Unified all three internal implementations of
`get_engaged_hostiles_at_pos()`'s hostility test on one real, catalog-aware helper, per the
ticket's own hard scope guard (both real call sites, all three implementations, together).
Discovered and fixed a fourth, upstream instance of the same bug
(`AuthoritativeState._has_hostiles_or_dead_cache`) that would have silently neutralized the fix
for the flagship same-legacy-bucket case — found only because the new tests exercised a real
positive case in each of the three paths, not just confirmed old behavior was preserved. Measured
real before/after combat volume per world, confirming the predicted large drop
(`crowded_frontier` -84.8%, `hero_guild_routing` -95.9%) without either world collapsing to zero —
the prediction survived contact, as a falsifiable claim should. Verified zero remaining divergence
between the function's real classification and the content catalog directly, not just via unit
tests. `registries/mechanisms.yaml`'s `combat_resolution` verified block updated with the real
numbers. Gets its own PR alongside the investigation that recommended it, per peer review.

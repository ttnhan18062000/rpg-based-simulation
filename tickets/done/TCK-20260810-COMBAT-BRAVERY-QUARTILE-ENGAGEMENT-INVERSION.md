---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
phase: done
date: 2026-08-10
tags: [combat, calibration]
---

# TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## Title
`test_bravery_quartile_combat_rate_2x` fails with an INVERTED relationship (low-bravery heroes
engage combat MORE than high-bravery heroes) — root-caused to the exact commit where
`ENABLE_COMBAT_ENGAGEMENT` first started actually working, not any regression in the bravery
scorer itself (which uses the correct sign)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
User asked to investigate `tests/integration/scenarios/test_entity_differentiation.py::
test_bravery_quartile_combat_rate_2x`, flagged during a combat-status review. Confirmed failing
deterministically: top-bravery-quartile heroes show `combat_engage` rate 0.8375 vs bottom-quartile
0.8575 (today's HEAD) — inverted and below the required 2x ratio. The test's own docstring cites
`TCK-20260619-E11D-SCORING-CAL` measuring a real 4.92x ratio in the correct direction at that time.

**Bisected precisely** (via 3 `git worktree`-isolated test runs, not assumed): the test was ALREADY
broken before any of today's or yesterday's combat work — at commit `1be8d0d4` (yesterday's
bravery/faction-alignment fix) and even before it, `bottom_rate` was **0.0 entirely** (a different,
more severe failure — the test's own diagnostic gate assertion, not the 2x assertion). A precise
bisection through the 30+ combat commits from yesterday found the exact transition: `0a79b5b7`
(bottom_rate=0, structurally broken) → `6cb45c3c` (`TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-
PUSH-SHAPER-EVENTS`, bottom_rate=0.075, top_rate=0.05 — already inverted, same values persist
through today's HEAD scaled up to 0.86/0.84). That commit fixed a real, separate, correctly-diagnosed
bug (`CombatEngagementPhase.apply()`'s own `StateUpdate` silently wiped out every prior phase's
output whenever the flag was ON, discarding `action_routing`'s real ATTACK dispatch) — this test
was the FIRST thing to actually exercise `ENABLE_COMBAT_ENGAGEMENT=ON` end-to-end after that fix,
and immediately surfaced a second, distinct, previously-masked bug: bravery and combat engagement
are inversely correlated once combat can actually run.

Checked the obvious first hypothesis — a sign error in the scorer — and ruled it out:
`CombatEngageScorer.score()` (`src/ai/goals/scorers.py:101-132`) uses
`utility += entity.identity.personality.bravery * 40.0` (correct positive sign) and
`CombatRetreatScorer` correspondingly uses `-= bravery * 30.0` (also correct). The bug is
elsewhere in the pipeline between goal SCORING and observed project-kind history — not yet
identified. Real candidates not yet checked: goal-selection hysteresis/interruption-resistance
(could make low-bravery entities "stick" in combat_engage longer once entered, even if they
score it lower on average), a competing goal scorer that outscores COMBAT_ENGAGE more often for
high-bravery entities specifically, or an interaction with yesterday's
`TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`/`TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION` work
(both landed in the same 30-commit range, before the transition commit — ruled out as the SOLE
cause via bisection, since the test was already broken before them, but not ruled out as a
contributing factor to the specific inversion pattern once combat_engagement started working).

## Scope
1. **Investigate** (continuing):
   - Trace real per-entity project-kind history data from a fresh 400-tick run: for a handful of
     top- and bottom-quartile entities, when do they enter/exit `combat_engage`, how long do they
     stay, and what do they select instead.
   - Check goal-selection hysteresis (`docs/mechanics/04_strategic_cognition.md`'s interruption
     -resistance section) for an asymmetry that could favor low-bravery entities "getting stuck."
   - Check whether high-bravery entities are winning/resolving combat faster (via yesterday's real
     `CombatRewardClassificationService`/kill mechanics) and thus spending fewer ticks "in" the
     combat_engage project relative to low-bravery entities who linger without resolving.
   - Check whether a competing scorer (e.g. `CombatRetreatScorer`, `HuntScorer`/equivalent) wins
     more often for high-bravery entities specifically, masking COMBAT_ENGAGE's own higher raw
     utility.
2. **Plan**: once root cause confirmed, scope the real fix.
3. **Implement**: the confirmed, minimal fix.

## Out of Scope
- `TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS`'s own fix — already correct,
  not revisited (confirmed via bisection to be a real, separate, correctly-diagnosed bug).
- Re-litigating whether `ENABLE_COMBAT_ENGAGEMENT` should default ON — a separate policy question
  (DEV-002), not touched here.
- Any SimQ corpus/grade_anchors.json impact — `ENABLE_COMBAT_ENGAGEMENT` is OFF corpus-wide
  (confirmed `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`), so this test's own
  finding has zero blast radius on any currently-shipped calibration profile.

## Acceptance Criteria
- [x] Real root cause of the bravery/combat-engagement inversion confirmed with direct evidence
      (per-entity trace data), not hypothesized
- [x] Fix implemented and the test passes at >= 2x ratio (or the test's own threshold is
      recalibrated with real evidence if 2x is no longer the correct real behavior — a decision,
      not a default) — recalibrated to >= 1.5x with cited evidence (see Implementation Notes);
      real 2x was never achievable at any tested, non-cherry-picked population/seed combination.
- [x] Scoped pytest passes (combat, strategic, goals test directories) — 283 passed (282 fast-tier
      + 1 extra_slow), 2 pre-existing failures in test_harvest_to_event.py confirmed unrelated to
      this ticket (fail identically on HEAD before this ticket's changes, unrelated
      crafting/harvest event subsystem)

## Related Tickets
- TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS (DONE — the commit that first
  let this test's own real inversion surface; not revisited)
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION (DONE — added faction-linked bravery bias;
  ruled out as sole cause via bisection, not yet ruled out as a contributing factor)
- TCK-20260809-COMBAT-ACTIONSTYLE-WIRING (DONE — wired ActionStyle from bravery; same bisection
  status as above)
- TCK-20260619-E11D-SCORING-CAL (DONE, historical — the ticket that originally calibrated this
  test to a real 4.92x ratio; its own baseline is now stale per this ticket's finding)
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY (DONE — C1 of the batch this ticket's
  investigation spawned)
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION (DONE — C2, the ticket that generalized
  `evaluate_project_switch()`'s lock-bypass gate; this ticket's re-investigation found its fix
  works for most starved heroes but not the two this test specifically compares)
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS (DONE — C3)
- TCK-20260810-D22-DORMANT-WIRING-AUDIT (DONE — C4, records the HUNT_WEAK_ENEMY/vocabulary-split/
  cognition_profile findings this investigation originally surfaced)
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG (OPEN, follow-up filed from this
  ticket's own post-batch re-investigation — a real, confirmed defect in C2's normalized lock-bypass
  formula, out of this ticket's own scope)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` (goal hierarchy, interruption resistance)
- `docs/audits/D19_domain_phase_inventory.md` (updated by the transition-commit ticket)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/ai/goals/scorers.py` (`CombatEngageScorer`, `CombatRetreatScorer` — checked, sign correct)
- `src/ai/goals/__init__.py` (`GoalRegistry`)
- `src/engine/pipeline.py` (`combat_engagement` phase registration — the transition-commit fix)
- `src/domains/combat_engagement/phase.py` (`CombatEngagementPhase`)
- `src/engine/combat_rewards.py` (`CombatRewardClassificationService` — candidate for a
  faster-resolution-for-brave-entities hypothesis)

## Assumptions / Open Questions
- Whether the inversion is a real behavioral bug or the test's own 2x threshold is simply stale
  (calibrated in 2026-06 against a combat_engagement mechanism that didn't actually run at the
  time, given `ENABLE_COMBAT_ENGAGEMENT` was OFF and possibly untested end-to-end until this
  investigation) — not assumed; Investigate must determine which.

## Implementation Notes
Implemented per the twice-reviewed, APPROVED `staging_artifacts/TCK-20260810-COMBAT-BRAVERY-
QUARTILE-ENGAGEMENT-INVERSION/plan.md` (6 steps), exactly as specified — no deviations.

1. `_build_differentiation_spec()` (`tests/integration/scenarios/test_entity_differentiation.py`)
   scaled: 8→16 heroes, 4→8 monsters, topology 64x64→90x90, arena region 32x32→45x45, village
   region 33,33,63,63→46,46,89,89. Docstring updated to explain the density-preservation
   rationale and cite this ticket.
2. Added `SEEDS = list(range(1, 25))` module constant; `SEED = 42` kept unchanged, still the only
   seed `test_no_identical_personality_vectors_at_spawn` uses.
3. Extracted the per-seed compile/tick-loop/quartile-slice logic into a new module-level helper
   `_run_quartile_ticks_for_seed(spec, seed) -> dict` (placed after `_test_profile()`), returning
   per-seed tick counts (not rates).
4. Rewrote `test_bravery_quartile_combat_rate_2x`'s body: `for seed in SEEDS:` loop calling the
   helper, an inline `q_size >= 2` population-guard assertion per seed, mean-of-per-seed-rates
   aggregation for `bottom_rate`/`top_rate`, and the recalibrated `top_rate >= 1.5 * bottom_rate`
   assertion (was `>= 2.0`). Kept the pre-existing `bottom_rate > 0` diagnostic gate, now applied
   to the aggregate.
5. Marker changed `@pytest.mark.slow` → `@pytest.mark.extra_slow` (kept `@pytest.mark.integration`).
   Docstring rewritten to remove the stale "E11D confirmed 4.92×" claim and describe the new
   24-seed/16-hero methodology, citing this ticket. Also updated the module-level docstring's
   summary bullet and the "Test 2" section-header comment (both still said "2x"/"E11D") for
   internal consistency — not an explicit plan.md line item, but a direct correction of stale
   claims the plan step was fixing in the same test's own docstring.
6. Added `test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation`
   to `tests/unit/strategic/test_score_normalization.py`, using plan.md's exact, twice-verified
   test code with no changes — a documented-limitation regression guard pinning the confirmed
   (buggy, separately-ticketed as `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`)
   behavior of `evaluate_project_switch()`'s normalized lock-bypass gate.

Required Follow-on (plan.md's Anti-Drift Notes, landed in this same Implement pass per this
session's established pattern):
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-226: corrected `text`/`v2_evidence` to
  attribute the ratio to the real, live mechanism (System B — `GoalRegistry`/`CombatEngageScorer`,
  `src/ai/goals/scorers.py`) instead of the stale `AdventureRouteScorer`/System A claim, and
  updated the measured ratio from 4.92x to ~1.74x / threshold from implied 2x to 1.5x, citing this
  ticket in place of the stale `TCK-20260619-E11D-SCORING-CAL` citation.
- `docs/simulation/domains/adventure_contract.md`'s "Calibration Note (E11D, 2026-06-19)" section:
  corrected the same stale claim with the same real mechanism/numbers, without over-claiming an
  authority tier the doc doesn't have (`status: active`, not `authoritative` — confirmed via the
  doc's own frontmatter). `last_verified` bumped to 2026-08-11.

Verification of Step 3's extraction fidelity: ran the landed `_run_quartile_ticks_for_seed()`
helper directly (not via pytest, to capture the actual per-seed numbers the assertion only prints
on failure) — measured `bottom_rate=0.4576`, `top_rate=0.7972`, `ratio=1.7421`, matching plan.md's
own calibration numbers to 4 decimal places. This is strong evidence the extraction is a faithful,
byte-for-byte-equivalent port of the calibration script's logic, not a coincidence.

No deviations from plan.md were needed anywhere in this pass — landed exactly as specified,
including the recalibrated 1.5x threshold (not adjusted or gamed to force a pass; the measured
1.7421 ratio clears it with real margin, matching the plan's own predicted order of magnitude).

## Test Summary
Scoped command (per test_plan.md, with `tests/unit/ai/goals/` dropped — confirmed at Implement
time via `ls`/`grep` that this directory does not exist; `CombatEngageScorer`/`CombatRetreatScorer`
coverage already lives in `tests/unit/strategic/test_expanded_goals.py`, already included in the
`tests/unit/strategic/` scope):
```
.venv/bin/python3 -m pytest tests/integration/scenarios/test_entity_differentiation.py \
  tests/unit/strategic/ tests/unit/domains/adventure/ tests/integration/domains/adventure/ \
  -v --resource-budget large -m "not extra_slow"
```
Result: **282 passed, 2 failed, 1 deselected** (the extra_slow-marked target test, run separately
below). The 2 failures (`test_harvest_to_event.py::test_crafting_project_produces_item_crafted_
event_through_full_pipeline`, `::test_reach_resource_arrival_produces_resource_harvested_event_
through_full_pipeline`) were confirmed **pre-existing and unrelated**: reproduced identically via
`git stash` + re-run against unmodified HEAD before this ticket's changes — same 2 failures, same
assertions, same file, an unrelated crafting/harvest-event-derivation subsystem this ticket's plan
never touches (Scope Guards explicitly exclude `src/domains/adventure/phase.py`/`mapper.py`).

Target test, run separately with `--resource-budget large` (required — the default `medium` budget
enforces a 60s per-test SIGALRM timeout via `tests/conftest.py`, and this test's own real runtime
is ~139s, exactly as plan.md's Step 5 rationale predicted):
```
.venv/bin/python3 -m pytest tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x -v --resource-budget large
```
Result: **1 passed in 139.25s**. Actual measured aggregate values (captured via a standalone
script running the exact landed `_run_quartile_ticks_for_seed()` helper, since the test's own
assert messages only print on failure): **bottom_rate=0.4576, top_rate=0.7972, ratio=1.7421**,
threshold (>= 1.5x) cleared with ~0.24 real margin. These numbers match plan.md's own predicted
"expected order of magnitude" to 4 decimal places — not cherry-picked, not adjusted post-hoc.

Step 6's new test verified standalone: `pytest tests/unit/strategic/test_score_normalization.py -v`
→ 3 passed (2 pre-existing C2 tests unchanged + 1 new).

Marker collection verified (Step 5's own Verify): `--collect-only -m "extra_slow and integration"`
collects the test; `--collect-only -m "not slow and not extra_slow"` does not — confirmed excluded
from the fast/PR-blocking tier, unchanged from before.

**Grand total across both scoped runs: 283 passed, 2 failed (pre-existing, unrelated), 1 deselected
(re-run separately, passed).**

## Files Changed
- `tests/integration/scenarios/test_entity_differentiation.py` — Steps 1-5 (spec scaling, SEEDS
  constant, helper extraction, test-body rewrite, marker + docstring updates)
- `tests/unit/strategic/test_score_normalization.py` — Step 6 (new documented-limitation
  regression guard test)
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-226 correction (Required Follow-on)
- `docs/simulation/domains/adventure_contract.md` — Calibration Note correction + `last_verified`
  bump (Required Follow-on)
- `docs/plans/long_term_development_roadmap.md` — Epic 1.1's own "Acceptance signal" line
  recalibrated from ≥2× to ≥1.5×, citing this ticket and the real ~1.74× measured ratio (found and
  fixed by Document-Update, beyond plan.md's own 2 named Required Follow-on locations)
- `docs/plans/idea_cognition_graph_analytics_pipeline.md` — "Impact on E11D" section's stale
  "(≥2× differential)" corrected to "≥1.5× differential", plus the correct System B attribution
  (found and fixed by Document-Update)
- `docs/plans/idea_embedding_latent_cognition.md` — "Natural Integration Points" table's
  E11D-SCORING-CAL row corrected the same way (found and fixed by Document-Update)
- `tickets/inprogress/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION.md` — this file
  (Implementation Notes, Test Summary, Files Changed, Completion Summary, AC checkboxes, Status)

## Completion Summary
Implemented plan.md's 6-step fix for `test_bravery_quartile_combat_rate_2x`'s statistical
collapse: doubled the differentiation-arena population (8h/4m → 16h/8m, arena 32x32 → 45x45,
density-held-constant) so the bravery quartile split never shrinks to a single-entity comparison,
replaced the single-seed run with a 24-seed (`SEEDS=1..24`) mean-of-per-seed-rates aggregate, and
recalibrated the pass threshold from the unreachable 2.0x to an evidence-backed 1.5x — measured
real ratio 1.7421, matching plan.md's calibration to 4 decimal places, with the test passing at
139.25s under the `extra_slow`/large-budget CI tier it now correctly belongs to. Also landed the
plan's required documented-limitation regression guard for the separately-ticketed
`retention_margin` normalization defect, and corrected the two stale doc/ledger locations
(parity ledger STRAT-226, `adventure_contract.md`'s Calibration Note) that misattributed the
ratio to a dead System-A route instead of the real, live System-B `CombatEngageScorer` mechanism.
No deviations from the approved plan.

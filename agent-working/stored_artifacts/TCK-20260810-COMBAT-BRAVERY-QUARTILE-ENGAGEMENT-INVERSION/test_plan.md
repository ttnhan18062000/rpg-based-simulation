---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
artifact_type: test_plan
tags: [combat, calibration]
---

# Test Plan — TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## Regression Surface

Existing tests that must keep passing after any fix lands (do not weaken or delete these):

**Unit — strategic / interruption resistance (owned by C2, must not regress):**
- `tests/unit/strategic/test_interruption_resistance.py` — including
  `TestInterruptionResistance` (unlocked-path margin tests) and
  `TestGenericInterruptionBypass` (the 6 tests added by C2: generic-kind bypass/block,
  detour-unconditional, danger-bypass-still-works / danger-bypass-now-blocked)
- `tests/unit/strategic/test_project_continuity.py` — `test_project_lock`,
  `test_interruption_resistance_margin` (explicit anti-drift guard for the raw,
  un-normalized `effective_current_score` formula — must stay byte-identical),
  `test_project_continuity_resume_suspended`
- `tests/unit/strategic/test_score_normalization.py` — both C2 cross-system tests
  (`test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`,
  `test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current`)

**Unit — adventure domain (mapper score fidelity, routing guard, owned by C2):**
- `tests/unit/domains/adventure/test_phase3_route_families.py` (mapper score-fidelity
  regression test added by C2 Step 10)
- `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py` (AST guard
  added by C2 Step 9 — `phase.py` must keep routing exclusively through
  `evaluate_project_switch()`, never construct `StrategicUpdate(current_project_id_set=...)`
  directly)
- `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`

**Integration — adventure domain (owned by C2):**
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` — including
  the pre-existing `test_filters_out_locked_projects` and C2's new
  `test_apply_respects_active_system_b_lock` / `test_apply_switches_when_candidate_clears_bar`

**Integration — the ticket's own target test:**
- `tests/integration/scenarios/test_entity_differentiation.py::test_no_identical_personality_vectors_at_spawn`
  (Test 1 in the same file — must keep passing; unrelated to this ticket's own change but shares
  the same `_build_differentiation_spec()` fixture, so any spec/world change must not break it)
- `tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x`
  (the ticket's own target — currently failing 0.8375/0.8575, inverted vs 2x requirement)

**Goal scoring (bravery sign correctness — already confirmed correct, must not regress):**
- `tests/unit/ai/goals/` (wherever `CombatEngageScorer`/`CombatRetreatScorer` unit tests live —
  confirm exact path at Implement time; not yet directly enumerated in this investigation) —
  any fix must not touch the scorer sign logic, which investigation.md already confirmed correct.

## New Tests Required

Per this ticket's own Acceptance Criteria (`## Acceptance Criteria` in the ticket file):

**AC1 — "Real root cause ... confirmed with direct evidence (per-entity trace data), not
hypothesized":** satisfied by this investigation's own trace data (1365 real
`evaluate_project_switch()` calls captured, 24 locked-state calls analyzed exhaustively, 0/0
cross-system locked bypasses ever passed). No new test required for AC1 itself — it is an
investigation-phase deliverable, already met.

**AC2 — "Fix implemented and the test passes at >= 2x ratio (or the test's own threshold is
recalibrated with real evidence ...)":** the exact fix is a Plan-phase decision (see
investigation.md's "Open questions for Plan"), but whichever direction Plan picks, these tests are
required:

1. **Test name**: `test_bravery_quartile_combat_rate_2x` (itself, updated in place if Plan changes
   its assertion methodology — e.g., a full-population correlation check instead of an
   extreme-pair quartile slice — or its numeric threshold with cited evidence)
   **Category**: integration (existing, `@pytest.mark.slow @pytest.mark.integration`)
   **Verifies**: the real, intended behavior — bravery meaningfully and directionally predicts
   `combat_engage` participation rate — using whatever methodology/threshold Plan selects, backed
   by this investigation's real per-hero data (see the "no bravery correlation across the full
   population" finding — Plan must confirm the chosen methodology actually produces a real,
   reproducible positive signal at SEED=42 before locking in a threshold, not assume one exists).
   **Location**: `tests/integration/scenarios/test_entity_differentiation.py`

2. **Test name**: `test_bravery_quartile_combat_rate_2x_population_guard` (or equivalent — exact
   name TBD by Plan)
   **Category**: unit or integration (whichever is cheaper — likely a lightweight assertion inside
   the existing test rather than a separate one)
   **Verifies**: the quartile/comparison-group computation does not silently collapse to a
   single-entity comparison (`q_size == 1`) without either (a) failing loudly with a clear message
   distinguishing "no real signal" from "statistically meaningless sample," or (b) the scenario
   itself being redesigned so the alive population reliably stays large enough (e.g., >= 8, or a
   documented minimum) for the quartile math to mean something. This directly targets the
   confirmed-unchanged statistical finding (`q_size = max(1, n // 4)` collapsing at `n=6`).
   **Location**: same file, or `tests/integration/scenarios/test_entity_differentiation.py`'s own
   module-level helper if Plan chooses (b).

3. **Test name**: `test_normalized_lock_bypass_gate_cross_system_small_max_current` (or equivalent)
   **Category**: unit
   **Verifies**: the newly-confirmed residual defect in C2's normalized lock-bypass gate — a
   locked, System-A-typed `current` (small `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` scale) can, for at
   least one realistic score combination, be interrupted by a sufficiently urgent System-B
   `candidate` (large `_GOAL_UTILITY_SCORE_MAX = 100.0` scale) — the exact direction this
   investigation found untested by C2's own `test_score_normalization.py` (which only tests the
   opposite direction: System-A candidate vs System-B current). **This test is only meaningful
   once/if a follow-up fix to `retention_margin` normalization lands — see "Not this ticket's scope
   to fix" in investigation.md.** If Plan decides this ticket does NOT fix the normalization defect
   (recommended reading of investigation.md, since it doesn't block this ticket's own AC2), this
   test instead becomes a **documented-limitation regression guard**: assert the gate is currently
   unreachable in this direction (0 passes for a maximal-urgency System-B candidate against a
   minimal-score, freshly-locked System-A current), so a future silent behavior change in either
   direction is caught, and cite this investigation as the reason the assertion exists.
   **Location**: `tests/unit/strategic/test_score_normalization.py` (co-locate with C2's existing
   cross-system tests).

**AC3 — "Scoped pytest passes (combat, strategic, goals test directories)":** no new test — this
is the Scoped Pytest Commands section below, run after Implement.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest \
  tests/integration/scenarios/test_entity_differentiation.py \
  tests/unit/strategic/ \
  tests/unit/domains/adventure/ \
  tests/integration/domains/adventure/ \
  tests/unit/ai/goals/ \
  -v
```

Never run bare `pytest tests/`. If the goals-scorer unit test directory has a different real path
than `tests/unit/ai/goals/`, confirm the exact path at Implement time (not yet directly enumerated
in this investigation) and substitute it — do not silently drop scorer coverage from the scoped run
just because the exact path wasn't confirmed here.

## Anti-Drift Test Guards

- **`test_interruption_resistance_margin` (`tests/unit/strategic/test_project_continuity.py`) must
  not be touched.** It is C2's own explicit anti-drift guard for the raw, un-normalized
  `effective_current_score` formula on the *unlocked* path — this ticket's fix must not leak
  normalization into that branch. If Implement finds itself needing to edit this test, that is a
  signal the fix has drifted into the wrong function/branch.
- **Do not "fix" the test by loosening `CombatEngageScorer`'s or `CombatRetreatScorer`'s bravery
  sign or coefficients.** Both are already confirmed correct (positive bravery weight for engage,
  negative for retreat) — re-verified again this session via C2's landed code read. Any diff to
  `src/ai/goals/scorers.py` as part of this ticket's fix is a scope-creep red flag, not a fix.
- **Do not revive `RouteFamily.HUNT_WEAK_ENEMY`'s dead generator path** as a shortcut to make the
  test pass by routing System A directly into combat — the original investigation already
  determined this would build a second, redundant combat-decision path duplicating `GoalRegistry`'s
  legitimate ownership of that decision. A guard test could assert
  `AdventureRouteGenerator.generate()` never yields a `HUNT_WEAK_ENEMY` candidate if this needs
  locking in explicitly, but is not required unless Implement's fix touches `generator.py`.
- **If Plan chooses to fix the `retention_margin`/`current_max` normalization defect as part of
  this ticket (not the recommended path, but possible if Plan judges it necessary for AC2), the
  fix must not weaken `STRAT-187`'s "current project retention priority" guarantee in the other
  direction** — i.e., do not simply zero out or drastically shrink `retention_margin`'s effect for
  System-A currents in a way that makes them trivially interruptible by any System-B candidate
  regardless of urgency. `test_switch_when_candidate_exceeds_margin` and
  `test_higher_resistance_prevents_more_switches` (both in
  `tests/unit/strategic/test_interruption_resistance.py`, both untouched by C2) are the existing
  guards for this direction and must keep passing.
- **Do not let a "correlate across the full population" test methodology change silently drop the
  `bottom_rate > 0` diagnostic gate assertion** (`test_bravery_quartile_combat_rate_2x`'s own
  existing check that flags a structurally-broken flag/proximity setup, distinct from the 2x
  ratio check) — if Plan redesigns the assertion shape, this diagnostic's intent (catch "combat
  engagement isn't happening at all," not just "isn't happening at the right rate") should be
  preserved in some form.
- **Any change to `_build_differentiation_spec()` or `TICKS`/`SEED` module constants** (e.g., to
  address the "6 of 8 heroes died, collapsing quartile math" population issue) must keep
  `test_no_identical_personality_vectors_at_spawn` passing — it shares the same fixture.

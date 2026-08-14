---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
artifact_type: test_plan
tags: [cognition, strategy]
---

# Test Plan — TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG

## Regression Surface

Existing tests that must keep passing (unit only — this subsystem has no dedicated
arena-combat/integration coverage; `evaluate_project_switch()` is exercised at the unit level).

**Unit — `tests/unit/strategic/test_interruption_resistance.py`**
- `TestInterruptionResistance` (all, e.g. `test_switch_when_no_current_project`,
  `test_retention_when_candidate_below_margin`) — exercise the raw/unlocked path (lines 976, 996),
  untouched by the fix.
- `TestGenericInterruptionBypass` (6 tests: `test_generic_kind_bypasses_when_score_and_floor_clear`,
  `test_generic_kind_blocked_when_floor_not_cleared`,
  `test_generic_kind_blocked_when_effective_current_not_cleared`,
  `test_detour_bypasses_lock_unconditionally`,
  `test_danger_bypass_still_works_when_effective_current_clears`,
  `test_danger_bypass_blocked_when_effective_current_not_cleared`) — all use raw-string `kind`
  values (`"crafting"`, `"scavenge"`, `"danger"`, `"detour"`) for `current`, which
  `_score_scale_max` classifies to `_GOAL_UTILITY_SCORE_MAX=100` by the default branch. Verified
  by direct arithmetic (investigation.md, Direction 4/B-vs-B) that `current_max=100` makes the
  fixed-denominator change a no-op for every one of these 6 — must all still pass unchanged.
- `TestCognitionProfile` — unrelated to this fix (profile derivation), unaffected.

**Unit — `tests/unit/strategic/test_project_continuity.py`**
- All tests using `evaluate_project_switch()` (lines ~47, 55, 76, 83, 88) — none construct a
  `ProjectKind`-typed locked `current`; confirmed via grep, no `ProjectKind`/`GoalKind` import used
  in this file at all — unaffected by the fix, must still pass unchanged.

**Unit — `tests/unit/strategic/test_score_normalization.py`**
- `test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current` — current is
  `GoalKind.SOCIAL` (`current_max=100`), unaffected, must still pass unchanged.
- `test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current` — current is
  `GoalKind.COMBAT_ENGAGE` (`current_max=100`), unaffected, must still pass unchanged.
- `test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation` — current
  is `ProjectKind.SOCIAL` (`current_max=2.9`), **directly affected — see "Contradicted Test"
  below, this is not a "still passes" case.**

**Scoped pytest command for the full regression surface (see Scoped Pytest Commands below).**

## New Tests Required

Per the ticket's 4 Acceptance Criteria:

### AC1 — "A locked System-A current CAN be interrupted by a genuinely high-urgency System-B
candidate, verified via real, realistic score values (not synthetic)"

- **Test name**: `test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
- **Category**: unit
- **What it verifies**: using the real, captured trace values from
  `stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md`
  (tick=2, hero=8 row) — `current = ProjectState(kind=ProjectKind.SOCIAL, score=0.8207,
  lock_until_tick=100)`, default `CognitionProfile` (`interruption_resistance=0.3,
  resistance_multiplier=30.0` → `retention_margin=9.0`), `candidate =
  ProjectState(kind=GoalKind.COMBAT_ENGAGE, score=132.58)`, `current_tick=50` (locked) →
  `evaluate_project_switch()` returns a non-`None` `StrategicUpdate` with
  `current_project_id_set == candidate.id`. These are real values pulled from a live 1365-call
  monkeypatched trace, not hand-picked to pass — satisfies AC1's "not synthetic" requirement
  directly. Worked arithmetic in the docstring: old formula gives `normalized_effective_current_pct
  = 3.386` (blocks, matches trace's `switched=False`), new formula gives `0.373` (bypasses).
- **Where**: `tests/unit/strategic/test_score_normalization.py` (co-locate with the existing
  cross-system tests; this is the direction none of them cover today).

### AC2 — "A locked System-A current is still NOT interrupted by a low-urgency System-B candidate
— must not overcorrect into 'any candidate can always interrupt'"

- **Test name**: `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`
- **Category**: unit
- **What it verifies**: same `current` as AC1's test (`ProjectKind.SOCIAL, score=0.8207,
  lock_until_tick=100`, default profile), but `candidate = ProjectState(kind=GoalKind.SOCIAL,
  score=30.0)` (or another realistic low-urgency System-B score, e.g. a `SocialScorer` output well
  under the floor) → `evaluate_project_switch()` returns `None`. Also add a second case at
  `candidate.score=75.0` (clears the margin term but not the `0.8` floor) to specifically pin the
  floor-still-binds behavior, matching the "explicit emergency" framing of STRAT-186 — this is the
  case that would silently pass under a broken "any candidate can bypass" overcorrection but must
  fail here.
- **Where**: `tests/unit/strategic/test_score_normalization.py`, adjacent to AC1's test.

### AC3 — regression: existing suites still pass, with buggy-behavior-encoding tests updated

- No new test *file* needed for this AC — it's satisfied by (a) the Regression Surface section
  above passing unchanged, and (b) the Contradicted Test below being explicitly updated, not left
  accidentally green.

### AC4 — "STRAT-186/187 parity-ledger entries updated to describe the fixed mechanism"

- Not a pytest-testable AC by itself, but the parity ledger's `test_path` field for both entries
  must point at a real, passing test. Recommend `test_path:
  tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
  for STRAT-186 (the "or explicit emergency" clause) and the same or
  `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate` for STRAT-187 (the
  "reservation priority, not absolute" clause) — Plan should pick the final mapping, but both new
  tests above jointly cover both IDs' claims.

### Contradicted test — must be updated, not silently left passing

`tests/unit/strategic/test_score_normalization.py::
test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation` currently
asserts `result is None` **specifically because of this bug** (its own docstring says so
explicitly and instructs future updaters not to just delete it). Under the fix, this exact
scenario (`current.score=0.1`, default profile, `candidate = GoalKind.COMBAT_ENGAGE, score=100.0`)
now bypasses:
- `current_pct = 0.1/2.9 = 0.0345`, `normalized = 0.0345 + 9.0/100 = 0.1245`.
- `candidate_pct = 100.0/100 = 1.0`. `1.0 > 0.1245` and `1.0 > 0.8` → **bypasses**.

**Required action**: rename and rewrite this test (do not delete — the assertion target flips, the
test's evidentiary value as a fixed-behavior regression guard remains valuable), e.g. to
`test_locked_system_a_current_now_reachable_by_system_b_candidate_fix_confirmed`, asserting
`result is not None` and `result.current_project_id_set == "candidate"`, with a docstring
explaining this is the confirmed fix for `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-
SCALE-BUG` and citing the old formula's `3.10`-vs-new formula's `0.09` margin-term arithmetic so a
future reader understands why the assertion flipped. This is functionally the same scenario as
AC1's new test but with the ticket's own originally-documented minimal-score edge case (`score=
0.1`) rather than AC1's real-trace value (`score=0.8207`) — keep both: the minimal-score case
guards the boundary condition (`current.score` near zero), the real-trace case satisfies AC1's
"realistic, not synthetic" requirement.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/strategic/test_interruption_resistance.py tests/unit/strategic/test_project_continuity.py tests/unit/strategic/test_score_normalization.py -v
```

Never `pytest tests/`. This is the exact scoped command the prior investigation
(`stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md:
285-287`) already used to confirm the pre-fix baseline (19 tests, all passing) — reuse it so the
new count (19 existing − 1 renamed/rewritten + 2 new AC tests = 21, net) is directly comparable.

If Plan/Implement also touches `docs/parity_ledger/strategic_cognition.yaml`'s `test_path` fields,
re-run this same command to confirm the newly-referenced test names actually exist and pass before
closing the ticket (the `done-checker`'s parity/test_path cross-check will otherwise fail).

## Anti-Drift Test Guards

- **`TestGenericInterruptionBypass`'s 6 tests must be run and pass with zero modification.** They
  are the direct evidence that the fix is a no-op for the B-current direction (all 6 use
  `current_max=100` via raw-string kinds). If any of these needs a code change to pass, the fix
  touched something outside the single margin-term denominator — stop and re-examine.
- **`test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current` and
  `test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current` must also pass with
  zero modification** — same guard, for the two existing `test_score_normalization.py` tests not
  targeted by this ticket.
- **A guard against re-breaking the raw/unlocked path**: `TestInterruptionResistance`'s existing
  tests (`test_retention_when_candidate_below_margin` and siblings) exercise line 976/996 directly
  with no lock involved — passing unchanged confirms the fix didn't touch
  `effective_current_score`'s raw computation.
- **A guard against clamping `candidate_pct`**: if Implement is tempted to "fix" extreme
  `candidate_pct` values (e.g. `TownScorer`'s ~200 raw giving `candidate_pct=2.0`) by clamping to
  `[0,1]`, the existing module comment (`intelligence.py:39-46`) forbids it — no new test needed
  for this since no existing test exercises it, but Implement/Verify should re-check this comment
  is still true of the final diff (a clamp would be a silent, undocumented behavior change outside
  this ticket's scope).
- **A guard against scope-creep into the raw-path's own separate cross-scale issue**: do not add a
  test that changes `test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`'s
  documented expectation that a maximal System-A candidate (`score=2.9`) fails the *raw* comparison
  against certain System-B currents — that is a pre-existing, out-of-scope, separately-flagged
  asymmetry (see investigation.md "Is the unlocked path affected?"), not something this ticket's
  fix touches or should touch.

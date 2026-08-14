---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
phase: done
date: 2026-08-11
tags: [cognition, strategy]
---

# TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG

## Title
`evaluate_project_switch()`'s normalized lock-bypass gate structurally cannot ever let a
System-B candidate interrupt a locked System-A current project

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` (C2) generalized
`StrategicIntelligenceSystem.evaluate_project_switch()`'s lock-bypass gate from a hardcoded
`"danger"/"detour"` allowlist to a normalized score/urgency-floor rule:

```python
candidate_max = _score_scale_max(candidate_project.kind)
current_max = _score_scale_max(current.kind)
candidate_pct = candidate_project.score / candidate_max
normalized_effective_current_pct = (current.score / current_max) + (retention_margin / current_max)
if not (candidate_pct > normalized_effective_current_pct and candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT):
    return None
```
(`src/systems/strategic_systems/intelligence.py:988-993`)

`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s post-batch re-investigation
(`stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md`'s
"Post-Batch Re-Investigation" section) found, via a live monkeypatched trace of 1365 real
`evaluate_project_switch()` calls (SEED=42, 400 ticks): **0 of 24** calls made while
`current.lock_until_tick > current_tick` ever resulted in a switch, for any kind, anywhere in the
run. The specific, confirmed mechanism: `retention_margin` (default `interruption_resistance(0.3) *
resistance_multiplier(30.0) = 9.0`, `src/core/strategic.py:320-321`) is divided by `current_max`
rather than normalized to any shared scale. When `current` is a System-A (`ProjectKind`) project,
`current_max = _ADVENTURE_ROUTE_SCORE_MAX = 2.9`, so `retention_margin / current_max ≈ 3.10` —
**a percentage-point value alone exceeding 310%** — before even adding `current.score/current_max`.
Since no real System-B `CombatEngageScorer` candidate observed in the trace ever produced
`candidate_pct` above ~1.0–1.33, a System-B candidate can never mathematically clear
`normalized_effective_current_pct` while `current` is System-A-typed, for any value either
system's scorers can realistically produce today.

This contradicts `STRAT-186`'s own documented intent ("Strategic project switching requires margin
or explicit emergency" — implying a genuine emergency-equivalent candidate should still be able to
get through) and makes `STRAT-187`'s "current project has reservation priority" absolute/
un-interruptible in this direction rather than merely favored, a stronger guarantee than the
Mechanics Bible documents.

This did not block `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s own fix from
working, because System-A locks in that scenario are short (10 ticks, capped at 50) and the
*unlocked* raw-score comparison path (`if candidate_project.score > effective_current_score:`,
C2-untouched) rescues stuck heroes once the lock naturally expires. A scenario with longer
System-A locks, or any future tightening of `_threat_resolved()`/`AdventureDecisionPhase`'s own
per-hero lock gate, would re-expose full starvation with no escape path at all.

## Scope
- Fix the normalization so `retention_margin` does not structurally dominate the comparison when
  `current` belongs to a small-max system (System A, `~2.9`) — the exact mechanism is an Implement-
  time design decision (see Assumptions/Open Questions below), not decided by this ticket's Scope
- Add a regression test exercising the specific direction C2's own test suite never covered: a
  locked System-A `current` (small max) challenged by a System-B `candidate` (large max) whose
  score represents a genuine emergency/high-urgency case — must be able to bypass under the fixed
  formula, while a low-urgency System-B candidate must still correctly fail to bypass
- Update `docs/parity_ledger/strategic_cognition.yaml`'s STRAT-186/187 entries to reflect the fix
  (their current `v2_evidence`, written by C2, describes the pre-fix behavior)
- Update `docs/mechanics/04_strategic_cognition.md` §2 if the normalization basis changes materially
  from what C3 already documented there

## Out of Scope
- `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`'s own test/statistical fix — that
  ticket does not depend on this fix landing (confirmed: the specific heroes it compares never hit
  the locked path)
- Any change to `CombatEngageScorer`'s bravery weighting or other scoring formulas
- Reviving `RouteFamily.HUNT_WEAK_ENEMY` or unifying `GoalKind`/`ProjectKind` — unrelated, tracked
  under D22

## Acceptance Criteria
- [x] A locked System-A `current` project CAN be interrupted by a genuinely high-urgency System-B
      candidate under the fixed formula — verified via a new test using real, realistic score values
      (not synthetic values chosen just to pass)
- [x] A locked System-A `current` project is still NOT interrupted by a low-urgency System-B
      candidate — the fix must not overcorrect into "any candidate can always interrupt"
- [x] All existing tests in `tests/unit/strategic/test_interruption_resistance.py`,
      `test_project_continuity.py`, `test_score_normalization.py` still pass (with any that encoded
      the buggy behavior updated, not just left green by accident)
- [x] STRAT-186/187 parity-ledger entries updated to describe the fixed mechanism

## Related Tickets
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION (C2 — landed the buggy normalization this
  ticket fixes)
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION (the ticket whose re-investigation
  discovered this bug as a byproduct)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
- stored_artifacts/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION/ (the plan/investigation that
  landed the current formula)
- stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md (the
  "Post-Batch Re-Investigation" section — the direct evidence and real trace numbers for this bug)

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (`evaluate_project_switch`, `_score_scale_max`,
  module constants)
- src/core/strategic.py (`CognitionProfile` defaults)

## Assumptions / Open Questions
- The exact fix mechanism is not decided: options include (a) normalizing `retention_margin` itself
  as a percentage of `current_max` at its point of origin rather than treating it as a raw-scale
  constant, (b) capping `retention_margin`'s contribution to the normalized comparison at some
  fraction, (c) computing `normalized_effective_current_pct` differently (e.g., percentage of
  `current_max` for the raw score, but comparing `retention_margin` against a fixed absolute
  floor instead of dividing it by `current_max`), or (d) something else — Investigate/Plan must
  determine the right approach with real evidence, not guess
- Whether this bug is severe enough to warrant a `hotfix`-tier minimal patch or a `standard`-tier
  redesign is also an Implement-time judgment call, informed by how many real corpus scenarios are
  actually affected (currently only 2 of 20 corpus worlds have `ENABLE_ADVENTURE_ROUTING=ON`)

## Implementation Notes
Implemented plan.md Steps 1, 3, and 4 directly in the Implement phase. Steps 2 (Mechanics Bible
update) and 5 (parity ledger update) were, as planned, carried out by the pipeline's own later
Document-Update and Parity phases respectively — both have since completed and are reflected below.

**Step 1** (`src/systems/strategic_systems/intelligence.py:991`): changed the margin term's
denominator in `normalized_effective_current_pct` from the variable `current_max` to the fixed
`_GOAL_UTILITY_SCORE_MAX` (100.0). Only that one denominator changed — `current.score/current_max`,
`candidate_pct`'s own computation, `candidate_max`/`current_max` (lines 988-989), line 976
(`effective_current_score`), and line 996 (unlocked-path comparison) are all byte-identical to
before. Added a one-sentence code comment directly above the changed line citing this ticket, so a
future reader does not "simplify" the denominator back to `current_max`.

**Step 3**: renamed
`test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation` to
`test_locked_system_a_current_now_reachable_by_system_b_candidate_fix_confirmed` in
`tests/unit/strategic/test_score_normalization.py`. Flipped the assertion from `result is None` to
`result is not None` + `result.current_project_id_set == "candidate"` (the fixture's candidate id
is `"candidate"`, confirmed against the file's existing construction). Rewrote the docstring to
cite the old formula's ~3.14 vs. new formula's ~0.1245 margin-term/normalized-pct arithmetic for
this test's exact fixture values (`current.score=0.1`, `candidate.score=100.0`). Fixture
construction (`ProjectState`/`CognitionProfile`/`_make_entity` calls) left untouched, as required.

**Step 4**: added two new tests to the same file, using the existing file's `_make_entity` /
`ProjectState` / `CognitionProfile` construction patterns (no new helpers invented):
- `test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate` (AC1) — uses the
  real trace values from the parent investigation (tick=2, hero=8: `current.score=0.8207`,
  `ProjectKind.SOCIAL`, locked; `candidate.score=132.58`, `GoalKind.COMBAT_ENGAGE`) — asserts a
  non-`None` result with the candidate winning.
- `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate` (AC2) — same locked
  `current`, two sub-cases (`candidate.score=30.0` fails the margin term itself;
  `candidate.score=75.0` clears the margin term but fails the `0.8` urgency floor) — both assert
  `result is None`.

No deviations from plan.md. Ran the exact scoped pytest command from test_plan.md after all
changes; full pass, 0 failures (see Test Summary).

**Step 2** (`docs/mechanics/04_strategic_cognition.md` §2, Document-Update phase): corrected the
Generalized Bypass formula sentence from `retention_margin/current_max` to
`retention_margin/_GOAL_UTILITY_SCORE_MAX`, matching the landed code exactly, with a clause
explaining `retention_margin`'s own raw 0-30 range was calibrated against System B's 0-100 scale
from the start. §6.6 checked and correctly left untouched (only the margin term's denominator
changed, not the score-term denominators it describes). Frontmatter `last_verified` bumped to
2026-08-11.

**Step 5** (`docs/parity_ledger/strategic_cognition.yaml`, Parity phase): STRAT-186 and STRAT-187
both updated — `v2_evidence` now cites `intelligence.py:991-996` and describes the fixed
mechanism, `test_path` set to `test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
(STRAT-186, the "or explicit emergency" clause) and
`test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate` (STRAT-187, the
"favored, not absolute" clause) respectively, closing both entries' pre-existing P0
test_path-null gap. STRAT-185 was investigated and correctly left unchanged — its claim
(`retention_margin` is derived from `interruption_resistance`) is about the margin's own
computation, which this fix does not touch, only its normalization denominator in the comparison.

## Test Summary
Command (from test_plan.md, matches plan.md's own scoped command exactly):
```
.venv/bin/python3 -m pytest tests/unit/strategic/test_interruption_resistance.py tests/unit/strategic/test_project_continuity.py tests/unit/strategic/test_score_normalization.py -v
```
Result: **22 passed, 0 failed** (0.18s). All pre-existing tests in the three files pass unchanged
(including the 6 `TestGenericInterruptionBypass` tests and the 2 untouched
`test_score_normalization.py` tests, confirming the fix is a no-op for the already-correct
directions), the renamed/flipped test passes with its new assertion, and both new AC-mapped tests
pass.

The pipeline's own Test phase (test-scoper) additionally ran a wider transitively-scoped pass —
`tests/unit/strategic/test_interruption_resistance.py`, `test_project_continuity.py`,
`test_score_normalization.py`, `test_strategic_reprioritization.py`,
`tests/unit/systems/test_quest_activation_pathway.py`,
`tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py` — **38 passed, 0
failed**, confirming no transitive regression in adjacent call sites.

## Files Changed
- `src/systems/strategic_systems/intelligence.py` — line 991 denominator fix + added comment
  (Step 1)
- `tests/unit/strategic/test_score_normalization.py` — renamed/flipped one test (Step 3), added
  two new tests (Step 4)
- `docs/mechanics/04_strategic_cognition.md` — §2 Generalized Bypass formula sentence corrected,
  `last_verified` bumped (Step 2)
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-186/187 `v2_evidence` + `test_path`
  updated (Step 5)

## Completion Summary
Fixed the confirmed bug in `evaluate_project_switch()`'s locked-branch normalization: the
`retention_margin` term now divides by the fixed `_GOAL_UTILITY_SCORE_MAX` (100.0) instead of the
variable `current_max`, so a locked System-A current (small declared max, ~2.9) no longer
structurally blocks every possible System-B candidate regardless of urgency. Added regression
coverage for both directions (AC1: genuine high-urgency candidate now bypasses; AC2: low-urgency
candidate still correctly blocked, including a floor-only-binds edge case) and updated the
previously bug-pinning test to assert the fixed behavior instead. The Mechanics Bible (§2) and the
STRAT-186/187 parity-ledger entries were both updated to describe the fixed mechanism. All 4
Acceptance Criteria are satisfied.

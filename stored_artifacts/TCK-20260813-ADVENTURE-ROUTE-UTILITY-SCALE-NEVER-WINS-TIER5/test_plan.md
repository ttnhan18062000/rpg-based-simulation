---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5
artifact_type: test_plan
tags: [adventure, agency, strategy, cognition]
---

# Test Plan — TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5

## Regression Surface

**Unit:**
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` — full file. In particular
  `test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact` (lines 96-113) currently pins
  `raw_score==2.9 → utility==100.0`, `1.45→50.0`, `0.0→0.0` — this test is **expected to require an
  update** if Plan adopts a dedicated tier-5 denominator (investigation.md Anti-Drift Hazards); it is
  not a silent-passing guard to leave untouched by accident.
- `tests/unit/strategic/test_score_normalization.py` — full file. Tests
  `evaluate_project_switch()`'s Generalized Bypass gate only (hand-built `ProjectState` objects, never
  calls `AdventureGoalScorer`/`AdventureRouteScorer`). Must stay green **unmodified** — confirms the
  recommended fix direction does not touch `_score_scale_max()`/`_ADVENTURE_ROUTE_SCORE_MAX`'s
  existing Generalized-Bypass-gate consumer.
- `tests/unit/ai/goals/test_region_stabilization_goal_scorer.py` — must stay green unmodified;
  confirms `RegionStabilizationGoalScorer`'s output is unaffected by any Adventure-side change
  (investigation.md's algebraic-cancellation finding should hold empirically too).
- `tests/unit/strategic/test_region_stabilization_materialization.py` — must stay green unmodified.
- `tests/unit/strategic/test_social_contract_materialization.py` — must stay green unmodified; guards
  against the hardcoded-`2.9`-literal-vs-shared-constant risk investigation.md flags (only relevant if
  a global-constant change were attempted, which the recommended direction avoids, but this test
  should still be run to prove it).
- `tests/unit/domains/adventure/` — full directory (`test_scoring.py` and siblings, if present;
  confirm via `find tests/unit/domains/adventure -name "test_*.py"` at Implement time) — the
  `AdventureRouteScorer.score()` formula itself is unchanged by the recommended direction (only the
  *consumer* normalization changes), so all existing formula-level tests must stay green unmodified.
- `tests/unit/strategic/test_adventure_route_materialization.py` — must stay green unmodified; proves
  the materialization branch (which uses raw `metadata["raw_score"]`, never `.utility`, per
  `intelligence.py:1496-1499`'s own comment) is unaffected by a tier-5-normalization-only change.
- `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`,
  `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`,
  `tests/unit/core/test_strategic_update_routing_family.py` — the write-path tests from the parent
  ticket (`TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`). Must stay green unmodified;
  this ticket does not touch the write-path.
- `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py` — must stay green
  unmodified; no `## Engine Phase` doc section or byte-identical guard is touched by this ticket.

**Integration:**
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` — must stay green
  unmodified (exercises `AdventureRouteScorer.score()`/`AdventureDecisionService.decide()` directly,
  unaffected by a tier-5-normalization-only change in `AdventureGoalScorer`).

**Simulation-quality / calibration (arena-combat-adjacent, cross-cutting):**
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "simq_routing_test or
  hero_guild_routing"` — full 6-run_key band, current-HEAD baseline before any change (AGENCY
  currently `C/0.0` on all 6, per the parent ticket's confirmed-unchanged state) must be captured and
  compared against, not assumed unchanged, since this ticket's own fix is specifically targeted at
  this exact pillar/run_key set.

## New Tests Required

1. **`test_adventure_goal_scorer_tier5_normalization_uses_dedicated_denominator`** (or equivalent,
   exact name TBD by Plan)
   - Category: unit
   - Verifies: `AdventureGoalScorer.score()`'s `utility` computation uses whatever new denominator
     Plan adopts (not `_ADVENTURE_ROUTE_SCORE_MAX` directly, if Plan implements the recommended
     decoupled-constant direction) — parametrized like the existing
     `test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact`, asserting the new
     denominator's own boundary values (`raw_score == new_max → utility == 100.0`, midpoint, `0.0`).
   - Where: `tests/unit/ai/goals/test_adventure_goal_scorer.py` (extend/replace the existing
     parametrized test named above)

2. **`test_region_stabilization_goal_scorer_unaffected_by_adventure_denominator_change`**
   - Category: unit, architecture-guard-flavored
   - Verifies: `RegionStabilizationGoalScorer.score()`'s `utility` output is unchanged for a fixed
     `urgency` input before/after the fix — direct proof of the algebraic-cancellation finding
     (investigation.md), guarding against a future regression that couples these two scorers'
     normalizations more tightly than intended.
   - Where: `tests/unit/ai/goals/test_region_stabilization_goal_scorer.py` (extend)

3. **`test_social_contract_goal_scorer_utility_stays_bounded_by_100`**
   - Category: unit, architecture-guard-flavored
   - Verifies: `SocialContractGoalScorer.score()`'s `utility` never exceeds `100.0` even at
     `raw_score`'s own hardcoded-`2.9`-literal clamp ceiling — a direct regression guard against the
     hardcoded-literal-vs-shared-constant fragility investigation.md flags, confirming whichever fix
     direction Plan adopts does not silently break this scorer's implicit 0-100 bound.
   - Where: `tests/unit/ai/goals/test_social_contract_goal_scorer.py` (create if it does not already
     exist — confirm via `find tests/unit/ai/goals -iname "*social_contract*"` at Implement time; the
     scorer itself already has coverage via `test_social_contract_materialization.py` but that file
     exercises materialization, not this specific bound)

4. **`test_adventure_route_typical_score_produces_meaningfully_higher_utility_than_before_fix`**
   - Category: unit
   - Verifies: using the real, live opportunity-generation constants this investigation measured
     (e.g. a CRAFT_UPGRADE route with `expected_benefit=0.9`, `expected_risk=0.0`, mid-range
     personality/urgency), the post-fix utility is measurably higher than the pre-fix
     `(raw_score/2.9)*100` value would have produced — pins the direction and rough magnitude of the
     fix's real-world effect, not just its boundary values.
   - Where: `tests/unit/ai/goals/test_adventure_goal_scorer.py` (extend)

5. **`test_evaluate_project_switch_generalized_bypass_gate_still_uses_original_2_9_ceiling`**
   - Category: unit, architecture guard
   - Verifies: `_score_scale_max()`/`_ADVENTURE_ROUTE_SCORE_MAX` remain `2.9` and are still the value
     `evaluate_project_switch()`'s lock-bypass gate uses (i.e. this fix did not accidentally change
     the Generalized Bypass gate's own denominator) — a direct guard for the "do not globally rescale
     the shared constant" Anti-Drift Hazard.
   - Where: `tests/unit/strategic/test_score_normalization.py` (extend) or a new file under
     `tests/architecture/` if Plan prefers a source-hash-style guard matching this repo's existing
     `test_evaluate_project_switch_source_hash_unchanged`-style precedent.

6. **Fresh `tools/calibrate_simq.py` verification (not a pytest unit test, but a required AC3
   verification step)** — run against `simq_routing_test`/`hero_guild_routing` × seeds {42,123,456}
   `_500t` (6 run_keys) post-fix, clean (non-instrumented, per the sibling investigation's Risk #4
   caution against DEBUG-handler timing perturbation), and record whether `route_selected`/
   `action_executed`/`route_family_first_use` fire. **Per investigation.md Risk #2, a fix that
   corrects the calibration defect is not provably sufficient to flip these to nonzero** — this step
   must report the actual measured outcome, not assume success from the unit-level fix landing.

## Scoped Pytest Commands

```
pytest tests/unit/ai/goals/test_adventure_goal_scorer.py -m "not slow" -q
pytest tests/unit/ai/goals/test_region_stabilization_goal_scorer.py -m "not slow" -q
pytest tests/unit/strategic/test_score_normalization.py -m "not slow" -q
pytest tests/unit/strategic/test_adventure_route_materialization.py tests/unit/strategic/test_region_stabilization_materialization.py tests/unit/strategic/test_social_contract_materialization.py -m "not slow" -q
pytest tests/unit/domains/adventure/ -m "not slow" -q
pytest tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py -m "not slow" -q
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "simq_routing_test or hero_guild_routing"
```

Never `pytest tests/` — scoped to the adventure/strategic-cognition/tier-5-scoring domain plus the
named simulation-quality run_keys this ticket's own AC targets.

## Anti-Drift Test Guards

- `test_score_normalization.py`'s existing 5 tests staying green, unmodified, is itself the guard
  that the Generalized Bypass gate's own use of `_ADVENTURE_ROUTE_SCORE_MAX`/`_score_scale_max()` was
  not touched by this ticket's fix.
- New Test 2 (RegionStabilization-unaffected) and New Test 3 (SocialContract-stays-bounded) are the
  direct guards against the two specific regression risks investigation.md identifies for a
  global-constant rescale — if Plan/Implement ever reconsiders that direction, these tests should
  fail loudly rather than silently degrading a scorer this ticket does not intend to touch.
- New Test 5 pins that `_ADVENTURE_ROUTE_SCORE_MAX` itself stays `2.9` post-fix (if Plan adopts the
  recommended decoupled-constant direction) — catches an accidental "just change the shared constant"
  shortcut during Implement that would silently reintroduce the SocialContract/RegionStabilization
  risk this investigation flags.
- The fresh `calibrate_simq.py` run (New Test 6) is the guard against overclaiming success — a green
  unit-test suite alone does not establish that `route_selected`/`action_executed` actually fire in
  the two named worlds; only a measured post-fix calibration run does, per investigation.md Risk #2's
  explicit warning not to conflate "the calibration defect is corrected" with "the AGENCY grade is
  restored."
- `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py` staying green is the
  guard that no doc-section or byte-identical constraint from the prior architecture migration was
  disturbed by this ticket's normalization-only change.

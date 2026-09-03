---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS
artifact_type: test_plan
tags: [lifecycle, adventure]
---

# Test Plan — TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS

## Regression Surface

**Unit — AdventureRouteScorer / scoring.py**
- `tests/unit/domains/adventure/test_scoring_plan_bonus.py` — plan-advance bonus tests; closest
  existing pattern for asserting a new additive score term and score-delta comparisons
  (`baseline = AdventureRouteScorer.score(entity, route)` without the new context vs. with it).
  Must keep passing unmodified — the new dependent-bias term must not perturb
  `plan_advance_bonus`'s own computation or its independence from other terms.
- `tests/unit/domains/adventure/test_phase3_route_scoring.py` — core Phase 3 route-scoring
  coverage (personality bias, urgency, risk, benefit terms).
- `tests/unit/domains/adventure/test_capability_confidence_scoring.py` — confidence_bonus term
  coverage; must remain unaffected since the new term is independent and additive.
- `tests/unit/domains/adventure/test_memory_informed_scoring.py` — memory_adjustment term
  coverage; same independence requirement.
- `tests/unit/domains/adventure/test_hero_quest_scoring.py` — HERO-specific QUEST_OPPORTUNITY
  scoring; must remain unaffected unless Plan scopes the dependent bias to also touch
  QUEST_OPPORTUNITY (not indicated by the ticket).
- `tests/unit/social/test_party_lifecycle.py` — covers SOC-230 escort scoring
  (`test_escort_target_route_scores_above_survival`) and defection; the new bias block sits
  immediately adjacent to §9 in `scoring.py` and must not alter these outcomes.

**Unit — Lifecycle / durable state**
- `tests/unit/progression/test_lifecycle.py` — covers `LifecycleComponent`/`LifecycleUpdate`
  canonical-dict round-trip, merge/is_noop, `LifecyclePatch.apply()` write-path,
  `_select_default_heir()`/`resolve_lifecycle()` succession behavior (including
  `test_default_heir_tie_break_deterministic`, SOC-245's `test_path`), and the birth-record schema
  added by the sibling `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` ticket. If Plan adds a new
  `LifecycleComponent`/`LifecycleUpdate` field for "dependent," this file's existing round-trip and
  merge/is_noop coverage patterns must be extended, and the pre-existing 24 tests must still pass.
- `tests/unit/social/test_social_bonds.py`, `tests/unit/social/test_social_lifecycle.py`,
  `tests/unit/social/test_social_party_regression.py` — if Plan instead keys "dependent" off
  `SocialComponent.bonds`/`SocialBond`/`RelationshipRole`, these are the relevant regression files.

**Architecture guard**
- `tests/architecture/test_adventure_route_score_max_unchanged.py` — pins
  `_ADVENTURE_ROUTE_SCORE_MAX == 2.9` (`src/systems/strategic_systems/intelligence.py`). Ticket AC
  #3 explicitly requires this pass unmodified after the new bias term is added.

**Integration (apply-path parity, only if a new durable field is added)**
- `tests/integration/optimization/test_component_patch_apply_parity.py`,
  `tests/integration/optimization/test_apply_plan_parity.py`,
  `tests/integration/optimization/test_phase_skip_parity.py` — sibling
  REPRODUCTION-BIRTH-RECORD-SCHEMA ticket ran these after extending `LifecyclePatch.apply()`; the
  same class of regression risk applies if this ticket also extends `LifecyclePatch.apply()`.

## New Tests Required

1. **`test_dependent_route_bias_lowers_risky_route_score`**
   - Category: unit
   - Verifies: an entity with an active dependent scores measurably lower on
     `RouteFamily.HUNT_WEAK_ENEMY` (or whichever risky family(ies) Plan selects) than an
     otherwise-identical entity without a dependent, all else equal (same traits, same route
     inputs, same `benefit`/`risk`/`confidence`). Assert via direct score-delta comparison
     (`result_with_dependent.score < result_without_dependent.score`) and, if Plan adds a
     dedicated trace field (recommended per investigation.md), assert the field's exact value
     directly — following `test_scoring_plan_bonus.py`'s
     `test_plan_advance_bonus_applied_when_route_matches_head_goal` pattern (baseline diff assert).
   - Location: `tests/unit/domains/adventure/test_scoring_dependent_bias.py` (new file, named for
     what it verifies, not a phase/ticket label — matches repo naming convention).

2. **`test_dependent_route_bias_raises_recovery_route_score`** (only if Plan implements the "and"
   half of the AC's "and/or")
   - Category: unit
   - Verifies: an entity with an active dependent scores measurably higher on a return/recovery
     route family (e.g. `RouteFamily.RECOVER` and/or `RETURN_TOWN`, per Plan's choice) than an
     otherwise-identical entity without a dependent.
   - Location: same new file as above.

3. **`test_dependent_route_bias_zero_when_no_dependent`**
   - Category: unit
   - Verifies: an entity with no dependent (field unset / empty) produces the same score as before
     this ticket's change — i.e. the new term is a true no-op absent a dependent, not merely
     "smaller." Guards against an accidental always-on default.
   - Location: same new file.

4. **`test_dependent_bias_independent_of_other_additive_terms`**
   - Category: unit
   - Verifies: the new bias term composes additively/independently — e.g. combining it with
     `plan_advance_bonus` (a `progression_plan` head-goal match) on the same route produces
     `baseline + dependent_delta + plan_advance_bonus`, not some interaction effect. Mirrors the
     regression-guard intent of `test_existing_hero_quest_bonus_still_applies` /
     `test_existing_warrior_mage_bonus_still_applies` in `test_scoring_plan_bonus.py`.
   - Location: same new file.

5. **Durable-field write-path test(s)** (exact shape depends on Plan's architecture decision):
   - If a new `LifecycleComponent`/`LifecycleUpdate` field is added:
     `test_dependent_field_round_trip` (canonical-dict serialization, matching
     `LifecycleComponent.to_canonical_dict()`'s existing pattern) and
     `test_dependent_field_applied_via_authoritative_patch` (asserts the field is only ever set via
     `LifecycleUpdate.<field>_set` → `LifecyclePatch.apply()`, never a direct mutation — mirrors
     the "no direct field mutation" assertions already present in `test_lifecycle.py` for
     `heir_entity_id_set`).
   - If `SocialBond`/`RelationshipRole` is extended instead: an equivalent round-trip/write-path
     test in `tests/unit/social/test_social_bonds.py` following that file's existing patterns.
   - Location: `tests/unit/progression/test_lifecycle.py` (extend existing file, matching the
     sibling `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` ticket's own approach of adding tests
     to this same file for its 5 new fields) or `tests/unit/social/test_social_bonds.py`.

6. **Architecture-guard confirmation** (not a new test — an explicit run, no code change expected):
   `tests/architecture/test_adventure_route_score_max_unchanged.py::test_adventure_route_score_max_stays_2_9_unchanged`
   must be run and confirmed passing unmodified, per ticket AC #3. If it fails, the new bias term
   has been implemented in a way that touches `_ADVENTURE_ROUTE_SCORE_MAX` — a scope violation to
   fix, not a test to edit (Gate Integrity rule, CLAUDE.md).

## Scoped Pytest Commands

```
# Core scoring unit tests (new tests + existing scoring regression surface)
pytest tests/unit/domains/adventure/ -v

# Lifecycle durable-state tests (if a new LifecycleComponent/LifecycleUpdate field is added)
pytest tests/unit/progression/test_lifecycle.py -v

# Social bond tests (if SocialBond/RelationshipRole is extended instead)
pytest tests/unit/social/test_social_bonds.py tests/unit/social/test_social_lifecycle.py tests/unit/social/test_social_party_regression.py tests/unit/social/test_party_lifecycle.py -v

# Architecture guard — must pass unmodified per AC #3
pytest tests/architecture/test_adventure_route_score_max_unchanged.py -v

# Apply-path parity (only if LifecyclePatch.apply() is extended)
pytest tests/integration/optimization/test_component_patch_apply_parity.py tests/integration/optimization/test_apply_plan_parity.py tests/integration/optimization/test_phase_skip_parity.py -v
```

Never `pytest tests/`. Each command above is scoped to the domain(s) this ticket touches
(adventure scoring, lifecycle/social durable state, and the one pinned architecture guard).

## Anti-Drift Test Guards

- **§9 escort-scoring (SOC-230) isolation guard**: `test_dependent_bias_independent_of_other_additive_terms`
  (New Test #4) and the existing `tests/unit/social/test_party_lifecycle.py::test_escort_target_route_scores_above_survival`
  together catch any accidental interaction between the new dependent-bias block and the adjacent
  §9 escort block — e.g. an entity that is both escorted and has a dependent must still receive
  both adjustments independently, not one overriding the other.
- **No-dependent no-op guard**: New Test #3 (`test_dependent_route_bias_zero_when_no_dependent`)
  directly guards against the class of bug this repo has already hit once
  (`_ADVENTURE_ROUTE_UTILITY_SCALE_NEVER_WINS_TIER5`-adjacent: a term that's silently always-on or
  mis-defaulted). It also indirectly guards the "dead mechanic" risk flagged in
  investigation.md (`faction_directives` never being threaded into the live call path) — if the
  bias term is implemented as a new optional parameter instead of reading off `entity` directly,
  this test (called through `AdventureRouteScorer.score()` directly, bypassing the live call path)
  would still pass while production usage silently never exercises it; pair this test with a
  direct read of `src/ai/goals/adventure_scorer.py`'s live call site during Verify to confirm the
  new field/param is actually reached, not just unit-testable in isolation.
- **Plan-advance / memory-adjustment independence guard**: `tests/unit/domains/adventure/test_scoring_plan_bonus.py`
  passing unmodified after this change is itself an anti-drift guard — plan-advance bonus math
  (`baseline + 1.5` assertions) would break if the new term were accidentally inserted before the
  `plan_advance_bonus` computation or altered the `round(max(0.0, ...))` clamp point.
  `test_existing_hero_quest_bonus_still_applies` / `test_existing_warrior_mage_bonus_still_applies`
  in the same file guard the §8 multiplicative terms similarly.
  In test_dependent_route_bias_lowers_risky_route_score, i.e New Test #1's assertions themselves must
  use the same style: compute a `baseline` score without a dependent and assert
  `abs(result.score - (baseline.score - expected_delta)) < 0.01`, not a hardcoded absolute score,
  so the guard survives unrelated future changes to `benefit`/`risk` inputs used in the fixture.
- **Tier-5 competition ceiling guard**: `tests/architecture/test_adventure_route_score_max_unchanged.py`
  run as part of every scoped verification catches any accidental widening of the new bias term's
  magnitude into territory that would require touching the pinned normalization constants.
- **Durable-state direct-mutation guard**: if a new `LifecycleComponent` field is added, New Test #5's
  write-path test must assert the field is unreachable except through
  `LifecycleUpdate.<field>_set` → `LifecyclePatch.apply()` — following the existing convention in
  `test_lifecycle.py` that already guards `heir_entity_id`/the birth-record fields this way. This
  catches any accidental direct mutation of the frozen `EntityState`/`LifecycleComponent`, which
  CLAUDE.md's Durable State Rule and Core Boundaries forbid.

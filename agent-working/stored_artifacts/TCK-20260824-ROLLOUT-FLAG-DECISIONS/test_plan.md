---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260824-ROLLOUT-FLAG-DECISIONS
artifact_type: test_plan
tags: [feature-flags]
---

# Test Plan — TCK-20260824-ROLLOUT-FLAG-DECISIONS

## Normal Flow
- `tests/unit/config/test_phase10_feature_flags.py` -- full suite, including the
  `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist test, after adding the 2 new entries.
- `FeatureFlagManager().is_enabled("ENABLE_BELIEF_ASSIMILATION")` and
  `.is_enabled("ENABLE_SOCIAL_COOPERATION")` both `True` by default, no override needed.

## Edge Cases / Regression
- The allowlist test must still reject a hypothetical non-allowlisted flag defaulting to `ON` --
  confirms the mechanism itself, not just the two new entries, per
  `TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE`'s own dedicated isolated test for this.
- `tests/perf/test_phase10_integrated_enhanced_stack_budget.py` -- must still pass after
  `RolloutProfileManager` is removed; read this test first to determine whether it needs editing
  or is fully removable itself.
- Broader corpus/engine sanity: with 2 more phases now defaulting to run
  (`information_belief`/social-cooperation-adjacent phases, per whichever real phase each flag
  gates), confirm no existing test asserting a specific tick-budget/phase-count baseline breaks.

## Failure Modes
- If flipping either flag ON causes any currently-passing test to fail, that is new, real
  information the decision must account for -- not something to route around by reverting to OFF
  without investigating why (the corpus-profile evidence says these are safe; a real regression
  here would mean that evidence has an unaccounted-for gap, worth surfacing, not hiding).

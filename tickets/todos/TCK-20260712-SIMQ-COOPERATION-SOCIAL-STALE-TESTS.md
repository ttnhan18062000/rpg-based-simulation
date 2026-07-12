---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS
phase: open
date: 2026-07-12
tags: [simulation-quality]
---

# TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS

## Title
3 pre-existing test failures in the cooperation/social regression surface — stale assertions,
not caused by SOCIAL-pillar activation

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Discovered while running `TCK-20260710-SIMQ-DEPTH-SOCIAL`'s required Step 6 full regression pass
(the exact `tests/unit/social/`, `tests/integration/scenarios/test_phase7_social_cooperation_
scenarios.py`, `tests/perf/test_phase7_social_cooperation_budget.py` commands from that ticket's
own `test_plan.md`). All 3 failures were confirmed **pre-existing and unrelated** to that ticket's
profile-YAML-only changes via `git stash` A/B testing (identical failures with the ticket's diff
stashed out).

1. `tests/unit/social/test_group_lifecycle_fields.py::test_group_canonical_dict_has_no_missing_keys`
   — `GroupSystem.to_canonical_dict()` now emits an extra `composition_score` key not present in
   the test's `EXPECTED_KEYS` set. Looks like a field was added to the canonical dict without
   updating this test's allowlist.

2. `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py::
   test_scenario_7_1_risky_objective_creates_help_request` and `::test_scenario_7_2_no_good_
   partner_causes_defer` — both fail with `AttributeError: 'str' object has no attribute
   'selected_posture'`. Root cause: `src/domains/cooperation/phase.py:139` intentionally stores
   `decision.selected_posture.value if hasattr(...) else str(decision.selected_posture)` (a plain
   string) into `property_updates["last_cooperation_decision"]` — this is the already-shipped fix
   for the non-serializable-object durable-state bug documented in
   `stored_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/`. These two tests were written against
   the pre-fix shape and still assert `decision.selected_posture == CooperationPosture.X` on what
   is now a bare string — the test assertions were never updated when the serialization fix
   landed.

3. `tests/perf/test_phase7_social_cooperation_budget.py::
   test_cooperation_phase_performance_budget_100_entities` — intermittently exceeds its 25.0ms
   budget (observed 27.8ms in one run, passed in another, same code both times). Appears to be
   VM-load-dependent flakiness rather than a real regression; worth a second look if it recurs
   with a wider margin or a retry/percentile-based assertion.

## Scope
- Update `test_group_lifecycle_fields.py`'s `EXPECTED_KEYS` to include `composition_score` (after
  confirming the field is intentional durable state, not a stray leak) or remove the field from
  `to_canonical_dict()` if it was accidental.
- Update the 2 scenario-test assertions in `test_phase7_social_cooperation_scenarios.py` to check
  the string/enum-value form of `last_cooperation_decision` instead of a `.selected_posture`
  attribute, matching the intentional serialization fix.
- Investigate whether the perf budget test needs a wider margin or a less load-sensitive
  measurement approach.

## Out of Scope
- Any change to `src/domains/cooperation/phase.py`'s serialization behavior itself — it is correct
  and intentional; only the stale test assertions need updating.
- Any change to `src/systems/world_systems/groups.py` unless investigation shows
  `composition_score` is an unintended leak rather than a real field.

## Acceptance Criteria
- [ ] All 3 tests pass (or the perf test's flakiness is resolved with a documented margin).
- [ ] Root cause of `composition_score`'s presence (intentional vs. leak) is documented.

## Related Tickets
- `TCK-20260710-SIMQ-DEPTH-SOCIAL` (done) — discovered these failures during its Step 6 regression
  pass; did not fix them (out of scope for a profile-YAML-only ticket; confirmed unrelated via
  `git stash` A/B test).
- `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO` (done) — source of the intentional serialization fix that
  `test_phase7_social_cooperation_scenarios.py` was never updated to match.

## Related Docs
None yet.

## Related Stored Artifacts
None yet — filed directly from a sibling ticket's Verify-phase finding, hotfix tier.

## Related Code Areas
- `tests/unit/social/test_group_lifecycle_fields.py`
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`
- `tests/perf/test_phase7_social_cooperation_budget.py`
- `src/domains/cooperation/phase.py:139` (reference only — not to be changed)
- `src/systems/world_systems/groups.py` (`to_canonical_dict()` — investigate only)

## Assumptions / Open Questions
- Whether `composition_score` is intentional durable state or an accidental leak is not yet
  determined — flagged for Investigate.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

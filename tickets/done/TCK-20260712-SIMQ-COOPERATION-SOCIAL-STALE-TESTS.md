---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS
phase: done
date: 2026-07-12
tags: [simulation-quality]
---

# TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS

## Title
3 pre-existing test failures in the cooperation/social regression surface — stale assertions,
not caused by SOCIAL-pillar activation

## Status
DONE

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
- [x] All 3 tests pass (or the perf test's flakiness is resolved with a documented margin).
- [x] Root cause of `composition_score`'s presence (intentional vs. leak) is documented.

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
1. **`composition_score` — confirmed intentional durable state, not a leak.** It's a typed field
   on `src/core/state.py:571` (`composition_score: float = 0.0  # PartyCompositionScorer result at
   formation (SOC-232)`), set by `src/systems/world_systems/groups.py:322` from
   `PartyCompositionScorer.score()` (`src/systems/social_systems/party_composition.py`), and
   already cited by parity ledger entry `SOC-232` (`docs/parity_ledger/social_narrative.yaml`).
   Added `composition_score` to `test_group_lifecycle_fields.py`'s `EXPECTED_KEYS` set with a
   citation comment — no `src/` change needed.
2. **Scenario test assertions updated** to match the already-shipped serialization fix
   (`src/domains/cooperation/phase.py:139`, untouched): `last_cooperation_decision` is now asserted
   as `CooperationPosture.X.value` (a plain string) instead of a `.selected_posture` attribute
   access on a non-existent object. The dropped `decision.selected_partner_id == 2` assertion in
   `test_scenario_7_1` was replaced with an equivalent check on
   `a_up.strategic.contracts_add_or_update[0].target_id == 2` — verified this is a faithful
   equivalent, not a loosened check: `src/domains/cooperation/services.py:149,174` shows the
   contract's `target_id` is derived directly from `decision.selected_partner_id`
   (`partner_id = decision.selected_partner_id` then `target_id=partner_id`).
3. **Perf budget test** switched from a single-sample average (`t_duration`) to a
   `statistics.median` over the same 20 iterations, with per-sample values included in the
   assertion failure message for diagnosability. Re-run independently 3 times after the fix:
   medians of 17.21ms/16.96ms/16.94ms, comfortably inside the 25.0ms budget with real margin
   (individual sample outliers up to 24.06ms no longer fail the run, matching the ticket's own
   suggested fix — "a retry/percentile-based assertion").

## Test Summary
- `pytest tests/unit/social/ tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py
  tests/perf/test_phase7_social_cooperation_budget.py -q` → 191 passed (previously 3 failing)
- Perf test re-run independently 3 times to confirm stability post-fix: all passed, medians
  16.94-17.21ms (budget: 25.0ms)

## Files Changed
- `tests/unit/social/test_group_lifecycle_fields.py`
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`
- `tests/perf/test_phase7_social_cooperation_budget.py`

## Completion Summary
Fixed all 3 pre-existing, unrelated test failures found during `TCK-20260710-SIMQ-DEPTH-SOCIAL`'s
regression pass. `composition_score` confirmed as intentional typed durable state (SOC-232,
`PartyCompositionScorer`), added to the canonical-dict test's allowlist. The 2 scenario test
assertions were updated to match the already-shipped `last_cooperation_decision` serialization fix
(string, not object) — no production code changed, `src/domains/cooperation/phase.py` untouched
per Out of Scope. The perf budget test's flakiness was resolved with a median-based measurement
across the same 20 samples, verified stable across 3 independent re-runs. All 191 tests in the
scoped regression surface pass.

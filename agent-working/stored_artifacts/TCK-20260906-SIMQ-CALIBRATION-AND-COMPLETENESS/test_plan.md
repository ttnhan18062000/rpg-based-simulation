---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS
date: 2026-09-06
---

# Test Plan: TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS

## Normal Flow
- `route_new_query_isolated_calibration.py` runs clean, prints before/after scores, asserts a real
  non-flat delta (0.0 -> 10.0) and `event_count == 1` for the after case.
- `completeness_check.py` runs clean, reports `gap_count` matching only the pre-disclosed
  governance/doc-fix exceptions (7 bare-`0/10` rows), never an unrecognized pillar name or count
  mismatch.

## Regression
- Full `tests/simulation_quality/` suite still passes (no production code changed by this ticket,
  but re-run to confirm the doc-only changes and the new proof/check scripts under
  `staging_artifacts/` introduce no accidental collateral — e.g. neither script should be
  auto-collected by pytest since neither is named `test_*`).
- `tests/simulation_quality/test_grade_regression.py` specifically — confirms
  `test_urban_political_selfmodel_execution_isolated_grade_anchor`'s existing "does not fire" finding
  is still consistent with this ticket's own fresh reproduction (no drift in either direction).

## Edge Cases
- The isolated proof's "before" case (0 events) must produce grade `C` (the documented zero-event
  default), not a spurious non-C grade from stale hub state — verified by using a fresh `QualityHub`
  instance per call, not a shared one.
- The completeness check must not silently swallow a genuinely malformed row (e.g. a future edit
  that breaks the `N/10` cell format) — `unparseable Pillar Reach cell` is a distinct, visible issue
  type from `unrecognized pillar name(s)`/`count mismatch`, so a real future break is caught, not
  misclassified as one of the known governance/doc-fix exceptions.

## Failure Modes
- If a future run of `route_new_query_isolated_calibration.py` ever shows `after["raw_score"] ==
  before["raw_score"]` (e.g. a scoring-weights regression zeroing the delta), its own `assert`
  fails loudly — not silently reported as PASS.
- If `completeness_check.py`'s `gap_count` ever exceeds 7 with a NEW idea number not in
  `{8,9,15,16,17,18,19}`, that is a real, previously-undisclosed gap requiring investigation before
  this ticket (or any re-run of it) can be considered complete — not something to reflexively add to
  the disclosed-exception set without checking.

## Non-Goals
- No new pytest test file is added — the two scripts are one-off verification/proof tooling for this
  ticket's own evidence trail (matching the ticket's Out-of-Scope: verifies, does not extend the rule
  set), migrated to `stored_artifacts/` at Finalize as citable evidence, not ongoing CI-gated tests.

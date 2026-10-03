---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE
artifact_type: test_plan
tags: [simulation-quality, agency, cognition, stasis, calibration, bug]
---

# Test Plan: TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE

## Scope of Testing

Covers the `AgencyScorer` stasis-penalty formula fix (`src/simulation_quality/scorers/agency.py`,
`et == "defer_with_reason"` branch, lines 87-112) determined in `investigation.md` §3. Decision
logic (`AdventureDecisionPhase`/`AdventureRouteGenerator`/`AdventureDecisionService`) is
**not** being changed — those tests are smoke-checked only, not modified, per investigation §3's
conclusion that the fix belongs in scoring, not decision logic.

## Normal Flow

- `AgencyScorer.score()` on `defer_with_reason` still returns `defer_idle` base delta
  (`-1.0`) for an entity's first few consecutive defers, before any gate/cap engages —
  unchanged behavior, regression-checked against `TestDefer::test_defer_base_delta`.
- `route_selected`/`action_executed`/`project_completed`/`route_family_first_use` scoring paths
  are untouched by this fix — regression-checked (no code path change), existing
  `TestActionExecuted`, `TestRouteFamily`, `TestRouteSelected`, `TestProjectCompleted` in
  `tests/simulation_quality/test_agency_scorer.py` must still pass unmodified.
- `simq_routing_test` seed42 and seed123 (500t) continue to grade `AGENCY=A` after the fix
  (they never hit the stasis path meaningfully today) — re-run both as a non-regression check.

## Edge Cases

- **Single entity, sustained defer streak (the exact seed456/entity-23 scenario):** an entity
  that defers every tick for 500 consecutive ticks must produce a *bounded* per-event penalty
  (whatever cap/ceiling mechanism Plan/Implementation choose) rather than growing without limit.
  This is the core regression case for this ticket — new test required.
- **Mixed population — one deferring entity, others active:** entity A defers every tick while
  entities B/C emit `action_executed`/`route_selected` regularly (mirrors the real seed456
  population of 23/24/25). If the fix moves to per-entity attribution, confirm B/C's activity no
  longer dilutes or inflates A's own streak count (today, the population-shared window means A's
  computed `defer_count` depends on how often B/C happen to act — this coupling should be
  removed or explicitly justified if kept).
- **Streak resets on a non-defer action:** if per-entity tracking is added, an entity that defers
  for `gate+N` ticks then successfully takes a non-defer action must have its streak counter reset
  to 0 — the next defer (if any) should NOT resume from the pre-reset streak length. New test
  required if this state is added.
- **Exactly at the gate boundary:** `defer_count == stasis_gate_ticks` (currently 5) must NOT
  trigger `stasis_N` (existing `test_stasis_no_fire_before_gate` semantics — confirm still holds
  under whatever counting mechanism replaces/augments `window_tag_counts`).
- **Multiple simultaneously-deferring entities:** if attribution moves per-entity, two entities
  both independently stuck (each with their own streak) should each accrue their own bounded
  penalty, not share/interfere with each other's count.

## Failure Modes

- **Formula must not silently reintroduce unbounded growth**: a test should assert that for an
  arbitrarily long defer streak (e.g. simulate 2000 consecutive `defer_with_reason` calls for one
  entity), the per-event delta and the cumulative contribution to `raw_score` stay within an
  explicit, named bound (whatever constant Plan/Implementation choose) — not just "smaller than
  before" but actually bounded/asymptotic.
- **`population_stasis` one-shot path (`agency.py:92-104`, `self._pop_stasis_fired`) must remain
  unaffected** — this is a separate mechanism (population-wide zero-action detection) from the
  per-defer-event `stasis_N` penalty and should not be touched by this fix; existing
  `test_population_stasis_fires_when_no_actions` / `test_population_stasis_fires_only_once` must
  keep passing unmodified.
- **`ScoringContext`/`window_tag_counts` shape must not change** if the fix is contained inside
  `AgencyScorer`'s own instance state (recommended in investigation §4) — a regression test should
  confirm other pillars' scorers (e.g. `CognitionScorer`, `CombatScorer`) are unaffected, e.g. by
  running `tests/simulation_quality/test_quality_hub_integration.py` unmodified and confirming no
  new failures.
- **`grade_anchors.json` anchor-band regression must correctly reflect the new, real grade** —
  `simq_routing_test_seed456_500t.AGENCY` must be updated from placeholder `"D"` to the true
  post-fix grade (likely `>= B` per AC6), and `test_grade_within_anchor_band[simq_routing_test_seed456_500t]`
  (`tests/simulation_quality/test_grade_regression.py`) must pass with real (not placeholder)
  calibration data present.

## Regression-Prone Paths

- `tests/simulation_quality/test_agency_scorer.py::TestDefer` — all four existing tests
  (`test_stasis_no_fire_before_gate`, `test_stasis_fires_after_gate`,
  `test_population_stasis_fires_when_no_actions`, `test_population_stasis_fires_only_once`) —
  the `stasis_fires_after_gate` test's hard-coded linear formula assertion is expected to change;
  the other three should NOT need behavioral changes (only re-verification).
- `tests/simulation_quality/test_timegate_penalties.py` — `test_stasis_N_timegate_fires_after_gate`,
  `test_stasis_N_timegate_not_before_gate`, `test_stasis_N_timegate_accumulates_linearly` (name
  itself will likely need renaming/rewriting to assert bounded, not linear, accumulation),
  `test_population_stasis_timegate_fires_at_gate`.
- `tests/simulation_quality/test_grade_regression.py` — full `FAST_ANCHOR_KEYS` sweep, at minimum
  the three `simq_routing_test_seed*` keys, to confirm seed42/123 unaffected and seed456 now
  passes with its real grade as anchor.
- `tests/simulation_quality/test_quality_hub_integration.py` — full pillar-integration smoke test,
  to catch any accidental cross-pillar leakage if the fix touches shared `ScoringContext`
  construction (`quality_hub.py:170-176`) instead of staying contained in `AgencyScorer`.
- Decision-logic tests (smoke-check only, no expected behavior change):
  `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`,
  `tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`,
  `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`,
  `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`,
  `tests/perf/test_phase3_adventure_decision_budget.py`,
  `tests/unit/observability/test_event_extractor_agency.py`,
  `tests/unit/observability/test_event_extractor_agency2.py`,
  `tests/unit/social/test_party_agency.py`.

## New Regression Test(s) Required (AC: "Add a regression test proving this specific
stasis-collapse scenario doesn't recur")

At minimum, add a test (likely in `tests/simulation_quality/test_agency_scorer.py::TestDefer` or
a new `TestStasisBounding` class) that:
1. Simulates a long consecutive defer streak for a single entity (e.g. 500+ calls to
   `AgencyScorer.score()` with `defer_with_reason` events for the same `entity_id`, driving
   `context`/internal state exactly as a 500-tick calibration run would).
2. Asserts the per-event delta at the tail of the streak is bounded by an explicit, named
   constant/formula (not "less negative than the old buggy value" — an explicit ceiling).
3. Asserts the cumulative `raw_score` contribution from this single entity's streak, over the
   full simulated run, does not push the pillar below some explicit reasonable floor (e.g. stays
   within a bounded multiple of the `D` grade threshold, not 345x past it).

Additionally, an **end-to-end regression** re-running `simq_routing_test` seed456 (500t)
calibration post-fix and asserting `AGENCY grade in ("S","A","B")` (matching AC6's `>= B`
requirement) should be added or confirmed via the existing `test_grade_regression.py` anchor
mechanism once `grade_anchors.json` is updated.

## Out of Scope for Testing

- Any test asserting new behavior in `AdventureRouteGenerator`/`FORM_PARTY` sociability threshold
  or `ResourceOpportunityProvider`'s region-tag matching — decision logic is not being changed by
  this ticket (investigation §3). If a follow-up ticket addresses the world-content gap (OQ-2),
  its own test plan covers that.
- Full-suite runs (`pytest tests/`) — scope test execution to
  `tests/simulation_quality/` and the adventure/observability smoke-check paths listed above, per
  project testing rule (do not run the entire suite).

## Test Execution Command Reference

```
pytest tests/simulation_quality/test_agency_scorer.py -v
pytest tests/simulation_quality/test_timegate_penalties.py -v
pytest tests/simulation_quality/test_grade_regression.py -v -m "not slow"
pytest tests/simulation_quality/test_quality_hub_integration.py -v
pytest tests/integration/domains/adventure/ tests/unit/domains/adventure/ tests/perf/test_phase3_adventure_decision_budget.py -v
pytest tests/unit/observability/test_event_extractor_agency.py tests/unit/observability/test_event_extractor_agency2.py tests/unit/social/test_party_agency.py -v

# End-to-end re-verification after fix:
rm -rf data/calibration/simq_routing_test_seed456_500t/
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 456 --name simq_routing_test
# confirm AGENCY grade in quality_report.json is >= B

make evaluate --dry-run   # AC: must exit 0
```

---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-TIMEGATE
phase: open
date: 2026-06-30
tags: [simulation-quality, calibration, testing, regression]
---

# TCK-20260630-SIMQ-TIMEGATE

## Title
1000-tick calibration and time-gate penalty verification

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Current calibrations run 200 ticks. Several scoring rules only fire after a tick threshold
(e.g., `zero_harvest_after_tick=100`, `zero_crafting_after_tick=200`, `all_level_1=300`,
`zero_calamity_events=500+`). No test currently verifies these penalties actually fire.
This ticket runs extended calibrations and adds tests that confirm time-gate behavior.

## Scope
1. Run 1000-tick calibrations on sandbox_world and dungeon_crawl (requires TCK-20260630-SIMQ-CALFIX)
2. Run 500-tick calibration on simq_routing_test (requires TCK-20260630-SIMQ-ROUTING-TEST)
3. Record and commit calibration results to `data/calibration/`
4. Add time-gate tests to `tests/simulation_quality/`:
   - ECONOMY: verify `zero_harvest` penalty fires after tick 100 with no harvest events
   - PROGRESSION: verify `progression_frozen` penalty fires after 200-tick window with 0 XP
   - PROGRESSION: verify `all_level_1` penalty fires at tick 300 when no level-ups emitted
   - NARRATIVE: verify `quest_system_dormant` fires after tick 200 with zero quest starts
   - AGENCY: verify `stasis_N` accumulates correctly for N>5 consecutive defer ticks

## Out of Scope
- Fixing the underlying simulation behaviors that cause zero-signal pillars
- Changing time-gate threshold values (calibration only)

## Acceptance Criteria
- [ ] sandbox_world 1000-tick: ECONOMY grade ≤ C by tick 300 (zero-harvest penalty active)
- [ ] dungeon_crawl 1000-tick: NARRATIVE grade ≥ B (quest density sustains score)
- [ ] PROGRESSION: `progression_frozen` penalty test passes (time-gate fires exactly at threshold)
- [ ] AGENCY: `stasis_N` accumulation test passes (per-tick -3 delta beyond tick 5)
- [ ] `pytest tests/simulation_quality/ -k timegate` passes (new tests added)
- [ ] Calibration results committed under `data/calibration/{world}_seed{seed}_1000t/`

## Related Tickets
- TCK-20260630-SIMQ-CALFIX (prerequisite — world loading needed for meaningful long runs)
- TCK-20260630-SIMQ-ROUTING-TEST (prerequisite for simq_routing_test 500-tick run)
- TCK-20260630-SIMQ-ANCHORS (long-run grades added to regression anchors)

## Related Docs
- `docs/plans/simq_deep_audit_plan.md` §5 Track C
- `docs/simulation_quality/quality_scoring_contract.md` §5 (time-gate rules per pillar)
- `config/simulation_quality/detection_params.yaml` (time-gate tick values)

## Related Code Areas
- `src/simulation_quality/scorers/*.py` — all time-gated scoring rules
- `config/simulation_quality/detection_params.yaml` — `stasis_gate_ticks`, `zero_harvest_tick`, etc.
- `tests/simulation_quality/test_grade_regression.py` — extended with long-run anchors
- `tools/calibrate_simq.py` — run at 1000 ticks

## Assumptions / Open Questions
- What tick value is `zero_harvest_after_tick` set to in detection_params.yaml? Must verify
  before writing the test (read from config, not hardcoded in test).
- Long-run calibrations (~30s per 200 ticks) will take ~150s for 1000 ticks. Mark as slow.

## Implementation Notes
- Time-gate tests should inject events directly (not run full simulation) and verify
  the scorer applies the penalty at the correct tick, not before.
- Use `@pytest.mark.slow` so they're excluded from default test suite runs.
- Calibration data commitment: add to `data/calibration/` and include in git.

## Test Summary
- Unit tests: per-pillar time-gate verification (inject events, control tick count)
- Integration: 1000-tick calibration output matches expected grade trajectory
- Regression: grades added to TCK-20260630-SIMQ-ANCHORS fixture after this ticket

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)

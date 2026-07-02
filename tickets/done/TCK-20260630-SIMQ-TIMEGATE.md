---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-TIMEGATE
phase: done
date: 2026-06-30
tags: [simulation-quality, calibration, testing, regression]
---

# TCK-20260630-SIMQ-TIMEGATE

## Title
1000-tick calibration and time-gate penalty verification

## Status
DONE

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
- [x] sandbox_world 1000-tick: ECONOMY grade ≤ C by tick 300 (zero-harvest penalty active) — ECONOMY grade=C ✓
- [x] dungeon_crawl 1000-tick: NARRATIVE grade ≥ B (quest density sustains score) — NARRATIVE grade=B ✓
- [x] PROGRESSION: `progression_frozen` penalty test passes (time-gate fires exactly at threshold) ✓
- [x] AGENCY: `stasis_N` accumulation test passes (per-tick -3 delta beyond tick 5) ✓
- [x] `pytest tests/simulation_quality/ -k timegate` passes (27 tests, new file) ✓
- [x] Calibration results committed under `data/calibration/{world}_seed{seed}_1000t/` ✓

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
All resolved during investigation.

## Implementation Notes
- Time-gate tests inject events directly (no full simulation) — 27 tests all pass in 0.16s
- `simq_routing_test_seed42_500t` already existed from ROUTING-TEST ticket — skipped re-run
- sandbox_world 1000t (126s): ECONOMY=C (0 events, no economy event bus coverage), NARRATIVE=A
- dungeon_crawl 1000t (128s): NARRATIVE=B (24 events), COMBAT=B, WORLD=B
- Parity ledger updated: INFRA-237 (Agency), INFRA-243 (Progression), INFRA-247 (Narrative)
  — all now reference test_timegate_penalties.py classes in test_path

## Test Summary
- 27 time-gate unit tests in `tests/simulation_quality/test_timegate_penalties.py`
- 4 pillars: ECONOMY (9), PROGRESSION (6), NARRATIVE (6), AGENCY (6)
- Coverage per gate: fires-at-threshold, not-before-threshold, fires-once
- Full non-slow SimQ suite: 336 passed, 11 deselected (slow)

## Files Changed
- `tests/simulation_quality/test_timegate_penalties.py` — new (27 tests)
- `data/calibration/sandbox_world_seed42_1000t/` — new calibration run
- `data/calibration/dungeon_crawl_seed42_1000t/` — new calibration run
- `docs/parity_ledger/infrastructure.yaml` — INFRA-237, 243, 247 test_path updated
- `staging_artifacts/TCK-20260630-SIMQ-TIMEGATE/` → `stored_artifacts/`

## Completion Summary
Added 27 per-pillar time-gate unit tests to `test_timegate_penalties.py`, covering all 8
time-gate rules across ECONOMY, PROGRESSION, NARRATIVE, and AGENCY pillars. Tests verify:
(1) penalty fires at threshold+1, (2) no fire before threshold, (3) one-shot flag behavior.
Ran 1000-tick calibrations for sandbox_world (ECONOMY=C, NARRATIVE=A, overall=B) and
dungeon_crawl (NARRATIVE=B, COMBAT=B, WORLD=B, overall=B) — both meeting acceptance criteria.
simq_routing_test 500t already present. Parity ledger updated for 3 entries.

---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1
artifact_type: test_plan
phase: done
date: 2026-10-24
tags: [testing, regression, simulation-quality]
---

# Test plan

- `tests/unit/tools` (1035 passed): known-reds registry lint of the new slow entries; `test_slow_regression_report.py` now pins "no corpus anchor has an owner" and "each held key is owned by the held-rows ticket, a neighbouring key is not"; `test_simq_pillar_compare.py` pins every committed anchor as a well-formed ok or no-data (below_min_events) anchor.
- `tests/simulation_quality` anchor tests (fixture structure, entry count, empty override table, audit-mode) pass.
- AC5 (the first scheduled slow run after the merge has no anchor red outside the held rows) is checked by testing-planner after the merge.

## Proof Plan

- level: unit plus the scheduled slow lane
- proof kind: recorded measurement (two identical isolated audit_mode runs per key) and registry tests
- oracle source: rpg-planner's ruling of 2026-10-24 on the 536 moved rows
- expected effect: 500 rows re-anchored, 36 held and owned; no anchor red outside the held rows in the next slow run
- selected commands: `pytest tests/unit/tools -q`, `pytest tests/simulation_quality -q -k anchor`

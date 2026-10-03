---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260924-DELIVERY-COST-MEASUREMENT
date: 2026-09-24
tags: [delivery, agent-monitoring, benchmarking]
---

# Test Plan — TCK-20260924-DELIVERY-COST-MEASUREMENT

`tests/tools/test_delivery_cost_measurement.py`, one test per Acceptance Criterion (AC1–AC8), plus:

## Regression-prone paths
- `test_gh_subcommand_extension_does_not_change_existing_bash_command_mix_behavior`: run
  `bash_command_mix.py`'s own existing test suite after the extension lands, unchanged.
- `test_gh_unparseable_rows_counted_not_dropped`: a `gh` row with no second token is counted in
  `gh_unparseable_count`, not silently excluded from the total.
- `test_no_write_side_effect`: mirrors the other delivery-tool tests.

## Full regression check
`pytest tests/tools/test_delivery_cost_measurement.py tests/tools/test_bash_command_mix.py -v`,
then `pytest tests/tools/ -m "not slow"`.

## Recorded in `## Test Summary` once run
Exact commands, pass/fail counts, and the real `origin/main` W30–W39 baseline run's output.

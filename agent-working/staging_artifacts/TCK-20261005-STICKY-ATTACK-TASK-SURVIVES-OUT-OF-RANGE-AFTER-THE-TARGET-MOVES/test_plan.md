---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

No behaviour changes, so no new tests and no disabling control. Verification is the measurement itself:

- `probes/measure.sh`: 4 worlds x 2 runs, 2000 ticks, `audit_mode=True`, budget disabled. Matched pairs, so values.
- Positive control for the instrument: `frontier_living_world` records 2 `OUT_OF_RANGE` verdicts and 1 repeat, so the
  probe can see the event it counts. Worlds with 0 calls were not instrument failures: `dungeon_crawl` and
  `frontier_living_world` show the wrapper firing on the same code path.
- Regression scope: none (no source touched). The registry/frontmatter tests are run for the ticket and registry edits.

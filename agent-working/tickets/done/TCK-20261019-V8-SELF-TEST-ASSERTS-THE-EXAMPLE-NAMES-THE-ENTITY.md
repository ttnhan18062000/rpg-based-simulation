---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-V8-SELF-TEST-ASSERTS-THE-EXAMPLE-NAMES-THE-ENTITY
phase: done
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# TCK-20261019-V8-SELF-TEST-ASSERTS-THE-EXAMPLE-NAMES-THE-ENTITY

## Title
V8's gate self-test, case (a), asserts that the example names the unsourced entity, and the format doc drops its "not yet emitted" line.

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
#653 (7f115a3d4) landed V8's self-test. Case (a) checks only that an example mentions "unsourced", because rpg's `compute` emitted aggregate `{adds, count}` examples. That gap is recorded in TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK (AC4 note) and in `rpg_gate_baseline_format.md` ("Not yet emitted").

rpg's TCK-20261019-V8-UNSOURCED-ADD-EXAMPLES-NAME-THE-ENTITY (PR #658) emits the ruled shape `{entity_id, tick, kind_group, check: "unsourced"}`, which has no `site` key (testing-planner ruling, 2026-10-19). Once that is on main, the test and the doc catch up.

**UNBLOCKED 2026-10-19:** rpg's change landed on main in 5c9b84505 (the pre-v1 batch). `run_ledger.py` keeps `_unsourced_examples` (L181-182: `{entity_id, tick, kind_group, check: UNSOURCED}`, capped at `run_ledger.MAX_EXAMPLES` = 5). `rpg_gate_metrics._check_unsourced_adds` returns `ledger["unsourced_examples"]`. Read `MAX_EXAMPLES` from `src.observability.run_ledger`.

## Scope
1. `tests/simulation_quality/rpg_gate/test_v8_fires.py` case (a) asserts that an example equals `{"entity_id": 500, "tick": <the applied tick>, "kind_group": <kind_group of the added entity>, "check": "unsourced"}`, and that no example has a `site` key.
2. Case (f) asserts that the examples name 502 and 504, the two unsourced adds.
3. The example list is bounded: add a case that applies more unsourced adds than rpg's `MAX_EXAMPLES` and asserts that the count is exact while the example list is capped at `MAX_EXAMPLES`.
4. In `rpg_gate_baseline_format.md`, remove the "Not yet emitted" sentence and the sentence saying case (a) does not yet check the entity. Keep the shape line.

## Out of Scope
- Any change to `src/` (rpg's).
- Any change to V8 counts or pass/fail.

## Acceptance Criteria
- [x] AC1: cases (a) and (f) assert the entity id, tick, kind_group and `check`, and that there is no `site` key. They run on the real path, as before, with no hand-built tally and no skip.
- [x] AC2: the cap case passes against rpg's real `MAX_EXAMPLES`, read from rpg's module and not hard-coded.
- [x] AC3: the format doc has no "not yet emitted" text for V8.
- [x] AC4: the `test_v8_fires.py` cases and `tests/unit/observability/test_rpg_gate_metrics.py` pass.

## Related Tickets
- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK (done, #653)
- TCK-20261019-V8-UNSOURCED-ADD-EXAMPLES-NAME-THE-ENTITY (rpg, #658)
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK/

## Related Code Areas
- tests/simulation_quality/rpg_gate/test_v8_fires.py
- src/observability/run_ledger.py, src/observability/rpg_gate_metrics.py (read only)

## Assumptions / Open Questions
- rpg's field and constant names are those in #658 as merged. If they differ from this ticket, follow the merged code and note the difference.

## Implementation Notes
Case (a) now asserts the example equals `{entity_id, tick, kind_group, check: "unsourced"}` (tick = the applied tick, kind_group from `kind_group(entity)`) and that no example has a `site` key. Case (f) asserts the two examples for 502 (tick 3) and 504 (tick 4). A new cap case applies `MAX_EXAMPLES + 3` unsourced adds and asserts the violation count is exact and the example list is exactly `MAX_EXAMPLES` long, with `MAX_EXAMPLES` imported from `src.observability.run_ledger`. The format doc lost its "Not yet emitted" sentences; the shape line stays. rpg's merged names matched the ticket.

## Test Summary
`test_v8_fires.py` (8 cases), `tests/unit/observability/test_rpg_gate_metrics.py` and `test_run_ledger.py`: 44 passed. The format doc has no "not yet emitted" text.

## Files Changed
`tests/simulation_quality/rpg_gate/test_v8_fires.py`; `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`; this ticket.

## Completion Summary
The V8 self-test now checks that an unsourced add's example names the entity, its tick, kind group and the failed check, and that the example list is bounded while the count stays exact.

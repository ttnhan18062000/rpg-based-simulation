---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-V8-SELF-TEST-ASSERTS-THE-EXAMPLE-NAMES-THE-ENTITY
phase: open
date: 2026-10-19
tags: [testing, regression, simulation-quality]
---

# TCK-20261019-V8-SELF-TEST-ASSERTS-THE-EXAMPLE-NAMES-THE-ENTITY

## Title
V8's gate self-test, case (a), asserts that the example names the unsourced entity, and the format doc drops its "not yet emitted" line.

## Status
BLOCKED

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
#653 (7f115a3d4) landed V8's self-test. Case (a) checks only that an example mentions "unsourced", because rpg's `compute` emitted aggregate `{adds, count}` examples. That gap is recorded in TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK (AC4 note) and in `rpg_gate_baseline_format.md` ("Not yet emitted").

rpg's TCK-20261019-V8-UNSOURCED-ADD-EXAMPLES-NAME-THE-ENTITY (PR #658) emits the ruled shape `{entity_id, tick, kind_group, check: "unsourced"}`, which has no `site` key (testing-planner ruling, 2026-10-19). Once that is on main, the test and the doc catch up.

**BLOCKED until #658 is on main.** testing-planner dispatches this ticket then.

## Scope
1. `tests/simulation_quality/rpg_gate/test_v8_fires.py` case (a) asserts that an example equals `{"entity_id": 500, "tick": <the applied tick>, "kind_group": <kind_group of the added entity>, "check": "unsourced"}`, and that no example has a `site` key.
2. Case (f) asserts that the examples name 502 and 504, the two unsourced adds.
3. The example list is bounded: add a case that applies more unsourced adds than rpg's `MAX_EXAMPLES` and asserts that the count is exact while the example list is capped at `MAX_EXAMPLES`.
4. In `rpg_gate_baseline_format.md`, remove the "Not yet emitted" sentence and the sentence saying case (a) does not yet check the entity. Keep the shape line.

## Out of Scope
- Any change to `src/` (rpg's).
- Any change to V8 counts or pass/fail.

## Acceptance Criteria
- [ ] AC1: cases (a) and (f) assert the entity id, tick, kind_group and `check`, and that there is no `site` key. They run on the real path, as before, with no hand-built tally and no skip.
- [ ] AC2: the cap case passes against rpg's real `MAX_EXAMPLES`, read from rpg's module and not hard-coded.
- [ ] AC3: the format doc has no "not yet emitted" text for V8.
- [ ] AC4: the `test_v8_fires.py` cases and `tests/unit/observability/test_rpg_gate_metrics.py` pass.

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
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)

---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE
phase: open
date: 2026-10-09
tags: [testing, regression]
---

# TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE

## Title
The known-reds registry becomes a shared module, so the slow suite and the rpg gate report use one schema, matcher and lint

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Child 1 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. `tools/test_architecture/slow_known_reds.yaml` already gives each failing slow test an owner, a ticket, added_on, expires_on and a kind; an unowned or expired red fails the run; a stale mapping is listed. The rpg gate report needs the same ownership model for metric ids (a VALIDITY fail needs an owner ticket; a DRIFT needs a trace ticket). Generalise, do not copy.

## Scope
1. Move the schema, the loader, the matcher (pattern to failing id, first match wins, shadowing rejected) and the lint into a shared module (for example `tools/test_architecture/known_reds.py`).
2. `slow_regression_report.py` and its lint test use the module, with behaviour identical: same verdicts, the same rolling-issue output on the same JUnit input (a golden test over a recorded input).
3. A registry kind for metric ids: entries match `<metric_id>[:<group>]` patterns, and each carries a `state` it covers (`fail` or `drift`). A drift entry's ticket is a trace ticket. Same expiry rules.
4. A file for the gate registry (for example `tools/test_architecture/rpg_gate_known.yaml`), empty but linted.

## Out of Scope
- Changing any existing slow known-red entry, or the slow report's verdict rules.

## Acceptance Criteria
1. The slow report's output on a recorded JUnit fixture is byte-identical before and after.
2. The shared module's unit tests cover match, shadowing, expiry, stale mapping, and both registry kinds.
3. The lint runs on both registry files in the existing CI lane.
4. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/test_architecture/slow_known_reds.yaml`, `tools/test_architecture/slow_regression_report.py`, `tests/unit/tools/test_slow_regression_report.py`

## Assumptions / Open Questions
None.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)

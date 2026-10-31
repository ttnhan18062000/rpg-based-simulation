---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261031-N14-KNOWN-V3-ENTRY-RENEWED-TO-1130
phase: done
date: 2026-10-31
tags: [testing]
---

# TCK-20261031-N14-KNOWN-V3-ENTRY-RENEWED-TO-1130

## Title
The N14 known V3 gate entry is renewed from 2026-11-05 to 2026-11-30, with nothing else changed

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Owner renewal on #715: issuecomment-6541804604 item 2, corrected by issuecomment-6541833976 (one case, not three). rpg-planner asked for it; tools/test_architecture/ is testing's. The entry expires on 2026-11-05, so the PR must merge before then.

## Scope
In tools/test_architecture/rpg_gate_known.yaml, the V3 entry for TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT: expires_on "2026-11-05" becomes "2026-11-30".

## Out of Scope
- The entry's case (urban_political/44 entity 28) and note, which stay unchanged.
- Any other known entry, including the 12 SimQ held-row slow_known_reds re-dates (routed via rpg-planner-ubuntu).

## Acceptance Criteria
- [x] AC1: the yaml diff is exactly one line.
- [x] AC2: tests/unit/tools/test_known_reds.py, tests/unit/tools/test_rpg_gate_baseline.py and tests/static/test_ci_rpg_gate_workflow_shape.py pass.
- [x] AC3: the known-file lint passes on the real file.

## Related Tickets
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (owner of the entry, rpg-planner)
- TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- tools/test_architecture/rpg_gate_known.yaml

## Assumptions / Open Questions
- The candidate records known_file_sha256, so this edit changes the hash a later candidate records. That is expected and needs no baseline change.

## Implementation Notes

## Test Summary
`pytest tests/unit/tools/test_known_reds.py tests/unit/tools/test_rpg_gate_baseline.py tests/static/test_ci_rpg_gate_workflow_shape.py`: 137 passed. `lint_file(rpg_gate_known.yaml, RPG_GATE_SPEC)`: no problems.

## Files Changed
- tools/test_architecture/rpg_gate_known.yaml (one line)

## Completion Summary
expires_on moved to 2026-11-30 under #715 6541804604 item 2 and 6541833976. The case and note are unchanged.

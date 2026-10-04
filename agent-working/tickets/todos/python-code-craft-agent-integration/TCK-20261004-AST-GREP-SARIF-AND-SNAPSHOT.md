---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT
phase: open
date: 2026-10-04
tags: [architecture, delivery]
---

# TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT

## Title
M5 follow-up: ast-grep in the SARIF feedback and the snapshot metrics

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add ast-grep to `codebase/gates/sarif_feedback.py` and one count per rule (n3, n4, e3) to the snapshot metrics. Advisory; ast-grep flip (soak ends 2026-10-18) is untouched.

## Scope
- SARIF: also run `ast-grep scan --format sarif` with `codebase/rules/sgconfig.yml` on changed `src/` files; filter findings whose `(file, symbol, rule)` is an `ast_grep` registry row within ceiling; missing binary is exit 2 with a summary line and warning, never a silent pass
- Snapshot: add `ast_grep` to `OFFLINE_TOOLS`; add `n3`, `n4`, `e3` dimensions to `compute_craft_metrics`; existing dimensions unchanged on the same tree (test before/after); check history schema accepts new keys, additive change documented if needed
- Tests: new, grandfathered and missing-binary SARIF cases; metrics with and without findings; existing dimensions unchanged

## Out of Scope
- Making ast-grep blocking
- New rules

## Acceptance Criteria
- [ ] SARIF reports a new ast-grep finding and omits a grandfathered one
- [ ] Missing binary gives exit 2 with a warning
- [ ] Three new snapshot dimensions; existing values identical on the fixture
- [ ] No threshold, tool version or registry row changed
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
- TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING

## Related Docs
- docs/plans/codebase_health/python_code_craft_m6_agent_integration_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/gates/sarif_feedback.py
- codebase/health/scan.py
- codebase/health/metrics.py
- .github/workflows/test.yml

## Assumptions / Open Questions
- Owner decision 8.17 (2026-10-04): codebase implements M6 although `.claude/**` is agent-working's territory; the PR body names agent-working as owner of those paths
- Nothing here blocks a PR or tool call; M4 and M5 soaks are not disturbed

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-CODEBASE-HEALTH-HISTORY-MOVE
phase: inprogress
date: 2026-10-04
tags: [delivery]
---

# TCK-20261004-CODEBASE-HEALTH-HISTORY-MOVE

## Title
Move the codebase-health snapshot history from agent-working/agent-monitoring/ to codebase/

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
The codebase-domain-root decision (`docs/plans/codebase_health/codebase_domain_root.md`) left
`agent-working/agent-monitoring/codebase_health_history.jsonl` in agent-working's tree until agent-working agreed.
agent-working-planner agreed on 2026-10-04 in the handoff PR #322 (`docs/plans/codebase_health/handoffs/handoff_to_agent_working.md`,
Responses item 3), with conditions. The file is written only by `codebase/reports/codebase_health_snapshot.py`.

## Scope
- `git mv agent-working/agent-monitoring/codebase_health_history.jsonl codebase/<dir>/codebase_health_history.jsonl`
  (choose `codebase/reports/` or a `codebase/history/` folder; record why). Content byte-identical, history kept.
- Same commit: `DEFAULT_HISTORY_PATH` in `codebase/reports/codebase_health_snapshot.py` (line 104 on `c049b9d65`),
  the `codebase-health-snapshot` Makefile help/recipe line (line 471), the schema doc's **File path** line and its
  append-only paragraph (`docs/agent-monitoring/codebase_health_history_schema.md` lines 20, 65), `codebase/README.md`,
  `docs/plans/codebase_health/codebase_domain_root.md`.
- Decide whether the schema doc moves next to the file (agent-working allows it); if it moves, regenerate
  `docs/REGISTRY.yaml` and fix links.
- Check that the frozen-history path map still resolves the old path (agent-working's condition), and dry-run
  `make agent-monitoring-close-week` once to confirm it does not touch the file.
- Tests: whatever pins the default path (grep `codebase_health_history` under `tests/`); add one asserting the new
  default path.

## Out of Scope
- Snapshot schema or content changes; rewriting history lines
- Any file under src/

## Acceptance Criteria
- [ ] `git log --follow` on the new path shows the old history
- [ ] `make codebase-health-snapshot` appends to the new path (run once, then revert the appended line or keep it,
      stated)
- [ ] No reference to the old path remains outside frozen history (`git grep`), or each one that does is explained
- [ ] Close-week dry run output recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE
- TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT

## Related Docs
- docs/plans/codebase_health/handoffs/handoff_to_agent_working.md (Responses, item 3)
- docs/agent-monitoring/codebase_health_history_schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/reports/codebase_health_snapshot.py
- Makefile

## Assumptions / Open Questions
- Carried in the gates-flip batch as an extra independent hotfix; it can go first.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

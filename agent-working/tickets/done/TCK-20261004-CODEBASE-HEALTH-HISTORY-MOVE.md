---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-CODEBASE-HEALTH-HISTORY-MOVE
phase: done
date: 2026-10-04
tags: [delivery]
---

# TCK-20261004-CODEBASE-HEALTH-HISTORY-MOVE

## Title
Move the codebase-health snapshot history from agent-working/agent-monitoring/ to codebase/

## Status
DONE

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
- [x] `git log --follow` on the new path shows the old history
- [x] `make codebase-health-snapshot` appends to the new path (run once, then revert the appended line or keep it,
      stated)
- [x] No reference to the old path remains outside frozen history (`git grep`), or each one that does is explained
- [x] Close-week dry run output recorded
- [x] `git diff --stat <base>...HEAD` lists no path under src/

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
- Target directory: `codebase/reports/` (confirmed by codebase-planner 2026-10-04): the file sits next to its only writer, `codebase_health_snapshot.py`, and a new `codebase/history/` folder would add a directory for one file.
- `git mv` (rename detected, content byte-identical: sha256 prefix e134f07f802e before and after; 1 line). Same commit: `DEFAULT_HISTORY_PATH` (now `_REPO_ROOT / "codebase" / "reports" / ...`, the unused `AGENT_MONITORING` import removed), the Makefile help line, the schema doc (File path paragraph rewritten, append-only line, version-table row), `codebase/README.md` (stale "keeps writing there" bullet removed; the reports row names the file), `codebase_domain_root.md` (two mentions now past tense).
- The schema doc stays at `docs/agent-monitoring/` (agent-working allowed either; no move, so no REGISTRY path churn).
- Tests: new `test_default_history_path_is_in_the_codebase_domain` (new default path, file exists, old path gone); the no-real-corpus-path guard also forbids the real history path now.
- Close-week dry run (`tools/agent-monitoring/week_close.py --week 2026-W40 --today 2026-10-20` on a scratch copy of `data/`, with the history file beside it): folded 49 runs/events/tools shards and 49 working-log shards; the history file's sha256 is unchanged. The tool only reads `data/<week>/` shards; it never names the history file.
- `make codebase-health-snapshot` run once for real: appended a second line to `codebase/reports/codebase_health_history.jsonl`; the line was then reverted (`git checkout`) so the move commit stays byte-identical; the old path no longer exists.
- Gap, stated: the frozen-history path map (`docs/guides/agent_working_path_map.md`) is prefix-only, so a frozen citation of `agent-monitoring/codebase_health_history.jsonl` resolves to `agent-working/agent-monitoring/...`, which no longer exists; `git log --follow codebase/reports/codebase_health_history.jsonl` reaches the old history. The doc belongs to agent-working, so it is not edited here; flagged to codebase-planner.
- Remaining mentions of the old path (`git grep`): frozen tickets/artifacts/archive docs and this ticket, the PR #322 handoff docs (frozen record), and `codebase_domain_root.md` (history, past tense).

## Test Summary
`.venv/bin/python3 -m pytest tests/codebase/test_codebase_health_snapshot.py` (own basetemp, MemoryMax=2G): 13 passed, 1 failed. The failure is `test_make_target_runs_successfully_end_to_end`: the known local time-limit failure ("Test execution exceeded the resource time limit"; the handover records it as failing on clean main); it writes to tmp paths only and left the real history file untouched.

## Files Changed
- codebase/reports/codebase_health_history.jsonl (moved from agent-working/agent-monitoring/)
- codebase/reports/codebase_health_snapshot.py, codebase/README.md, Makefile
- docs/agent-monitoring/codebase_health_history_schema.md, docs/plans/codebase_health/codebase_domain_root.md
- tests/codebase/test_codebase_health_snapshot.py
- agent-working/tickets/ (this ticket), monitoring shards, docs/REGISTRY.yaml

## Completion Summary
Done: the snapshot history lives in `codebase/reports/` with its history kept, the writer, Makefile, schema doc and README updated in one commit, a test pins the new default path, and the close-week dry run left it untouched. Known gaps: the path-map gap above; the make-target test fails locally for the known time-limit reason. No src/ path touched.

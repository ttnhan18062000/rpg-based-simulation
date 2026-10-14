---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RATCHET-TIGHTEN-AFTER-PAYDOWN
phase: done
date: 2026-10-09
tags: [architecture, delivery]
---

# TCK-20261009-RATCHET-TIGHTEN-AFTER-PAYDOWN

## Title
Lock in the code-health and mypy debt other domains have paid down

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Main `8754f94f2` reported `OK: 0 new, 0 worse, 72 improved, 32 gone, 3619 unchanged` in the Code health job and a green Type check. Other domains' work had paid debt that the baselines still allowed, so the ceilings were loose. `codebase.health tighten` and `make typecheck-baseline-sync` lock it in. Owner-approved 2026-10-09, brief from codebase-planner.

## Scope
- `python3 -m codebase.health tighten --yes` (lowers ceilings, removes rows for paid debt; never skips a tool, jscpd ran)
- `make typecheck-baseline-sync` with the acceptance condition that the diff of `codebase/baselines/mypy_baseline.txt` has deletions only
- Prove from the diff that no ceiling rose and no row was added

## Out of Scope
- `codebase/baselines/parity_ledger_schema_baseline.json` (shared) and anything under `src/`
- Hand edits of any baseline row

## Acceptance Criteria
- [x] `make code-health` gives 0 new, 0 worse, 0 improved, 0 gone
- [x] `make typecheck-py` gives 0 new
- [x] The mypy baseline diff is deletions only (0 added lines)
- [x] The code-health baseline diff has no added row and no raised ceiling (script output below)
- [x] `git diff --stat` touches only the two baseline files plus the ticket and monitoring
- [x] `tests/codebase` passes

## Related Tickets
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Related Docs
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/baselines/code_health_exceptions.jsonl
- codebase/baselines/mypy_baseline.txt

## Assumptions / Open Questions
- The rough "which domains" grouping below is by top-level `src/` package, not by ticket: the rows carry no author. Several domains' work lands in `engine` (the largest package).

## Implementation Notes
- Ran from `origin/main` `8754f94f2` in a fresh worktree, one heavy command at a time under the 2 GB cap. `tighten --yes` finished with exit 0 (jscpd ran via npx; nothing was skipped or hand-edited). `make typecheck-baseline-sync` exit 0.
- Code-health baseline: 3723 -> 3691 rows (32 removed), 72 ceilings lowered; sum of all ceilings 103,497 -> 102,131. mypy baseline: 1563 -> 1520 lines (43 deleted, 0 added).
- Locks in, by top-level `src/` package: removed rows {engine 21, core 3, domains 3, systems 2, content 1, town 1, worldbuilding 1}; lowered rows {engine 49, systems 6, core 5, domains 4, worldbuilding 3, certification 2, cognition 1, town 1, worldassembly 1}; mypy deletions {engine 35, config 6, core 2}. By tool: removed ruff 23, line_count 5, complexipy 3, ast_grep 1; lowered line_count 26, ruff 24, complexipy 20, jscpd 2.

## Test Summary
Proof script (rows keyed by file, symbol, tool, rule; the baselines saved before the run vs now; it asserts no added row, no raised ceiling, no other field change, and `value <= ceiling` on every row — about 10 lines, not 5, because it also groups the paydown):

```
rows before=3723 after=3691 added=0 removed=32 ceilings_rose=0 lowered=72 other_field_changes=0 value_over_ceiling=0
removed rows by src package: {'engine': 21, 'core': 3, 'domains': 3, 'systems': 2, 'content': 1, 'town': 1, 'worldbuilding': 1}
lowered rows by src package: {'engine': 49, 'systems': 6, 'core': 5, 'domains': 4, 'worldbuilding': 3, 'certification': 2, 'cognition': 1, 'town': 1, 'worldassembly': 1}
sum of ceilings before/after: 103497 102131
removed by tool: {'line_count': 5, 'ruff': 23, 'complexipy': 3, 'ast_grep': 1}
lowered by tool: {'ruff': 24, 'line_count': 26, 'complexipy': 20, 'jscpd': 2}
```

- `make code-health`: `OK: 0 new, 0 worse, 0 improved, 0 gone, 3691 unchanged`.
- `make typecheck-py`: no output, exit 0 (0 new).
- `tests/codebase`: 467 passed, 2 skipped, with the two known local 60 s make-target tests deselected.
- `git diff --stat`: 2 baseline files (72 insertions, 147 deletions in total; the insertions in the jsonl are lowered numbers on rows that remain).

## Files Changed
- `codebase/baselines/code_health_exceptions.jsonl`
- `codebase/baselines/mypy_baseline.txt`

## Completion Summary
The ratchet now allows exactly what the code has: 32 paid-off rows are gone and 72 ceilings are lower, and 43 stale mypy entries are deleted, with no row added and no ceiling raised. Gates are at zero slack.

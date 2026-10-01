---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261001-RETRO-REPORT-READ-ONLY
phase: done
date: 2026-10-01
tags: [agent-monitoring, data-quality]
---

# TCK-20261001-RETRO-REPORT-READ-ONLY

## Title
The retro report must not mutate the working tree

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`generate_retro.py` (around line 2118) calls `consolidate_all()` before reading, which deleted about 30 tracked shard files in a shared worktree on 2026-10-01. The retro already reads through the shard-aware loaders (`load_data_glob`, `shard_paths`), so it does not need the fold to see the data. That call was a deliberate consolidation trigger, so remove it only after `TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND` provides the replacement.

## Scope
1. Remove the `consolidate_all()` call and its import from `generate_retro.py`.
2. Confirm every reader the retro uses (runs, events, tools, working log) reads shards through the shard-aware path, and fix any that reads canonical files only.
3. Check other callers that relied on the retro's side effect (`post_tool_hook.py`, `record_hand_orchestrated_closure.py` mention consolidation in comments) and record what each does.
4. Update the retro skill and `docs/guides/agent_monitoring.md` to say consolidation is the week-close command's job.

## Out of Scope
- Changing what the report computes.
- Any change to the week-close command itself.

## Acceptance Criteria
1. `git status --porcelain` is identical before and after a retro run, in a fixture tree with per-batch shards; a test pins this.
2. The report's numbers on that fixture are the same as before the change.
3. No caller is left depending on the removed side effect, with the check recorded in Implementation Notes.

## Related Tickets
- TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND (must land first)
- TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE (done; origin of the retro trigger)
- TCK-20260926-MONITORING-READ-PATH-CONSOLIDATION (done; the shard-aware read path)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md` (update the matching row's status in this ticket's own batch)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py`, `.claude/skills/agent-monitoring-retro/SKILL.md`, `tests/tools/test_generate_retro.py`

## Assumptions / Open Questions
- Depends on the week-close ticket; if it slips, this ticket waits, otherwise shards pile up with no trigger.

## Implementation Notes
Removed the `consolidate_all()` call and import from `generate_retro.py`; `main()` now only reads. Reader check (scope 2): the retro loads runs/events/tools through `_load_runs_and_events`/`_load_source` -> `load_data_glob`, the SQLite index build (`build_index.py`) uses `load_data_glob`, and the staleness probe uses `shard_paths`: all shard-aware, nothing reads canonical files only. The retro does not read the working log at all. Caller check (scope 3): `post_tool_hook.py` (comment at line ~185) and `record_hand_orchestrated_closure.py` (comment about a past cross-checkout bug) only mention consolidation in comments; `done_checker_static` and `record_hand_orchestrated_closure` read pending working_log shards directly, so none depended on the retro's fold. Only the Makefile help text and docs claimed it ran before every retro; both updated. Test hygiene: two lines in test_generate_retro.py that monkeypatched `generate_retro.consolidate_all` were removed (the attribute no longer exists); the module-level guard that fails if a test changes real monitoring paths stays.
Draft by agent-working-design; the implementer commits it.

## Test Summary
tests/tools/test_generate_retro.py 188 passed, including two new tests: a retro run over per-batch shards leaves the data tree byte-identical and the shard files in place (AC1), and the report equals the one produced from the same data as a closed week (AC2, separate index per run). 571 passed across the retro/monitoring/consolidation/week_close/skill selection.
Not started.

## Files Changed
- `tools/agent-monitoring/generate_retro.py`, `tests/tools/test_generate_retro.py`
- `Makefile` (help text), `docs/guides/agent_monitoring.md`, `.claude/skills/agent-monitoring-retro/SKILL.md`
- `docs/plans/agent_infrastructure/agent_working_direction.md`
None yet.

## Completion Summary
The retro report no longer mutates the working tree; consolidation is the explicit week-close command's job (previous ticket).
Not started.

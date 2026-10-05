---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED
phase: done
date: 2026-10-04
tags: [ai, process-improvement]
---

# TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED

## Title
`clean_data_runs_early` deletes other sessions' run data: make the cleaner report-only

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Reported by `rpg-feature-planning`: the post-Test cleanup removed 3684 files across 14 distinct PID suffixes, not just its own session's. Nothing in flight was lost, by luck: of the 14 suffixes only one matched a live process, and that was a GNOME daemon that had recycled a dead session's PID.

Verified here from `tools/gate_checks/done_checker_static.py`: `_find_flagged_data_run_files` flags every file under `data/runs/` and `reports/release_proof/` with `mtime >= start_ts`, and `clean_data_runs_early` unlinks all of them. Its own docstring concedes it does not protect against a concurrent session and calls this an accepted, not mitigated, tradeoff. With ~15 Claude processes live on this machine the window is open on every pipeline run. Blast radius is untracked run data (both directories are gitignored; confirmed), not source, but another session's in-flight evidence can vanish.

The peer's second point stands: the obvious fix "clean by PID suffix" is incomplete, because a PID liveness check can return a false LIVE after PID reuse, exactly as it did here. Ownership must come from a session identifier or an ownership marker, not a PID.

## Scope
Owner direction (2026-10-05): proceed on the design recommendation, option B. Options considered and why B: (A) writers mark their own files needs a marker added to at least six independent writers (src/observability/sweeper.py, src/observability/mining/controller.py, src/observability/personality/recorder.py, src/simulation_quality/worker.py, src/api/routes/decisions.py, src/observability/anomaly/worker.py, plus test writers under data/runs/<run_id>) and one in tools/ (tools/release/generate_release_proof.py for reports/release_proof); most are rpg/observability code, so it would need rpg-planner and still leaves unmarked legacy files. (C) defer leaves the window open on every pipeline run with ~15 Claude processes live.
- `clean_data_runs_early` (tools/gate_checks/done_checker_static.py) no longer unlinks anything. It reports the flagged paths and their count and returns a non-deleting status; the `implement-ticket.js` call site (line ~1518) keeps working unchanged in shape.
- `check_data_runs_clean` and `clean_data_runs_early` keep sharing `_find_flagged_data_run_files` (single definition, per its docstring).
- Deletion becomes an explicit, scoped act: a separate opt-in command `python3 tools/gate_checks/done_checker_static.py --clean-data-runs --path <dir-or-run-id>` (name open) that deletes only the named run directories, never a blanket sweep. The hand-run `rm -rf data/runs/*` in CLAUDE.md is a governing-file item: report it to the owner, do not edit it here.
- Decide, and record in the ticket, what the Verify check does while leftovers exist: report-only means a pipeline whose own tests wrote files would otherwise FAIL `data_runs_clean` with no automatic way out. Recommended: it downgrades to an advisory WARN that lists the files (consistent with the repo's "agent tooling checks proportionate" stance). This weakens a Definition-of-Done check, so it needs the owner's explicit yes before activation.
- Update the docstring's "accepted residual risk" paragraph and the Anti-Drift note to the new behaviour.

## Out of Scope
- PID-liveness-based ownership; changing where run data is written for unrelated reasons; CLAUDE.md edits.

## Acceptance Criteria
1. Two simulated sessions with overlapping mtimes: `clean_data_runs_early` run as session A deletes nothing; B's files survive (positive control: the old behaviour deletes both).
2. `clean_data_runs_early` reports every flagged path and the count, and returns a status the `implement-ticket.js` call site handles without change.
3. The opt-in scoped delete removes only the named run directories and refuses a blanket or empty path.
4. `check_data_runs_clean` behaviour for leftovers is whatever the owner chose (WARN advisory recommended); INDETERMINATE (no start_ts) still reports.
5. Existing tests are updated with the reason stated for each change in meaning; none is weakened silently.
6. Docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20260708-DATA-RUNS-CLEANUP-TIMING` (origin), `TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS`

## Related Docs
- `.claude/agents/parity-updater.md` (where relevant), `docs/guides/delivery_process.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/gate_checks/done_checker_static.py`, `.claude/workflows/implement-ticket.js` (call site, line ~1469), whatever creates the run directories, tests.

## Assumptions / Open Questions
- OPEN, needs the owner before activation: whether the Verify check may become an advisory WARN (weakens a Definition-of-Done condition).
- Writers were inventoried 2026-10-05 by grep of src/ and tools/ (not exhaustive); the investigation should re-run the inventory before relying on it.
- Until fixed, anyone running several pipelines at once risks losing another's run evidence: report to the owner as a standing caveat.

## Implementation Notes
- Owner direction 2026-10-05: option B (report-only cleaner), and an explicit yes to downgrading `check_data_runs_clean` leftovers to an advisory WARN (asked directly in this session). Option A (writers mark their own files) was rejected: design's inventory found at least six independent writers under `data/runs/` (`src/observability/sweeper.py`, `mining/controller.py`, `personality/recorder.py`, `src/simulation_quality/worker.py`, `src/api/routes/decisions.py`, `anomaly/worker.py`, plus test writers) and one in `tools/` for `reports/release_proof`, mostly rpg/observability code, and legacy files would stay unmarked. Option C (defer) leaves the window open on every pipeline run.
- `tools/gate_checks/done_checker_static.py`:
  - `clean_data_runs_early` no longer unlinks. It returns `PASS` when nothing is flagged, else `REPORTED` with the count and every path ("none deleted"). It never returns `FAIL` (no deletion to fail). It still uses the shared `_find_flagged_data_run_files`.
  - `check_data_runs_clean` returns `WARN` instead of `FAIL` for leftovers, in both the explicit-`start_ts` and the run-record-resolved branches (an unparsable `start_ts` still flags every file, now as `WARN`). `INDETERMINATE` is unchanged. Every consumer branches only on the literal `"FAIL"` (documented in the module docstring), so `WARN` never blocks.
  - New `delete_data_run_paths` plus CLI `--clean-data-runs --path <run_id>` (needs no `--ticket-id`): deletes only the named entries, relative to `data/runs/` or `reports/release_proof/`. It refuses an empty list, wildcards, `.`/`..`, absolute paths, anything resolving outside both directories (symlinks included) and the directories themselves, all before deleting anything.
- `.claude/workflows/implement-ticket.js`: the call site gets a `REPORTED` log branch (previously it fell into the "already clean" log, which would have been misleading); the checkpoint comment is updated. `FAIL`/`DATA_RUNS_CLEAN_FAILED` handling is left in place but can no longer trigger.
- Docs updated: `docs/ai/ticket-lifecycle.md` (checkpoint, Step 0a, status table: `DATA_RUNS_CLEAN_FAILED` marked legacy), `.claude/agents/done-checker.md` Step 0a, `.claude/skills/implement-ticket/SKILL.md`. The `rm -rf data/runs/*` line in the project CLAUDE.md is a governing-file item and was NOT edited; it is reported to the owner. The ticket-close cleanup step there still deletes by hand-run command.
- Not done: nothing attributes files to a session, so the Verify WARN list can include another session's files; that is why it is only advisory.

## Test Summary
`tests/tools/test_done_checker_static.py`: 174 pass; the wider run over `tests/tools` and `tests/docs` (done_checker, lifecycle, workflow, skill, agent, registry, drift, vocabulary selectors) passed 1182. Changed in meaning, reason stated in each test: three `check_data_runs_clean` tests (failing result now a warning), the cleaner's detect-and-remove test (now report-only), the cleaner reuses-definition test (now asserts nothing is deleted) and the deletion-error test (replaced: nothing is deleted any more). New: two overlapping sessions leave each other's files (AC1, with the old behaviour as the positive control in the ticket text); scoped delete removes only the named directory, refuses blanket, empty, absolute, escaping and symlink paths, and refuses everything when one name is bad (AC3); the CLI needs no ticket id and refuses a blanket path.

## Files Changed
- tools/gate_checks/done_checker_static.py
- tests/tools/test_done_checker_static.py
- .claude/workflows/implement-ticket.js
- .claude/agents/done-checker.md
- .claude/skills/implement-ticket/SKILL.md
- docs/ai/ticket-lifecycle.md

## Completion Summary
The post-Test cleanup checkpoint is report-only and the Verify check reports leftovers as an advisory WARN. Deleting run data is now an explicit, scoped command naming the run directory, so one session can no longer remove another's files.

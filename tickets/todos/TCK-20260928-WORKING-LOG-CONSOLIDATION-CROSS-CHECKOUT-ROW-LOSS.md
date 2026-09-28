---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS
phase: open
date: 2026-09-28
tags: [agent-monitoring, data-quality]
---

# TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS

## Title

Working-log consolidation reads pending shards from the script's own checkout but appends the rows
to the caller's cwd-relative `tickets/working_log.csv`, then deletes the shards. A run from a
different checkout moves rows out of the branch that owns them. Two tickets in PR #253 lost their
rows this way, and one ticket in PR #252 did too.

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

Found 2026-09-28 after PR #253 merged as `4512eae30`. Three tickets are in `tickets/done/` on
`origin/main` with run and event records in the monitoring shards, but none of them has a
`tickets/working_log.csv` row anywhere on main. They are not in the CSV and not in any pending
`*.working_log.jsonl` shard (checked with `git grep` against `origin/main`; a sweep of every
`tickets/done/` ticket dated 2026-09-24 onward found only these three):

- `TCK-20260928-MONITORING-LOADER-CWD-RELATIVE-PATHS` (PR #253)
- `TCK-20260928-PR-LIFECYCLE-OMITS-RENDER-AFTER-FOLD-IN` (PR #253)
- `TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS` (closed 2026-09-27)

`done_checker_static`'s `working_log_exactly_one_row` therefore fails for all three on main.

Each row now exists only as an uncommitted line in a *different* checkout's CSV:

- The first two are in the `agent-monitoring-data-quality-fix` worktree (detached HEAD at `fa7c10e7d`).
- The third is the last line (line 2154) of the **main checkout's** `tickets/working_log.csv`. That
  matches the CWD-PATHS ticket's own record that the implementer ran pytest with cwd = the main
  checkout, since `.venv` lives only there.

Exact bytes:

```
2026-09-28T07:36:09.600694Z,TCK-20260928-MONITORING-LOADER-CWD-RELATIVE-PATHS,generate_retro.py's shared run/event loader reads cwd-relative paths,DONE,"Anchored generate_retro.py's 5 data-loading constants to the module's own repo root instead of the caller's cwd, fixing a real false failure found verifying this same batch.",none (hotfix — no staging artifacts)
2026-09-28T07:36:20.601108Z,TCK-20260928-PR-LIFECYCLE-OMITS-RENDER-AFTER-FOLD-IN,"PR Lifecycle contract never names pr_render.py, no step for adding tickets to an open PR",DONE,Named pr_render.py in delivery_process.md's PR Lifecycle step 3 and added a step for re-checking/re-rendering after pushing more tickets to an open PR.,none (hotfix — no staging artifacts)
2026-09-27T15:13:03.727116Z,TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS,implement-ticket's Test and Verify phase prompts omit the precondition their own gate enforces,DONE,"Injects the required test-directory floor into the Test phase prompt before the test-scoper agent runs (via expected_test_dirs_for), and declares the pipeline-owned tickets/todos duplicate to done-checker in the Verify prompt when non-empty; done-checker.md gains the matching declared-vs-undeclared rule. Neither gate weakened.",none (hotfix — no staging artifacts)
```

**Mechanism, verified from source (confirmed by construction):**

- `tools/agent-monitoring/monitoring_consolidation.py:56` anchors
  `DEFAULT_DATA_DIR = Path(__file__)…/agent-monitoring/data`, which is the script's own checkout.
- `consolidate_all()` (line ~104) calls `consolidate_pending_rows(data_root=data_dir)` and never
  passes `csv_path`.
- `tools/working_log_writer.py` defaults `csv_path` to `_WORKING_LOG_PATH = Path("tickets/working_log.csv")`,
  which is **cwd-relative**. Its `_DEFAULT_DATA_ROOT` is cwd-relative too.
- `consolidate_pending_rows()` appends the pending rows to that CSV and then **deletes the source
  shards**.
- `generate_retro.py`'s `main()` calls `consolidate_all()` unconditionally at startup, so every
  retro run triggers this path, and so does `make` target `monitoring_consolidation.py`.

Run checkout A's `generate_retro.py` or `monitoring_consolidation.py` with cwd = checkout B, and
A's pending working_log shards are consumed while their rows land in B's CSV. The rows vanish from A
(the branch that owns them), and B gets unrelated uncommitted rows. The runs/events/tools kinds
don't lose data this way, because `consolidate_jsonl_kind()` writes to `week_dir / "<kind>.jsonl"`
under the same anchored `data_dir`. **Only the working_log kind crosses checkouts.**

The exact invocations weren't captured. Both destinations are checkouts that ran another checkout's
code, which is the pattern this mechanism predicts: the main checkout ran worktree tests (per the
CWD-PATHS ticket), and the design worktree ran a foreign-cwd review of the same batch. `TCK-20260928-MONITORING-LOADER-CWD-RELATIVE-PATHS` anchored only `generate_retro.py`'s
loader constants and left this write path cwd-relative.

## Scope

1. **Restore the three rows on the batch branch.** Write each row through the sanctioned writer,
   `tools/working_log_writer.py`, with its original timestamp/title/summary/artifacts values as
   shown above, so it goes through the per-batch staging shard. No hand edit of the CSV. If the
   writer can't preserve the original timestamp, record the actual write timestamp and say so in
   Implementation Notes.
2. **Anchor the working_log write/consolidation path to its own checkout.** At minimum,
   `working_log_writer._WORKING_LOG_PATH` and `_DEFAULT_DATA_ROOT` resolve from `Path(__file__)`,
   keeping `_WORKING_LOG_PATH` a genuine module-level constant (the AST single-writer guard in
   `tests/tools/test_working_log_writer.py` depends on that). Also check
   `record_hand_orchestrated_closure.py`'s cwd-relative `Path("tickets/working_log.csv")` (line ~363)
   and `data_root=Path("agent-monitoring/data")` default (line ~74), and anchor them the same way,
   or record why they are safe as they are.
3. **Ensure the consolidator's CSV and shard source are always the same checkout.**
   `consolidate_all()` passes an explicit `csv_path` derived from the same root as `data_dir`. When
   `--data-dir` points at a test tmp dir, it must not write to the real CSV (derive the CSV from
   `data_dir`'s repo root, or require both together — implementer's choice, documented).
4. Regression test: run consolidation with cwd set to a *different* temp directory that contains
   its own `tickets/working_log.csv`. Assert the foreign CSV is untouched and the rows land in the
   CSV next to the data dir. The test must fail on the pre-fix code.

## Out of Scope

- Anchoring every other cwd-relative path in `tools/` (a broader sweep is a separate ticket if
  needed).
- Changing the consolidation trigger (retro startup and the make target stay as they are).
- The stray uncommitted rows in the two destination CSVs. The design worktree discards its two
  once the restore lands. The main checkout's line 2154 must be removed by whoever owns that
  checkout (the implementer), or the next commit from there double-writes it.

## Acceptance Criteria

- AC1: On the batch branch, `python3 tools/gate_checks/done_checker_static.py --ticket-id <ID>`
  passes `working_log_exactly_one_row` for all three named tickets, after consolidation.
- AC2: `working_log_writer`'s CSV path and data root, and `consolidate_all()`'s CSV target, resolve
  from the module's own checkout regardless of cwd.
- AC3: The new foreign-cwd regression test fails on the pre-fix code and passes after.
- AC4: `tests/tools/test_working_log_writer.py` (including the single-writer AST guard) and the
  consolidation tests pass.

## Related Tickets

- `TCK-20260928-MONITORING-LOADER-CWD-RELATIVE-PATHS` (same defect class, read side only)
- `TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET` (introduced the staging + consolidation path)
- `TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE`
- `TCK-20260912-WORKING-LOG-APPEND-HELPER`

## Related Docs

- `docs/agent-monitoring/README.md`

## Related Stored Artifacts

None.

## Related Code Areas

- `tools/working_log_writer.py`
- `tools/agent-monitoring/monitoring_consolidation.py`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tools/agent-monitoring/generate_retro.py` (caller only)

## Assumptions / Open Questions

- The sweep covered only ticket IDs dated 2026-09-24 onward, since the staging path landed with
  `TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET`. `TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE`
  is not missing: it sits in a pending shard on main
  (`2026-W40/ticket-corpus-guard-test-scope-map.working_log.jsonl`).
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` (epic tier) also has no row. Confirm whether epic
  closes are expected to write one before treating it as a fourth loss.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

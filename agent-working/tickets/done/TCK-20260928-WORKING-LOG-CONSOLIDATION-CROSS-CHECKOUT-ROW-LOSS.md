---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260928-WORKING-LOG-CONSOLIDATION-CROSS-CHECKOUT-ROW-LOSS
phase: done
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

DONE

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
  (`2026-W40/ticket-corpus-guard-test-scope-map.working_log.jsonl`) — consolidated as part of this
  ticket's own closure (see Implementation Notes).
- **RESOLVED**: `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` (epic tier) also has no row. Confirmed
  this is *not* a fourth instance of the row-loss bug: `.claude/workflows/implement-epic.js`
  contains zero references to `working_log`, `append_working_log_row`, `done_checker`, or
  `Finalize` — epic tier's own pipeline never calls the working-log writer or
  `done_checker_static.py`'s Part B checks at all (consistent with the Tier Routing table: epic is
  "Scope only — tracks child tickets; no direct implementation" — its children's own rows are the
  real log entries). No fix needed for this ticket's scope.

## Implementation Notes

**Fix shape (matches Scope items 1-3; item 2's `record_hand_orchestrated_closure.py` sub-item
resolved as "safe as-is", documented in place rather than anchored):**

1. `tools/working_log_writer.py`: `_WORKING_LOG_PATH`/`_DEFAULT_DATA_ROOT` stay literal, relative
   module-level constants (`Path("tickets/working_log.csv")` / `Path("agent-monitoring/data")`) —
   changing their own assigned value to an `__file__`-derived expression (e.g.
   `_REPO_ROOT / "tickets" / "working_log.csv"`) would have broken the AST single-writer guard,
   whose `_literal_value()` resolver only recognizes a bare string constant or `Path("literal")`,
   not a `BinOp`/path-join chain — confirmed by trying it first and watching
   `test_working_log_csv_has_exactly_one_writer` drop to 0 hits. Instead, added a new `_anchored()`
   helper (`_REPO_ROOT = _TOOLS_DIR.parent`, from `Path(__file__)`) that resolves a relative path
   against the module's own checkout and passes an already-absolute path through untouched; called
   at the top of `_append_csv_row()` and `consolidate_pending_rows()`. The guard's resolver still
   sees the literal default-parameter binding unchanged (the runtime reassignment inside the
   function body isn't a literal, so it doesn't override the resolver's mapping) — guard still
   finds exactly 1 hit, in `working_log_writer.py`, unchanged.
2. `tools/agent-monitoring/monitoring_consolidation.py`: `consolidate_all()` now derives an
   explicit `csv_path` from `data_dir`'s own root (`_default_csv_path_for()`) and passes it to
   `consolidate_pending_rows()`, instead of leaving `csv_path` to that function's own default. This
   is what actually closes the cross-checkout gap end-to-end: `DEFAULT_DATA_DIR` was already
   correctly `__file__`-anchored (per the ticket's own source-verified mechanism write-up); the bug
   was specifically that nothing derived a matching, equally-anchored `csv_path`.
3. `tools/agent-monitoring/record_hand_orchestrated_closure.py`: left `data_root`/`working_log_path`
   cwd-relative, with a documented reason at both sites (`_existing_row_for()`'s docstring, and a
   short pointer comment at `main()`'s own `working_log_path` assignment). This script's paths are
   *consistently* cwd-relative together (matching `monitoring_batch_identifier.resolve_write_target()`'s
   own documented convention that every real call site assumes cwd is the checkout being recorded
   for) — there's no anchor mismatch here the way there was in `monitoring_consolidation.py` (an
   `__file__`-anchored data dir paired with a cwd-relative CSV write). Anchoring this script to
   `__file__` instead would break its real invariant (a hand-orchestrating session always runs it
   from within the checkout it's closing a ticket in) and its own test suite, which exercises it as
   a subprocess with `cwd=` a scratch checkout distinct from this file's own location.
4. Restored the 3 lost rows (Scope item 1) through the sanctioned writer only: staged via
   `append_working_log_row()` with their original timestamp/title/summary/artifacts values (see
   this ticket's "Exact bytes" block above — preserved verbatim, no hand edit of the CSV), then
   consolidated via `python3 tools/agent-monitoring/monitoring_consolidation.py` run from *this*
   checkout (exercising the fix's own anchoring). That same consolidation run also folded in one
   *unrelated*, already-legitimately-pending shard left on `origin/main`
   (`2026-W40/ticket-corpus-guard-test-scope-map.{runs,events,tools,working_log}.jsonl`, for the
   already-closed `TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE`) — this is the
   consolidator doing its documented job correctly, not new work; flagging it here for
   transparency since it lands in the same commit.
5. New regression tests (Scope item 4, AC3) added to `tests/tools/test_monitoring_consolidation.py`:
   `test_consolidate_all_derives_csv_path_from_data_dir_not_foreign_cwd` and
   `test_consolidate_pending_rows_default_path_resolves_against_module_not_foreign_cwd`. Both
   verified to FAIL on the pre-fix code (temporarily reverted the two source files to `HEAD`,
   re-ran just these two tests, confirmed failure, restored the fix) and PASS after.

## Test Summary

- `tests/tools/test_working_log_writer.py` (72 tests incl. the AST single-writer guard),
  `tests/tools/test_monitoring_consolidation.py` (now 16 tests, +2 new),
  `tests/tools/test_record_hand_orchestrated_closure.py` (38 tests),
  `tests/tools/test_done_checker_static.py` — all pass (run via the main checkout's `.venv`
  interpreter with cwd kept in this worktree, never cwd = the main checkout, per this same
  ticket's own subject matter).
- The 2 new regression tests independently confirmed to fail on pre-fix code before being
  confirmed to pass on the fix (AC3).
- `python3 tools/gate_checks/done_checker_static.py --ticket-id <ID>` run for all 3 restored
  tickets: `working_log_exactly_one_row` PASSes for each (AC1). (`working_log_no_row_yet` FAILs as
  expected — that precheck condition only applies at a ticket's own close time, not to a
  historical row restoration.)

## Files Changed

- `tools/working_log_writer.py`
- `tools/agent-monitoring/monitoring_consolidation.py`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (comments only, no behavior change)
- `tests/tools/test_monitoring_consolidation.py` (2 new regression tests)
- `docs/REGISTRY.yaml` (unconditional post-migration regeneration per CLAUDE.md's After Work step,
  no manual doc edits this ticket)
- `tickets/working_log.csv` (3 rows restored + 1 unrelated already-pending row consolidated, see
  Implementation Notes item 4)
- `agent-monitoring/data/2026-W40/` (per-ticket shards consolidated into the canonical week files)

## Completion Summary

Anchored `working_log_writer.py`'s CSV/data-root resolution and `monitoring_consolidation.py`'s
`consolidate_all()`'s CSV target to each script's own checkout instead of cwd, closing the gap that
let a foreign-cwd consolidation run move rows out of the branch that owned them. Restored the 3
lost rows through the sanctioned writer with their original values, and resolved the epic-tier open
question (not a fourth loss — `implement-epic.js` never writes a working_log row). Left
`record_hand_orchestrated_closure.py`'s cwd-relative paths as-is with a documented rationale, since
anchoring them would have broken a real invariant its own test suite depends on.

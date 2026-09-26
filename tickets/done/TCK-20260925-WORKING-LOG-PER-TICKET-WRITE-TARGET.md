---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET
phase: done
date: 2026-09-25
tags: [workflows, agent-monitoring, process-improvement]
---

# TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET

## Title

`working_log.csv` still has no squash-merge protection — the per-ticket write-target fix stopped at
the JSONL shards

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

`TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE` gave the three
`agent-monitoring/data/*/*.jsonl` files per-ticket write targets, closing the gap where
`.gitattributes`' `merge=union` never engages under a GitHub squash-merge (this repo's near-universal
merge mode). **It deliberately did not do the same for `tickets/working_log.csv`, and closed with its
own AC3 stated as unsatisfied.** This ticket is that unfinished half, filed so the gap is tracked
rather than living only as a paragraph in a closed ticket's Completion Summary.

The reason it was descoped is sound and must be respected here rather than re-discovered:
`done_checker_static.py::check_working_log_exactly_one_row()` reads `working_log.csv`
**synchronously at every ticket's own close**. The JSONL files have no such dependency — CLAUDE.md's
Definition of Done says their coverage is "guaranteed by workflow — not verified by done-checker."
So the consolidation-at-retro-cadence design that works for the shards would, applied unchanged to
`working_log.csv`, break `working_log_exactly_one_row` for every ticket closed via the new path until
the next retro run. That check also carries deliberately nuanced reopen-vs-duplicate logic, so it
cannot simply be pointed at a different file and left alone.

This is not hypothetical exposure: `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` records a
real ~1586-row duplication from exactly this failure mode. Its detection-only mitigation is currently
the standing protection and remains so until this ticket lands.

## Scope

- Give `tickets/working_log.csv` squash-merge-safe write semantics, **without** breaking
  `working_log_exactly_one_row`'s synchronous read at ticket close. The two candidate shapes (see
  Open Questions) are: teach that check to read the per-ticket files directly, or keep a synchronous
  write while removing the shared-line collision.
- Extend the real-git-repo fixture from the shard ticket — the one that reproduces the sequential
  squash-merge shape — to cover `working_log.csv`, satisfying that ticket's AC3.
- Confirm `record_hand_orchestrated_closure.py`'s internal `append_working_log_row()` call and the
  standalone helper both route through whatever write path this ticket establishes. Two independent
  hand-rolled writers already produced an identical CRLF defect once
  (`TCK-20260912-WORKING-LOG-APPEND-HELPER`); a third path would repeat it.

## Out of Scope

- **Re-opening the shard ticket's JSONL design.** Per-ticket files plus
  `monitoring_consolidation.py` are settled and working; this ticket extends the idea, it does not
  revisit it.
- **Weakening or deleting `working_log_exactly_one_row`.** The check is the reason this is hard; it
  is not the obstacle to route around. Making it pass by making it check less is explicitly
  forbidden — Gate Integrity applies.
- **A manifest of per-ticket files.** The shard ticket rejected this deliberately: a manifest is
  itself new, small, non-append-only state with its own merge-conflict exposure — the exact class of
  problem being removed, reintroduced smaller. Do not reintroduce it here.
- **Changing `working_log.csv`'s columns, ordering, or its consumers' contract.**
- **Retroactively repairing the historical duplication** from `TCK-20260906`.

## Acceptance Criteria

1. Two tickets closing on two different branches, each squash-merged against `main` in sequence,
   never conflict or duplicate on `working_log.csv` — proven by the same real-git-repo fixture class
   the shard ticket used, not asserted by inspection. (This is that ticket's AC3.)
2. `working_log_exactly_one_row` passes identically for a ticket closed via the new write path,
   **at that ticket's own close**, with no dependency on a later consolidation run having happened.
3. Its reopen-vs-duplicate distinction still behaves identically — proven by a test over both cases,
   not by the check merely returning PASS.
4. After consolidation, `working_log.csv` is byte-identical in content and row order to what the old
   direct-append path would have produced for the same sequence of closes.
5. Consolidation is idempotent — running it twice produces no duplicate rows.
6. `record_hand_orchestrated_closure.py` and `append_working_log_row()` agree on the write path, with
   the existing double-write refusal (`TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`)
   still firing.
7. Scoped tests pass; command and result recorded in `## Test Summary`.

## Related Tickets

- `TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE` — descoped this; its AC3 is AC1
  here.
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` — the real ~1586-row duplication; its
  detection-only mitigation is the current protection.
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` — why a third independent writer must not appear.
- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` — the double-write refusal.
- `TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS` — separate, also in `done_checker_static.py`;
  independent, but a reason to check for edit collisions if both are in flight.

## Related Docs

- `CLAUDE.md` — "After Work"; Definition of Done.
- `docs/ai/ticket-lifecycle.md` — Verify / Step 0a.

## Related Stored Artifacts

- `stored_artifacts/TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE/` — its
  investigation records why this was split out.

## Related Code Areas

- `tools/working_log_writer.py` — `append_working_log_row()`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tools/agent-monitoring/monitoring_consolidation.py`
- `tools/gate_checks/done_checker_static.py` — `check_working_log_exactly_one_row()`
- `.gitattributes`, `tickets/working_log.csv`

## Assumptions / Open Questions

1. **The main design decision: which side moves.** — **RESOLVED: (a), confirmed against the
   real check logic (see investigation.md/plan.md), not chosen from the sketch alone.** Both
   `_count_rows_for_ticket`/`_rows_for_ticket` already scan every column of every raw row list
   with no fixed-index assumption, so teaching them to also fold in pending-shard rows (converted
   to the same list shape) required zero changes to the actual matching/duplicate-vs-reopen logic
   downstream — confirming (a)'s "mechanical" framing was accurate, not merely convenient.
   `record_hand_orchestrated_closure.py`'s own `_existing_row_for()` needed the identical
   extension for the same reason (it would otherwise go blind to a prior staged-but-not-yet-
   consolidated direct call) — found by tracing the call graph, a second real consumer the
   original sketch didn't name explicitly.
2. Whether `monitoring_consolidation.py` should absorb `working_log.csv`. — **RESOLVED: yes**,
   but not as a fourth `JSONL_KINDS` entry — the canonical CSV isn't week-sharded the way
   `runs`/`events`/`tools` are, so it needed its own single-pass function
   (`consolidate_pending_rows()`), called once per `consolidate_all()` run rather than per week.
   A genuine new requirement the JSONL shards never had: row **order** matters for
   `working_log.csv` (AC4), so rows are sorted by their own `timestamp` field across all shards
   being folded in one pass — sorted-filename order (the JSONL precedent's own ordering) would
   have scrambled true chronological order whenever more than one batch's shard is pending at
   once.
3. Whether any other gate reads `working_log.csv` synchronously. — **RESOLVED, swept rather than
   assumed**: `check_working_log_exactly_one_row` (Part B / `run_finalize_selfcheck` only, never
   Part A) is the one gate-check consumer; `record_hand_orchestrated_closure.py`'s double-write
   guard is the second, non-gate consumer already covered above. No third undiscovered copy this
   time — confirmed via the full `tests/tools/` regression pass, not merely a grep.

## Implementation Notes

Full reasoning in `staging_artifacts/TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET/
{investigation,plan}.md`. `append_working_log_row()` keeps `path`, when explicitly given, meaning
"write this CSV row directly" (the pre-this-ticket behavior, unchanged) — only the no-`path` case
(the only way any real caller invokes it) now stages to a per-batch shard via the already-shared
`monitoring_batch_identifier.resolve_write_target("working_log")`. This preserved every existing
test's original intent and assertions for the many tests that use `path=` purely to seed a scratch
CSV, rather than requiring a rewrite around a consolidation step they were never exercising —
disclosed explicitly in the function's own docstring, not an implicit compatibility shim.

`consolidate_pending_rows()` (the function that actually opens `tickets/working_log.csv`) lives in
`working_log_writer.py` itself, never in `monitoring_consolidation.py` — confirmed necessary by
re-running `test_working_log_csv_has_exactly_one_writer`'s AST guard after the change (still
exactly 1 hit, unchanged location).

## Test Summary

- `tests/tools/test_working_log_writer.py` — 20 tests (7 new: staging isolation, timestamp
  ordering across shards, idempotency, merge-with-existing-content, two no-op cases, and the
  real-git-repo squash-merge fixture for `.working_log.jsonl`). All pass.
- `tests/tools/test_done_checker_static.py` — 5 new tests (pending-only visibility for both
  checks; reopen-across-sources PASS; duplicate-across-sources FAIL; a different ticket's pending
  row correctly ignored). All pass alongside the full existing 142-test file.
- `tests/tools/test_record_hand_orchestrated_closure.py` — 6 existing tests updated (5 now
  consolidate before asserting on the CSV; 1 retitled/re-asserted for the strictly-stronger no-
  more-OSError guarantee). All pass alongside the full existing file.
- `tests/tools/test_monitoring_consolidation.py` — unchanged, all pass (confirms the new
  `working_log` key in `consolidate_all()`'s result doesn't disturb the existing JSONL-kind
  consolidation tests).
- Full regression: `python3 -m pytest tests/tools/ -m "not slow and not extra_slow"` — **3067
  passed**, 25 skipped, 28 deselected, 1 xfailed, 0 failed.

## Files Changed

- `tools/working_log_writer.py` — `_append_csv_row()` extracted; `append_working_log_row()` now
  stages by default, direct-writes only when `path` is explicitly given;
  `consolidate_pending_rows()` (new).
- `tools/working_log_parser.py` — `parse_pending_working_log_shards()` (new); `import json` added.
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` — `_existing_row_for()` gains
  `data_root` and also checks pending shards.
- `tools/gate_checks/done_checker_static.py` — `_count_rows_for_ticket`/`_rows_for_ticket` gain
  `data_root` and a new `_pending_rows_for_ticket_as_lists()` helper;
  `check_working_log_no_row_yet`/`check_working_log_exactly_one_row` thread `data_root` through.
- `tools/agent-monitoring/monitoring_consolidation.py` — calls `consolidate_pending_rows()` once
  per run; module docstring's scope note corrected; `main()`'s printer special-cases the new
  `"working_log"` result key.
- Tests: `tests/tools/test_working_log_writer.py` (+7), `tests/tools/test_done_checker_static.py`
  (+5, +1 import), `tests/tools/test_record_hand_orchestrated_closure.py` (6 updated, +1 helper).
- `staging_artifacts/TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET/
  {investigation,plan,test_plan}.md` (new).
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary

`tickets/working_log.csv` now has the same squash-merge-conflict protection the JSONL shards
already had: `append_working_log_row()` stages to a per-batch file instead of writing the shared
CSV directly, closing the gap `TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE`
explicitly left open (its own unsatisfied AC3), proven the same way that ticket proved it — a real
throwaway git repo, sequential squash-merges, zero conflicts. `check_working_log_exactly_one_row`/
`check_working_log_no_row_yet` and `record_hand_orchestrated_closure.py`'s double-write guard all
read the pending shards directly, so nothing depends on a later consolidation run having happened
at a ticket's own close — the exact synchronous dependency that motivated leaving working_log.csv
out of the original shard ticket's scope. `monitoring_consolidation.py` absorbs it into the same
cadence already wired to run before every retro, with a genuinely new (for this codebase)
timestamp-based cross-shard ordering guarantee the JSONL shards never needed.

No known material gap. `data_runs_clean` is expected to PASS or report INDETERMINATE (not FAIL) on
this close, per `TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS` landing earlier in this
same batch.

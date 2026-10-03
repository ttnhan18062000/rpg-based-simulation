---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET
artifact_type: investigation
tags: [workflows, agent-monitoring, process-improvement]
---

# Investigation — TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET

## Which side moves (Open Question 1) — recommendation confirmed against the real check logic

Read `check_working_log_exactly_one_row()`/`check_working_log_no_row_yet()` and their two backing
helpers (`_count_rows_for_ticket`, `_rows_for_ticket`) in full. Both already scan every column of
every row (never a fixed index, tolerating the historical column-shift bug class) and return the
raw row lists themselves — the matching *rule* is independent of where the rows come from. This
confirms option (a) (teach the checks to also read pending shards) is mechanical: convert each
pending shard row (a dict) to the same 6-cell list shape via `HEADER_FIELDS`, append to whatever
the CSV scan already produced, and every downstream line (`_status_for_row`, the duplicate/reopen
logic) needs zero changes. Option (b) (keep a synchronous CSV write, change what's written to
avoid collision) has no equivalent mechanical path — a squash-merge conflict is about *identical
insertion points*, not row semantics, so nothing about "what's written" fixes it without also
changing *where* it's written, which is option (a) by another name.

## `record_hand_orchestrated_closure.py`'s own double-write guard — the second real consumer

`_existing_row_for()` was the second, easy-to-miss consumer: it currently scans only the canonical
CSV to decide whether `append_working_log_row()` was already called directly for this exact
`(ticket_id, title)` before running this script. Once `append_working_log_row()` stages instead of
writing the CSV directly, a prior direct call becomes invisible to a CSV-only scan — the guard
would silently stop catching the exact double-write shape it exists to catch. Confirmed by tracing
the call graph, not assumed: this needed the same pending-shard read as the two `done_checker_
static.py` checks, which is why `working_log_parser.parse_pending_working_log_shards()` is a
shared function rather than living inside either caller.

## Absorbing into `monitoring_consolidation.py` (Open Question 2) — confirmed, with one structural
difference from the JSONL shards

Read `monitoring_consolidation.py` in full. `consolidate_jsonl_kind()` is inherently per-week (each
`runs.jsonl`/`events.jsonl`/`tools.jsonl` canonical file lives inside its own week directory).
`tickets/working_log.csv` is a single flat file for the whole repo's history, not week-sharded —
so working_log consolidation cannot reuse `consolidate_week()`'s per-week loop unchanged; it needs
one pass across every week directory's `*.working_log.jsonl` shards at once. This is why
`consolidate_pending_rows()` is a separate function (called once from `consolidate_all()`, not
folded into `JSONL_KINDS`) rather than a fourth entry in that tuple.

**A genuine new correctness requirement the JSONL shards never had**: `runs.jsonl`/`events.jsonl`/
`tools.jsonl` are read via aggregation (counts, lookups by `run_id`), so the *order* rows land in
the canonical file has never mattered. `working_log.csv` is read sequentially by humans and by
`working_log_parser.py`'s "kept vs duplicate" logic in append order — AC4 explicitly requires
"byte-identical... row order" after consolidation. `consolidate_jsonl_kind()`'s own ordering
(sorted filename, then file-internal line order) does NOT guarantee chronological order when
consolidating shards from *multiple different batches* in one pass — a branch named `aaa-fix`
merged after `zzz-fix` still sorts first alphabetically. Fixed by sorting the collected rows by
their own `timestamp` field before appending (every row already carries one; no new field needed),
with Python's stable sort keeping file/line order as the tiebreak for equal timestamps.

## `.gitattributes`/AST-guard interaction — where the CSV write physically lives

`tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer` asserts
`working_log_writer.py` is the *only* file that ever opens `tickets/working_log.csv` in write
mode. Consolidation therefore cannot open that file from inside `monitoring_consolidation.py`
itself without breaking that invariant — `consolidate_pending_rows()` (the one function that
calls the module-private `_append_csv_row()`) lives in `working_log_writer.py`, and
`monitoring_consolidation.py` only ever calls into it, confirmed by re-running the AST guard after
the change (unchanged: still exactly 1 hit, inside `working_log_writer.py`).

## Sweep for other synchronous readers (Open Question 3)

Grepped every call site of `check_working_log_exactly_one_row`/`check_working_log_no_row_yet`
(`done_checker_static.py`'s own `run_static_precheck`, `implement-ticket.js`'s Verify-phase
static-precheck invocation) — confirmed `check_working_log_exactly_one_row` is only reachable from
`run_finalize_selfcheck` (Part B, post-Finalize), never Part A. No other gate reads
`tickets/working_log.csv` synchronously at a ticket's own close beyond the two already named.
`tools/retrieval_events.py`'s own undiscovered write-formula copy (the shard ticket's own
cautionary precedent) writes a *different* JSONL kind entirely, unrelated to working_log; not a
working_log write-path copy, so out of scope here regardless.

## Existing test coupling to the old direct-write behavior

Many existing tests across `test_working_log_writer.py` and `test_record_hand_orchestrated_
closure.py` call `append_working_log_row(..., path=some_scratch_csv)` purely to seed a scratch CSV
file directly (testing round-trip/LF/tricky-field correctness, or seeding "there's already a row"
fixtures for other functions' tests) — none of them are actually testing the *staging* behavior.
Rather than rewrite dozens of tests around a consolidation step they were never exercising,
`append_working_log_row()` keeps `path`, when explicitly given, meaning "write this CSV row
directly to this path" (unchanged, pre-this-ticket behavior) — only the no-`path` case (the *only*
way any real caller ever invokes it) goes through staging. This kept every existing test's
original intent and assertions valid unchanged, and is disclosed explicitly in the function's own
docstring rather than left as an implicit compatibility shim.

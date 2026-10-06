# Investigation — TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS

- `build_records` wrote `start_ts or now` / `end_ts or now`; `record_run.compute_duration_s` then returned 0. Design decisions come from the TIME-SOURCE-DESIGN stored artifacts (claim algorithm, `MIN_CLAIMED_ROWS = 3`, 1800 s block gap reusing `duration_utils.PAUSE_THRESHOLD_SECONDS`).
- `start_ts` stays required in `record_run.REQUIRED`, so unknown records `start_ts == end_ts` with `duration_s: null`; `generate_retro.generate` and the duplicate-run check load such rows (tested).
- `--end-ts` alone bounds the derivation; `--start-ts` makes the source `declared`. A declared span that comes out negative degrades to `unknown` (the duration is null, so the label must not claim a measurement).
- Reading is bounded to the current and previous ISO-week folders; `*tools.jsonl` matches both the hook's unconsolidated `tools.jsonl` and branch shards.
- The closure that records itself runs in the session that did the work, so the session's own rows are the evidence; a closure from a session with no hooks (see TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS) records `unknown`, which is the honest answer.

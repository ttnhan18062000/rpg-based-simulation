# Plan — TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT

## Steps
1. Create `tools/agent-monitoring/duration_utils.py`:
   - `PAUSE_THRESHOLD_SECONDS = 1800` module constant (see investigation.md Decision 2).
   - `_parse_ts(ts_str)` — returns `datetime` or `None`, matching the existing
     `datetime.fromisoformat(ts_str.replace("Z", "+00:00"))` pattern used throughout
     `tools/agent-monitoring/*.py`; never raises.
   - `compute_active_idle_split(start_ts, end_ts, events, pause_threshold_s=PAUSE_THRESHOLD_SECONDS) -> dict | None`:
     builds a sorted-by-ts timeline of `[("start", start_dt), *(label, event_dt) for valid events, ("end", end_dt)]`
     (see investigation.md Decision 1), skips events with unparseable `ts` (scope requirement),
     returns `None` if `start_ts`/`end_ts` themselves don't parse. Returns
     `{total_duration_s, active_duration_s, idle_gap_s, largest_gap_s, largest_gap_from,
     largest_gap_to, pause_threshold_s}`. `active_duration_s = total - idle_gap_s` (complement,
     invariant holds by construction).
2. Wire into `generate_retro.py`:
   - Build a `run_id -> events` index once (events already loaded); for each row in `slow_runs_list`
     and each `duration_s` outlier row, call `compute_active_idle_split` and attach
     `active_duration_s`/`idle_gap_s` (raw seconds; renderer converts to minutes) when non-None.
   - Render: add columns to the Slow Runs table and Duration outliers table; add one italic
     disclaimer line (mirroring the existing Outliers caveat style) when a row's `idle_gap_s`
     exceeds half its `duration_s` — i.e. the reported "slowness" is dominated by idle time, not
     active work.
3. `retrieval_baseline_metrics.py`:
   - `build_duration_section(runs, events)` — index events by run_id, call
     `compute_active_idle_split` per row, replace the static `"pause-contaminated"` flag/note with
     real `active_duration_s`/`idle_gap_s` fields (keep a `flag` key only when idle_gap_s > 0, for
     backward-compatible shape).
   - Update the one caller (`build_baseline_report`) to pass `events` through.
4. Docs: `docs/agent-monitoring/schema.md` `### What is not recorded` gains a new bullet on
   `duration_s`'s naive-wall-clock limitation, cross-referencing `active_duration_s`/`idle_gap_s`
   by name, same bold-lead-in voice as the existing Token-counts bullet.
5. Tests:
   - `tests/tools/test_duration_utils.py` (new): normal split, all-active (gap below threshold),
     all-idle (single huge gap / zero events), seq-collision case (two events same `seq`, real
     `ts` out of seq order — confirms strict ts-ordering), missing/non-string event `ts` skipped
     without crashing, unparseable `start_ts`/`end_ts` returns `None`, sum invariant
     (`active + idle == total`) asserted directly, and the AC5 real-corpus reproduction
     (`TCK-20260710-SIMQ-DEPTH-SOCIAL`: idle_gap_s captures the ~590.6 min gap, active_duration_s
     materially below raw 828 min).
   - `tests/tools/test_generate_retro.py`: extend/add rendering assertions for the new columns.
   - `tests/tools/test_retrieval_baseline_metrics.py`: rewrite
     `test_baseline_report_flags_duration_as_pause_contaminated_when_no_gap_aware_view_exists` for
     the new real-computation shape; retire+replace the trip-wire test
     (`test_baseline_report_would_prefer_gap_aware_view_if_available`) with a real positive
     assertion that `build_duration_section` now uses `duration_utils`.
6. Parity ledger: new `infrastructure.yaml` entry for this real behavior change.
7. Finalize per CLAUDE.md — do NOT move the batch folder yet (sibling ticket 2 not done).

## Explicit non-goals (Out of Scope, restated)
- No re-ranking of Slow Runs by `active_duration_s` — additive/flagging only.
- No rewriting of historical `RETRO-*.md` reports.
- No write-path change to `runs.jsonl`/`events.jsonl` — pure read-time computation.
- No dashboard changes (sibling ticket 2).

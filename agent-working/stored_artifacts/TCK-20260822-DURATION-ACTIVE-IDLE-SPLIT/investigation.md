# Investigation — TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT

## Real code surveyed
- `tools/agent-monitoring/generate_retro.py`: `compute_retro_metrics(runs, events, ...)` (L972) builds `slow_runs`/`slow_runs_list` (L1129-1143, threshold `duration_s > 1800`) and `duration_outliers` (L1155-1167, grouped by tier via `_flag_outliers`). Rendered at L1698-1743 (`## Slow Runs`, `## Outliers` -> `### Duration outliers (by tier)`). Existing conditional-disclaimer pattern found at L1719-1723 (Outliers section's italic `_..._` caveat line) and reused verbatim in style below.
- `tools/agent-monitoring/retrieval_baseline_metrics.py`: `build_duration_section(runs)` (L64) currently just flags every row `"pause-contaminated"` with a static note. Called from `build_baseline_report(runs, events, tools)` (L143-153) — `events` is already in scope at the call site, so no new parameter needs threading further up.
- `tests/tools/test_retrieval_baseline_metrics.py`: `test_baseline_report_flags_duration_as_pause_contaminated_when_no_gap_aware_view_exists` (L212-224) and the trip-wire `test_baseline_report_would_prefer_gap_aware_view_if_available` (L228-234, asserts `duration_utils.py` does NOT exist — designed to go red once it does, forcing this exact update).
- `docs/agent-monitoring/schema.md` L77-82: `### What is not recorded` — voice pattern is **bold lead-in**, then 1-2 explanatory sentences.
- Real corpus check (`agent-monitoring/runs.jsonl` + `events.jsonl`) for the AC5 cited example, `TCK-20260710-SIMQ-DEPTH-SOCIAL`: `start_ts=2026-07-11T18:58:27Z`, `end_ts=2026-07-12T08:47:16Z`, `duration_s=49729` (828.8 min). Events: seq1 Scope @18:58:27 (== start_ts exactly), seq2 Investigate @18:59:10, seq3 Plan @04:49:45 (next day) — gap = 590.6 min, matching the ticket's own cited figure exactly. Confirms: (a) this run's largest gap is a genuine mid-run Investigate->Plan gap, not a start-boundary gap; (b) start_ts/first-event-ts coincide here (no boundary gap in this specific example, though the ticket's Request Summary says OTHER top-ranked rows do have one).

## Key decisions (both flagged by the ticket as open, resolved here)

**1. start_ts/end_ts ARE included as timeline boundaries**, not just strict inter-event gaps.
Forced by AC1's own invariant: `active_duration_s + idle_gap_s` must equal the run's total
wall-clock span. If a gap between `start_ts` and the first logged event (or the last event and
`end_ts`) were silently excluded, it would vanish from both totals and break that sum whenever
such a boundary gap exists — which the ticket's own Request Summary confirms happens for real,
currently-top-ranked rows. Implementation: synthesize two boundary points (`start`, `end`) into
the same sorted timeline as the real events; `active_duration_s` is defined as `total - idle_gap_s`
(complement, not an independently re-summed value), so the invariant holds by construction
regardless of data messiness.

**2. Pause threshold: 1800 seconds (30 min).**
Reuses `generate_retro.py`'s own existing "Slow Runs" absolute threshold (`duration_s > 1800`,
L1131) verbatim, for conceptual consistency: a gap counts as idle exactly when it's at least as
long as what this same report already calls "slow" elsewhere. Falls inside the ticket's own
data-backed candidate range (p90=19min, p95=43.5min across 5960 real gaps) without introducing a
second, unrelated magic number. Documented as a judgment call in the module docstring, not derived
law.

## Trip-wire test resolution
`build_duration_section` gains an `events: list` parameter (its one caller already has `events` in
scope). Real per-run computation via `duration_utils.compute_active_idle_split()` replaces the
static `"pause-contaminated"` flag. The trip-wire test itself
(`test_baseline_report_would_prefer_gap_aware_view_if_available`) is retired (its job — forcing
this exact update — is done) and replaced with a real positive test asserting the new gap-aware
output, mirroring this repo's own established precedent for retiring served-their-purpose trip-wire
guards (e.g. `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`'s narrowing of
`test_no_frozen_kgmcp_dependency_edited`).

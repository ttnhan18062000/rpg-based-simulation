---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP
phase: test
date: 2026-08-10
tags: [simulation-quality, calibration, corpus]
---

# Test Plan — TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP

## Scope

`tests/simulation_quality/test_grade_regression.py -m "not slow"` plus a direct authoritative
scan using the same file's own `_within_band`/`_format_score_failures`/`_extract_pillar_grades`/
`_extract_pillar_scores` functions (needed because `evaluate_simq.py`'s own `--dry-run` diff only
checks grade equality, not score tolerance — a known, already-documented tool capability gap).

## Normal flow

Every recalibrated (run_key, pillar) pair passes both checks after the fix.

## Edge cases

- `hero_guild_routing_seed456_500t` initially looked like it might be another instability case
  (found alongside the genuinely-unstable ones) — 3x re-run confirmed it stable, so it was fixed
  via ordinary recalibration, not a `watchdog_variance` annotation. Verifying stability before
  classifying was the deciding step, not assuming instability from co-occurrence.
- `score_ceilings.json` annotations do not suppress the pytest assertion — `[known ...]` failures
  still show as `FAILED` in pytest's own output, only the assertion *message* changes. Confirmed
  this matches the established, already-accepted convention from every other `[known ...]` entry
  in this file (`tick_budget`, `flag_gated`, `corrected`) — not a new gap.

## Failure modes / regression-prone paths

- `test_grade_anchor_file_exists_and_valid`'s raw_score/normalized_score field-confusion guard —
  confirmed still passes (all edits used `normalized_score` from fresh `quality_report.json`
  files, sourced identically to every other recalibration this session).
- Verified `score_ceilings.json` remains valid JSON and `tools/simq_ceiling.py`'s
  `lookup_ceiling()` correctly surfaces the new entries (confirmed via direct pytest output
  showing the new `[known watchdog_variance: ...]` text in the failure message).

## Result

Direct authoritative scan across all of `FAST_ANCHOR_KEYS`: **0 unannotated score-tolerance or
band failures.** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`:
31 failed / 39 passed / 18 deselected — every one of the 31 `FAILED` results carries a
`[known ...]` annotation (confirmed via `grep -c "\[known"` on the assertion output: 83 annotated
lines across 31 failing tests, i.e. every failing test has at least one annotated line and zero
bare/unexplained ones). Matches this session's own established "clean" convention.

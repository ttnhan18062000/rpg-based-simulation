# Corpus sweep: a25619971 (parent) vs d914bace7 (#769), 2026-10-31

Measurement only. 81 anchored scenarios, 162 runs (one per commit per key), 11:37 to 13:14, sequential on cores 4-5, `systemd-run ... MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, PYTHONHASHSEED=0, `tools/evaluate_simq.py --scenario <key>` (calibrate_simq --audit-mode, profile feature flags applied), clean `git archive` trees, `grade_anchors.json` held at one copy (d914bace7's, byte-equal to the worktree's) for both. rc=1 lines in `sweep_done_lines.txt` are the evaluator's own regression exit (a report is written); no run hung or failed to write a report; 81 of 81 keys have both reports.

`moved_keys.md` is `compare_sweep.py` output over all 810 pillar anchors (338 no-data anchors with `status`, 472 scored anchors with `grade` and `score`). Correction: the first version of the script skipped the 472 scored anchors, so its first table showed only 3 rows; the table here is the fixed run. "In tolerance" is the test's own `_within_score_tolerance` with abs_floor plus a grade band of +/-1, or for a no-data anchor "stays no-data".

Result: 85 of 810 pillar anchors moved between the two commits; 16 move from inside to outside tolerance; 38 are already outside tolerance at the parent. No anchor was touched.

Exit codes: 7 of 162 runs exited rc=1 (checked in all 7 logs): simq_routing_test_seed123_500t and hero_guild_routing_seed123_500t at both commits (COGNITION C to A, identical at both), and urban_political_seed42_500t, _1000t and _2000t at d914bace7 only (COGNITION no-data to B, FACTION C to no-data). All are the evaluator's REGRESS verdict; a quality_report.json exists for each, and no log has a traceback.

`moved_keys.md` now also ends with the 38 pillar anchors already outside tolerance at the parent a25619971 (pre-existing reds, not #769's; no re-anchor under this ticket). Of those 38, 11 (urban_political seed456 500t and 1000t) also move between the two commits while already out; they are not among the 16 in-to-out rows.

# Corpus sweep: a25619971 (parent) vs d914bace7 (#769), 2026-10-31

Measurement only. 81 anchored scenarios, 162 runs (one per commit per key), 11:37 to 13:14, sequential on cores 4-5, `systemd-run ... MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, PYTHONHASHSEED=0, `tools/evaluate_simq.py --scenario <key>` (calibrate_simq --audit-mode, profile feature flags applied), clean `git archive` trees, `grade_anchors.json` held at one copy (d914bace7's, byte-equal to the worktree's) for both. rc=1 lines in `sweep_done_lines.txt` are the evaluator's own regression exit (a report is written); no run hung or failed to write a report; 81 of 81 keys have both reports.

`moved_keys.md` is `compare_sweep.py` output over all 810 pillar anchors (338 no-data anchors with `status`, 472 scored anchors with `grade` and `score`). Correction: the first version of the script skipped the 472 scored anchors, so its first table showed only 3 rows; the table here is the fixed run. "In tolerance" is the test's own `_within_score_tolerance` with abs_floor plus a grade band of +/-1, or for a no-data anchor "stays no-data".

Result: 85 of 810 pillar anchors moved between the two commits; 16 move from inside to outside tolerance; 38 are already outside tolerance at the parent. No anchor was touched.

---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED
date: 2026-10-05
tags: [ai, process-improvement]
---

# Investigation: TCK-20261004-DATA-RUNS-CLEAN-NOT-SESSION-SCOPED

Reported by rpg-feature-planning: the post-Test cleanup removed 3684 files across 14 PID suffixes. Verified in `done_checker_static.py`: `_find_flagged_data_run_files` flags every file with `mtime >= start_ts` and `clean_data_runs_early` unlinked them all, with the concurrent-session overlap documented as an accepted tradeoff. The files carry no owner, and a PID check is no fix because PIDs recycle. Design's writer inventory (six-plus rpg/observability writers, one tools writer) ruled out marking at the writers; the owner chose report-only.

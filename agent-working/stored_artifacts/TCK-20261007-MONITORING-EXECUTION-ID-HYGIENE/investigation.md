---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE
artifact_type: investigation
tags: [agent-monitoring, retro]
---

# Investigation

Baseline measured on origin/main 821d543a6 (2026-10-08), not taken from the ticket:
- `make agent-monitoring-validate`: **165 warnings** (the ticket said 139, the epic 318), 2144 run rows, 13878 events, exit 0. Of the 165 warnings: 164 are "Run marked DONE has no working_log entry" and 1 is an incomplete run. The Scope/seq=1 collisions (26 tickets) are a separate printed report, not counted among the warnings. Errors: none.
- Run rows without `execution_id`: **1012 of 2144**. By week: W34 74, W35 13, W36 22, W37 1, W39 1, **W40 5, W41 4**, unknown-week 5, the rest before W34. W40+ is 9 rows, not 8.
- The 9 W40+ rows: W40, 5 rows from `create-tickets` (3) and `implement-epic` (2, `FOLDER-*`); W41, 2 rows `TCK-20261006-NATIVE-RUN-FAILING-GATE-PROBE` (a deliberate failing-gate probe, workflow implement-ticket) and 2 `create-tickets` rows (`CREATE-TICKETS-*`).
- Why create-tickets / implement-epic omit it: their own comments (`implement-epic.js:167`, `create-tickets.js:185`) say the native runtime has no clock or shell, the sidecar helper omits `execution_id`/`provider`, and `post_tool_hook.py` tolerates the absence. `implement-ticket.js` makes `execution_id_suffix` a required arg of the native runtime (:211), so its rows carry one except for a probe that ran without it.
- Tiers: `epic_batch` 1 and `epic-batch` 1 (both `unknown-week`/old), null tier 21, `n/a` 50 (create-tickets, canonical for that workflow). `validate.py` already prints non-canonical tiers and null required fields (`compute_drift_report`) and the Scope/seq=1 collisions (`compute_multi_invocation_collision_report`). What it does NOT report: execution_id gaps by class, and tools-shard lines the loader skips.
- Loader-skipped tools rows: **0 on current main**. The three torn lines (planner, rpg, rpg-planner shards) were repaired today, and the writer no longer produces them, so the ticket's "3 rows" are stale. The report is still worth having: `load_jsonl_with_line_count` can show a count of lines it could not parse.
- Finding outside scope: the "DONE has no working_log entry" check reads only `working_log.csv`, but new closures write working_log rows to per-branch shards. 126 of the 164 warnings name a TCK-202609xx or TCK-202610xx closure, including ones recorded today; those are false positives of that kind (the CSV has 2340 TCK rows while 66 working_log shards exist in W41 alone). The ticket lists this class as out of scope; it dominates the W40+ count, so the plan reports W40+ warnings split by class.

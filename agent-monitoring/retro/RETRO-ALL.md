# Agent Monitoring Retro — All Time

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 481 |
| Completed (DONE) | 403 (83%) |
| Gate failures | 58 |
| Avg duration | 0 min |
| Avg agents per run | 5.1 |
| Total agent calls | 1965 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| success | 16 | 3% |
| completed | 12 | 2% |
| None | 10 | 2% |
| complete | 8 | 1% |
| done | 5 | 1% |
| DOD_BLOCKED | 2 | 0% |
| INPROGRESS | 1 | 0% |
| NEEDS_HUMAN_INPUT | 1 | 0% |
| GATE_FAIL | 1 | 0% |
| ALL_SCOPED | 1 | 0% |
| STOPPED_BY_USER | 1 | 0% |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 58 | 19 | 31 | 79% |
| epic-batch | 1 | 0 | 1 | 100% |
| epic_batch | 1 | 1 | 0 | 0% |
| hotfix | 62 | 0 | 60 | 96% |
| standard | 338 | 0 | 296 | 87% |
| unknown | 21 | 0 | 15 | 71% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 258 | 0 | 0 | 0 | 0 |
| architecture-reviewer | 134 | 110 | 11 | 0 | 13 |
| claude | 23 | 22 | 0 | 1 | 0 |
| claude-sonnet | 9 | 9 | 0 | 0 | 0 |
| claude-sonnet-4-6 | 16 | 16 | 0 | 0 | 0 |
| coordinator | 1 | 1 | 0 | 0 | 0 |
| doc-writer | 2 | 2 | 0 | 0 | 0 |
| dod-verifier | 1 | 1 | 0 | 0 | 0 |
| done-checker | 130 | 128 | 2 | 0 | 0 |
| epic-coordinator | 7 | 7 | 0 | 0 | 0 |
| epic-discoverer | 1 | 1 | 0 | 0 | 0 |
| epic-loop | 1 | 1 | 0 | 0 | 0 |
| epic-reporter | 1 | 1 | 0 | 0 | 0 |
| epic-runner | 1 | 1 | 0 | 0 | 0 |
| finalizer | 134 | 134 | 0 | 0 | 0 |
| hotfix-agent | 5 | 5 | 0 | 0 | 0 |
| implement | 1 | 1 | 0 | 0 | 0 |
| implement-epic | 19 | 19 | 0 | 0 | 0 |
| implement-ticket | 270 | 262 | 3 | 0 | 0 |
| implementer | 211 | 210 | 1 | 0 | 0 |
| investigator | 132 | 119 | 0 | 0 | 13 |
| main | 6 | 6 | 0 | 0 | 0 |
| manual-hotfix | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 27 | 26 | 0 | 1 | 0 |
| orchestrator-audit | 1 | 1 | 0 | 0 | 0 |
| orchestrator-fix | 3 | 3 | 0 | 0 | 0 |
| parity-checker | 3 | 3 | 0 | 0 | 0 |
| parity-updater | 125 | 122 | 0 | 0 | 3 |
| plan-expander | 1 | 1 | 0 | 0 | 0 |
| plan-fixer | 6 | 6 | 0 | 0 | 0 |
| planner | 129 | 115 | 0 | 1 | 13 |
| planner+implementer | 1 | 1 | 0 | 0 | 0 |
| reviewer | 4 | 4 | 0 | 0 | 0 |
| scope-agent | 9 | 9 | 0 | 0 | 0 |
| scoper | 4 | 4 | 0 | 0 | 0 |
| test-runner | 2 | 2 | 0 | 0 | 0 |
| test-scoper | 133 | 131 | 0 | 1 | 1 |
| tester | 4 | 4 | 0 | 0 | 0 |
| ticket-scoper | 145 | 145 | 0 | 0 | 0 |
| verifier | 2 | 2 | 0 | 0 | 0 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 258 |
| Truncated (>200 chars) | 46 |

## Slow Runs (> 30 min)

_No slow runs this period._

## Notes

**This report was regenerated under `TCK-20260705-RETRO-METRIC-ACCURACY`, which corrected three counting bugs in `generate_retro.py`** (the empty-summary false alarm, the epic DONE-rate miscalculation, and a missing `final_status`/`status` legacy-schema fallback that pervaded every DONE/gate-fail computation in the file). The original raw findings that motivated this fix — the pre-fix report showing `71% DONE`, `44% epic DONE rate`, and `246 empty summaries — check agent prompts` — are preserved verbatim in `stored_artifacts/TCK-20260705-RETRO-METRIC-ACCURACY/` for historical reference. If you're comparing this report against an older copy or a prior session's notes and the numbers look different, that's why: the underlying `runs.jsonl`/`events.jsonl` data didn't change, the counting logic did.

1. **What failed most?** `architecture-reviewer` — 11 failed / 134 calls (8%) all-time. Read alongside `done-checker`'s 2/130 (1.5%) and `implement-ticket`'s 3/270 (1.1%), the gate structure is doing real work catching real issues, not rubber-stamping.

2. **What was slow?** Not assessable from this data — `Avg duration: 0 min` and zero slow runs flagged is not credible given 481 runs including many multi-phase standard-tier tickets. This is very likely an artifact of a missing-`end_ts` data-integrity gap (tracked separately in `TCK-20260705-MONITORING-RUNID-JOIN`), not a real signal. Fix the data before trusting this metric.

3. **What to change, in priority order:**
   - **Overall DONE rate is now correctly 83% (403/481)** after the schema-fallback fix — previously reported as 71% (342/480), which undercounted by misclassifying legacy `status`-only DONE runs as gate failures. `epic` tier is now correctly 79% (31/39, excluding the 19 correctly-scoped `EPIC_SCOPED` epics from the denominator) rather than the previous misleading 44% (26/58). `hotfix` (96%) and `standard` (87%) remain healthy.
   - **Empty-summary count is now 0 under "current schema"; the previous 246 was 100% legacy-data noise** from 258 pre-normalization `events.jsonl` records (`agent: null`) that never had a `summary` field. `Truncated (>200 chars)` remains a real, live finding at 46, unchanged by this fix — worth a follow-up to audit which agent prompts most often produce truncated output.
   - **`make agent-monitoring-validate` warnings (missing `end_ts`, zero-event runs, `working_log.csv` mismatches)** remain an open, unrelated data-integrity issue, tracked in `TCK-20260705-MONITORING-RUNID-JOIN` and (partially) closed for the `working_log.csv`-mismatch case by `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`.

4. **What worked?** `ticket-scoper` (145/145 ok) and `finalizer` (134/134 ok) remain the two most reliable phases in the entire pipeline. `hotfix` tier's 96% DONE rate confirms the fast-path routing genuinely works.

# Agent Monitoring Retro — All Time

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 484 |
| Completed (DONE) | 406 (83%) |
| Gate failures | 58 |
| Avg duration | 0 min |
| Avg agents per run | 5.1 |
| Total agent calls | 1991 |

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
| epic | 59 | 19 | 32 | 80% |
| epic-batch | 1 | 0 | 1 | 100% |
| epic_batch | 1 | 1 | 0 | 0% |
| hotfix | 62 | 0 | 60 | 96% |
| standard | 340 | 0 | 298 | 87% |
| unknown | 21 | 0 | 15 | 71% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 258 | 0 | 0 | 0 | 0 |
| architecture-reviewer | 139 | 112 | 14 | 0 | 13 |
| claude | 23 | 22 | 0 | 1 | 0 |
| claude-sonnet | 9 | 9 | 0 | 0 | 0 |
| claude-sonnet-4-6 | 16 | 16 | 0 | 0 | 0 |
| coordinator | 1 | 1 | 0 | 0 | 0 |
| doc-writer | 2 | 2 | 0 | 0 | 0 |
| dod-verifier | 1 | 1 | 0 | 0 | 0 |
| done-checker | 132 | 130 | 2 | 0 | 0 |
| epic-coordinator | 7 | 7 | 0 | 0 | 0 |
| epic-discoverer | 1 | 1 | 0 | 0 | 0 |
| epic-loop | 1 | 1 | 0 | 0 | 0 |
| epic-reporter | 1 | 1 | 0 | 0 | 0 |
| epic-runner | 1 | 1 | 0 | 0 | 0 |
| finalizer | 136 | 136 | 0 | 0 | 0 |
| hotfix-agent | 5 | 5 | 0 | 0 | 0 |
| implement | 1 | 1 | 0 | 0 | 0 |
| implement-epic | 19 | 19 | 0 | 0 | 0 |
| implement-ticket | 273 | 265 | 3 | 0 | 0 |
| implementer | 213 | 212 | 1 | 0 | 0 |
| investigator | 135 | 122 | 0 | 0 | 13 |
| main | 6 | 6 | 0 | 0 | 0 |
| manual-hotfix | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 27 | 26 | 0 | 1 | 0 |
| orchestrator-audit | 1 | 1 | 0 | 0 | 0 |
| orchestrator-fix | 3 | 3 | 0 | 0 | 0 |
| parity-checker | 3 | 3 | 0 | 0 | 0 |
| parity-updater | 127 | 122 | 0 | 0 | 5 |
| plan-expander | 1 | 1 | 0 | 0 | 0 |
| plan-fixer | 6 | 6 | 0 | 0 | 0 |
| planner | 132 | 118 | 0 | 1 | 13 |
| planner+implementer | 1 | 1 | 0 | 0 | 0 |
| reviewer | 4 | 4 | 0 | 0 | 0 |
| scope-agent | 9 | 9 | 0 | 0 | 0 |
| scoper | 4 | 4 | 0 | 0 | 0 |
| test-runner | 2 | 2 | 0 | 0 | 0 |
| test-scoper | 135 | 133 | 0 | 1 | 1 |
| tester | 4 | 4 | 0 | 0 | 0 |
| ticket-scoper | 147 | 147 | 0 | 0 | 0 |
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

**Regenerated under `TCK-20260705-RETRO-INDEX-ALL-ROW`**, which fixed `agent-monitoring/retro/index.md`'s "ALL" row (previously hardcoded to `0|0|0` since the retro tool was built — `_update_index()` looked up `runs_by_week.get("ALL", [])`, but no run's ISO week is ever literally `"ALL"`). The index's ALL row now correctly matches this report's own Run Summary (484 runs, 406 DONE, 58 gate failures) using the same `_resolve_status()` helper this report already uses. No counting logic changed in this report itself — only `index.md`'s separate lookup bug was fixed.

**Known friction, not fixed here**: `generate_retro.py`'s `generate()` unconditionally resets this Notes section to a placeholder on every regeneration — it has already had to be manually re-added twice in one session (once after `TCK-20260705-RETRO-METRIC-ACCURACY`'s implementation, once after its own test-phase re-run, and now a third time after this ticket's verification re-run). This is a real, recurring gap worth its own small follow-up (e.g. preserve/re-inject an existing Notes section rather than overwrite it), not addressed in this ticket.

1. **What failed most?** `architecture-reviewer` — 14 failed / 139 calls (10%) all-time. Still reads as the gate doing real work — see `TCK-20260705-MONITORING-RUNID-JOIN`'s own history (3 substantive correction rounds) for a concrete recent example.
2. **What was slow?** Still not assessable — `Avg duration: 0 min` remains not credible for older runs; the missing-`end_ts` investigation (`TCK-20260705-MONITORING-RUNID-JOIN`) reduced false "crashed run" warnings to 1 but did not backfill `duration_s`.
3. **What to change?** Data-integrity debt from the June 19 – July 1 window is now substantially addressed. Remaining known follow-ups: `TCK-20260705-WORKING-LOG-BACKFILL` (62 tickets missing a `working_log.csv` row) and `TCK-20260705-SIX-SKILLS-INVESTIGATION` (unrelated — a skill-usage question). Consider filing the Notes-placeholder-reset friction (above) as its own small ticket.
4. **What worked?** `ticket-scoper` (147/147 ok) and `finalizer` (136/136 ok) remain the two most reliable phases in the entire pipeline.

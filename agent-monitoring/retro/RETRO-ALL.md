# Agent Monitoring Retro — All Time

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 480 |
| Completed (DONE) | 342 (71%) |
| Gate failures | 119 |
| Avg duration | 0 min |
| Avg agents per run | 5.1 |
| Total agent calls | 1956 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| None | 105 | 21% |
| success | 6 | 1% |
| DOD_BLOCKED | 2 | 0% |
| done | 1 | 0% |
| INPROGRESS | 1 | 0% |
| NEEDS_HUMAN_INPUT | 1 | 0% |
| GATE_FAIL | 1 | 0% |
| ALL_SCOPED | 1 | 0% |
| STOPPED_BY_USER | 1 | 0% |

## Tier Distribution

| Tier | Count | DONE count | DONE rate |
|---|---|---|---|
| epic | 58 | 26 | 44% |
| epic-batch | 1 | 1 | 100% |
| epic_batch | 1 | 0 | 0% |
| hotfix | 61 | 57 | 93% |
| standard | 338 | 257 | 76% |
| unknown | 21 | 1 | 4% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 258 | 0 | 0 | 0 | 0 |
| architecture-reviewer | 133 | 110 | 11 | 0 | 12 |
| claude | 23 | 22 | 0 | 1 | 0 |
| claude-sonnet | 9 | 9 | 0 | 0 | 0 |
| claude-sonnet-4-6 | 16 | 16 | 0 | 0 | 0 |
| coordinator | 1 | 1 | 0 | 0 | 0 |
| doc-writer | 2 | 2 | 0 | 0 | 0 |
| dod-verifier | 1 | 1 | 0 | 0 | 0 |
| done-checker | 129 | 127 | 2 | 0 | 0 |
| epic-coordinator | 7 | 7 | 0 | 0 | 0 |
| epic-discoverer | 1 | 1 | 0 | 0 | 0 |
| epic-loop | 1 | 1 | 0 | 0 | 0 |
| epic-reporter | 1 | 1 | 0 | 0 | 0 |
| epic-runner | 1 | 1 | 0 | 0 | 0 |
| finalizer | 133 | 133 | 0 | 0 | 0 |
| hotfix-agent | 5 | 5 | 0 | 0 | 0 |
| implement | 1 | 1 | 0 | 0 | 0 |
| implement-epic | 19 | 19 | 0 | 0 | 0 |
| implement-ticket | 270 | 262 | 3 | 0 | 0 |
| implementer | 210 | 209 | 1 | 0 | 0 |
| investigator | 131 | 119 | 0 | 0 | 12 |
| main | 6 | 6 | 0 | 0 | 0 |
| manual-hotfix | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 27 | 26 | 0 | 1 | 0 |
| orchestrator-audit | 1 | 1 | 0 | 0 | 0 |
| orchestrator-fix | 3 | 3 | 0 | 0 | 0 |
| parity-checker | 3 | 3 | 0 | 0 | 0 |
| parity-updater | 124 | 122 | 0 | 0 | 2 |
| plan-expander | 1 | 1 | 0 | 0 | 0 |
| plan-fixer | 6 | 6 | 0 | 0 | 0 |
| planner | 128 | 115 | 0 | 1 | 12 |
| planner+implementer | 1 | 1 | 0 | 0 | 0 |
| reviewer | 4 | 4 | 0 | 0 | 0 |
| scope-agent | 9 | 9 | 0 | 0 | 0 |
| scoper | 4 | 4 | 0 | 0 | 0 |
| test-runner | 2 | 2 | 0 | 0 | 0 |
| test-scoper | 132 | 130 | 0 | 1 | 1 |
| tester | 4 | 4 | 0 | 0 | 0 |
| ticket-scoper | 144 | 144 | 0 | 0 | 0 |
| verifier | 2 | 2 | 0 | 0 | 0 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary | 246 |
| Truncated (>200 chars) | 46 |

_⚠ 246 empty summaries — check agent prompts for `summary` field._

## Slow Runs (> 30 min)

_No slow runs this period._

## Notes

**This replaces a zero-data smoke-test artifact from 2026-06-12 that sat unregenerated for ~4 weeks and 310+ completed runs** — see `TCK-20260704-RETRO-LOOP-ENFORCEMENT` for the process fix (skill + nudge hook) that closes this gap going forward, and `RETRO-2026-W27.md` for this week's report.

1. **What failed most?** `architecture-reviewer` — 11 failed / 133 calls (8%) all-time. Read alongside `done-checker`'s 2/129 (1.5%) and `implement-ticket`'s 3/270 (1.1%), the gate structure is doing real work catching real issues, not rubber-stamping — consistent with this week's spot-check (see W27 notes).

2. **What was slow?** Not assessable from this data — `Avg duration: 0 min` and zero slow runs flagged is not credible given 480 runs including many multi-phase standard-tier tickets. This is very likely an artifact of the same missing-`end_ts` data-integrity gap noted below, not a real signal. Fix the data before trusting this metric.

3. **What to change, in priority order:**
   - **Overall DONE rate is 71% (342/480), below this guide's own 80% threshold.** But this is skewed by tier: `epic` tier is only 44% DONE (26/58) and `unknown` tier (no parseable tier field — legacy/malformed records) is 4% DONE (1/21). `hotfix` (93%) and `standard` (76%) are both healthy. The `epic`/`unknown` numbers likely reflect epic-batch runs that legitimately stop mid-batch on a child gate failure (not a true failure of the epic mechanism itself) and pre-schema-normalization legacy records respectively — but this should be confirmed, not assumed, before treating 71% as a real problem.
   - **246 empty summaries, 46 truncated (>200 chars), all-time** — the same finding that motivated `TCK-20260704-RETRO-LOOP-ENFORCEMENT` in the first place, now with an exact baseline. Worth a small follow-up: audit which agent prompts most often produce an empty `summary` field and tighten those specifically, rather than a blanket prompt-wording pass.
   - **`make agent-monitoring-validate` reports 180 warnings/errors** (21 runs with no `end_ts` — "CRASHED?", 5 runs with zero events at all, 38+ `DONE` runs with no matching `working_log.csv` row), concentrated in the June 19 – July 1 window (E13/E41-43/E53/E62-63 phase batches, SIMQ EMIT/WIRE batches, the June 23 FIX-* batch). This is the actual root cause of Notes point 2's untrustworthy duration/slow-run metrics, and deserves its own investigation ticket — is there a crash-handling gap in `writeMonitoring`, or a batch-mode code path that skips the run-record write on certain exits?

4. **What worked?** `ticket-scoper` (144/144 ok, 0 failures) and `finalizer` (133/133 ok) are the two most reliable phases in the entire pipeline — zero recorded failures across the full history. `hotfix` tier's 93% DONE rate confirms the fast-path routing genuinely works, not just in theory.

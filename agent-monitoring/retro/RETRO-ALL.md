# Agent Monitoring Retro — All Time

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 533 |
| Completed (DONE) | 452 (84%) |
| Gate failures | 61 |
| Avg duration | 0 min |
| Avg agents per run | 5.5 |
| Total agent calls | 2372 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| success | 16 | 3% |
| completed | 12 | 2% |
| None | 10 | 1% |
| complete | 8 | 1% |
| done | 5 | 0% |
| DOD_BLOCKED | 3 | 0% |
| NEEDS_HUMAN_INPUT | 2 | 0% |
| INPROGRESS | 1 | 0% |
| GATE_FAIL | 1 | 0% |
| ALL_SCOPED | 1 | 0% |
| STOPPED_BY_USER | 1 | 0% |
| NEEDS_CHANGES | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 12 |
| needs_human_input | 2 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 4 | 100% | 0 |
| agency | 4 | 100% | 0 |
| cognition | 3 | 100% | 0 |
| ecology | 1 | 100% | 0 |
| faction | 5 | 100% | 0 |
| feature-flags | 2 | 100% | 0 |
| information | 2 | 100% | 0 |
| observability | 3 | 100% | 0 |
| resource-registry | 4 | 75% | 1 |
| self-model | 1 | 100% | 0 |
| simulation-quality | 23 | 95% | 1 |
| stasis | 2 | 100% | 0 |
| world | 15 | 93% | 1 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| security | 1 | 0 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 66 | 19 | 39 | 82% |
| epic-batch | 1 | 0 | 1 | 100% |
| epic_batch | 1 | 1 | 0 | 0% |
| hotfix | 73 | 0 | 71 | 97% |
| standard | 371 | 0 | 326 | 87% |
| unknown | 21 | 0 | 15 | 71% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 258 | 0 | 0 | 0 | 0 |
| architecture-reviewer | 203 | 149 | 30 | 0 | 24 |
| claude | 23 | 22 | 0 | 1 | 0 |
| claude-sonnet | 9 | 9 | 0 | 0 | 0 |
| claude-sonnet-4-6 | 16 | 16 | 0 | 0 | 0 |
| coordinator | 1 | 1 | 0 | 0 | 0 |
| doc-writer | 2 | 2 | 0 | 0 | 0 |
| dod-verifier | 1 | 1 | 0 | 0 | 0 |
| done-checker | 173 | 158 | 15 | 0 | 0 |
| epic-coordinator | 7 | 7 | 0 | 0 | 0 |
| epic-discoverer | 1 | 1 | 0 | 0 | 0 |
| epic-loop | 1 | 1 | 0 | 0 | 0 |
| epic-reporter | 1 | 1 | 0 | 0 | 0 |
| epic-runner | 1 | 1 | 0 | 0 | 0 |
| finalizer | 158 | 158 | 0 | 0 | 0 |
| hotfix-agent | 5 | 5 | 0 | 0 | 0 |
| implement | 1 | 1 | 0 | 0 | 0 |
| implement-epic | 19 | 19 | 0 | 0 | 0 |
| implement-ticket | 294 | 286 | 3 | 0 | 0 |
| implementer | 251 | 249 | 2 | 0 | 0 |
| investigator | 170 | 151 | 0 | 0 | 19 |
| main | 6 | 6 | 0 | 0 | 0 |
| manual-hotfix | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 51 | 50 | 0 | 1 | 0 |
| orchestrator-audit | 1 | 1 | 0 | 0 | 0 |
| orchestrator-fix | 3 | 3 | 0 | 0 | 0 |
| parity-checker | 3 | 3 | 0 | 0 | 0 |
| parity-updater | 155 | 137 | 0 | 0 | 18 |
| plan-expander | 1 | 1 | 0 | 0 | 0 |
| plan-fixer | 8 | 8 | 0 | 0 | 0 |
| planner | 171 | 148 | 0 | 4 | 19 |
| planner+implementer | 1 | 1 | 0 | 0 | 0 |
| reviewer | 4 | 4 | 0 | 0 | 0 |
| scope-agent | 9 | 9 | 0 | 0 | 0 |
| scoper | 4 | 4 | 0 | 0 | 0 |
| test-runner | 2 | 2 | 0 | 0 | 0 |
| test-scoper | 165 | 163 | 0 | 1 | 1 |
| tester | 4 | 4 | 0 | 0 | 0 |
| ticket-scoper | 184 | 184 | 0 | 0 | 0 |
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

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

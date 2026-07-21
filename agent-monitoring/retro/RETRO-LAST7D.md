# Agent Monitoring Retro — Last 7 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 80 |
| Completed (DONE) | 71 (88%) |
| Gate failures | 9 |
| Avg duration | 95 min |
| Avg agents per run | 8.1 |
| Total agent calls | 646 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| DOD_BLOCKED | 5 | 6% |
| CONFLICTS_DETECTED | 1 | 1% |
| STOPPED_BY_USER | 1 | 1% |
| NEEDS_HUMAN_INPUT | 1 | 1% |
| NEEDS_CHANGES | 1 | 1% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 14 |
| conflicts_detected | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| cognition | 5 | 80% | 1 |
| dashboard | 14 | 100% | 0 |
| observability | 15 | 100% | 0 |
| self-model | 2 | 50% | 1 |
| simulation-quality | 13 | 84% | 2 |
| stasis | 1 | 100% | 0 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| api-design | 6 | N/A — no gate implemented |
| debugging | 4 | N/A — no gate implemented |
| performance | 1 | N/A — no gate implemented |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 8 | 0 | 6 | 75% |
| hotfix | 9 | 0 | 9 | 100% |
| n/a | 8 | 0 | 8 | 100% |
| standard | 55 | 0 | 48 | 87% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| architecture-reviewer | 100 | 83 | 9 | 0 | 8 |
| claude-fork-direct | 12 | 12 | 0 | 0 | 0 |
| create-tickets | 9 | 8 | 1 | 0 | 0 |
| done-checker | 61 | 47 | 14 | 0 | 0 |
| finalizer | 57 | 57 | 0 | 0 | 0 |
| implement-ticket | 21 | 18 | 3 | 0 | 0 |
| implement-ticket-orchestrator | 7 | 7 | 0 | 0 | 0 |
| implementer | 54 | 53 | 0 | 0 | 1 |
| investigate:C1 | 7 | 7 | 0 | 0 | 0 |
| investigate:C2 | 6 | 6 | 0 | 0 | 0 |
| investigate:C3 | 6 | 6 | 0 | 0 | 0 |
| investigate:C4 | 6 | 6 | 0 | 0 | 0 |
| investigate:C5 | 5 | 5 | 0 | 0 | 0 |
| investigate:C6 | 2 | 2 | 0 | 0 | 0 |
| investigate:direct | 1 | 1 | 0 | 0 | 0 |
| investigator | 48 | 44 | 0 | 0 | 4 |
| link-epic | 2 | 2 | 0 | 0 | 0 |
| parity-updater | 47 | 39 | 0 | 0 | 8 |
| planner | 48 | 43 | 0 | 1 | 4 |
| structure | 8 | 8 | 0 | 0 | 0 |
| test-scoper | 49 | 49 | 0 | 0 | 0 |
| ticket-scoper | 90 | 89 | 1 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 45 | 42 | 0 | 0 | 3 |
| Comprehend | 8 | 8 | 0 | 0 | 0 |
| Finalize | 59 | 59 | 0 | 0 | 0 |
| Implement | 76 | 73 | 3 | 0 | 0 |
| Investigate | 84 | 79 | 1 | 0 | 4 |
| Link | 2 | 2 | 0 | 0 | 0 |
| Parity | 49 | 40 | 0 | 0 | 9 |
| Plan | 48 | 43 | 0 | 1 | 4 |
| Review | 55 | 41 | 9 | 0 | 5 |
| Scope | 59 | 58 | 1 | 0 | 0 |
| Structure | 8 | 8 | 0 | 0 | 0 |
| Test | 53 | 53 | 0 | 0 | 0 |
| Verify | 64 | 50 | 14 | 0 | 0 |
| Write | 36 | 36 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 33 | 1781.3 | 54.0 |
| Finalize | 34 | 5677.9 | 167.0 |
| Implement | 36 | 45052.3 | 1251.5 |
| Investigate | 35 | 36973.4 | 1056.4 |
| Parity | 33 | 1726.6 | 52.3 |
| Plan | 35 | 1845.0 | 52.7 |
| Review | 41 | 1999.4 | 48.8 |
| Scope | 38 | 34971.6 | 920.3 |
| Test | 35 | 8134.8 | 232.4 |
| Verify | 46 | 3811.0 | 82.8 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 74 | 3780.7 | 51.1 |
| claude-fork-direct | 3 | 0.0 | 0.0 |
| done-checker | 45 | 3811.0 | 84.7 |
| finalizer | 34 | 5677.9 | 167.0 |
| implementer | 35 | 45052.3 | 1287.2 |
| investigator | 35 | 36973.4 | 1056.4 |
| parity-updater | 33 | 1726.6 | 52.3 |
| planner | 35 | 1845.0 | 52.7 |
| test-scoper | 35 | 8134.8 | 232.4 |
| ticket-scoper | 37 | 34971.6 | 945.2 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 5 |

## Slow Runs (> 30 min)

| run_id | duration | final_status |
|---|---|---|
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | 585 min | DONE |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | 576 min | DONE |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 541 min | STOPPED_BY_USER |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 483 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 440 min | DOD_BLOCKED |
| TCK-20260719-TAG-COLLISION-DEDUP | 429 min | DONE |
| TCK-20260718-AGENTOPS-STATS-BOARD-EPIC | 275 min | DONE |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | 248 min | DONE |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 173 min | DONE |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | 173 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard-ui-fixes | 173 min | DONE |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 149 min | DONE |
| TCK-20260718-AGENTOPS-STATS-API | 148 min | DONE |
| TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE | 148 min | DONE |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 147 min | DONE |
| TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE | 144 min | DONE |
| TCK-20260718-RETRO-STATS-REFACTOR | 130 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 127 min | DONE |
| FOLDER-tickets-todos-simq-scoring-improvement | 124 min | DONE |
| TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE | 121 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | 119 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 111 min | DOD_BLOCKED |
| TCK-20260717-GANTT-TIME-AXIS | 103 min | DONE |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 88 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 88 min | DONE |
| TCK-20260718-STATS-TAB-FRONTEND | 86 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-PROGRESS-TIMELINE | 84 min | DONE |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 81 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 80 min | DOD_BLOCKED |
| TCK-20260718-GLOSSARY-TOOLTIPS-EPIC | 78 min | DONE |
| TCK-20260716-AGENTOPS-REPLAY-TIMELINE | 75 min | DONE |
| EPIC-TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC | 70 min | DONE |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 65 min | DONE |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 63 min | DONE |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 62 min | DONE |
| TCK-20260718-STATUS-DRIFT-REPAIR | 61 min | DONE |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 58 min | DONE |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 57 min | DOD_BLOCKED |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 54 min | DONE |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 54 min | DONE |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 51 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 47 min | NEEDS_CHANGES |
| TCK-20260718-STATUS-SUFFIX-TRIM | 40 min | DONE |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 39 min | DOD_BLOCKED |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 37 min | DONE |
| TCK-20260717-TICKETS-TAG-SEARCH | 35 min | DONE |
| TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND | 31 min | DONE |
| TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE | 31 min | DONE |

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Duration outliers (by tier)

| run_id | tier | duration_s | tier median | ratio |
|---|---|---|---|---|
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | standard | 35107 | 3271 | 10.7x |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | standard | 34600 | 3271 | 10.6x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | standard | 32485 | 3271 | 9.9x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | standard | 28991 | 3271 | 8.9x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | hotfix | 8827 | 1070 | 8.2x |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | n/a | 7189 | 874.5 | 8.2x |
| TCK-20260719-TAG-COLLISION-DEDUP | standard | 25786 | 3271 | 7.9x |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-PROGRESS-TIMELINE | n/a | 5066 | 874.5 | 5.8x |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | standard | 14911 | 3271 | 4.6x |
| FOLDER-tickets-todos-agent-ops-dashboard | epic | 26444 | 7566.5 | 3.5x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | standard | 10434 | 3271 | 3.2x |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | standard | 10411 | 3271 | 3.2x |

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 2 | Investigate | investigator | 28601.745 | 72.0 | 397.0x |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | 1 | Scope | ticket-scoper | 19056.244 | 53.5 | 356.2x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 2 | Implement | implementer | 28601.745 | 182.6 | 156.7x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE | 1 | Scope | ticket-scoper | 6503.344 | 53.5 | 121.6x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 1 | Scope | ticket-scoper | 5659.732 | 53.5 | 105.8x |
| TCK-20260717-GANTT-TIME-AXIS | 2 | Investigate | investigator | 4330.635 | 72.0 | 60.1x |
| TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE | 1 | Scope | ticket-scoper | 1963.451 | 53.5 | 36.7x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 5 | Implement | implementer | 6415.868 | 182.6 | 35.1x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 7 | Test | test-scoper | 2222.629 | 80.6 | 27.6x |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 10 | Finalize | finalizer | 1314.544 | 63.9 | 20.6x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 7 | Test | test-scoper | 1478.29 | 80.6 | 18.3x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Verify | done-checker | 1060.682 | 58.0 | 18.3x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 5 | Implement | implementer | 3104.991 | 182.6 | 17.0x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 7 | Test | test-scoper | 1099.442 | 80.6 | 13.6x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 9 | Finalize | finalizer | 774.179 | 63.9 | 12.1x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 7 | Test | test-scoper | 957.445 | 80.6 | 11.9x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 2 | Investigate | investigator | 802.218 | 72.0 | 11.1x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 2 | Investigate | investigator | 617.064 | 72.0 | 8.6x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 10 | Finalize | finalizer | 536.0 | 63.9 | 8.4x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 2 | Investigate | investigator | 512.132 | 72.0 | 7.1x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 6 | Architecture-Verify | architecture-reviewer | 333.693 | 52.8 | 6.3x |
| TCK-20260717-GANTT-TIME-AXIS | 11 | Finalize | finalizer | 386.02 | 63.9 | 6.0x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Implement | implementer | 1059.236 | 182.6 | 5.8x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 8 | Parity | parity-updater | 304.841 | 56.5 | 5.4x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 5 | Finalize | finalizer | 343.786 | 63.9 | 5.4x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 11 | Finalize | finalizer | 338.657 | 63.9 | 5.3x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 10 | Finalize | finalizer | 322.315 | 63.9 | 5.0x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 260.409 | 52.6 | 4.9x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 260.409 | 52.6 | 4.9x |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 10 | Finalize | finalizer | 302.356 | 63.9 | 4.7x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 2 | Investigate | investigator | 319.704 | 72.0 | 4.4x |
| TCK-20260717-GANTT-TIME-AXIS | 6 | Architecture-Verify | architecture-reviewer | 232.32 | 52.8 | 4.4x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 7 | Test | test-scoper | 347.36 | 80.6 | 4.3x |
| TCK-20260717-TICKETS-TAG-SEARCH | 9 | Verify | done-checker | 247.557 | 58.0 | 4.3x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 2 | Investigate | investigator | 278.746 | 72.0 | 3.9x |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 3 | Test | test-scoper | 311.175 | 80.6 | 3.9x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 202.994 | 52.6 | 3.9x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 13 | Finalize | finalizer | 238.314 | 63.9 | 3.7x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 5 | Implement | implementer | 619.269 | 182.6 | 3.4x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 9 | Verify | done-checker | 189.63 | 58.0 | 3.3x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 7 | Implement | implementer | 559.772 | 182.6 | 3.1x |

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

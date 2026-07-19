# Agent Monitoring Retro — All Time

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 677 |
| Completed (DONE) | 582 (85%) |
| Gate failures | 73 |
| Avg duration | 116 min |
| Avg agents per run | 6.1 |
| Total agent calls | 3435 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| completed | 12 | 1% |
| success | 10 | 1% |
| None | 10 | 1% |
| DOD_BLOCKED | 9 | 1% |
| complete | 8 | 1% |
| NEEDS_HUMAN_INPUT | 7 | 1% |
| done | 4 | 0% |
| NEEDS_CHANGES | 4 | 0% |
| STOPPED_BY_USER | 3 | 0% |
| INPROGRESS | 1 | 0% |
| GATE_FAIL | 1 | 0% |
| ALL_SCOPED | 1 | 0% |
| DONE_NO_TICKET | 1 | 0% |
| BLOCKED | 1 | 0% |
| CONFLICTS_DETECTED | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 38 |
| needs_human_input | 2 |
| conflicts_detected | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 4 | 100% | 0 |
| agency | 4 | 100% | 0 |
| cognition | 11 | 81% | 2 |
| dashboard | 12 | 100% | 0 |
| ecology | 1 | 100% | 0 |
| faction | 7 | 100% | 0 |
| feature-flags | 4 | 100% | 0 |
| information | 5 | 80% | 1 |
| observability | 19 | 89% | 2 |
| resource-registry | 4 | 75% | 1 |
| self-model | 6 | 66% | 2 |
| simulation-quality | 55 | 90% | 5 |
| social | 1 | 100% | 0 |
| stasis | 3 | 100% | 0 |
| world | 22 | 95% | 1 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| api-design | 6 | N/A — no gate implemented |
| debugging | 4 | N/A — no gate implemented |
| performance | 1 | N/A — no gate implemented |
| security | 1 | 0 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 89 | 20 | 56 | 81% |
| epic-batch | 1 | 0 | 1 | 100% |
| epic_batch | 1 | 1 | 0 | 0% |
| hotfix | 94 | 0 | 92 | 97% |
| n/a | 12 | 0 | 12 | 100% |
| standard | 459 | 0 | 406 | 88% |
| unknown | 21 | 0 | 15 | 71% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 258 | 0 | 0 | 0 | 0 |
| anchor-updater | 1 | 1 | 0 | 0 | 0 |
| architecture-reviewer | 375 | 280 | 47 | 0 | 48 |
| claude | 26 | 25 | 0 | 1 | 0 |
| claude-fork-direct | 9 | 9 | 0 | 0 | 0 |
| claude-sonnet | 9 | 9 | 0 | 0 | 0 |
| claude-sonnet-4-6 | 16 | 16 | 0 | 0 | 0 |
| concern-investigator | 1 | 1 | 0 | 0 | 0 |
| coordinator | 1 | 1 | 0 | 0 | 0 |
| create-tickets | 11 | 11 | 0 | 0 | 0 |
| doc-syncer | 1 | 1 | 0 | 0 | 0 |
| doc-writer | 2 | 2 | 0 | 0 | 0 |
| dod-verifier | 1 | 1 | 0 | 0 | 0 |
| done-checker | 280 | 239 | 41 | 0 | 0 |
| drift-classifier | 1 | 1 | 0 | 0 | 0 |
| epic-closure | 1 | 1 | 0 | 0 | 0 |
| epic-coordinator | 7 | 7 | 0 | 0 | 0 |
| epic-discoverer | 1 | 1 | 0 | 0 | 0 |
| epic-loop | 1 | 1 | 0 | 0 | 0 |
| epic-reporter | 1 | 1 | 0 | 0 | 0 |
| epic-runner | 1 | 1 | 0 | 0 | 0 |
| finalizer | 247 | 247 | 0 | 0 | 0 |
| hotfix-agent | 5 | 5 | 0 | 0 | 0 |
| implement | 1 | 1 | 0 | 0 | 0 |
| implement-epic | 19 | 19 | 0 | 0 | 0 |
| implement-ticket | 337 | 325 | 7 | 0 | 0 |
| implement-ticket-orchestrator | 8 | 8 | 0 | 0 | 0 |
| implementer | 341 | 338 | 2 | 0 | 1 |
| investigate:C1 | 10 | 9 | 1 | 0 | 0 |
| investigate:C2 | 8 | 7 | 1 | 0 | 0 |
| investigate:C3 | 8 | 7 | 1 | 0 | 0 |
| investigate:C4 | 7 | 6 | 1 | 0 | 0 |
| investigate:C5 | 6 | 5 | 1 | 0 | 0 |
| investigate:C6 | 1 | 1 | 0 | 0 | 0 |
| investigate:direct | 1 | 1 | 0 | 0 | 0 |
| investigator | 254 | 222 | 0 | 1 | 31 |
| link-epic | 4 | 4 | 0 | 0 | 0 |
| main | 6 | 6 | 0 | 0 | 0 |
| manual-hotfix | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 55 | 54 | 0 | 1 | 0 |
| orchestrator-audit | 1 | 1 | 0 | 0 | 0 |
| orchestrator-fix | 3 | 3 | 0 | 0 | 0 |
| parity-checker | 3 | 3 | 0 | 0 | 0 |
| parity-updater | 235 | 188 | 0 | 0 | 47 |
| plan-expander | 1 | 1 | 0 | 0 | 0 |
| plan-fixer | 8 | 8 | 0 | 0 | 0 |
| planner | 255 | 217 | 0 | 7 | 31 |
| planner+implementer | 1 | 1 | 0 | 0 | 0 |
| reviewer | 4 | 4 | 0 | 0 | 0 |
| scope-agent | 9 | 9 | 0 | 0 | 0 |
| scoper | 4 | 4 | 0 | 0 | 0 |
| structure | 10 | 10 | 0 | 0 | 0 |
| test-runner | 2 | 2 | 0 | 0 | 0 |
| test-scoper | 249 | 247 | 0 | 1 | 1 |
| tester | 4 | 4 | 0 | 0 | 0 |
| ticket-scoper | 317 | 316 | 1 | 0 | 0 |
| verifier | 2 | 2 | 0 | 0 | 0 |
| workflow | 2 | 2 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 177 | 0 | 0 | 0 | 0 |
| Architecture-Verify | 93 | 76 | 1 | 0 | 16 |
| Clarification | 1 | 0 | 0 | 1 | 0 |
| Classify Drift | 1 | 1 | 0 | 0 | 0 |
| Comprehend | 11 | 11 | 0 | 0 | 0 |
| Discover | 3 | 3 | 0 | 0 | 0 |
| Epic | 1 | 1 | 0 | 0 | 0 |
| Finalize | 355 | 342 | 0 | 0 | 0 |
| Implement | 503 | 481 | 7 | 0 | 0 |
| Implement+Finalize | 4 | 4 | 0 | 0 | 0 |
| Investigate | 315 | 278 | 5 | 1 | 31 |
| Investigate+Plan+Implement | 1 | 1 | 0 | 0 | 0 |
| Link | 4 | 4 | 0 | 0 | 0 |
| Parity | 275 | 222 | 0 | 0 | 48 |
| Parity Check | 1 | 1 | 0 | 0 | 0 |
| Plan | 265 | 227 | 0 | 7 | 31 |
| Plan+Implement | 1 | 1 | 0 | 0 | 0 |
| Recalibrate | 1 | 1 | 0 | 0 | 0 |
| Report | 16 | 16 | 0 | 0 | 0 |
| Review | 297 | 219 | 46 | 0 | 32 |
| Scope | 334 | 324 | 1 | 0 | 0 |
| Smoke-Test | 1 | 1 | 0 | 0 | 0 |
| Structure | 11 | 11 | 0 | 0 | 0 |
| Sync Docs | 1 | 1 | 0 | 0 | 0 |
| Test | 305 | 293 | 1 | 1 | 1 |
| Update Anchors | 1 | 1 | 0 | 0 | 0 |
| Verify | 316 | 273 | 42 | 1 | 0 |
| Write | 44 | 44 | 0 | 0 | 0 |
| child-ticket-creation | 2 | 2 | 0 | 0 | 0 |
| context-search | 2 | 2 | 0 | 0 | 0 |
| discover | 1 | 0 | 0 | 0 | 0 |
| finalize | 15 | 11 | 0 | 0 | 0 |
| implement | 22 | 7 | 0 | 0 | 0 |
| investigate | 8 | 7 | 0 | 0 | 0 |
| investigation | 2 | 2 | 0 | 0 | 0 |
| parity | 8 | 5 | 0 | 0 | 0 |
| plan | 5 | 5 | 0 | 0 | 0 |
| report | 3 | 3 | 0 | 0 | 0 |
| review | 3 | 3 | 0 | 0 | 0 |
| scope | 9 | 8 | 0 | 0 | 0 |
| test | 16 | 7 | 0 | 0 | 0 |
| verify | 1 | 0 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 51 | 3748.0 | 73.5 |
| Finalize | 52 | 19613.2 | 377.2 |
| Implement | 55 | 79898.8 | 1452.7 |
| Investigate | 54 | 88900.4 | 1646.3 |
| Parity | 44 | 3559.0 | 80.9 |
| Plan | 54 | 2784.7 | 51.6 |
| Review | 63 | 4541.3 | 72.1 |
| Scope | 50 | 34845.3 | 696.9 |
| Test | 54 | 12372.0 | 229.1 |
| Verify | 72 | 7342.1 | 102.0 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 114 | 8289.3 | 72.7 |
| done-checker | 72 | 7342.1 | 102.0 |
| finalizer | 52 | 19613.2 | 377.2 |
| implementer | 55 | 79898.8 | 1452.7 |
| investigator | 54 | 88900.4 | 1646.3 |
| parity-updater | 44 | 3559.0 | 80.9 |
| planner | 54 | 2784.7 | 51.6 |
| test-scoper | 54 | 12372.0 | 229.1 |
| ticket-scoper | 50 | 34845.3 | 696.9 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 258 |
| Truncated (>200 chars) | 51 |

## Slow Runs (> 30 min)

| run_id | duration | final_status |
|---|---|---|
| FOLDER-tickets-todos-simq-scoring-improvement | 839 min | STOPPED_BY_USER |
| FOLDER-tickets-todos-simq-roadmap-phase2-depth-social | 830 min | DONE |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 828 min | DONE |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | 585 min | DONE |
| EPIC-TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC | 548 min | DONE |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 541 min | STOPPED_BY_USER |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 484 min | DONE |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 483 min | DONE |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | 475 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 440 min | DOD_BLOCKED |
| FOLDER-tickets-todos-simq-roadmap-phase3-depth-faction-information | 434 min | DONE |
| TCK-20260719-TAG-COLLISION-DEDUP | 429 min | DONE |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 396 min | DONE |
| TCK-20260718-AGENTOPS-STATS-BOARD-EPIC | 275 min | DONE |
| TCK-20260710-SIMQ-DEPTH-FACTION | 261 min | DONE |
| FOLDER-tickets-todos-simq-roadmap-phase0-reliability-foundation | 256 min | DONE |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | 248 min | DONE |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 204 min | DONE |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 173 min | DONE |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | 173 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard-ui-fixes | 173 min | DONE |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 171 min | DONE |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 163 min | DONE |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 152 min | NEEDS_CHANGES |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 152 min | DONE |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 149 min | DONE |
| TCK-20260718-AGENTOPS-STATS-API | 148 min | DONE |
| TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE | 148 min | DONE |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 147 min | DONE |
| TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE | 144 min | DONE |
| TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS | 136 min | DONE |
| FOLDER-tickets-todos-simq-scoring-improvement | 134 min | NEEDS_HUMAN_INPUT |
| TCK-20260718-RETRO-STATS-REFACTOR | 130 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 127 min | DONE |
| FOLDER-tickets-todos-simq-scoring-improvement | 124 min | DONE |
| TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE | 121 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | 119 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 111 min | DOD_BLOCKED |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | 109 min | DONE |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 106 min | DONE |
| TCK-20260717-GANTT-TIME-AXIS | 103 min | DONE |
| FOLDER-tickets-todos-simq-roadmap-phase1-process-hardening | 98 min | DONE |
| FOLDER-tickets-todos-epic-scope-orphan-cleanup | 89 min | DONE |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | 89 min | DONE |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 88 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 88 min | DONE |
| TCK-20260718-STATS-TAB-FRONTEND | 86 min | DONE |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 81 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 80 min | DOD_BLOCKED |
| TCK-20260718-GLOSSARY-TOOLTIPS-EPIC | 78 min | DONE |
| TCK-20260716-AGENTOPS-REPLAY-TIMELINE | 75 min | DONE |
| EPIC-TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC | 70 min | DONE |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 65 min | DONE |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 63 min | DONE |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 62 min | DONE |
| TCK-20260718-STATUS-DRIFT-REPAIR | 61 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-SIMQ-SCORING-IMPROVEMENT-ROADMAP | 60 min | DONE |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 58 min | DONE |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 57 min | DOD_BLOCKED |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 54 min | DONE |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 54 min | DONE |
| TCK-20260710-EPIC-STALENESS-CHECK | 52 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 47 min | NEEDS_CHANGES |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 47 min | DONE |
| TCK-20260711-EPIC-SCOPE-ORPHAN-FIX | 47 min | DONE |
| TCK-20260710-FEATURE-FLAGS-GUIDE | 44 min | DONE |
| TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION | 43 min | DONE |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 41 min | DONE |
| TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH | 41 min | DONE |
| TCK-20260718-STATUS-SUFFIX-TRIM | 40 min | DONE |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 40 min | DONE |
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
| TCK-20260710-SIMQ-DEPTH-SOCIAL | standard | 49729 | 3254 | 15.3x |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | n/a | 7189 | 661 | 10.9x |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | standard | 35107 | 3254 | 10.8x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | standard | 32485 | 3254 | 10.0x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | hotfix | 8827 | 900.5 | 9.8x |
| TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS | hotfix | 8185 | 900.5 | 9.1x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | standard | 29073 | 3254 | 8.9x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | standard | 28991 | 3254 | 8.9x |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | standard | 28516 | 3254 | 8.8x |
| TCK-20260719-TAG-COLLISION-DEDUP | standard | 25786 | 3254 | 7.9x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | standard | 23793 | 3254 | 7.3x |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | hotfix | 6560 | 900.5 | 7.3x |
| FOLDER-tickets-todos-simq-scoring-improvement | epic | 50386 | 7849.0 | 6.4x |
| FOLDER-tickets-todos-simq-roadmap-phase2-depth-social | epic | 49832 | 7849.0 | 6.3x |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | hotfix | 5381 | 900.5 | 6.0x |
| CREATE-TICKETS-DOCS-PLANS-SIMQ-SCORING-IMPROVEMENT-ROADMAP | n/a | 3626 | 661 | 5.5x |
| TCK-20260710-SIMQ-DEPTH-FACTION | standard | 15661 | 3254 | 4.8x |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | standard | 14911 | 3254 | 4.6x |
| EPIC-TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC | epic | 32893 | 7849.0 | 4.2x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | standard | 12296 | 3254 | 3.8x |
| FOLDER-tickets-todos-agent-ops-dashboard | epic | 26444 | 7849.0 | 3.4x |
| FOLDER-tickets-todos-simq-roadmap-phase3-depth-faction-information | epic | 26096 | 7849.0 | 3.3x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | standard | 10434 | 3254 | 3.2x |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | standard | 10411 | 3254 | 3.2x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | standard | 10261 | 3254 | 3.2x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | standard | 9827 | 3254 | 3.0x |

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 2 | Investigate | investigator | 34837.628 | 78.4 | 444.1x |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | 1 | Scope | ticket-scoper | 19056.244 | 51.4 | 370.4x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 2 | Investigate | investigator | 28601.745 | 78.4 | 364.6x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 2 | Implement | implementer | 28601.745 | 178.1 | 160.6x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE | 1 | Scope | ticket-scoper | 6503.344 | 51.4 | 126.4x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 1 | Scope | ticket-scoper | 5659.732 | 51.4 | 110.0x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 2 | Investigate | investigator | 8243.029 | 78.4 | 105.1x |
| TCK-20260710-SIMQ-DEPTH-FACTION | 5 | Implement | implementer | 14058.238 | 178.1 | 78.9x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 10 | Finalize | finalizer | 6145.832 | 95.5 | 64.4x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 2 | Investigate | investigator | 4360.288 | 78.4 | 55.6x |
| TCK-20260717-GANTT-TIME-AXIS | 2 | Investigate | investigator | 4330.635 | 78.4 | 55.2x |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | 6 | Finalize | finalizer | 4267.525 | 95.5 | 44.7x |
| TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE | 1 | Scope | ticket-scoper | 1963.451 | 51.4 | 38.2x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 5 | Implement | implementer | 6415.868 | 178.1 | 36.0x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 7 | Test | test-scoper | 2222.629 | 61.8 | 35.9x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 7 | Test | test-scoper | 2101.762 | 61.8 | 34.0x |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | 5 | Implement | implementer | 5392.113 | 178.1 | 30.3x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 5 | Implement | implementer | 4994.127 | 178.1 | 28.0x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 7 | Test | test-scoper | 1478.29 | 61.8 | 23.9x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 5 | Implement | implementer | 3589.04 | 178.1 | 20.1x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Verify | done-checker | 1060.682 | 56.7 | 18.7x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 6 | Implement | implementer | 3227.086 | 178.1 | 18.1x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 7 | Test | test-scoper | 1099.442 | 61.8 | 17.8x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 2 | Investigate | investigator | 1383.699 | 78.4 | 17.6x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 5 | Implement | implementer | 3104.991 | 178.1 | 17.4x |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 9 | Verify | done-checker | 973.098 | 56.7 | 17.2x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 4 | Review | architecture-reviewer | 869.171 | 53.7 | 16.2x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 8 | Parity | parity-updater | 909.948 | 57.1 | 15.9x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 7 | Test | test-scoper | 957.445 | 61.8 | 15.5x |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 10 | Finalize | finalizer | 1314.544 | 95.5 | 13.8x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 4 | Review | architecture-reviewer | 630.599 | 53.7 | 11.7x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 2 | Investigate | investigator | 802.218 | 78.4 | 10.2x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 6 | Architecture-Verify | architecture-reviewer | 535.464 | 53.1 | 10.1x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 5 | Implement | implementer | 1676.257 | 178.1 | 9.4x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 7 | Test | test-scoper | 547.336 | 61.8 | 8.9x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 9 | Finalize | finalizer | 774.179 | 95.5 | 8.1x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 2 | Investigate | investigator | 617.064 | 78.4 | 7.9x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 12 | Finalize | finalizer | 675.303 | 95.5 | 7.1x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 8 | Parity | parity-updater | 402.54 | 57.1 | 7.0x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 9 | Architecture-Verify | architecture-reviewer | 354.638 | 53.1 | 6.7x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 2 | Investigate | investigator | 512.132 | 78.4 | 6.5x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 6 | Architecture-Verify | architecture-reviewer | 333.693 | 53.1 | 6.3x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 2 | Investigate | investigator | 482.209 | 78.4 | 6.1x |
| TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME | 2 | Investigate | investigator | 475.986 | 78.4 | 6.1x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Implement | implementer | 1059.236 | 178.1 | 5.9x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 8 | Parity | parity-updater | 324.288 | 57.1 | 5.7x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 7 | Test | test-scoper | 347.36 | 61.8 | 5.6x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 7 | Test | test-scoper | 347.264 | 61.8 | 5.6x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 10 | Finalize | finalizer | 536.0 | 95.5 | 5.6x |
| TCK-20260710-SIMQ-DEPTH-FACTION | 2 | Investigate | investigator | 438.081 | 78.4 | 5.6x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 12 | Finalize | finalizer | 527.988 | 95.5 | 5.5x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 9 | Verify | done-checker | 303.037 | 56.7 | 5.3x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 8 | Parity | parity-updater | 304.841 | 57.1 | 5.3x |
| TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME | 2 | Investigate | investigator | 416.131 | 78.4 | 5.3x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 9 | Verify | done-checker | 293.789 | 56.7 | 5.2x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 10 | Verify | done-checker | 289.145 | 56.7 | 5.1x |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 3 | Test | test-scoper | 311.175 | 61.8 | 5.0x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 260.409 | 53.7 | 4.8x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 260.409 | 53.7 | 4.8x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 2 | Investigate | investigator | 360.99 | 78.4 | 4.6x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 10 | Verify | done-checker | 259.841 | 56.7 | 4.6x |
| TCK-20260711-EPIC-SCOPE-ORPHAN-FIX | 9 | Verify | done-checker | 252.345 | 56.7 | 4.4x |
| TCK-20260717-GANTT-TIME-AXIS | 6 | Architecture-Verify | architecture-reviewer | 232.32 | 53.1 | 4.4x |
| TCK-20260717-TICKETS-TAG-SEARCH | 9 | Verify | done-checker | 247.557 | 56.7 | 4.4x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 7 | Test | test-scoper | 254.593 | 61.8 | 4.1x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 2 | Investigate | investigator | 319.704 | 78.4 | 4.1x |
| TCK-20260717-GANTT-TIME-AXIS | 11 | Finalize | finalizer | 386.02 | 95.5 | 4.0x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 11 | Verify | done-checker | 218.014 | 56.7 | 3.8x |
| TCK-20260711-DOC-STALENESS-GATE-CHECK | 9 | Verify | done-checker | 214.347 | 56.7 | 3.8x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 202.994 | 53.7 | 3.8x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 5 | Finalize | finalizer | 343.786 | 95.5 | 3.6x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 2 | Investigate | investigator | 278.746 | 78.4 | 3.6x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 11 | Finalize | finalizer | 338.657 | 95.5 | 3.5x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 5 | Implement | implementer | 619.269 | 178.1 | 3.5x |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | 10 | Finalize | finalizer | 330.731 | 95.5 | 3.5x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 2 | Investigate | investigator | 271.207 | 78.4 | 3.5x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 4 | Review | architecture-reviewer | 184.09 | 53.7 | 3.4x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 10 | Finalize | finalizer | 322.315 | 95.5 | 3.4x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 9 | Verify | done-checker | 189.63 | 56.7 | 3.3x |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 10 | Finalize | finalizer | 302.356 | 95.5 | 3.2x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 7 | Implement | implementer | 559.772 | 178.1 | 3.1x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 5 | Implement | implementer | 546.789 | 178.1 | 3.1x |

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

# Agent Monitoring Retro — All Time

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 656 |
| Completed (DONE) | 564 (85%) |
| Gate failures | 70 |
| Avg duration | 128 min |
| Avg agents per run | 6.1 |
| Total agent calls | 3312 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| completed | 12 | 1% |
| success | 10 | 1% |
| None | 10 | 1% |
| complete | 8 | 1% |
| DOD_BLOCKED | 8 | 1% |
| NEEDS_HUMAN_INPUT | 6 | 0% |
| done | 4 | 0% |
| STOPPED_BY_USER | 3 | 0% |
| NEEDS_CHANGES | 3 | 0% |
| INPROGRESS | 1 | 0% |
| GATE_FAIL | 1 | 0% |
| ALL_SCOPED | 1 | 0% |
| DONE_NO_TICKET | 1 | 0% |
| BLOCKED | 1 | 0% |
| CONFLICTS_DETECTED | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 37 |
| needs_human_input | 2 |
| conflicts_detected | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 4 | 100% | 0 |
| agency | 4 | 100% | 0 |
| cognition | 11 | 81% | 2 |
| dashboard | 1 | 100% | 0 |
| ecology | 1 | 100% | 0 |
| faction | 7 | 100% | 0 |
| feature-flags | 4 | 100% | 0 |
| information | 5 | 80% | 1 |
| observability | 11 | 81% | 2 |
| resource-registry | 4 | 75% | 1 |
| self-model | 6 | 66% | 2 |
| simulation-quality | 55 | 90% | 5 |
| social | 1 | 100% | 0 |
| stasis | 3 | 100% | 0 |
| world | 22 | 95% | 1 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| api-design | 3 | N/A — no gate implemented |
| debugging | 4 | N/A — no gate implemented |
| performance | 1 | N/A — no gate implemented |
| security | 1 | 0 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 87 | 20 | 54 | 80% |
| epic-batch | 1 | 0 | 1 | 100% |
| epic_batch | 1 | 1 | 0 | 0% |
| hotfix | 91 | 0 | 89 | 97% |
| n/a | 10 | 0 | 10 | 100% |
| standard | 445 | 0 | 395 | 88% |
| unknown | 21 | 0 | 15 | 71% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 258 | 0 | 0 | 0 | 0 |
| anchor-updater | 1 | 1 | 0 | 0 | 0 |
| architecture-reviewer | 359 | 268 | 46 | 0 | 45 |
| claude | 26 | 25 | 0 | 1 | 0 |
| claude-fork-direct | 6 | 6 | 0 | 0 | 0 |
| claude-sonnet | 9 | 9 | 0 | 0 | 0 |
| claude-sonnet-4-6 | 16 | 16 | 0 | 0 | 0 |
| concern-investigator | 1 | 1 | 0 | 0 | 0 |
| coordinator | 1 | 1 | 0 | 0 | 0 |
| create-tickets | 9 | 9 | 0 | 0 | 0 |
| doc-syncer | 1 | 1 | 0 | 0 | 0 |
| doc-writer | 2 | 2 | 0 | 0 | 0 |
| dod-verifier | 1 | 1 | 0 | 0 | 0 |
| done-checker | 270 | 230 | 40 | 0 | 0 |
| drift-classifier | 1 | 1 | 0 | 0 | 0 |
| epic-closure | 1 | 1 | 0 | 0 | 0 |
| epic-coordinator | 7 | 7 | 0 | 0 | 0 |
| epic-discoverer | 1 | 1 | 0 | 0 | 0 |
| epic-loop | 1 | 1 | 0 | 0 | 0 |
| epic-reporter | 1 | 1 | 0 | 0 | 0 |
| epic-runner | 1 | 1 | 0 | 0 | 0 |
| finalizer | 231 | 231 | 0 | 0 | 0 |
| hotfix-agent | 5 | 5 | 0 | 0 | 0 |
| implement | 1 | 1 | 0 | 0 | 0 |
| implement-epic | 19 | 19 | 0 | 0 | 0 |
| implement-ticket | 337 | 325 | 7 | 0 | 0 |
| implement-ticket-orchestrator | 8 | 8 | 0 | 0 | 0 |
| implementer | 330 | 327 | 2 | 0 | 1 |
| investigate:C1 | 8 | 7 | 1 | 0 | 0 |
| investigate:C2 | 7 | 6 | 1 | 0 | 0 |
| investigate:C3 | 7 | 6 | 1 | 0 | 0 |
| investigate:C4 | 6 | 5 | 1 | 0 | 0 |
| investigate:C5 | 5 | 4 | 1 | 0 | 0 |
| investigate:C6 | 1 | 1 | 0 | 0 | 0 |
| investigate:direct | 1 | 1 | 0 | 0 | 0 |
| investigator | 244 | 213 | 0 | 1 | 30 |
| link-epic | 4 | 4 | 0 | 0 | 0 |
| main | 6 | 6 | 0 | 0 | 0 |
| manual-hotfix | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 55 | 54 | 0 | 1 | 0 |
| orchestrator-audit | 1 | 1 | 0 | 0 | 0 |
| orchestrator-fix | 3 | 3 | 0 | 0 | 0 |
| parity-checker | 3 | 3 | 0 | 0 | 0 |
| parity-updater | 226 | 181 | 0 | 0 | 45 |
| plan-expander | 1 | 1 | 0 | 0 | 0 |
| plan-fixer | 8 | 8 | 0 | 0 | 0 |
| planner | 245 | 209 | 0 | 6 | 30 |
| planner+implementer | 1 | 1 | 0 | 0 | 0 |
| reviewer | 4 | 4 | 0 | 0 | 0 |
| scope-agent | 9 | 9 | 0 | 0 | 0 |
| scoper | 4 | 4 | 0 | 0 | 0 |
| structure | 8 | 8 | 0 | 0 | 0 |
| test-runner | 2 | 2 | 0 | 0 | 0 |
| test-scoper | 239 | 237 | 0 | 1 | 1 |
| tester | 4 | 4 | 0 | 0 | 0 |
| ticket-scoper | 299 | 298 | 1 | 0 | 0 |
| verifier | 2 | 2 | 0 | 0 | 0 |
| workflow | 2 | 2 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 46 | 3629.1 | 78.9 |
| Finalize | 48 | 19467.3 | 405.6 |
| Implement | 50 | 79325.5 | 1586.5 |
| Investigate | 47 | 88429.9 | 1881.5 |
| Parity | 39 | 3404.1 | 87.3 |
| Plan | 47 | 2328.7 | 49.5 |
| Review | 57 | 3817.5 | 67.0 |
| Scope | 43 | 34328.3 | 798.3 |
| Test | 49 | 12203.3 | 249.0 |
| Verify | 67 | 7025.5 | 104.9 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 103 | 7446.6 | 72.3 |
| done-checker | 67 | 7025.5 | 104.9 |
| finalizer | 48 | 19467.3 | 405.6 |
| implementer | 50 | 79325.5 | 1586.5 |
| investigator | 47 | 88429.9 | 1881.5 |
| parity-updater | 39 | 3404.1 | 87.3 |
| planner | 47 | 2328.7 | 49.5 |
| test-scoper | 49 | 12203.3 | 249.0 |
| ticket-scoper | 43 | 34328.3 | 798.3 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 258 |
| Truncated (>200 chars) | 46 |

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
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 396 min | DONE |
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
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 81 min | DONE |
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

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

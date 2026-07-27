# Agent Monitoring Retro — Last 28 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 299 |
| Completed (DONE) | 269 (89%) |
| Gate failures | 25 |
| Avg duration | 108 min |
| Avg agents per run | 7.6 |
| Total agent calls | 2212 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| DOD_BLOCKED | 9 | 3% |
| NEEDS_HUMAN_INPUT | 6 | 2% |
| NEEDS_CHANGES | 4 | 1% |
| STOPPED_BY_USER | 3 | 1% |
| DONE_NO_TICKET | 1 | 0% |
| BLOCKED | 1 | 0% |
| CONFLICTS_DETECTED | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 46 |
| needs_human_input | 2 |
| conflicts_detected | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 4 | 100% | 0 |
| agency | 4 | 100% | 0 |
| cognition | 11 | 81% | 2 |
| dashboard | 15 | 100% | 0 |
| ecology | 1 | 100% | 0 |
| faction | 7 | 100% | 0 |
| feature-flags | 4 | 100% | 0 |
| information | 5 | 80% | 1 |
| observability | 23 | 91% | 2 |
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
| epic | 48 | 4 | 37 | 84% |
| hotfix | 57 | 0 | 57 | 100% |
| n/a | 16 | 0 | 16 | 100% |
| standard | 178 | 0 | 159 | 89% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 20 | 0 | 0 | 0 | 0 |
| anchor-updater | 1 | 1 | 0 | 0 | 0 |
| architecture-reviewer | 325 | 230 | 46 | 5 | 44 |
| claude | 24 | 23 | 0 | 1 | 0 |
| claude-fork-direct | 12 | 12 | 0 | 0 | 0 |
| claude-orchestrator | 2 | 2 | 0 | 0 | 0 |
| concern-investigator | 1 | 1 | 0 | 0 | 0 |
| create-tickets | 16 | 15 | 1 | 0 | 0 |
| doc-syncer | 1 | 1 | 0 | 0 | 0 |
| doc-writer | 2 | 2 | 0 | 0 | 0 |
| done-checker | 213 | 163 | 48 | 2 | 0 |
| drift-classifier | 1 | 1 | 0 | 0 | 0 |
| epic-closure | 1 | 1 | 0 | 0 | 0 |
| finalizer | 164 | 164 | 0 | 0 | 0 |
| hotfix-agent | 5 | 5 | 0 | 0 | 0 |
| implement-ticket | 119 | 111 | 8 | 0 | 0 |
| implement-ticket-orchestrator | 8 | 8 | 0 | 0 | 0 |
| implementer | 220 | 217 | 2 | 0 | 1 |
| investigate:C1 | 14 | 13 | 1 | 0 | 0 |
| investigate:C2 | 12 | 11 | 1 | 0 | 0 |
| investigate:C3 | 12 | 11 | 1 | 0 | 0 |
| investigate:C4 | 11 | 10 | 1 | 0 | 0 |
| investigate:C5 | 9 | 8 | 1 | 0 | 0 |
| investigate:C6 | 4 | 4 | 0 | 0 | 0 |
| investigate:C7 | 1 | 1 | 0 | 0 | 0 |
| investigate:direct | 1 | 1 | 0 | 0 | 0 |
| investigator | 174 | 148 | 0 | 1 | 25 |
| link-epic | 5 | 5 | 0 | 0 | 0 |
| main | 1 | 1 | 0 | 0 | 0 |
| manual-hotfix | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 53 | 52 | 0 | 1 | 0 |
| orchestrator-audit | 1 | 1 | 0 | 0 | 0 |
| orchestrator-fix | 3 | 3 | 0 | 0 | 0 |
| parity-updater | 155 | 94 | 0 | 0 | 61 |
| plan-expander | 1 | 1 | 0 | 0 | 0 |
| plan-fixer | 8 | 8 | 0 | 0 | 0 |
| planner | 175 | 144 | 0 | 6 | 25 |
| structure | 14 | 14 | 0 | 0 | 0 |
| test-runner | 1 | 1 | 0 | 0 | 0 |
| test-scoper | 167 | 166 | 0 | 0 | 1 |
| ticket-scoper | 249 | 248 | 1 | 0 | 0 |
| workflow | 2 | 2 | 0 | 0 | 0 |
| write-sequence | 1 | 1 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 20 | 0 | 0 | 0 | 0 |
| Architecture-Verify | 113 | 93 | 1 | 1 | 18 |
| Clarification | 1 | 0 | 0 | 1 | 0 |
| Classify Drift | 1 | 1 | 0 | 0 | 0 |
| Comprehend | 15 | 15 | 0 | 0 | 0 |
| Finalize | 197 | 197 | 0 | 0 | 0 |
| Implement | 335 | 327 | 8 | 0 | 0 |
| Implement+Finalize | 1 | 1 | 0 | 0 | 0 |
| Investigate | 242 | 210 | 6 | 1 | 25 |
| Link | 5 | 5 | 0 | 0 | 0 |
| Parity | 171 | 109 | 0 | 0 | 62 |
| Parity Check | 1 | 1 | 0 | 0 | 0 |
| Plan | 177 | 146 | 0 | 6 | 25 |
| Recalibrate | 1 | 1 | 0 | 0 | 0 |
| Report | 2 | 2 | 0 | 0 | 0 |
| Review | 219 | 144 | 45 | 4 | 26 |
| Scope | 202 | 201 | 1 | 0 | 0 |
| Smoke-Test | 1 | 1 | 0 | 0 | 0 |
| Structure | 15 | 15 | 0 | 0 | 0 |
| Sync Docs | 1 | 1 | 0 | 0 | 0 |
| Test | 186 | 184 | 1 | 0 | 1 |
| Update Anchors | 1 | 1 | 0 | 0 | 0 |
| Verify | 237 | 185 | 49 | 3 | 0 |
| Write | 68 | 68 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 71 | 3804.3 | 53.6 |
| Finalize | 77 | 19681.0 | 255.6 |
| Implement | 89 | 80637.5 | 906.0 |
| Investigate | 74 | 89065.2 | 1203.6 |
| Parity | 63 | 3715.8 | 59.0 |
| Plan | 73 | 2933.4 | 40.2 |
| Review | 87 | 4662.8 | 53.6 |
| Scope | 69 | 35125.7 | 509.1 |
| Test | 77 | 12591.1 | 163.5 |
| Verify | 101 | 7750.0 | 76.7 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 158 | 8467.2 | 53.6 |
| claude-fork-direct | 3 | 0.0 | 0.0 |
| claude-orchestrator | 2 | 0.0 | 0.0 |
| done-checker | 104 | 7750.0 | 74.5 |
| finalizer | 73 | 19681.0 | 269.6 |
| implementer | 86 | 80637.5 | 937.6 |
| investigator | 74 | 89065.2 | 1203.6 |
| parity-updater | 63 | 3715.8 | 59.0 |
| planner | 73 | 2933.4 | 40.2 |
| test-scoper | 77 | 12591.1 | 163.5 |
| ticket-scoper | 68 | 35125.7 | 516.6 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 20 |
| Truncated (>200 chars) | 13 |

## Slow Runs (> 30 min)

| run_id | duration | final_status |
|---|---|---|
| FOLDER-tickets-todos-simq-scoring-improvement | 839 min | STOPPED_BY_USER |
| FOLDER-tickets-todos-simq-roadmap-phase2-depth-social | 830 min | DONE |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 828 min | DONE |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | 585 min | DONE |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | 576 min | DONE |
| EPIC-TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC | 548 min | DONE |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 541 min | STOPPED_BY_USER |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 484 min | DONE |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 483 min | DONE |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | 475 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 440 min | DOD_BLOCKED |
| FOLDER-tickets-todos-simq-roadmap-phase3-depth-faction-information | 434 min | DONE |
| TCK-20260719-TAG-COLLISION-DEDUP | 429 min | DONE |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 396 min | DONE |
| TCK-20260721-MONITORING-WRITER-UNIFICATION | 325 min | DONE |
| EPIC-TCK-20260721-PROVIDER-AGNOSTIC-EPIC | 323 min | DONE |
| TCK-20260718-AGENTOPS-STATS-BOARD-EPIC | 275 min | DONE |
| TCK-20260710-SIMQ-DEPTH-FACTION | 261 min | DONE |
| FOLDER-tickets-todos-simq-roadmap-phase0-reliability-foundation | 256 min | DONE |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | 248 min | DONE |
| TCK-20260721-MONITORING-WRITER-DECISION | 223 min | DONE |
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
| TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE | 122 min | DONE |
| TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE | 121 min | DONE |
| TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER | 121 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | 119 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 111 min | DOD_BLOCKED |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | 109 min | DONE |
| TCK-20260721-ORCHESTRATION-CONTRACT-CORE | 109 min | DONE |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 106 min | DONE |
| TCK-20260717-GANTT-TIME-AXIS | 103 min | DONE |
| FOLDER-tickets-todos-simq-roadmap-phase1-process-hardening | 98 min | DONE |
| TCK-20260721-CODEX-REPLAY-PARITY | 91 min | DONE |
| FOLDER-tickets-todos-epic-scope-orphan-cleanup | 89 min | DONE |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | 89 min | DONE |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 88 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 88 min | DONE |
| TCK-20260718-STATS-TAB-FRONTEND | 86 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-PROGRESS-TIMELINE | 84 min | DONE |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 81 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 80 min | DOD_BLOCKED |
| TCK-20260718-GLOSSARY-TOOLTIPS-EPIC | 78 min | DONE |
| TCK-20260716-AGENTOPS-REPLAY-TIMELINE | 75 min | DONE |
| TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS | 73 min | DONE |
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
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 51 min | DONE |
| TCK-20260727-CODEX-SKILL-COMPANION-ASSETS | 48 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 47 min | NEEDS_CHANGES |
| TCK-20260721-CODEX-REPLAY-PROOF | 47 min | DONE |
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
| TCK-20260721-BASELINE-MONITORING-MANIFEST | 30 min | DONE |

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Duration outliers (by tier)

| run_id | tier | duration_s | tier median | ratio |
|---|---|---|---|---|
| TCK-20260710-SIMQ-DEPTH-SOCIAL | standard | 49729 | 3198.0 | 15.6x |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | standard | 35107 | 3198.0 | 11.0x |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | standard | 34600 | 3198.0 | 10.8x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | hotfix | 8827 | 826 | 10.7x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | standard | 32485 | 3198.0 | 10.2x |
| TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS | hotfix | 8185 | 826 | 9.9x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | standard | 29073 | 3198.0 | 9.1x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | standard | 28991 | 3198.0 | 9.1x |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | standard | 28516 | 3198.0 | 8.9x |
| TCK-20260719-TAG-COLLISION-DEDUP | standard | 25786 | 3198.0 | 8.1x |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | n/a | 7189 | 902 | 8.0x |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | hotfix | 6560 | 826 | 7.9x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | standard | 23793 | 3198.0 | 7.4x |
| FOLDER-tickets-todos-simq-scoring-improvement | epic | 50386 | 7476 | 6.7x |
| FOLDER-tickets-todos-simq-roadmap-phase2-depth-social | epic | 49832 | 7476 | 6.7x |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | hotfix | 5381 | 826 | 6.5x |
| TCK-20260721-MONITORING-WRITER-UNIFICATION | standard | 19540 | 3198.0 | 6.1x |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-PROGRESS-TIMELINE | n/a | 5066 | 902 | 5.6x |
| TCK-20260710-SIMQ-DEPTH-FACTION | standard | 15661 | 3198.0 | 4.9x |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | standard | 14911 | 3198.0 | 4.7x |
| EPIC-TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC | epic | 32893 | 7476 | 4.4x |
| TCK-20260721-MONITORING-WRITER-DECISION | standard | 13426 | 3198.0 | 4.2x |
| CREATE-TICKETS-DOCS-PLANS-SIMQ-SCORING-IMPROVEMENT-ROADMAP | n/a | 3626 | 902 | 4.0x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | standard | 12296 | 3198.0 | 3.8x |
| FOLDER-tickets-todos-agent-ops-dashboard | epic | 26444 | 7476 | 3.5x |
| FOLDER-tickets-todos-simq-roadmap-phase3-depth-faction-information | epic | 26096 | 7476 | 3.5x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | standard | 10434 | 3198.0 | 3.3x |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | standard | 10411 | 3198.0 | 3.3x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | standard | 10261 | 3198.0 | 3.2x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | standard | 9827 | 3198.0 | 3.1x |

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 2 | Investigate | investigator | 34837.628 | 65.4 | 532.8x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 2 | Implement | implementer | 28601.745 | 60.5 | 472.9x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 2 | Investigate | investigator | 28601.745 | 65.4 | 437.4x |
| TCK-20260710-SIMQ-DEPTH-FACTION | 5 | Implement | implementer | 14058.238 | 60.5 | 232.4x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 4 | Review | architecture-reviewer | 869.171 | 4.4 | 197.3x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 4 | Review | architecture-reviewer | 630.599 | 4.4 | 143.2x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 2 | Investigate | investigator | 8243.029 | 65.4 | 126.1x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 5 | Implement | implementer | 6415.868 | 60.5 | 106.1x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 10 | Finalize | finalizer | 6145.832 | 58.1 | 105.8x |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | 5 | Implement | implementer | 5392.113 | 60.5 | 89.2x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 5 | Implement | implementer | 4994.127 | 60.5 | 82.6x |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | 6 | Finalize | finalizer | 4267.525 | 58.1 | 73.5x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 2 | Investigate | investigator | 4360.288 | 65.4 | 66.7x |
| TCK-20260717-GANTT-TIME-AXIS | 2 | Investigate | investigator | 4330.635 | 65.4 | 66.2x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 5 | Implement | implementer | 3589.04 | 60.5 | 59.3x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 260.409 | 4.4 | 59.1x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 260.409 | 4.4 | 59.1x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 6 | Implement | implementer | 3227.086 | 60.5 | 53.4x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 5 | Implement | implementer | 3104.991 | 60.5 | 51.3x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 202.994 | 4.4 | 46.1x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 4 | Review | architecture-reviewer | 184.09 | 4.4 | 41.8x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 7 | Test | test-scoper | 2222.629 | 58.4 | 38.0x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 7 | Test | test-scoper | 2101.762 | 58.4 | 36.0x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 4 | Review | architecture-reviewer | 143.682 | 4.4 | 32.6x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 5 | Implement | implementer | 1676.257 | 60.5 | 27.7x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 7 | Test | test-scoper | 1478.29 | 58.4 | 25.3x |
| TCK-20260717-GANTT-TIME-AXIS | 4 | Review | architecture-reviewer | 107.796 | 4.4 | 24.5x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 4 | Review | architecture-reviewer | 104.942 | 4.4 | 23.8x |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 10 | Finalize | finalizer | 1314.544 | 58.1 | 22.6x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 2 | Investigate | investigator | 1383.699 | 65.4 | 21.2x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Verify | done-checker | 1060.682 | 53.2 | 19.9x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 7 | Test | test-scoper | 1099.442 | 58.4 | 18.8x |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 9 | Verify | done-checker | 973.098 | 53.2 | 18.3x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Implement | implementer | 1059.236 | 60.5 | 17.5x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 7 | Test | test-scoper | 957.445 | 58.4 | 16.4x |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | 4 | Review | architecture-reviewer | 65.137 | 4.4 | 14.8x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 4 | Review | architecture-reviewer | 63.881 | 4.4 | 14.5x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 6 | Review | architecture-reviewer | 62.539 | 4.4 | 14.2x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 4 | Review | architecture-reviewer | 60.221 | 4.4 | 13.7x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 9 | Finalize | finalizer | 774.179 | 58.1 | 13.3x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 4 | Review | architecture-reviewer | 58.685 | 4.4 | 13.3x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 5 | Review | architecture-reviewer | 58.081 | 4.4 | 13.2x |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 4 | Review | architecture-reviewer | 58.004 | 4.4 | 13.2x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 4 | Review | architecture-reviewer | 57.709 | 4.4 | 13.1x |
| TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT | 4 | Review | architecture-reviewer | 57.553 | 4.4 | 13.1x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 4 | Review | architecture-reviewer | 57.475 | 4.4 | 13.0x |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 4 | Review | architecture-reviewer | 56.405 | 4.4 | 12.8x |
| TCK-20260718-STATUS-SUFFIX-TRIM | 4 | Review | architecture-reviewer | 56.107 | 4.4 | 12.7x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 4 | Review | architecture-reviewer | 56.077 | 4.4 | 12.7x |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 4 | Review | architecture-reviewer | 55.912 | 4.4 | 12.7x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 4 | Review | architecture-reviewer | 55.876 | 4.4 | 12.7x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 4 | Review | architecture-reviewer | 55.501 | 4.4 | 12.6x |
| TCK-20260710-SIMQ-DEPTH-FACTION | 4 | Review | architecture-reviewer | 54.966 | 4.4 | 12.5x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 5 | Review | architecture-reviewer | 54.761 | 4.4 | 12.4x |
| TCK-20260717-TICKETS-TAG-SEARCH | 4 | Review | architecture-reviewer | 54.659 | 4.4 | 12.4x |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 4 | Review | architecture-reviewer | 54.229 | 4.4 | 12.3x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 5 | Review | architecture-reviewer | 54.199 | 4.4 | 12.3x |
| TCK-20260716-AGENTOPS-REPLAY-TIMELINE | 4 | Review | architecture-reviewer | 54.127 | 4.4 | 12.3x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 4 | Review | architecture-reviewer | 54.048 | 4.4 | 12.3x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 2 | Investigate | investigator | 802.218 | 65.4 | 12.3x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 4 | Review | architecture-reviewer | 54.026 | 4.4 | 12.3x |
| TCK-20260711-EPIC-SCOPE-ORPHAN-FIX | 4 | Review | architecture-reviewer | 53.749 | 4.4 | 12.2x |
| TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK | 4 | Review | architecture-reviewer | 53.485 | 4.4 | 12.1x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 4 | Review | architecture-reviewer | 53.187 | 4.4 | 12.1x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 4 | Review | architecture-reviewer | 52.879 | 4.4 | 12.0x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 5 | Review | architecture-reviewer | 52.637 | 4.4 | 11.9x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 4 | Review | architecture-reviewer | 52.089 | 4.4 | 11.8x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 7 | Review | architecture-reviewer | 52.078 | 4.4 | 11.8x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 5 | Review | architecture-reviewer | 51.815 | 4.4 | 11.8x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 6 | Review | architecture-reviewer | 51.435 | 4.4 | 11.7x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 12 | Finalize | finalizer | 675.303 | 58.1 | 11.6x |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 4 | Review | architecture-reviewer | 50.814 | 4.4 | 11.5x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 6 | Architecture-Verify | architecture-reviewer | 535.464 | 51.7 | 10.4x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 5 | Implement | implementer | 619.269 | 60.5 | 10.2x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 2 | Investigate | investigator | 617.064 | 65.4 | 9.4x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 7 | Test | test-scoper | 547.336 | 58.4 | 9.4x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 7 | Implement | implementer | 559.772 | 60.5 | 9.3x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 10 | Finalize | finalizer | 536.0 | 58.1 | 9.2x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 12 | Finalize | finalizer | 527.988 | 58.1 | 9.1x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 5 | Implement | implementer | 546.789 | 60.5 | 9.0x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 5 | Implement | implementer | 528.578 | 60.5 | 8.7x |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 5 | Implement | implementer | 495.92 | 60.5 | 8.2x |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 5 | Implement | implementer | 478.353 | 60.5 | 7.9x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 2 | Investigate | investigator | 512.132 | 65.4 | 7.8x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 2 | Investigate | investigator | 482.209 | 65.4 | 7.4x |
| TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME | 2 | Investigate | investigator | 475.986 | 65.4 | 7.3x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 9 | Architecture-Verify | architecture-reviewer | 354.638 | 51.7 | 6.9x |
| TCK-20260710-SIMQ-DEPTH-FACTION | 2 | Investigate | investigator | 438.081 | 65.4 | 6.7x |
| TCK-20260717-GANTT-TIME-AXIS | 11 | Finalize | finalizer | 386.02 | 58.1 | 6.6x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 6 | Architecture-Verify | architecture-reviewer | 333.693 | 51.7 | 6.5x |
| TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME | 2 | Investigate | investigator | 416.131 | 65.4 | 6.4x |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 5 | Implement | implementer | 374.292 | 60.5 | 6.2x |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 5 | Implement | implementer | 360.303 | 60.5 | 6.0x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 7 | Test | test-scoper | 347.36 | 58.4 | 5.9x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 7 | Test | test-scoper | 347.264 | 58.4 | 5.9x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 5 | Finalize | finalizer | 343.786 | 58.1 | 5.9x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 11 | Finalize | finalizer | 338.657 | 58.1 | 5.8x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 9 | Verify | done-checker | 303.037 | 53.2 | 5.7x |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | 10 | Finalize | finalizer | 330.731 | 58.1 | 5.7x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 10 | Finalize | finalizer | 322.315 | 58.1 | 5.5x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 9 | Verify | done-checker | 293.789 | 53.2 | 5.5x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 2 | Investigate | investigator | 360.99 | 65.4 | 5.5x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 10 | Verify | done-checker | 289.145 | 53.2 | 5.4x |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 2 | Implement | implementer | 326.196 | 60.5 | 5.4x |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | 2 | Implement | implementer | 325.528 | 60.5 | 5.4x |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 3 | Test | test-scoper | 311.175 | 58.4 | 5.3x |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 10 | Finalize | finalizer | 302.356 | 58.1 | 5.2x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 2 | Investigate | investigator | 319.704 | 65.4 | 4.9x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 10 | Verify | done-checker | 259.841 | 53.2 | 4.9x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 10 | Finalize | finalizer | 280.802 | 58.1 | 4.8x |
| TCK-20260711-EPIC-SCOPE-ORPHAN-FIX | 9 | Verify | done-checker | 252.345 | 53.2 | 4.7x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 5 | Implement | implementer | 286.954 | 60.5 | 4.7x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 5 | Implement | implementer | 286.615 | 60.5 | 4.7x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 5 | Implement | implementer | 286.615 | 60.5 | 4.7x |
| TCK-20260717-TICKETS-TAG-SEARCH | 9 | Verify | done-checker | 247.557 | 53.2 | 4.7x |
| TCK-20260717-GANTT-TIME-AXIS | 6 | Architecture-Verify | architecture-reviewer | 232.32 | 51.7 | 4.5x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 7 | Test | test-scoper | 254.593 | 58.4 | 4.4x |
| TCK-20260717-TICKETS-TAG-SEARCH | 5 | Implement | implementer | 258.501 | 60.5 | 4.3x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 2 | Investigate | investigator | 278.746 | 65.4 | 4.3x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 2 | Investigate | investigator | 271.207 | 65.4 | 4.1x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 13 | Finalize | finalizer | 238.314 | 58.1 | 4.1x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 11 | Verify | done-checker | 218.014 | 53.2 | 4.1x |
| TCK-20260711-DOC-STALENESS-GATE-CHECK | 9 | Verify | done-checker | 214.347 | 53.2 | 4.0x |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | 5 | Implement | implementer | 242.763 | 60.5 | 4.0x |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 11 | Finalize | finalizer | 232.945 | 58.1 | 4.0x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 13 | Finalize | finalizer | 221.584 | 58.1 | 3.8x |
| TCK-20260712-WORKFLOW-FRICTION-FIXES | 5 | Implement | implementer | 225.843 | 60.5 | 3.7x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 9 | Verify | done-checker | 189.63 | 53.2 | 3.6x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 11 | Finalize | finalizer | 206.978 | 58.1 | 3.6x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 5 | Implement | implementer | 208.463 | 60.5 | 3.4x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 2 | Investigate | investigator | 220.452 | 65.4 | 3.4x |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | 10 | Finalize | finalizer | 191.232 | 58.1 | 3.3x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 5 | Implement | implementer | 197.676 | 60.5 | 3.3x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 2 | Investigate | investigator | 211.216 | 65.4 | 3.2x |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 9 | Verify | done-checker | 169.024 | 53.2 | 3.2x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 9 | Verify | done-checker | 166.731 | 53.2 | 3.1x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 7 | Test | test-scoper | 183.068 | 58.4 | 3.1x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 10 | Finalize | finalizer | 181.322 | 58.1 | 3.1x |
| TCK-20260717-TICKETS-TAG-SEARCH | 7 | Test | test-scoper | 181.619 | 58.4 | 3.1x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 1 | Implement | implementer | 187.02 | 60.5 | 3.1x |

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

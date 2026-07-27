# Agent Monitoring Retro — Last 14 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 112 |
| Completed (DONE) | 97 (86%) |
| Gate failures | 12 |
| Avg duration | 95 min |
| Avg agents per run | 7.9 |
| Total agent calls | 892 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| DOD_BLOCKED | 5 | 4% |
| NEEDS_HUMAN_INPUT | 3 | 2% |
| STOPPED_BY_USER | 2 | 1% |
| CONFLICTS_DETECTED | 1 | 0% |
| NEEDS_CHANGES | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 19 |
| conflicts_detected | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| cognition | 5 | 80% | 1 |
| dashboard | 15 | 100% | 0 |
| observability | 16 | 100% | 0 |
| self-model | 2 | 50% | 1 |
| simulation-quality | 18 | 83% | 3 |
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
| epic | 15 | 3 | 8 | 66% |
| hotfix | 17 | 0 | 17 | 100% |
| n/a | 11 | 0 | 11 | 100% |
| standard | 69 | 0 | 61 | 88% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| architecture-reviewer | 138 | 109 | 10 | 5 | 14 |
| claude-fork-direct | 12 | 12 | 0 | 0 | 0 |
| claude-orchestrator | 2 | 2 | 0 | 0 | 0 |
| create-tickets | 12 | 11 | 1 | 0 | 0 |
| done-checker | 89 | 68 | 19 | 2 | 0 |
| finalizer | 73 | 73 | 0 | 0 | 0 |
| implement-ticket | 27 | 23 | 4 | 0 | 0 |
| implement-ticket-orchestrator | 7 | 7 | 0 | 0 | 0 |
| implementer | 84 | 83 | 0 | 0 | 1 |
| investigate:C1 | 10 | 9 | 1 | 0 | 0 |
| investigate:C2 | 9 | 8 | 1 | 0 | 0 |
| investigate:C3 | 9 | 8 | 1 | 0 | 0 |
| investigate:C4 | 9 | 8 | 1 | 0 | 0 |
| investigate:C5 | 8 | 7 | 1 | 0 | 0 |
| investigate:C6 | 4 | 4 | 0 | 0 | 0 |
| investigate:C7 | 1 | 1 | 0 | 0 | 0 |
| investigate:direct | 1 | 1 | 0 | 0 | 0 |
| investigator | 65 | 58 | 0 | 0 | 7 |
| link-epic | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 4 | 4 | 0 | 0 | 0 |
| parity-updater | 63 | 43 | 0 | 0 | 20 |
| planner | 64 | 55 | 0 | 2 | 7 |
| structure | 10 | 10 | 0 | 0 | 0 |
| test-scoper | 70 | 70 | 0 | 0 | 0 |
| ticket-scoper | 117 | 116 | 1 | 0 | 0 |
| write-sequence | 1 | 1 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 62 | 55 | 0 | 1 | 6 |
| Comprehend | 11 | 11 | 0 | 0 | 0 |
| Finalize | 79 | 79 | 0 | 0 | 0 |
| Implement | 114 | 110 | 4 | 0 | 0 |
| Investigate | 120 | 107 | 6 | 0 | 7 |
| Link | 3 | 3 | 0 | 0 | 0 |
| Parity | 65 | 44 | 0 | 0 | 21 |
| Plan | 64 | 55 | 0 | 2 | 7 |
| Review | 76 | 54 | 10 | 4 | 8 |
| Scope | 74 | 73 | 1 | 0 | 0 |
| Structure | 11 | 11 | 0 | 0 | 0 |
| Test | 74 | 74 | 0 | 0 | 0 |
| Verify | 88 | 67 | 19 | 2 | 0 |
| Write | 51 | 51 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 49 | 1893.0 | 38.6 |
| Finalize | 54 | 5925.3 | 109.7 |
| Implement | 66 | 53671.5 | 813.2 |
| Investigate | 51 | 37244.6 | 730.3 |
| Parity | 48 | 1883.4 | 39.2 |
| Plan | 50 | 1900.3 | 38.0 |
| Review | 61 | 2237.6 | 36.7 |
| Scope | 52 | 35125.7 | 675.5 |
| Test | 54 | 8254.7 | 152.9 |
| Verify | 68 | 3977.1 | 58.5 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 110 | 4130.6 | 37.6 |
| claude-fork-direct | 3 | 0.0 | 0.0 |
| claude-orchestrator | 2 | 0.0 | 0.0 |
| done-checker | 71 | 3977.1 | 56.0 |
| finalizer | 50 | 5925.3 | 118.5 |
| implementer | 63 | 53671.5 | 851.9 |
| investigator | 51 | 37244.6 | 730.3 |
| parity-updater | 48 | 1883.4 | 39.2 |
| planner | 50 | 1900.3 | 38.0 |
| test-scoper | 54 | 8254.7 | 152.9 |
| ticket-scoper | 51 | 35125.7 | 688.7 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 5 |

## Slow Runs (> 30 min)

| run_id | duration | final_status |
|---|---|---|
| FOLDER-tickets-todos-simq-scoring-improvement | 839 min | STOPPED_BY_USER |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | 585 min | DONE |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | 576 min | DONE |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 541 min | STOPPED_BY_USER |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 483 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 440 min | DOD_BLOCKED |
| TCK-20260719-TAG-COLLISION-DEDUP | 429 min | DONE |
| TCK-20260721-MONITORING-WRITER-UNIFICATION | 325 min | DONE |
| EPIC-TCK-20260721-PROVIDER-AGNOSTIC-EPIC | 323 min | DONE |
| TCK-20260718-AGENTOPS-STATS-BOARD-EPIC | 275 min | DONE |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | 248 min | DONE |
| TCK-20260721-MONITORING-WRITER-DECISION | 223 min | DONE |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 173 min | DONE |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | 173 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard-ui-fixes | 173 min | DONE |
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
| TCK-20260717-GANTT-TIME-AXIS | 103 min | DONE |
| TCK-20260721-CODEX-REPLAY-PARITY | 91 min | DONE |
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
| CREATE-TICKETS-DOCS-PLANS-SIMQ-SCORING-IMPROVEMENT-ROADMAP | 60 min | DONE |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 58 min | DONE |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 57 min | DOD_BLOCKED |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 54 min | DONE |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 54 min | DONE |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 51 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 47 min | NEEDS_CHANGES |
| TCK-20260721-CODEX-REPLAY-PROOF | 47 min | DONE |
| TCK-20260718-STATUS-SUFFIX-TRIM | 40 min | DONE |
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
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | standard | 35107 | 3271 | 10.7x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | hotfix | 8827 | 826 | 10.7x |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | standard | 34600 | 3271 | 10.6x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | standard | 32485 | 3271 | 9.9x |
| TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS | hotfix | 8185 | 826 | 9.9x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | standard | 28991 | 3271 | 8.9x |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | hotfix | 6560 | 826 | 7.9x |
| TCK-20260719-TAG-COLLISION-DEDUP | standard | 25786 | 3271 | 7.9x |
| FOLDER-tickets-todos-simq-scoring-improvement | epic | 50386 | 7476 | 6.7x |
| TCK-20260721-MONITORING-WRITER-UNIFICATION | standard | 19540 | 3271 | 6.0x |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | n/a | 7189 | 1246 | 5.8x |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | standard | 14911 | 3271 | 4.6x |
| TCK-20260721-MONITORING-WRITER-DECISION | standard | 13426 | 3271 | 4.1x |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-PROGRESS-TIMELINE | n/a | 5066 | 1246 | 4.1x |
| FOLDER-tickets-todos-agent-ops-dashboard | epic | 26444 | 7476 | 3.5x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | standard | 10434 | 3271 | 3.2x |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | standard | 10411 | 3271 | 3.2x |

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | 1 | Scope | ticket-scoper | 19056.244 | 51.5 | 369.8x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE | 1 | Scope | ticket-scoper | 6503.344 | 51.5 | 126.2x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 1 | Scope | ticket-scoper | 5659.732 | 51.5 | 109.8x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 7 | Test | test-scoper | 2222.629 | 56.7 | 39.2x |
| TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE | 1 | Scope | ticket-scoper | 1963.451 | 51.5 | 38.1x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 7 | Test | test-scoper | 1478.29 | 56.7 | 26.0x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Verify | done-checker | 1060.682 | 51.9 | 20.4x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 7 | Test | test-scoper | 1099.442 | 56.7 | 19.4x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 7 | Test | test-scoper | 957.445 | 56.7 | 16.9x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 7 | Test | test-scoper | 347.36 | 56.7 | 6.1x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 8 | Parity | parity-updater | 304.841 | 52.8 | 5.8x |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 3 | Test | test-scoper | 311.175 | 56.7 | 5.5x |
| TCK-20260717-TICKETS-TAG-SEARCH | 9 | Verify | done-checker | 247.557 | 51.9 | 4.8x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 9 | Verify | done-checker | 189.63 | 51.9 | 3.7x |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 9 | Verify | done-checker | 169.024 | 51.9 | 3.3x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 9 | Verify | done-checker | 166.731 | 51.9 | 3.2x |
| TCK-20260717-TICKETS-TAG-SEARCH | 7 | Test | test-scoper | 181.619 | 56.7 | 3.2x |

## Notes

**What failed most.** `DOD_BLOCKED` (Verify phase) is the dominant gate: 5 runs ended there terminally, but 19 individual DOD_BLOCKED *events* across the window — meaning most recover on a second pass rather than staying blocked. `done-checker` has the highest failure rate of any agent (19 failed + 2 blocked / 89 calls, ~24%), followed by `architecture-reviewer` (10 failed + 5 blocked / 138, ~11%). This session's own `TCK-20260716-AGENTOPS-BUILD-SERVE` hit exactly this pattern: Verify blocked because a partial-verification gap (AC #5's port-collision check) was disclosed in Implementation Notes but not restated in the Completion Summary — fixed on retry. Given this is now a repeat pattern, not a one-off.

**What was slow.** Implement (813 avg cost-proxy) and Investigate (730 avg) dominate spend by a wide margin over every other phase — expected, they do the heaviest reading/writing. A few runs are true duration outliers regardless of tier: `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` (585 min, 10.7x its tier's median) and `TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS` (576 min, 10.6x) stand out as ticket-specific, not systemic. More notable: a cluster of SIMQ tickets show extreme **Scope-phase** cost-proxy outliers — `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`'s Scope call alone scored 19056 vs a 51.5 median (369.8x), and two more SIMQ tickets scored 100x+ — `ticket-scoper` is doing something disproportionately expensive on this ticket family specifically (worth a targeted look, likely repeated full-repo scanning rather than using the semantic search tools).

**What to change.** (1) Add an explicit Plan-phase checklist item — "if any AC is only partially/manually verified, state that explicitly in the plan's eventual Completion Summary, not just Implementation Notes" — since this is now a confirmed, reproducible cause of `DOD_BLOCKED`, not a one-off oversight. (2) Investigate why `ticket-scoper`'s Scope-phase cost blows up 100–370x on the SIMQ ticket family specifically — likely a raw-scan fallback path instead of `search_docs`/`graphify query`.

**What worked.** `dashboard` (15 runs) and `observability` (16 runs) tags — largely this session's agent-ops-dashboard batch plus its follow-up docs ticket — both closed at 100% DONE rate with zero gate failures. The SEQUENCE.md-ordered epic + sibling-ticket "Handoff Notes" pattern (each ticket's investigation leaving concrete warm-start facts for the next one in the batch) is a confirmed-good template worth reusing for future multi-ticket batches.

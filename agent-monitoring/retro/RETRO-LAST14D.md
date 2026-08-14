# Agent Monitoring Retro — Last 14 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 258 |
| Completed (DONE) | 215 (83%) |
| Gate failures | 38 |
| Avg duration | 102 min |
| Avg agents per run | 6.4 |
| Total agent calls | 1867 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| DOD_BLOCKED | 12 | 4% |
| NEEDS_CHANGES | 11 | 4% |
| NEEDS_HUMAN_INPUT | 4 | 1% |
| CONFLICTS_DETECTED | 3 | 1% |
| DOC_STALENESS_BLOCKED | 2 | 0% |
| TESTS_FAILED | 2 | 0% |
| STOPPED_FOR_HUMAN_INPUT | 1 | 0% |
| VERIFY_WRITE_CYCLE_EVIDENCE | 1 | 0% |
| BACKLOG | 1 | 0% |
| DONE_NO_TICKET | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 20 |
| needs_changes | 5 |
| conflicts_detected | 3 |
| DOD_BLOCKED | 3 |
| DOC_STALENESS_BLOCKED | 1 |
| FRONTMATTER_INVALID | 1 |
| operational_mistake | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 2 | 100% | 0 |
| cognition | 2 | 100% | 0 |
| combat | 17 | 100% | 0 |
| content | 1 | 100% | 0 |
| dashboard | 11 | 72% | 2 |
| economy | 4 | 100% | 0 |
| engine | 16 | 100% | 0 |
| faction | 5 | 100% | 0 |
| feature-flags | 4 | 100% | 0 |
| observability | 74 | 87% | 9 |
| progression | 19 | 100% | 0 |
| simulation-quality | 72 | 100% | 0 |
| strategy | 4 | 100% | 0 |
| testing | 36 | 55% | 16 |
| world | 26 | 100% | 0 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| api-design | 2 | N/A — no gate implemented |
| debugging | 1 | N/A — no gate implemented |
| performance | 6 | N/A — no gate implemented |
| security | 9 | 7 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 22 | 4 | 14 | 77% |
| hotfix | 44 | 0 | 39 | 88% |
| n/a | 8 | 0 | 8 | 100% |
| standard | 184 | 0 | 154 | 83% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| architecture-reviewer | 238 | 188 | 19 | 4 | 27 |
| claude | 90 | 90 | 0 | 0 | 0 |
| context-packet-wrapper | 12 | 12 | 0 | 0 | 0 |
| create-tickets | 7 | 7 | 0 | 0 | 0 |
| doc-updater | 67 | 67 | 0 | 0 | 0 |
| done-checker | 190 | 166 | 20 | 4 | 0 |
| epic-orchestrator | 2 | 2 | 0 | 0 | 0 |
| finalizer | 116 | 116 | 0 | 0 | 0 |
| implement-epic | 7 | 7 | 0 | 0 | 0 |
| implement-epic-orchestrator | 1 | 1 | 0 | 0 | 0 |
| implement-ticket | 35 | 32 | 3 | 0 | 0 |
| implement-ticket-orchestrator | 131 | 130 | 0 | 0 | 1 |
| implementer | 196 | 193 | 3 | 0 | 0 |
| investigate:C1 | 8 | 8 | 0 | 0 | 0 |
| investigate:C2 | 6 | 6 | 0 | 0 | 0 |
| investigate:C3 | 6 | 6 | 0 | 0 | 0 |
| investigate:C4 | 3 | 3 | 0 | 0 | 0 |
| investigator | 145 | 131 | 0 | 1 | 13 |
| link-epic | 7 | 7 | 0 | 0 | 0 |
| orchestrator | 34 | 34 | 0 | 0 | 0 |
| parity-updater | 141 | 82 | 0 | 0 | 59 |
| planner | 134 | 116 | 0 | 5 | 13 |
| security-reviewer | 2 | 2 | 0 | 0 | 0 |
| structure | 8 | 8 | 0 | 0 | 0 |
| test-scoper | 128 | 126 | 2 | 0 | 0 |
| ticket-scoper | 142 | 139 | 3 | 0 | 0 |
| workflow | 7 | 7 | 0 | 0 | 0 |
| write-sequence | 4 | 4 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 119 | 100 | 3 | 2 | 14 |
| Classify Drift | 1 | 1 | 0 | 0 | 0 |
| Comprehend | 8 | 8 | 0 | 0 | 0 |
| Discover | 5 | 5 | 0 | 0 | 0 |
| Doc-Staleness-Gate | 1 | 1 | 0 | 0 | 0 |
| Document-Update | 85 | 85 | 0 | 0 | 0 |
| Finalize | 181 | 181 | 0 | 0 | 0 |
| Implement | 219 | 213 | 6 | 0 | 0 |
| Investigate | 190 | 176 | 0 | 1 | 13 |
| Investigate-Deepen | 1 | 1 | 0 | 0 | 0 |
| Link | 7 | 7 | 0 | 0 | 0 |
| Parity | 165 | 105 | 0 | 0 | 60 |
| Parity Check | 1 | 1 | 0 | 0 | 0 |
| Plan | 156 | 138 | 0 | 5 | 13 |
| Recalibrate | 1 | 1 | 0 | 0 | 0 |
| Report | 6 | 6 | 0 | 0 | 0 |
| Retrieval | 12 | 12 | 0 | 0 | 0 |
| Review | 142 | 111 | 16 | 2 | 13 |
| Scope | 152 | 149 | 3 | 0 | 0 |
| Security-Review | 2 | 2 | 0 | 0 | 0 |
| Structure | 8 | 8 | 0 | 0 | 0 |
| Sync Docs | 1 | 1 | 0 | 0 | 0 |
| Test | 176 | 174 | 2 | 0 | 0 |
| Update Anchors | 1 | 1 | 0 | 0 | 0 |
| Verify | 204 | 180 | 20 | 4 | 0 |
| Write | 23 | 23 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 119 | 1793.9 | 15.1 |
| Doc-Staleness-Gate | 1 | 0.0 | 0.0 |
| Document-Update | 85 | 375.5 | 4.4 |
| Finalize | 181 | 4047.1 | 22.4 |
| Implement | 185 | 7287.2 | 39.4 |
| Investigate | 166 | 6694.2 | 40.3 |
| Investigate-Deepen | 1 | 0.0 | 0.0 |
| Parity | 165 | 1672.1 | 10.1 |
| Plan | 156 | 4032.8 | 25.9 |
| Report | 2 | 0.0 | 0.0 |
| Review | 142 | 3297.7 | 23.2 |
| Scope | 151 | 3364.3 | 22.3 |
| Security-Review | 2 | 0.0 | 0.0 |
| Test | 176 | 4173.7 | 23.7 |
| Verify | 203 | 4744.6 | 23.4 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 238 | 4010.8 | 16.9 |
| claude | 89 | 2444.2 | 27.5 |
| doc-updater | 67 | 292.0 | 4.4 |
| done-checker | 190 | 4665.2 | 24.6 |
| epic-orchestrator | 1 | 0.0 | 0.0 |
| finalizer | 116 | 3343.9 | 28.8 |
| implement-epic-orchestrator | 1 | 0.0 | 0.0 |
| implement-ticket | 1 | 0.0 | 0.0 |
| implement-ticket-orchestrator | 131 | 0.0 | 0.0 |
| implementer | 196 | 8414.8 | 42.9 |
| investigator | 144 | 5950.4 | 41.3 |
| orchestrator | 34 | 0.0 | 0.0 |
| parity-updater | 141 | 1672.1 | 11.9 |
| planner | 134 | 3989.8 | 29.8 |
| security-reviewer | 2 | 0.0 | 0.0 |
| test-scoper | 128 | 4141.6 | 32.4 |
| ticket-scoper | 122 | 2558.2 | 21.0 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 1 |

## Slow Runs (> 30 min)

| run_id | duration | final_status |
|---|---|---|
| TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC | 10688 min | BACKLOG |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 613 min | DONE |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 610 min | NEEDS_CHANGES |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 603 min | NEEDS_CHANGES |
| FOLDER-tickets-todos-progress-timeline | 603 min | DONE |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 592 min | NEEDS_CHANGES |
| TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD | 500 min | DONE |
| TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC | 480 min | DONE |
| TCK-20260801-CODEX-REALREPO-PILOT-HARNESS | 440 min | DONE |
| TCK-20260720-PROGRESS-TIMELINE-VIEW | 427 min | DONE |
| TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP | 390 min | DONE |
| TCK-20260802-STORED-ARTIFACT-KIND | 373 min | DONE |
| TCK-20260720-TIMELINE-RANGE-CONTROL | 369 min | DONE |
| TCK-20260804-AGENT-DEF-GAP-FIXES | 329 min | DONE |
| TCK-20260731-CODEX-PILOT-EXECUTOR | 295 min | DONE |
| TCK-20260804-EXPANSION-RATE-WIRING | 284 min | DONE |
| TCK-20260730-CODEX-RUNTIME-SHADOW | 282 min | DONE |
| TCK-20260730-CODEX-RUNTIME-SHADOW | 276 min | DOD_BLOCKED |
| EPIC-TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC | 260 min | DONE |
| EPIC-TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC | 236 min | DONE |
| FOLDER-tickets-todos-context-retrieval-phase3 | 231 min | DONE |
| FOLDER-tickets-todos-context-retrieval-phase5 | 228 min | DONE |
| FOLDER-tickets-todos-tag-registry-redesign | 224 min | DONE |
| FOLDER-tickets-todos-agent-monitoring-derived-index | 172 min | DONE |
| TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION | 145 min | DONE |
| FOLDER-tickets-todos-tag-registry-redesign | 133 min | DOC_STALENESS_BLOCKED |
| FOLDER-tickets-todos-context-retrieval-phase4 | 130 min | DONE |
| FOLDER-tickets-todos-context-efficient-retrieval | 126 min | EPIC_SCOPED |
| TCK-20260809-COMBAT-ACTIONSTYLE-WIRING | 115 min | DONE |
| TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION | 110 min | DONE |
| TCK-20260702-OBSISO-ISOLATION-PROOF | 106 min | DONE |
| TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY | 105 min | DONE |
| FOLDER-tickets-todos-placement-legality | 104 min | DONE |
| TCK-20260729-HYBRID-RETRIEVAL-FUSION | 95 min | DONE |
| TCK-20260702-OBSISO-TRACE-ASYNC | 95 min | DONE |
| TCK-20260702-OBSISO-BROKER-CONFIG | 93 min | DONE |
| TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING | 90 min | DONE |
| TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE | 90 min | DONE |
| TCK-20260804-SKILL-DRIFT-DETECTION | 89 min | DONE |
| TCK-20260720-TAG-TOUCHPOINT-CLEANUP | 87 min | DONE |
| TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC | 86 min | DONE |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 81 min | DONE |
| TCK-20260728-EVAL-FIXTURE-REPAIR | 80 min | DOD_BLOCKED |
| TCK-20260730-CODEX-POSTTOOL-ADAPTER | 79 min | DONE |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 78 min | DONE |
| TCK-20260801-CODEX-LIVE-TRANSPORT | 78 min | DONE |
| TCK-20260730-CLAUDE-EXECUTION-IDENTITY | 78 min | DONE |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 76 min | DOD_BLOCKED |
| FOLDER-tickets-todos-simq-pillar-lifecycle-depth | 76 min | DONE |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 72 min | DOD_BLOCKED |
| TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT | 70 min | DONE |
| TCK-20260730-CODEX-POSTTOOL-ADAPTER | 69 min | DOD_BLOCKED |
| TCK-20260720-SKILL-MAPPING-DEDUP | 68 min | DONE |
| TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY | 66 min | DONE |
| TCK-20260802-DOC-UPDATE-DISCIPLINE | 65 min | DONE |
| TCK-20260720-TAG-RELEVANCE-VERIFY | 63 min | DONE |
| TCK-20260731-PARITY-READPATH-GATE | 62 min | DONE |
| FOLDER-tickets-todos-context-retrieval-phase2 | 61 min | DONE |
| TCK-20260729-DETERMINISTIC-CODE-INDEX | 60 min | DONE |
| TCK-20260731-PARITY-INDEX-IMPORTER | 60 min | DONE |
| TCK-20260720-TAG-TOUCHPOINT-CLEANUP | 59 min | DOC_STALENESS_BLOCKED |
| SIMQ-AUDIT-20260807T142932Z | 59 min | DONE_NO_TICKET |
| TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT | 59 min | DONE |
| TCK-20260730-CLAUDE-EXECUTION-IDENTITY | 58 min | DOD_BLOCKED |
| TCK-20260806-PUSH-CUTOVER-PHASE2 | 57 min | DONE |
| TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW | 57 min | DONE |
| TCK-20260720-ECHARTS-PHASE-PALETTE | 57 min | DONE |
| TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION | 55 min | DONE |
| TCK-20260806-PUSH-SHADOW-VALIDATION-PERF | 55 min | DONE |
| TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF | 55 min | DONE |
| TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION | 54 min | DONE |
| TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS | 54 min | DONE |
| TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE | 53 min | DONE |
| TCK-20260730-PROVIDER-HOOK-POLICY | 53 min | DONE |
| TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE | 52 min | DONE |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 51 min | DONE |
| TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP | 51 min | DONE |
| TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP | 50 min | DONE |
| TCK-20260716-PLACELEGAL-HARDLAW | 49 min | DONE |
| TCK-20260727-CODEX-SKILL-COMPANION-ASSETS | 48 min | DONE |
| TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE | 47 min | DONE |
| TCK-20260729-RETRIEVAL-RETRO-VIEWS | 46 min | DONE |
| TCK-20260804-SKILL-JS-PHASE-SYNC | 45 min | DONE |
| TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP | 45 min | DONE |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 44 min | DOD_BLOCKED |
| TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER | 43 min | DONE |
| TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP | 42 min | DONE |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 41 min | DONE |
| TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX | 40 min | DONE |
| TCK-20260805-SKILL-GATE-CONVERSION-DECISION | 40 min | DONE |
| TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED | 40 min | DONE |
| TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG | 40 min | DONE |
| TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD | 40 min | DONE |
| TCK-20260731-PARITY-IMPACT-PROOF | 39 min | DONE |
| TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE | 38 min | DONE |
| TCK-20260729-SHADOW-PACKET-CALL-SITE | 38 min | DONE |
| TCK-20260805-PROGRESSION-ENTITIES-SKILL | 38 min | DONE |
| TCK-20260720-TAG-CATEGORY-REGISTRY | 37 min | DONE |
| TCK-20260802-CONTEXT-KIND-PRIORITY | 36 min | DONE |
| TCK-20260729-RETRIEVAL-CACHE-LEVELS | 35 min | DONE |
| TCK-20260802-EXACT-LOOKUP-CONVENTION | 35 min | DONE |
| TCK-20260805-SECURITY-GATE-FIRING-MONITOR | 35 min | DONE |
| TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT | 35 min | DONE |
| TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION | 35 min | DONE |
| TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP | 35 min | DONE |
| TCK-20260807-QUEST-EVENT-PUSH-MIGRATION | 35 min | DONE |
| TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS | 35 min | DONE |
| TCK-20260729-SHADOW-BASELINE-COMPARISON | 34 min | DONE |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 33 min | DOD_BLOCKED |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 33 min | TESTS_FAILED |
| TCK-20260805-OBSERVABILITY-SKILL | 33 min | DONE |
| TCK-20260805-SIMQ-DEV-SKILL | 33 min | DONE |
| TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION | 33 min | DONE |
| TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE | 32 min | DONE |
| TCK-20260729-CONTEXT-PACKET-ASSEMBLY | 32 min | DONE |
| TCK-20260720-TAG-CORPUS-REPAIR-SWEEP | 32 min | DONE |
| TCK-20260713-MONITORING-SQLITE-INDEX | 31 min | DONE |
| TCK-20260731-PARITY-INDEX-BASELINE | 31 min | DONE |
| TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH | 31 min | DONE |
| TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX | 31 min | DONE |
| TCK-20260728-RETRIEVAL-BASELINE-METRICS | 30 min | DONE |

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Duration outliers (by tier)

| run_id | tier | duration_s | tier median | ratio |
|---|---|---|---|---|
| TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC | epic | 641310 | 7706.0 | 83.2x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36832 | 1996 | 18.5x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36615 | 1996 | 18.3x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36222 | 1996 | 18.1x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 35563 | 1996 | 17.8x |
| TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD | standard | 30000 | 1996 | 15.0x |
| TCK-20260801-CODEX-REALREPO-PILOT-HARNESS | standard | 26413 | 1996 | 13.2x |
| TCK-20260720-PROGRESS-TIMELINE-VIEW | standard | 25634 | 1996 | 12.8x |
| TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP | standard | 23400 | 1996 | 11.7x |
| TCK-20260802-STORED-ARTIFACT-KIND | standard | 22385 | 1996 | 11.2x |
| TCK-20260720-TIMELINE-RANGE-CONTROL | standard | 22182 | 1996 | 11.1x |
| TCK-20260804-AGENT-DEF-GAP-FIXES | standard | 19762 | 1996 | 9.9x |
| TCK-20260731-CODEX-PILOT-EXECUTOR | standard | 17701 | 1996 | 8.9x |
| TCK-20260804-EXPANSION-RATE-WIRING | standard | 17081 | 1996 | 8.6x |
| TCK-20260730-CODEX-RUNTIME-SHADOW | standard | 16974 | 1996 | 8.5x |
| TCK-20260730-CODEX-RUNTIME-SHADOW | standard | 16592 | 1996 | 8.3x |
| TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW | hotfix | 3436 | 682.0 | 5.0x |
| FOLDER-tickets-todos-progress-timeline | epic | 36205 | 7706.0 | 4.7x |
| TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION | standard | 8700 | 1996 | 4.4x |
| TCK-20260804-SKILL-JS-PHASE-SYNC | hotfix | 2702 | 682.0 | 4.0x |
| TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC | epic | 28800 | 7706.0 | 3.7x |
| TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX | hotfix | 2457 | 682.0 | 3.6x |
| TCK-20260809-COMBAT-ACTIONSTYLE-WIRING | standard | 6900 | 1996 | 3.5x |
| TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION | standard | 6600 | 1996 | 3.3x |
| TCK-20260702-OBSISO-ISOLATION-PROOF | standard | 6400 | 1996 | 3.2x |
| TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY | standard | 6300 | 1996 | 3.2x |

## Retrieval Quality

_Retrieval-event volume reflects test/manual invocations only; visible under `--all`, not `--days`/`--week`, since these run_ids are deliberately unlinked from any `runs.jsonl` row._

### Cache Rates by Level

_No cache-level data this period._

### Noise Indicators

| Signal | Numerator | Denominator | Ratio |
|---|---|---|---|
| Candidate → Selected | 0 | 0 | n/a |
| Selected → Cited | 0 | 0 | n/a |

### Freshness / Authority Distribution

**Authority**

_No authority data this period._

**Freshness**

_No freshness data this period._

### Expansion Rate

**Expansion rate:** 0.0%

## Shadow vs. Baseline Retrieval Comparison

_Compares shadow-packet-covered (real TCK-... run_id) retrieval events against the synthetic/manual-invocation baseline, using the same cache-rate/noise-ratio/freshness-authority/expansion-rate measurement domain as `## Retrieval Quality` above. Comparison data only._

| Metric | Shadow | Baseline |
|---|---|---|
| Retrieval event count | 12 | 0 |
| Candidate → Selected ratio | n/a | n/a |
| Selected → Cited ratio | n/a | n/a |
| Expansion rate | 0.0% | 0.0% |

**Cache Rates by Level — Shadow**

_No cache-level data this period._

**Cache Rates by Level — Baseline**

_No cache-level data this period._

**Freshness / Authority — Shadow**

Authority: _none_
Freshness: _none_

**Freshness / Authority — Baseline**

Authority: _none_
Freshness: _none_

## Tool Safety Audit

### Search-Before-Grep Compliance (Investigate Phase)

**Compliance rate:** 58.5% (38/65 Investigate-phase calls)

### Parity Ledger Write-Safety

**`docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build` call:** 0
**Unsafe `parity_index.py build` invocations (real repo path):** 3

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

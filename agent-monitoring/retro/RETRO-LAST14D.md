# Agent Monitoring Retro — Last 14 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 248 |
| Completed (DONE) | 214 (86%) |
| Gate failures | 32 |
| Avg duration | 83 min |
| Avg agents per run | 6.8 |
| Total agent calls | 1896 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| NEEDS_CHANGES | 9 | 3% |
| NEEDS_HUMAN_INPUT | 7 | 2% |
| DOD_BLOCKED | 6 | 2% |
| CONFLICTS_DETECTED | 3 | 1% |
| TESTS_FAILED | 2 | 0% |
| DONE_NO_TICKET | 1 | 0% |
| NEEDS_TICKET | 1 | 0% |
| PARITY_INCOMPLETE | 1 | 0% |
| ANCHORS_STILL_FAILING | 1 | 0% |
| PAUSED_SESSION_LIMIT | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 22 |
| needs_changes | 5 |
| conflicts_detected | 3 |
| DOD_BLOCKED | 3 |
| architecture_violation | 3 |
| DOC_STALENESS_BLOCKED | 1 |
| FRONTMATTER_INVALID | 1 |
| operational_mistake | 1 |
| documentation_accuracy | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 11 | 100% | 0 |
| agency | 2 | 100% | 0 |
| cognition | 23 | 86% | 3 |
| combat | 34 | 100% | 0 |
| content | 2 | 100% | 0 |
| dashboard | 7 | 57% | 2 |
| economy | 6 | 100% | 0 |
| engine | 19 | 100% | 0 |
| faction | 5 | 100% | 0 |
| feature-flags | 8 | 100% | 0 |
| observability | 57 | 92% | 4 |
| progression | 20 | 100% | 0 |
| self-model | 1 | 100% | 0 |
| simulation-quality | 90 | 100% | 0 |
| social | 2 | 100% | 0 |
| strategy | 12 | 75% | 3 |
| testing | 25 | 60% | 10 |
| world | 26 | 100% | 0 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| performance | 7 | N/A — no gate implemented |
| security | 8 | 7 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 10 | 1 | 8 | 88% |
| hotfix | 43 | 0 | 40 | 93% |
| n/a | 3 | 0 | 3 | 100% |
| standard | 192 | 0 | 163 | 84% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| anchor-updater | 2 | 1 | 1 | 0 | 0 |
| architecture-reviewer | 230 | 172 | 39 | 4 | 15 |
| claude | 262 | 261 | 1 | 0 | 0 |
| context-packet-wrapper | 14 | 14 | 0 | 0 | 0 |
| create-tickets | 6 | 6 | 0 | 0 | 0 |
| doc-syncer | 1 | 1 | 0 | 0 | 0 |
| doc-updater | 98 | 98 | 0 | 0 | 0 |
| done-checker | 186 | 160 | 20 | 6 | 0 |
| drift-classifier | 2 | 2 | 0 | 0 | 0 |
| epic-orchestrator | 2 | 2 | 0 | 0 | 0 |
| finalizer | 97 | 97 | 0 | 0 | 0 |
| implement-epic | 1 | 1 | 0 | 0 | 0 |
| implement-epic-orchestrator | 1 | 1 | 0 | 0 | 0 |
| implement-ticket | 20 | 19 | 1 | 0 | 0 |
| implement-ticket-orchestrator | 105 | 105 | 0 | 0 | 0 |
| implementer | 186 | 183 | 3 | 0 | 0 |
| investigate:C1 | 6 | 6 | 0 | 0 | 0 |
| investigate:C2 | 5 | 5 | 0 | 0 | 0 |
| investigate:C3 | 5 | 5 | 0 | 0 | 0 |
| investigate:C4 | 3 | 3 | 0 | 0 | 0 |
| investigate:C5 | 1 | 1 | 0 | 0 | 0 |
| investigate:C6 | 1 | 1 | 0 | 0 | 0 |
| investigate:C7 | 1 | 1 | 0 | 0 | 0 |
| investigator | 132 | 122 | 2 | 1 | 7 |
| link-epic | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 31 | 31 | 0 | 0 | 0 |
| parity-updater | 124 | 76 | 1 | 0 | 47 |
| planner | 123 | 109 | 0 | 7 | 7 |
| security-reviewer | 2 | 2 | 0 | 0 | 0 |
| structure | 6 | 6 | 0 | 0 | 0 |
| test-scoper | 123 | 121 | 2 | 0 | 0 |
| ticket-scoper | 106 | 103 | 3 | 0 | 0 |
| workflow | 9 | 9 | 0 | 0 | 0 |
| write-sequence | 2 | 2 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 113 | 91 | 12 | 2 | 8 |
| Classify Drift | 3 | 3 | 0 | 0 | 0 |
| Comprehend | 6 | 6 | 0 | 0 | 0 |
| Doc-Staleness-Gate | 1 | 1 | 0 | 0 | 0 |
| Document-Update | 126 | 126 | 0 | 0 | 0 |
| Finalize | 189 | 189 | 0 | 0 | 0 |
| Implement | 210 | 206 | 4 | 0 | 0 |
| Investigate | 194 | 184 | 2 | 1 | 7 |
| Investigate-Deepen | 1 | 1 | 0 | 0 | 0 |
| Link | 3 | 3 | 0 | 0 | 0 |
| Parity | 165 | 117 | 1 | 0 | 47 |
| Parity Check | 2 | 2 | 0 | 0 | 0 |
| Plan | 152 | 138 | 0 | 7 | 7 |
| Recalibrate | 3 | 3 | 0 | 0 | 0 |
| Report | 8 | 8 | 0 | 0 | 0 |
| Retrieval | 14 | 14 | 0 | 0 | 0 |
| Review | 140 | 104 | 27 | 2 | 7 |
| Scope | 137 | 134 | 3 | 0 | 0 |
| Security-Review | 2 | 2 | 0 | 0 | 0 |
| Structure | 6 | 6 | 0 | 0 | 0 |
| Sync Docs | 2 | 2 | 0 | 0 | 0 |
| Test | 179 | 177 | 2 | 0 | 0 |
| Update Anchors | 3 | 2 | 1 | 0 | 0 |
| Verify | 215 | 188 | 21 | 6 | 0 |
| Write | 22 | 22 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 113 | 3666.0 | 32.4 |
| Doc-Staleness-Gate | 1 | 0.0 | 0.0 |
| Document-Update | 126 | 2399.7 | 19.0 |
| Finalize | 189 | 4479.3 | 23.7 |
| Implement | 191 | 10266.0 | 53.7 |
| Investigate | 171 | 13170.0 | 77.0 |
| Investigate-Deepen | 1 | 0.0 | 0.0 |
| Parity | 165 | 2497.4 | 15.1 |
| Plan | 152 | 5155.0 | 33.9 |
| Report | 2 | 0.0 | 0.0 |
| Review | 140 | 4545.9 | 32.5 |
| Scope | 136 | 2057.3 | 15.1 |
| Security-Review | 2 | 0.0 | 0.0 |
| Test | 179 | 5236.9 | 29.3 |
| Verify | 213 | 6623.8 | 31.1 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 230 | 6897.6 | 30.0 |
| claude | 260 | 13399.0 | 51.5 |
| doc-updater | 98 | 2121.6 | 21.6 |
| done-checker | 185 | 5541.6 | 30.0 |
| epic-orchestrator | 1 | 0.0 | 0.0 |
| finalizer | 97 | 2742.1 | 28.3 |
| implement-epic-orchestrator | 1 | 0.0 | 0.0 |
| implement-ticket | 1 | 0.0 | 0.0 |
| implement-ticket-orchestrator | 105 | 7.7 | 0.1 |
| implementer | 186 | 10675.6 | 57.4 |
| investigator | 131 | 7001.6 | 53.4 |
| orchestrator | 31 | 0.0 | 0.0 |
| parity-updater | 123 | 2223.7 | 18.1 |
| planner | 123 | 4237.3 | 34.4 |
| security-reviewer | 2 | 0.0 | 0.0 |
| test-scoper | 123 | 4012.3 | 32.6 |
| ticket-scoper | 84 | 1236.9 | 14.7 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 1 |

## Slow Runs (> 30 min)

| run_id | duration | final_status |
|---|---|---|
| FOLDER-tickets-todos-adventure-cognition-merge | 1912 min | DONE |
| TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP | 630 min | DONE |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 613 min | DONE |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 610 min | NEEDS_CHANGES |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 603 min | NEEDS_CHANGES |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 592 min | NEEDS_CHANGES |
| TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD | 500 min | DONE |
| TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC | 480 min | DONE |
| EPIC-TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC | 476 min | DONE |
| TCK-20260801-CODEX-REALREPO-PILOT-HARNESS | 440 min | DONE |
| FOLDER-cognition-adventure-eligibility | 416 min | DONE |
| TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG | 399 min | DONE |
| TCK-20260811-REGION-STABILIZATION-GOAL-SCORER | 396 min | DONE |
| TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP | 390 min | DONE |
| TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE | 386 min | DONE |
| TCK-20260802-STORED-ARTIFACT-KIND | 373 min | DONE |
| TCK-20260804-AGENT-DEF-GAP-FIXES | 329 min | DONE |
| TCK-20260731-CODEX-PILOT-EXECUTOR | 295 min | DONE |
| TCK-20260804-EXPANSION-RATE-WIRING | 284 min | DONE |
| TCK-20260811-ADVENTURE-GOAL-SCORER | 266 min | DONE |
| EPIC-TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC | 260 min | DONE |
| EPIC-TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC | 236 min | DONE |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | 224 min | DONE |
| TCK-20260811-MULTI-STEP-PLANNING-DESIGN | 211 min | DONE |
| TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING | 206 min | DONE |
| TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION | 196 min | DONE |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | 176 min | DONE |
| EPIC-TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC | 172 min | NEEDS_HUMAN_INPUT |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | 171 min | NEEDS_HUMAN_INPUT |
| TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE | 153 min | DONE |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | 149 min | DONE |
| TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION | 145 min | DONE |
| TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE | 135 min | DONE |
| TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS | 127 min | DONE |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | 124 min | PARITY_INCOMPLETE |
| TCK-20260809-COMBAT-ACTIONSTYLE-WIRING | 115 min | DONE |
| TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION | 110 min | DONE |
| TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE | 107 min | DONE |
| TCK-20260702-OBSISO-ISOLATION-PROOF | 106 min | DONE |
| TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY | 105 min | DONE |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 104 min | DONE |
| TCK-20260812-COMMITTED-INTENTION-SEQUENCE | 100 min | DONE |
| TCK-20260702-OBSISO-TRACE-ASYNC | 95 min | DONE |
| TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION | 95 min | DONE |
| TCK-20260702-OBSISO-BROKER-CONFIG | 93 min | DONE |
| TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING | 90 min | DONE |
| TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE | 90 min | DONE |
| TCK-20260804-SKILL-DRIFT-DETECTION | 89 min | DONE |
| TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC | 86 min | DONE |
| TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY | 85 min | DONE |
| TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY | 83 min | DONE |
| TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER | 82 min | DONE |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 81 min | DONE |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 78 min | DONE |
| TCK-20260801-CODEX-LIVE-TRANSPORT | 78 min | DONE |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 76 min | DOD_BLOCKED |
| FOLDER-tickets-todos-simq-pillar-lifecycle-depth | 76 min | DONE |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 72 min | DOD_BLOCKED |
| TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS | 72 min | DONE |
| SIMQ-AUDIT-20260811T111151Z | 70 min | ANCHORS_STILL_FAILING |
| TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL | 70 min | DONE |
| TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT | 70 min | DONE |
| TCK-20260810-SKILL-USAGE-RETRO-TRACKING | 67 min | DONE |
| TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY | 66 min | DONE |
| TCK-20260802-DOC-UPDATE-DISCIPLINE | 65 min | DONE |
| TCK-20260731-PARITY-READPATH-GATE | 62 min | DONE |
| TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING | 62 min | DONE |
| TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING | 60 min | DONE |
| TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION | 60 min | DONE |
| TCK-20260731-PARITY-INDEX-IMPORTER | 60 min | DONE |
| SIMQ-AUDIT-20260807T142932Z | 59 min | DONE_NO_TICKET |
| TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY | 59 min | DONE |
| TCK-20260806-PUSH-CUTOVER-PHASE2 | 57 min | DONE |
| TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW | 57 min | DONE |
| TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION | 55 min | DONE |
| TCK-20260806-PUSH-SHADOW-VALIDATION-PERF | 55 min | DONE |
| TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF | 55 min | DONE |
| TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES | 55 min | DONE |
| TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS | 54 min | DONE |
| TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP | 54 min | DONE |
| TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET | 52 min | DONE |
| TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE | 52 min | DONE |
| TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS | 51 min | DONE |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 51 min | DONE |
| TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP | 51 min | DONE |
| TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY | 50 min | DONE |
| TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP | 50 min | DONE |
| TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION | 47 min | DONE |
| TCK-20260810-STATUS-DRIFT-CHECK-WIRING | 46 min | DONE |
| TCK-20260804-SKILL-JS-PHASE-SYNC | 45 min | DONE |
| TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP | 45 min | DONE |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 44 min | DOD_BLOCKED |
| TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG | 43 min | DONE |
| TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER | 43 min | DONE |
| TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP | 42 min | DONE |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 41 min | DONE |
| TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX | 40 min | DONE |
| TCK-20260805-SKILL-GATE-CONVERSION-DECISION | 40 min | DONE |
| TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED | 40 min | DONE |
| TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG | 40 min | DONE |
| TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD | 40 min | DONE |
| TCK-20260731-PARITY-IMPACT-PROOF | 39 min | DONE |
| TCK-20260805-PROGRESSION-ENTITIES-SKILL | 38 min | DONE |
| TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION | 36 min | DONE |
| TCK-20260802-CONTEXT-KIND-PRIORITY | 36 min | DONE |
| TCK-20260802-EXACT-LOOKUP-CONVENTION | 35 min | DONE |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | 35 min | NEEDS_CHANGES |
| TCK-20260805-SECURITY-GATE-FIRING-MONITOR | 35 min | DONE |
| TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT | 35 min | DONE |
| TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION | 35 min | DONE |
| TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP | 35 min | DONE |
| TCK-20260807-QUEST-EVENT-PUSH-MIGRATION | 35 min | DONE |
| TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS | 35 min | DONE |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 33 min | DOD_BLOCKED |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 33 min | TESTS_FAILED |
| TCK-20260805-OBSERVABILITY-SKILL | 33 min | DONE |
| TCK-20260805-SIMQ-DEV-SKILL | 33 min | DONE |
| TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION | 33 min | DONE |
| TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE | 32 min | DONE |
| TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK | 32 min | DONE |
| TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK | 31 min | DONE |
| SIMQ-AUDIT-20260810T032558Z | 31 min | NEEDS_TICKET |
| TCK-20260731-PARITY-INDEX-BASELINE | 31 min | DONE |
| TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH | 31 min | DONE |
| TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX | 31 min | DONE |
| TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT | 31 min | DONE |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | 30 min | NEEDS_HUMAN_INPUT |
| TCK-20260809-MONITORING-ZERO-DURATION-COMBAT-RUNS-HOTFIX | 30 min | DONE |

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Duration outliers (by tier)

| run_id | tier | duration_s | tier median | ratio |
|---|---|---|---|---|
| TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG | hotfix | 23963 | 852 | 28.1x |
| TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP | standard | 37834 | 2122 | 17.8x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36832 | 2122 | 17.4x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36615 | 2122 | 17.3x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36222 | 2122 | 17.1x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 35563 | 2122 | 16.8x |
| TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD | standard | 30000 | 2122 | 14.1x |
| TCK-20260801-CODEX-REALREPO-PILOT-HARNESS | standard | 26413 | 2122 | 12.4x |
| FOLDER-cognition-adventure-eligibility | standard | 25009 | 2122 | 11.8x |
| TCK-20260811-REGION-STABILIZATION-GOAL-SCORER | standard | 23794 | 2122 | 11.2x |
| TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP | standard | 23400 | 2122 | 11.0x |
| TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE | standard | 23162 | 2122 | 10.9x |
| TCK-20260802-STORED-ARTIFACT-KIND | standard | 22385 | 2122 | 10.5x |
| FOLDER-tickets-todos-adventure-cognition-merge | epic | 114727 | 12256.0 | 9.4x |
| TCK-20260804-AGENT-DEF-GAP-FIXES | standard | 19762 | 2122 | 9.3x |
| TCK-20260731-CODEX-PILOT-EXECUTOR | standard | 17701 | 2122 | 8.3x |
| TCK-20260804-EXPANSION-RATE-WIRING | standard | 17081 | 2122 | 8.0x |
| TCK-20260811-ADVENTURE-GOAL-SCORER | standard | 16005 | 2122 | 7.5x |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | standard | 13482 | 2122 | 6.4x |
| TCK-20260811-MULTI-STEP-PLANNING-DESIGN | standard | 12676 | 2122 | 6.0x |
| TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING | standard | 12385 | 2122 | 5.8x |
| TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION | standard | 11810 | 2122 | 5.6x |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | standard | 10587 | 2122 | 5.0x |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | standard | 10273 | 2122 | 4.8x |
| TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE | standard | 9237 | 2122 | 4.4x |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | standard | 8960 | 2122 | 4.2x |
| TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION | standard | 8700 | 2122 | 4.1x |
| TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW | hotfix | 3436 | 852 | 4.0x |
| TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE | standard | 8109 | 2122 | 3.8x |
| TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS | standard | 7654 | 2122 | 3.6x |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | standard | 7496 | 2122 | 3.5x |
| TCK-20260809-COMBAT-ACTIONSTYLE-WIRING | standard | 6900 | 2122 | 3.3x |
| TCK-20260804-SKILL-JS-PHASE-SYNC | hotfix | 2702 | 852 | 3.2x |
| TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION | standard | 6600 | 2122 | 3.1x |
| TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE | standard | 6454 | 2122 | 3.0x |
| TCK-20260702-OBSISO-ISOLATION-PROOF | standard | 6400 | 2122 | 3.0x |

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS | 1 | Investigate | claude | 888.051 | 6.6 | 135.5x |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 1 | Investigate | investigator | 860.991 | 6.6 | 131.3x |
| TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP | 1 | Investigate | claude | 692.077 | 6.6 | 105.6x |
| TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION | 1 | Investigate | claude | 602.912 | 6.6 | 92.0x |
| TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE | 1 | Investigate | investigator | 581.595 | 6.6 | 88.7x |
| TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK | 1 | Investigate | claude | 503.72700000000003 | 6.6 | 76.8x |
| TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION | 1 | Investigate | claude | 476.866 | 6.6 | 72.7x |
| TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS | 1 | Investigate | claude | 425.931 | 6.6 | 65.0x |
| TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION | 2 | Investigate | claude | 405.94100000000003 | 6.6 | 61.9x |
| TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP | 1 | Investigate | investigator | 403.29900000000004 | 6.6 | 61.5x |
| TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX | 1 | Investigate | investigator | 356.40500000000003 | 6.6 | 54.4x |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | 1 | Investigate | investigator | 338.936 | 6.6 | 51.7x |
| TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE | 2 | Investigate | claude | 318.337 | 6.6 | 48.6x |
| TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION | 1 | Investigate | investigator | 291.056 | 6.6 | 44.4x |
| TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY | 2 | Investigate | claude | 252.69 | 6.6 | 38.5x |
| TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION | 1 | Investigate | investigator | 248.818 | 6.6 | 38.0x |
| TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK | 1 | Investigate | claude | 248.793 | 6.6 | 38.0x |
| TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE | 2 | Investigate | claude | 240.983 | 6.6 | 36.8x |
| TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE | 1 | Investigate | claude | 214.196 | 6.6 | 32.7x |
| TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET | 1 | Investigate | claude | 179.53 | 6.6 | 27.4x |
| TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG | 1 | Investigate | claude | 179.048 | 6.6 | 27.3x |
| TCK-20260731-PARITY-INDEX-IMPORTER | 3 | Investigate | investigator | 172.419 | 6.6 | 26.3x |
| TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS | 1 | Investigate | claude | 162.693 | 6.6 | 24.8x |
| TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP | 1 | Investigate | investigator | 157.624 | 6.6 | 24.0x |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | 2 | Investigate | investigator | 151.514 | 6.6 | 23.1x |
| TCK-20260812-COMMITTED-INTENTION-SEQUENCE | 1 | Investigate | investigator | 151.483 | 6.6 | 23.1x |
| TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE | 1 | Investigate | claude | 146.59 | 6.6 | 22.4x |
| TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG | 1 | Investigate | investigator | 133.68099999999998 | 6.6 | 20.4x |
| TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE | 1 | Investigate | investigator | 132.888 | 6.6 | 20.3x |
| TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF | 1 | Investigate | investigator | 125.657 | 6.6 | 19.2x |
| TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES | 2 | Investigate | claude | 121.867 | 6.6 | 18.6x |
| TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS | 1 | Investigate | investigator | 115.831 | 6.6 | 17.7x |
| TCK-20260731-PARITY-INDEX-BASELINE | 12 | Investigate | investigator | 105.90700000000001 | 6.6 | 16.2x |
| TCK-20260731-PARITY-IMPACT-PROOF | 2 | Investigate | investigator | 98.941 | 6.6 | 15.1x |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | 2 | Investigate | investigator | 88.196 | 6.6 | 13.5x |
| TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE | 1 | Investigate | investigator | 87.494 | 6.6 | 13.3x |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 3 | Investigate | investigator | 85.925 | 6.6 | 13.1x |
| TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE | 1 | Investigate | investigator | 85.8 | 6.6 | 13.1x |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 2 | Investigate | investigator | 85.197 | 6.6 | 13.0x |
| TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING | 1 | Investigate | investigator | 84.041 | 6.6 | 12.8x |
| TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION | 1 | Investigate | investigator | 83.39 | 6.6 | 12.7x |
| TCK-20260802-CONTEXT-KIND-PRIORITY | 2 | Investigate | investigator | 83.029 | 6.6 | 12.7x |
| TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION | 1 | Investigate | investigator | 82.851 | 6.6 | 12.6x |
| TCK-20260811-MULTI-STEP-PLANNING-DESIGN | 1 | Investigate | investigator | 82.679 | 6.6 | 12.6x |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 2 | Investigate | investigator | 82.2 | 6.6 | 12.5x |
| TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING | 2 | Investigate | investigator | 82.179 | 6.6 | 12.5x |
| TCK-20260802-STORED-ARTIFACT-KIND | 2 | Investigate | investigator | 81.844 | 6.6 | 12.5x |
| TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL | 2 | Investigate | investigator | 81.104 | 6.6 | 12.4x |
| TCK-20260810-SKILL-USAGE-RETRO-TRACKING | 2 | Investigate | investigator | 79.20400000000001 | 6.6 | 12.1x |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | 4 | Investigate | investigator | 79.11 | 6.6 | 12.1x |
| TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING | 1 | Investigate | investigator | 78.798 | 6.6 | 12.0x |
| TCK-20260811-REGION-STABILIZATION-GOAL-SCORER | 1 | Investigate | investigator | 76.489 | 6.6 | 11.7x |
| TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY | 1 | Investigate | investigator | 75.842 | 6.6 | 11.6x |
| TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER | 1 | Investigate | investigator | 74.964 | 6.6 | 11.4x |
| TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT | 1 | Investigate | claude | 74.90700000000001 | 6.6 | 11.4x |
| TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS | 1 | Investigate | investigator | 74.745 | 6.6 | 11.4x |
| TCK-20260810-STATUS-DRIFT-CHECK-WIRING | 2 | Investigate | investigator | 74.225 | 6.6 | 11.3x |
| TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION | 1 | Investigate | investigator | 71.352 | 6.6 | 10.9x |
| TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS | 1 | Investigate | investigator | 70.515 | 6.6 | 10.8x |
| TCK-20260802-EXACT-LOOKUP-CONVENTION | 2 | Investigate | investigator | 69.777 | 6.6 | 10.6x |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | 3 | Investigate | investigator | 69.679 | 6.6 | 10.6x |
| TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION | 1 | Investigate | investigator | 69.029 | 6.6 | 10.5x |
| TCK-20260731-PARITY-READPATH-GATE | 2 | Investigate | investigator | 68.467 | 6.6 | 10.4x |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 2 | Investigate | investigator | 65.017 | 6.6 | 9.9x |
| TCK-20260807-SIMQ-COMBAT-SCORE-TOLERANCE-DRIFT-INVESTIGATION | 1 | Investigate | investigator | 38.335 | 6.6 | 5.8x |
| TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS | 1 | Investigate | investigator | 34.624 | 6.6 | 5.3x |
| TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE | 1 | Investigate | investigator | 24.923000000000002 | 6.6 | 3.8x |

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
| Retrieval event count | 14 | 0 |
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

## Search & Investigation Effort

### Search Calls (Follow-Up Search Tooling)

**Total:** 254

### Raw Investigation (Read) Calls

**Total:** 3668
**Read-to-search ratio:** 14.4409

## Tool Safety Audit

### Search-Before-Grep Compliance (Investigate Phase)

**Compliance rate:** 63.7% (58/91 Investigate-phase calls)

### Parity Ledger Write-Safety

**`docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build` call:** 15
**Unsafe `parity_index.py build` invocations (real repo path):** 13

### Read-Count Correlation (Search-Before-Grep Compliance)

| Group | Pairs | Median Read count | Avg Read count |
|---|---|---|---|
| Compliant | 58 | 10.0 | 10.4 |
| Non-compliant | 33 | 2.0 | 6.9 |

## Parity Index Read-Path Usage

**`entry`/`impact`/`health` call count:** 0/12084 Bash rows scanned

_Counts tools.jsonl rows where tool == "Bash" and input_summary matches parity_index.py followed immediately by entry, impact, or health (path-anchored, so a filename mention alone — e.g. test_parity_index.py, --help, `git log -- ... parity_index.py`, `sed -n '1,60p' tools/parity_index.py` — never counts). bash_rows_scanned is the total Bash-tool row population this detector ran against (the section's own 'N' denominator). Confirmed 0 real call sites as of TCK-20260731-PARITY-READPATH-GATE's Gate A review (reviewed GO, not yet wired into any real workflow call site) — this is the expected, correct value until a future ticket adds a real entry/impact/health call site, not a bug._

## Skill Usage

### Per-Skill Invocation Counts (This Period)

| Skill | Invocations |
|---|---|
| agent-monitoring-retro | 4 |
| artifact-design | 1 |
| brainstorming | 2 |
| cognition-strategy | 1 |
| create-tickets | 1 |
| dataviz | 1 |
| graphify | 2 |
| implement-epic | 1 |
| implement-ticket | 1 |
| simq-audit | 2 |

**Total:** 16

_Derived from tools.jsonl's literal `tool` field, filtered to `tool == 'Skill'`, with the skill name extracted from `input_summary` via regex (r\"'skill':\s*'([^']*)'\") — never json.loads(), since input_summary is a Python dict-repr string, not JSON. Records where the regex finds no match are counted under `unparseable`, never silently dropped. `unattributed` covers Skill invocations with no run_id (interactive, outside any workflow run). Distinct from generate_retro.py's tag_breakdown_skill aggregate — this is a raw per-skill invocation count, not a tag-driven gate-hit count._

### Zero-Invocation Flags (All-Time, 14-Day Grace Period)

**Flagged (confirmed age past grace period):** api-design-principles, architecture
**Flagged (unknown age, no `date_added`):** debugging-strategies, doc-coauthoring, frontend-design, prompt-builder, python-performance-optimization, python-testing-patterns, test-driven-development

_All-time (never period-scoped) cross-reference of the real .claude/skills/*/SKILL.md catalog against build_skill_usage_section(tools)'s per_skill counts. A skill with any nonzero invocation count is never flagged, regardless of age. Of the remaining zero-invocation skills: `flagged_stale` requires a real, parseable `date_added` older than the 14-day grace period — a confirmed-age signal. `flagged_unknown_age` covers skills with no (or unparseable) `date_added` and zero invocations — an honest, lower-certainty signal, not proof of staleness, since no authorship date can be established. This fail-open policy on missing date_added is deliberate: it is what makes backend-testing's real pre-TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED state (no date_added field at all) correctly flaggable, per TCK-20260810-SKILL-USAGE-RETRO-TRACKING's AC2._

## Notes

### Epic verification check — TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC

This window's report was generated specifically to check whether
`agent-tooling-integrity-hardening`'s 5 child tickets (all closed 2026-08-14) produced real,
observable effect, per that epic's own Verification Note requirement. Findings against its 3
named signals plus the separate status-drift check:

1. **Parity ledger write-safety co-occurrence** — moved from the epic's original 0/N baseline to
   **15** `docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build`
   call in this window (13 flagged as the real-repo-path "unsafe" variant, which the metric's own
   design treats as informational, not a failure — the new schema-validating writer built by
   `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` triggers the in-process rebuild plus a required
   separate visible build call on every write). Real, positive, measured movement.

2. **Skill-adoption numbers** — the zero-invocation flag mechanism (`TCK-20260810-SKILL-USAGE-RETRO-TRACKING`)
   is now live and correctly excludes all 6 domain skills from `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`
   (still within the 14-day grace period). `cognition-strategy` already shows 1 real invocation
   this window, up from the epic's original 0. Real, positive, measured movement — full "did
   adoption actually happen" evidence needs more time past the grace period, but the visibility
   mechanism itself is confirmed working on real data.

3. **Search-before-grep compliance rate** — corpus-wide compliance this window is 63.7% (58/91
   Investigate-phase calls), but **this number does not yet demonstrate
   `TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`'s specific fix**. That ticket targeted
   hand-orchestrated (`agent=claude`) Investigate-phase work that never spawns the `investigator`
   subagent — checking `events.jsonl` directly, the most recent `agent=claude` Investigate-phase
   event in the entire corpus is from 2026-08-10T07:12:00Z, before the fix landed
   (committed 2026-08-14T18:47Z as part of this epic's closing work). No hand-orchestrated
   Investigate-phase run has occurred since the fix shipped, so there is no real data yet
   confirming compliance improved for the specific gap this ticket closed — only that the callout
   is present and reachable (already verified structurally during that ticket's own Architecture-Verify
   pass). This is a genuine, honest gap, not a fabricated pass: the fix's effect can only be
   measured once a real hand-orchestrated Investigate run recurs naturally.

4. **Status drift (separate criterion, not retro-based)** — `status_drift_check.py` run live
   post-fix shows exactly 2 FAIL findings, both the documented known false positives
   (`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md`, `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md`).
   Zero real drift remains. This criterion is fully satisfied.

**Conclusion:** 2 of 3 retro-based signals plus the separate status-drift check show real,
positive, non-fabricated movement. The 3rd (search-before-grep compliance) cannot be confirmed
or denied yet — the fix is real and reachable, but its target failure mode has not recurred since
the fix shipped. Recommend flagging the epic as substantially verified with one signal pending
natural recurrence, rather than either closing it outright or blocking it indefinitely on a
metric that structurally cannot move faster than real hand-orchestrated work occurs.

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

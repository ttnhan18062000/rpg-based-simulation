# Agent Monitoring Retro — Last 28 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 455 |
| Completed (DONE) | 427 (93%) |
| Gate failures | 24 |
| Avg duration | 109 min |
| Avg agents per run | 7.4 |
| Total agent calls | 3748 |

_Note: 468 raw `runs.jsonl` rows in this window collapsed to 455 real executions after deduplicating gate-checkpoint rows that share one `(run_id, execution_id, start_ts)` identity (TCK-20260915-DUPLICATE-RUN-RECORDS) — the counts above are the deduplicated figures._

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| BLOCKED | 12 | 2% |
| NEEDS_HUMAN_INPUT | 7 | 1% |
| DOD_BLOCKED | 2 | 0% |
| NEEDS_CHANGES | 2 | 0% |
| TESTS_FAILED | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 35 |
| needs_changes | 13 |
| plan_needs_changes | 3 |
| conflicts_detected | 2 |
| no_behavior_change | 1 |
| transient_infra_error | 1 |
| new_open_question_discovered | 1 |
| governance_conflict | 1 |
| scope_larger_than_anticipated | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 3 | 100% | 0 |
| architecture | 66 | 89% | 5 |
| cognition | 35 | 82% | 6 |
| combat | 17 | 82% | 3 |
| content | 42 | 92% | 2 |
| core | 2 | 100% | 0 |
| dashboard | 2 | 100% | 0 |
| ecology | 1 | 100% | 0 |
| economy | 9 | 88% | 1 |
| engine | 27 | 96% | 1 |
| faction | 9 | 100% | 0 |
| feature-flags | 15 | 93% | 1 |
| governance | 10 | 100% | 0 |
| grade-thresholds | 3 | 66% | 1 |
| grand-strategy | 2 | 100% | 0 |
| hud | 2 | 100% | 0 |
| information | 12 | 66% | 4 |
| lifecycle | 13 | 100% | 0 |
| live-map | 1 | 100% | 0 |
| mcp | 15 | 100% | 0 |
| observability | 27 | 92% | 1 |
| progression | 6 | 100% | 0 |
| rendering | 8 | 87% | 0 |
| resource | 1 | 100% | 0 |
| self-model | 6 | 50% | 3 |
| simulation-quality | 46 | 89% | 4 |
| social | 37 | 91% | 3 |
| strategy | 14 | 92% | 1 |
| temporal | 1 | 100% | 0 |
| testing | 72 | 93% | 5 |
| visualization | 10 | 90% | 0 |
| websocket | 8 | 100% | 0 |
| world | 48 | 87% | 4 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| api-design | 8 | N/A — no gate implemented |
| debugging | 7 | N/A — no gate implemented |
| performance | 23 | N/A — no gate implemented |
| security | 5 | 4 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 15 | 4 | 11 | 100% |
| hotfix | 129 | 0 | 126 | 97% |
| n/a | 17 | 0 | 17 | 100% |
| standard | 294 | 0 | 273 | 92% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| advisory-checks | 4 | 4 | 0 | 0 | 0 |
| architecture-reviewer | 422 | 286 | 43 | 28 | 65 |
| claude | 1162 | 1030 | 1 | 14 | 117 |
| cleanup-checkpoint | 4 | 4 | 0 | 0 | 0 |
| concern-investigator | 7 | 7 | 0 | 0 | 0 |
| consolidation | 1 | 1 | 0 | 0 | 0 |
| context-packet-wrapper | 35 | 35 | 0 | 0 | 0 |
| create-tickets | 22 | 22 | 0 | 0 | 0 |
| doc-updater | 185 | 184 | 0 | 0 | 1 |
| done-checker | 258 | 195 | 46 | 17 | 0 |
| finalizer | 156 | 156 | 0 | 0 | 0 |
| implement-ticket | 18 | 17 | 1 | 0 | 0 |
| implement-ticket-orchestrator | 6 | 6 | 0 | 0 | 0 |
| implementer | 199 | 195 | 2 | 2 | 0 |
| investigate:C1 | 11 | 11 | 0 | 0 | 0 |
| investigate:C10 | 3 | 3 | 0 | 0 | 0 |
| investigate:C11 | 2 | 2 | 0 | 0 | 0 |
| investigate:C12 | 2 | 2 | 0 | 0 | 0 |
| investigate:C13 | 2 | 2 | 0 | 0 | 0 |
| investigate:C14 | 2 | 2 | 0 | 0 | 0 |
| investigate:C15 | 2 | 2 | 0 | 0 | 0 |
| investigate:C2 | 10 | 10 | 0 | 0 | 0 |
| investigate:C3 | 9 | 9 | 0 | 0 | 0 |
| investigate:C4 | 7 | 7 | 0 | 0 | 0 |
| investigate:C5 | 6 | 5 | 0 | 0 | 1 |
| investigate:C6 | 4 | 4 | 0 | 0 | 0 |
| investigate:C7 | 4 | 4 | 0 | 0 | 0 |
| investigate:C8 | 4 | 3 | 0 | 1 | 0 |
| investigate:C9 | 3 | 3 | 0 | 0 | 0 |
| investigate:D1 | 1 | 1 | 0 | 0 | 0 |
| investigate:D2 | 1 | 1 | 0 | 0 | 0 |
| investigate:D3 | 1 | 1 | 0 | 0 | 0 |
| investigator | 171 | 134 | 0 | 0 | 37 |
| link-epic | 6 | 5 | 0 | 0 | 1 |
| orchestrator | 215 | 194 | 5 | 0 | 16 |
| parity-updater | 176 | 144 | 2 | 0 | 30 |
| planner | 190 | 146 | 0 | 7 | 37 |
| security-reviewer | 10 | 4 | 0 | 0 | 6 |
| self-doc-update | 1 | 1 | 0 | 0 | 0 |
| self-parity | 1 | 1 | 0 | 0 | 0 |
| self-review | 2 | 2 | 0 | 0 | 0 |
| self-test | 1 | 1 | 0 | 0 | 0 |
| self-verify | 2 | 1 | 1 | 0 | 0 |
| structure | 14 | 14 | 0 | 0 | 0 |
| test-scoper | 184 | 168 | 14 | 1 | 1 |
| ticket-scoper | 207 | 205 | 2 | 0 | 0 |
| write:CAPABILITY-DRIVEN-TARGETING | 1 | 1 | 0 | 0 | 0 |
| write:CLAN-STATE-SCHEMA | 1 | 1 | 0 | 0 | 0 |
| write:CLASS-TIER-BRANCHING | 1 | 1 | 0 | 0 | 0 |
| write:CREATURE-TERRITORY-LIFECYCLE | 1 | 1 | 0 | 0 | 0 |
| write:DEAD-COGNITION-SCHEMA-DECISION | 1 | 1 | 0 | 0 | 0 |
| write:HABIT-BIAS-WIRING | 1 | 1 | 0 | 0 | 0 |
| write:ITEM-INSTANCE-HISTORY | 1 | 1 | 0 | 0 | 0 |
| write:METAMORPHIC-LAB-PILOT | 1 | 1 | 0 | 0 | 0 |
| write:POPULATION-COHORT-SEEDING | 1 | 1 | 0 | 0 | 0 |
| write:RACE-RELATIONS-MATRIX | 1 | 1 | 0 | 0 | 0 |
| write:READINESS-SPEED-FORMULA | 1 | 1 | 0 | 0 | 0 |
| write:ROLE-MODEL-IMITATION | 1 | 1 | 0 | 0 | 0 |
| write:SPECIES-INTELLIGENCE-TIER | 1 | 1 | 0 | 0 | 0 |
| write:STATUS-EFFECT-STATE-UNIFICATION | 1 | 1 | 0 | 0 | 0 |
| write:TRUST-GATED-TEACHING | 1 | 1 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 195 | 154 | 2 | 7 | 32 |
| Architecture-Verify-Recheck | 1 | 1 | 0 | 0 | 0 |
| Comprehend | 16 | 16 | 0 | 0 | 0 |
| Doc-Staleness-Gate | 1 | 1 | 0 | 0 | 0 |
| Document-Update | 203 | 201 | 0 | 0 | 2 |
| Document-Update-Gate | 6 | 6 | 0 | 0 | 0 |
| Finalize | 411 | 406 | 0 | 3 | 2 |
| Fix | 1 | 1 | 0 | 0 | 0 |
| Implement | 405 | 393 | 2 | 3 | 7 |
| Investigate | 323 | 282 | 1 | 2 | 38 |
| Link | 8 | 7 | 0 | 0 | 1 |
| Parity | 341 | 196 | 3 | 1 | 141 |
| Parity-Gate | 4 | 4 | 0 | 0 | 0 |
| Plan | 227 | 182 | 0 | 8 | 37 |
| Plan-Fix | 4 | 4 | 0 | 0 | 0 |
| Retrieval | 35 | 35 | 0 | 0 | 0 |
| Review | 253 | 158 | 41 | 21 | 33 |
| Review-Recheck | 5 | 5 | 0 | 0 | 0 |
| Scope | 351 | 349 | 2 | 0 | 0 |
| Security-Review | 17 | 4 | 0 | 0 | 13 |
| Structure | 17 | 17 | 0 | 0 | 0 |
| Test | 385 | 362 | 14 | 3 | 6 |
| Test-Cleanup-Checkpoint | 6 | 6 | 0 | 0 | 0 |
| Verify | 427 | 354 | 52 | 21 | 0 |
| Verify-Recheck | 5 | 4 | 0 | 1 | 0 |
| Verify-Recheck2 | 1 | 1 | 0 | 0 | 0 |
| Write | 84 | 84 | 0 | 0 | 0 |
| data-runs-clean-checkpoint | 4 | 4 | 0 | 0 | 0 |
| doc-staleness-gate | 12 | 12 | 0 | 0 | 0 |

_Computed over 72.5% of this window's events (2718 of 3748 scored) — see TCK-20260915-SIDECAR-ATTRIBUTION-GAP for why the rest lack a `cost_proxy_score`._

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 188 | 20101.5 | 106.9 |
| Architecture-Verify-Recheck | 1 | 86.5 | 86.5 |
| Comprehend | 1 | 174.4 | 174.4 |
| Doc-Staleness-Gate | 1 | 0.0 | 0.0 |
| Document-Update | 193 | 17847.6 | 92.5 |
| Document-Update-Gate | 6 | 728.0 | 121.3 |
| Finalize | 287 | 12257.3 | 42.7 |
| Fix | 1 | 55.3 | 55.3 |
| Implement | 280 | 36388.3 | 130.0 |
| Investigate | 209 | 16060.4 | 76.8 |
| Link | 1 | 0.0 | 0.0 |
| Parity | 234 | 13397.6 | 57.3 |
| Parity-Gate | 4 | 0.0 | 0.0 |
| Plan | 206 | 10954.1 | 53.2 |
| Plan-Fix | 4 | 236.6 | 59.1 |
| Review | 243 | 19621.1 | 80.7 |
| Review-Recheck | 5 | 5887.0 | 1177.4 |
| Scope | 238 | 10152.9 | 42.7 |
| Security-Review | 17 | 1090.9 | 64.2 |
| Structure | 1 | 0.0 | 0.0 |
| Test | 268 | 36744.6 | 137.1 |
| Test-Cleanup-Checkpoint | 6 | 237.3 | 39.5 |
| Verify | 300 | 20314.5 | 67.7 |
| Verify-Recheck | 5 | 602.4 | 120.5 |
| Verify-Recheck2 | 1 | 235.1 | 235.1 |
| Write | 2 | 0.0 | 0.0 |
| data-runs-clean-checkpoint | 4 | 0.0 | 0.0 |
| doc-staleness-gate | 12 | 0.0 | 0.0 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| advisory-checks | 4 | 0.0 | 0.0 |
| architecture-reviewer | 407 | 41883.4 | 102.9 |
| claude | 454 | 13714.5 | 30.2 |
| cleanup-checkpoint | 4 | 0.0 | 0.0 |
| create-tickets | 1 | 174.4 | 174.4 |
| doc-updater | 179 | 16800.3 | 93.9 |
| done-checker | 248 | 20242.5 | 81.6 |
| finalizer | 156 | 11307.0 | 72.5 |
| implement-ticket | 7 | 0.0 | 0.0 |
| implement-ticket-orchestrator | 6 | 7.2 | 1.2 |
| implementer | 193 | 34906.3 | 180.9 |
| investigate:C1 | 1 | 54.2 | 54.2 |
| investigate:C2 | 1 | 115.3 | 115.3 |
| investigator | 165 | 15328.8 | 92.9 |
| link-epic | 1 | 0.0 | 0.0 |
| orchestrator | 198 | 3562.4 | 18.0 |
| parity-updater | 170 | 11686.0 | 68.7 |
| planner | 182 | 10929.3 | 60.1 |
| security-reviewer | 10 | 265.5 | 26.5 |
| self-doc-update | 1 | 0.0 | 0.0 |
| self-parity | 1 | 0.0 | 0.0 |
| self-review | 2 | 0.0 | 0.0 |
| self-test | 1 | 0.0 | 0.0 |
| self-verify | 2 | 0.0 | 0.0 |
| structure | 1 | 0.0 | 0.0 |
| test-scoper | 178 | 35865.2 | 201.5 |
| ticket-scoper | 145 | 6331.2 | 43.7 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 108 |

## Slow Runs (> 30 min)

| run_id | duration | active | idle | final_status |
|---|---|---|---|---|
| FOLDER-tickets-todos-ai-first-hardening-h1-h2-followon | 3841 min | 0 min | 3841 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M3-FAMILY-SPECIES-EPIC | 3327 min | 0 min | 3327 min | DONE |
| FOLDER-tickets-todos-ai-first-hardening-h0-governance-guardrail | 1165 min | 0 min | 1165 min | DONE |
| TCK-20260912-WORKING-LOG-APPEND-HELPER | 1086 min | 0 min | 1337 min | DONE |
| TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE | 1016 min | 0 min | 1015 min | DONE |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 977 min | 0 min | 977 min | DONE |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 828 min | 91 min | 737 min | DONE |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 760 min | 31 min | 728 min | DONE |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | 580 min | 14 min | 565 min | DONE |
| TCK-20260904-INHERITED-REPUTATION-SEED | 569 min | 1 min | 568 min | DONE |
| FOLDER-tickets-todos-semantic-entity-index | 532 min | 16 min | 516 min | DONE |
| TCK-20260824-ROLLOUT-FLAG-DECISIONS | 494 min | 19 min | 479 min | DONE |
| TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE | 470 min | 5 min | 465 min | DONE |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 462 min | 0 min | 462 min | DONE |
| TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP | 434 min | 51 min | 383 min | DONE |
| TCK-20260822-GUARD-SCAN-INDEX-RETROFIT | 400 min | 35 min | 365 min | DONE |
| TCK-20260902-PLACE-MIGRATION-RECALIBRATION | 385 min | 0 min | 385 min | DONE |
| TCK-20260821-LIVE-MAP-PERF-VALIDATION | 379 min | 108 min | 271 min | DONE |
| TCK-20260831-RACE-RELATIONS-MATRIX | 360 min | 47 min | 312 min | DONE |
| TCK-20260824-OCCUPATION-CHANGE-TRIGGER | 329 min | 60 min | 268 min | DONE |
| TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | 314 min | 75 min | 238 min | DONE |
| TCK-20260817-STATE-DESIGN-PRIORITY-ORDER | 264 min | 0 min | 396 min | DONE |
| TCK-20260825-HOTFIX-EXEC-IDENTITY-TEST-SIDECAR-STALENESS | 252 min | 0 min | 252 min | DONE |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | 248 min | 0 min | 983 min | DONE |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 235 min | 113 min | 122 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M4-BEYOND-CITY-EPIC | 204 min | 2 min | 202 min | DONE |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 202 min | 41 min | 161 min | DONE |
| TCK-20260821-WS-ENTITY-DELTA-BROADCAST | 173 min | 173 min | 0 min | DONE |
| TCK-20260821-PHASED-LOADING-STATE-MACHINE | 164 min | 124 min | 40 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M1-QUICK-WINS-EPIC | 154 min | 30 min | 124 min | DONE |
| TCK-20260831-READINESS-SPEED-FORMULA | 148 min | 44 min | 103 min | DONE |
| TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT | 147 min | 0 min | 147 min | DONE |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 147 min | 0 min | 147 min | DONE |
| FOLDER-tickets-todos-world-grammar-semantic-constraints | 144 min | 0 min | 144 min | DONE |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 143 min | 54 min | 89 min | DONE |
| TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT | 141 min | 52 min | 88 min | DONE |
| TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT | 131 min | 69 min | 62 min | DONE |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 123 min | 123 min | 0 min | DONE |
| TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE | 120 min | 120 min | 0 min | DONE |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | 119 min | 62 min | 57 min | DONE |
| TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND | 112 min | 51 min | 60 min | DONE |
| TCK-20260903-CLAN-LIFECYCLE-SUCCESSION | 111 min | 0 min | 111 min | DONE |
| TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT | 106 min | 106 min | 0 min | DONE |
| TCK-20260831-ITEM-INSTANCE-HISTORY | 103 min | 53 min | 49 min | DONE |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 103 min | 103 min | 0 min | DONE |
| TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING | 102 min | 60 min | 41 min | DONE |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | 102 min | 68 min | 33 min | DONE |
| TCK-20260823-HTTP-API-KEY-AUTH | 101 min | 60 min | 41 min | DONE |
| TCK-20260903-ECONOMIC-VACANCY-SIGNAL | 99 min | 0 min | 99 min | DONE |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 98 min | 0 min | 98 min | DONE |
| TCK-20260824-WIRE-ORPHANED-MECHANISMS | 98 min | 50 min | 47 min | DONE |
| TCK-20260831-POPULATION-COHORT-SEEDING | 97 min | 59 min | 38 min | DONE |
| TCK-20260822-SEMANTIC-ENTITY-INDEX | 94 min | 94 min | 0 min | DONE |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 93 min | 57 min | 35 min | DONE |
| TCK-20260903-INFORMATION-HUB-ACCUMULATION | 93 min | 0 min | 93 min | DONE |
| TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING | 90 min | 0 min | 90 min | DONE |
| TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL | 89 min | 53 min | 36 min | DONE |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 89 min | 0 min | 89 min | DONE |
| TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE | 89 min | 37 min | 51 min | DONE |
| TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC | 88 min | 55 min | 33 min | DONE |
| TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET | 88 min | 26 min | 62 min | DONE |
| TCK-20260902-WORLDCOMPILER-PLACE-WIRING | 88 min | 0 min | 88 min | DONE |
| TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET | 87 min | 87 min | 0 min | DONE |
| TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD | 86 min | 0 min | 338 min | DONE |
| TCK-20260902-PARITY-TEST-PATH-GAP | 86 min | 41 min | 45 min | DONE |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 85 min | 0 min | 85 min | DONE |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 83 min | 0 min | 83 min | DONE |
| TCK-20260905-CHRONICLE-FIDELITY-DRIFT | 79 min | 0 min | 79 min | DONE |
| TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD | 76 min | 76 min | 0 min | DONE |
| TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD | 75 min | 0 min | 75 min | DONE |
| TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON | 75 min | 0 min | 75 min | DONE |
| TCK-20260824-LIFE-STAGE-TRANSITIONS | 74 min | 37 min | 37 min | DONE |
| TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION | 74 min | 35 min | 39 min | DONE |
| TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP | 74 min | 0 min | 74 min | DONE |
| TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING | 71 min | 71 min | 0 min | DONE |
| TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC | 69 min | 69 min | 0 min | DONE |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 67 min | 67 min | 0 min | DONE |
| CREATE-TICKETS-AI-FIRST-HARDENING-EPICS | 67 min | 0 min | 67 min | DONE |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 66 min | 66 min | 0 min | DONE |
| TCK-20260824-ALLOCATE-AP-BRANCH-DECISION | 65 min | 65 min | 0 min | DONE |
| TCK-20260821-WORLD-RENDER-CORE | 65 min | 29 min | 35 min | DONE |
| TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR | 65 min | 65 min | 0 min | DONE |
| TCK-20260831-ROLE-MODEL-IMITATION | 65 min | 65 min | 0 min | DONE |
| TCK-20260821-REST-MAP-STATIC-STATS | 65 min | 65 min | 0 min | DONE |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 64 min | 64 min | 0 min | DONE |
| TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION | 63 min | 63 min | 0 min | DONE |
| TCK-20260826-PARITY-FACTION-CANONICAL-SCAN | 63 min | 63 min | 0 min | DONE |
| TCK-20260824-AFFECTION-CONTRACT-GATE | 63 min | 63 min | 0 min | DOD_BLOCKED |
| TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE | 62 min | 62 min | 0 min | DONE |
| TCK-20260831-TRUST-GATED-TEACHING | 60 min | 60 min | 0 min | DONE |
| TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING | 60 min | 60 min | 0 min | DONE |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 60 min | 60 min | 0 min | DONE |
| TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP | 60 min | 30 min | 30 min | DONE |
| TCK-20260904-SPECIES-CORE-SCHEMA-RENAME | 60 min | 15 min | 45 min | DONE |
| TCK-20260831-HABIT-BIAS-WIRING | 59 min | 59 min | 0 min | DONE |
| TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP | 59 min | 59 min | 0 min | DONE |
| TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY | 58 min | 58 min | 0 min | DONE |
| TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD | 58 min | 58 min | 0 min | DONE |
| TCK-20260825-LIVE-VERIFICATION-TOOLING | 58 min | 18 min | 40 min | DONE |
| TCK-20260821-VISUAL-AGENT-REVIEW | 57 min | 57 min | 0 min | DONE |
| TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING | 57 min | 57 min | 0 min | DONE |
| TCK-20260902-ASPECT-TERM-CLEANUP | 56 min | 56 min | 0 min | DONE |
| TCK-20260906-CI-FRONTEND-PATH-FILTER | 55 min | 0 min | 417 min | DONE |
| TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC | 54 min | 54 min | 0 min | DONE |
| TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT | 54 min | 0 min | 54 min | DONE |
| TCK-20260831-SPECIES-INTELLIGENCE-TIER | 53 min | 53 min | 0 min | DONE |
| TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC | 53 min | 53 min | 0 min | DONE |
| TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE | 52 min | 20 min | 32 min | DONE |
| TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC | 51 min | 51 min | 0 min | DONE |
| TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT | 51 min | 51 min | 0 min | DONE |
| TCK-20260819-SKILL-STALENESS-SOFT-WARNING | 51 min | 51 min | 0 min | DONE |
| TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC | 50 min | 50 min | 0 min | DONE |
| TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION | 50 min | 50 min | 0 min | DONE |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | 50 min | 50 min | 0 min | DONE |
| TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS | 50 min | 50 min | 0 min | DONE |
| TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP | 50 min | 0 min | 50 min | DONE |
| TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT | 49 min | 0 min | 49 min | DONE |
| TCK-20260824-TACTICAL-WOUND-SCAR-WIRING | 48 min | 48 min | 0 min | DONE |
| TCK-20260831-CAPABILITY-DRIVEN-TARGETING | 48 min | 48 min | 0 min | DONE |
| TCK-20260831-CREATURE-TERRITORY-LIFECYCLE | 48 min | 48 min | 0 min | DONE |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 48 min | 48 min | 0 min | DONE |
| TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC | 48 min | 48 min | 0 min | DONE |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | 47 min | 47 min | 0 min | DOD_BLOCKED |
| TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR | 46 min | 46 min | 0 min | DONE |
| TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION | 45 min | 45 min | 0 min | DONE |
| TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP | 45 min | 0 min | 45 min | DONE |
| TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT | 44 min | 44 min | 0 min | DONE |
| TCK-20260821-VISUAL-GRADE-SCORER | 43 min | 43 min | 0 min | DONE |
| TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES | 43 min | 43 min | 0 min | DONE |
| TCK-20260824-DEFAULT-HEIR-ASSIGNMENT | 43 min | 43 min | 0 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-LIVE-MAP-RECONNECTION-EPIC | 42 min | 42 min | 0 min | DONE |
| TCK-20260831-CLASS-TIER-BRANCHING | 42 min | 42 min | 0 min | DONE |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | 42 min | 42 min | 0 min | DONE |
| TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS | 42 min | 0 min | 419 min | DONE |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 41 min | 41 min | 0 min | DONE |
| TCK-20260821-VISUAL-QUALITY-CALIBRATION | 41 min | 41 min | 0 min | DONE |
| TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG | 41 min | 41 min | 0 min | DONE |
| TCK-20260824-WOUND-THRESHOLD-DECISION | 41 min | 41 min | 0 min | DONE |
| TCK-20260823-LIVE-TEST-API-KEY-AUTH | 40 min | 40 min | 0 min | DONE |
| TCK-20260824-RETRO-METRIC-CAVEATS | 40 min | 5 min | 35 min | DONE |
| TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING | 40 min | 40 min | 0 min | DONE |
| TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE | 40 min | 0 min | 40 min | DONE |
| TCK-20260824-WOUND-HEALING-DECISION | 39 min | 6 min | 32 min | NEEDS_HUMAN_INPUT |
| TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM | 39 min | 39 min | 0 min | DONE |
| TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION | 39 min | 3 min | 35 min | DONE |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 39 min | 39 min | 0 min | DONE |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 39 min | 0 min | 39 min | DONE |
| TCK-20260731-CODEX-EXECUTION-IDENTITY-TAG-SWEEP | 38 min | 38 min | 0 min | DONE |
| TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION | 38 min | 38 min | 0 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-WORLD-GENERATION-ORGANIC-TERRAIN-EPIC | 38 min | 38 min | 0 min | DONE |
| TCK-20260821-VISUAL-QUALITY-DOCS | 38 min | 38 min | 0 min | DONE |
| TCK-20260822-PAID-INFO-INDEX-RETROFIT | 37 min | 37 min | 0 min | DONE |
| TCK-20260821-VISUAL-SHAPE-METRIC | 37 min | 37 min | 0 min | DONE |
| TCK-20260821-VISUAL-VARIANTS-METRIC | 36 min | 36 min | 0 min | DONE |
| TCK-20260824-WOUND-HEALING-DECISION | 36 min | 4 min | 32 min | DONE |
| TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK | 36 min | 36 min | 0 min | DONE |
| TCK-20260823-CI-STEP-SUMMARY-REPORTING | 36 min | 0 min | 102 min | DONE |
| TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE | 35 min | 35 min | 0 min | DONE |
| TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION | 35 min | 35 min | 0 min | DONE |
| TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE | 35 min | 0 min | 35 min | DONE |
| TCK-20260825-METADATA-API-BACKEND-MISSING | 35 min | 0 min | 211 min | DONE |
| TCK-20260821-VISUAL-CONNECTIVITY-METRIC | 34 min | 34 min | 0 min | DONE |
| TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX | 34 min | 34 min | 0 min | DONE |
| TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP | 33 min | 33 min | 0 min | DONE |
| TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION | 33 min | 33 min | 0 min | DONE |
| TCK-20260902-HARVEST-LOOT-TEST-COVERAGE | 33 min | 33 min | 0 min | DONE |
| TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION | 32 min | 32 min | 0 min | DONE |
| TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ | 31 min | 31 min | 0 min | DONE |

_75 of the runs above spend at least half their reported duration idle (gaps ≥ 30 min between phase transitions, e.g. waiting on human review) rather than in active work — see `active`/`idle` columns; "slow" here does not mean "took a long time to actively work on."_

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Duration outliers (by tier)

| run_id | tier | duration_s | tier median | ratio | active | idle |
|---|---|---|---|---|---|---|
| FOLDER-tickets-todos-ai-first-hardening-h1-h2-followon | epic | 230499 | 360 | 640.3x | 0 min | 3841 min |
| FOLDER-tickets-todos-ai-first-hardening-h0-governance-guardrail | epic | 69900 | 360 | 194.2x | 0 min | 1165 min |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M3-FAMILY-SPECIES-EPIC | n/a | 199620 | 1142 | 174.8x | 0 min | 3327 min |
| FOLDER-tickets-todos-semantic-entity-index | epic | 31978 | 360 | 88.8x | 16 min | 516 min |
| TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE | hotfix | 28259 | 600 | 47.1x | 5 min | 465 min |
| TCK-20260912-WORKING-LOG-APPEND-HELPER | standard | 65164 | 1538.0 | 42.4x | 0 min | 1337 min |
| TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE | standard | 60960 | 1538.0 | 39.6x | 0 min | 1015 min |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | standard | 58672 | 1538.0 | 38.1x | 0 min | 977 min |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | standard | 49716 | 1538.0 | 32.3x | 91 min | 737 min |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | standard | 45628 | 1538.0 | 29.7x | 31 min | 728 min |
| TCK-20260825-HOTFIX-EXEC-IDENTITY-TEST-SIDECAR-STALENESS | hotfix | 15137 | 600 | 25.2x | 0 min | 252 min |
| FOLDER-tickets-todos-world-grammar-semantic-constraints | epic | 8645 | 360 | 24.0x | 0 min | 144 min |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | standard | 34806 | 1538.0 | 22.6x | 14 min | 565 min |
| TCK-20260904-INHERITED-REPUTATION-SEED | standard | 34172 | 1538.0 | 22.2x | 1 min | 568 min |
| TCK-20260824-ROLLOUT-FLAG-DECISIONS | standard | 29694 | 1538.0 | 19.3x | 19 min | 479 min |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | standard | 27777 | 1538.0 | 18.1x | 0 min | 462 min |
| TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP | standard | 26088 | 1538.0 | 17.0x | 51 min | 383 min |
| TCK-20260822-GUARD-SCAN-INDEX-RETROFIT | standard | 24039 | 1538.0 | 15.6x | 35 min | 365 min |
| TCK-20260902-PLACE-MIGRATION-RECALIBRATION | standard | 23100 | 1538.0 | 15.0x | 0 min | 385 min |
| TCK-20260821-LIVE-MAP-PERF-VALIDATION | standard | 22740 | 1538.0 | 14.8x | 108 min | 271 min |
| TCK-20260831-RACE-RELATIONS-MATRIX | standard | 21613 | 1538.0 | 14.1x | 47 min | 312 min |
| TCK-20260824-OCCUPATION-CHANGE-TRIGGER | standard | 19745 | 1538.0 | 12.8x | 60 min | 268 min |
| TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | standard | 18867 | 1538.0 | 12.3x | 75 min | 238 min |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M4-BEYOND-CITY-EPIC | n/a | 12280 | 1142 | 10.8x | 2 min | 202 min |
| TCK-20260817-STATE-DESIGN-PRIORITY-ORDER | standard | 15845 | 1538.0 | 10.3x | 0 min | 396 min |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | standard | 14925 | 1538.0 | 9.7x | 0 min | 983 min |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | standard | 14139 | 1538.0 | 9.2x | 113 min | 122 min |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M1-QUICK-WINS-EPIC | n/a | 9289 | 1142 | 8.1x | 30 min | 124 min |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | standard | 12161 | 1538.0 | 7.9x | 41 min | 161 min |
| TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD | hotfix | 4617 | 600 | 7.7x | 76 min | 0 min |
| TCK-20260821-WS-ENTITY-DELTA-BROADCAST | standard | 10390 | 1538.0 | 6.8x | 173 min | 0 min |
| TCK-20260821-PHASED-LOADING-STATE-MACHINE | standard | 9840 | 1538.0 | 6.4x | 124 min | 40 min |
| TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE | hotfix | 3721 | 600 | 6.2x | 62 min | 0 min |
| TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP | hotfix | 3569 | 600 | 5.9x | 59 min | 0 min |
| TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY | hotfix | 3536 | 600 | 5.9x | 58 min | 0 min |
| TCK-20260825-LIVE-VERIFICATION-TOOLING | hotfix | 3480 | 600 | 5.8x | 18 min | 40 min |
| TCK-20260831-READINESS-SPEED-FORMULA | standard | 8916 | 1538.0 | 5.8x | 44 min | 103 min |
| TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT | standard | 8844 | 1538.0 | 5.8x | 0 min | 147 min |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | standard | 8826 | 1538.0 | 5.7x | 0 min | 147 min |
| TCK-20260902-ASPECT-TERM-CLEANUP | hotfix | 3406 | 600 | 5.7x | 56 min | 0 min |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | standard | 8599 | 1538.0 | 5.6x | 54 min | 89 min |
| TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT | standard | 8478 | 1538.0 | 5.5x | 52 min | 88 min |
| TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT | hotfix | 3264 | 600 | 5.4x | 0 min | 54 min |
| TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC | hotfix | 3183 | 600 | 5.3x | 53 min | 0 min |
| TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT | standard | 7902 | 1538.0 | 5.1x | 69 min | 62 min |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | hotfix | 3027 | 600 | 5.0x | 50 min | 0 min |
| TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD | epic | 1800 | 360 | 5.0x | 0 min | 30 min |
| TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY | epic | 1800 | 360 | 5.0x | 0 min | 390 min |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | standard | 7395 | 1538.0 | 4.8x | 123 min | 0 min |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | hotfix | 2849 | 600 | 4.7x | 47 min | 0 min |
| TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE | standard | 7200 | 1538.0 | 4.7x | 120 min | 0 min |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | standard | 7192 | 1538.0 | 4.7x | 62 min | 57 min |
| TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND | standard | 6750 | 1538.0 | 4.4x | 51 min | 60 min |
| TCK-20260903-CLAN-LIFECYCLE-SUCCESSION | standard | 6672 | 1538.0 | 4.3x | 0 min | 111 min |
| TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES | hotfix | 2589 | 600 | 4.3x | 43 min | 0 min |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | hotfix | 2534 | 600 | 4.2x | 42 min | 0 min |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | hotfix | 2505 | 600 | 4.2x | 41 min | 0 min |
| TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT | standard | 6407 | 1538.0 | 4.2x | 106 min | 0 min |
| TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG | hotfix | 2471 | 600 | 4.1x | 41 min | 0 min |
| TCK-20260823-LIVE-TEST-API-KEY-AUTH | hotfix | 2459 | 600 | 4.1x | 40 min | 0 min |
| TCK-20260824-RETRO-METRIC-CAVEATS | hotfix | 2450 | 600 | 4.1x | 5 min | 35 min |
| TCK-20260831-ITEM-INSTANCE-HISTORY | standard | 6229 | 1538.0 | 4.1x | 53 min | 49 min |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | standard | 6202 | 1538.0 | 4.0x | 103 min | 0 min |
| TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING | standard | 6154 | 1538.0 | 4.0x | 60 min | 41 min |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | standard | 6121 | 1538.0 | 4.0x | 68 min | 33 min |
| TCK-20260823-HTTP-API-KEY-AUTH | standard | 6081 | 1538.0 | 4.0x | 60 min | 41 min |
| TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM | hotfix | 2352 | 600 | 3.9x | 39 min | 0 min |
| TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION | hotfix | 2351 | 600 | 3.9x | 3 min | 35 min |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | hotfix | 2351 | 600 | 3.9x | 39 min | 0 min |
| TCK-20260903-ECONOMIC-VACANCY-SIGNAL | standard | 5968 | 1538.0 | 3.9x | 0 min | 99 min |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | standard | 5920 | 1538.0 | 3.8x | 0 min | 98 min |
| TCK-20260824-WIRE-ORPHANED-MECHANISMS | standard | 5886 | 1538.0 | 3.8x | 50 min | 47 min |
| TCK-20260831-POPULATION-COHORT-SEEDING | standard | 5860 | 1538.0 | 3.8x | 59 min | 38 min |
| TCK-20260822-SEMANTIC-ENTITY-INDEX | standard | 5675 | 1538.0 | 3.7x | 94 min | 0 min |
| TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK | hotfix | 2195 | 600 | 3.7x | 36 min | 0 min |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | standard | 5614 | 1538.0 | 3.7x | 57 min | 35 min |
| TCK-20260903-INFORMATION-HUB-ACCUMULATION | standard | 5587 | 1538.0 | 3.6x | 0 min | 93 min |
| CREATE-TICKETS-AI-FIRST-HARDENING-EPICS | n/a | 4049 | 1142 | 3.5x | 0 min | 67 min |
| TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING | standard | 5400 | 1538.0 | 3.5x | 0 min | 90 min |
| TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL | standard | 5374 | 1538.0 | 3.5x | 53 min | 36 min |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | standard | 5369 | 1538.0 | 3.5x | 0 min | 89 min |
| TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE | standard | 5352 | 1538.0 | 3.5x | 37 min | 51 min |
| TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX | hotfix | 2077 | 600 | 3.5x | 34 min | 0 min |
| TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC | standard | 5320 | 1538.0 | 3.5x | 55 min | 33 min |
| TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET | standard | 5319 | 1538.0 | 3.5x | 26 min | 62 min |
| TCK-20260902-WORLDCOMPILER-PLACE-WIRING | standard | 5290 | 1538.0 | 3.4x | 0 min | 88 min |
| TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET | standard | 5256 | 1538.0 | 3.4x | 87 min | 0 min |
| TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP | hotfix | 2037 | 600 | 3.4x | 33 min | 0 min |
| TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD | standard | 5216 | 1538.0 | 3.4x | 0 min | 338 min |
| TCK-20260902-PARITY-TEST-PATH-GAP | standard | 5203 | 1538.0 | 3.4x | 41 min | 45 min |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | standard | 5105 | 1538.0 | 3.3x | 0 min | 85 min |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | standard | 5000 | 1538.0 | 3.3x | 0 min | 83 min |
| TCK-20260905-CHRONICLE-FIDELITY-DRIFT | standard | 4772 | 1538.0 | 3.1x | 0 min | 79 min |

_56 of the duration outliers above spend at least half their reported duration idle rather than in active work — see `active`/`idle` columns; a large ratio here does not mean "took unusually long to actively work on."_

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX | 1 | Scope | claude | 862.641 | 4.0 | 213.2x |
| TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE | 1 | Scope | claude | 360.141 | 4.0 | 89.0x |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | 8 | Test | test-scoper | 4614.366 | 64.8 | 71.3x |
| TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE | 1 | Scope | claude | 285.16200000000003 | 4.0 | 70.5x |
| TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD | 1 | Scope | ticket-scoper | 268.586 | 4.0 | 66.4x |
| TCK-20260825-METADATA-API-BACKEND-MISSING | 1 | Scope | claude | 238.752 | 4.0 | 59.0x |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | 9 | Architecture-Verify | architecture-reviewer | 3171.214 | 55.1 | 57.5x |
| TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS | 1 | Scope | claude | 206.951 | 4.0 | 51.1x |
| TCK-20260907-FILTERED-REPLAY-EVAL-PILOT | 1 | Scope | ticket-scoper | 206.79500000000002 | 4.0 | 51.1x |
| TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION | 1 | Scope | ticket-scoper | 165.117 | 4.0 | 40.8x |
| TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN | 1 | Scope | orchestrator | 163.589 | 4.0 | 40.4x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 6 | Review | architecture-reviewer | 2336.572 | 59.4 | 39.3x |
| TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH | 1 | Scope | ticket-scoper | 155.18200000000002 | 4.0 | 38.3x |
| TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP | 1 | Scope | orchestrator | 154.248 | 4.0 | 38.1x |
| TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE | 1 | Scope | claude | 148.718 | 4.0 | 36.7x |
| TCK-20260908-HOTFIX-OWNERSHIP-LIFECYCLE-DOC-STALE-PRESHIP-GUARD | 1 | Scope | orchestrator | 140.72 | 4.0 | 34.8x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 1 | Scope | claude | 138.034 | 4.0 | 34.1x |
| TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST | 7 | Architecture-Verify | architecture-reviewer | 1788.286 | 55.1 | 32.4x |
| TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND | 1 | Scope | ticket-scoper | 130.135 | 4.0 | 32.2x |
| TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS | 1 | Scope | claude | 127.416 | 4.0 | 31.5x |
| TCK-20260817-STATE-DESIGN-PRIORITY-ORDER | 1 | Investigate | investigator | 2067.306 | 70.7 | 29.2x |
| TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY | 6 | Architecture-Verify | claude | 1593.737 | 55.1 | 28.9x |
| TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP | 1 | Scope | orchestrator | 114.68 | 4.0 | 28.3x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 1 | Scope | ticket-scoper | 111.029 | 4.0 | 27.4x |
| TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL | 1 | Scope | claude | 107.419 | 4.0 | 26.5x |
| TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES | 8 | Test | test-scoper | 1566.065 | 64.8 | 24.2x |
| TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL | 1 | Scope | claude | 97.28800000000001 | 4.0 | 24.0x |
| TCK-20260902-ASPECT-TERM-CLEANUP | 5 | Test | test-scoper | 1547.051 | 64.8 | 23.9x |
| TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS | 1 | Scope | claude | 94.46000000000001 | 4.0 | 23.3x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 8 | Document-Update | doc-updater | 1483.53 | 63.9 | 23.2x |
| TCK-20260909-KGMCP-DOC-STATUS-SWEEP | 1 | Scope | ticket-scoper | 93.202 | 4.0 | 23.0x |
| TCK-20260831-ROLE-MODEL-IMITATION | 1 | Scope | ticket-scoper | 92.42699999999999 | 4.0 | 22.8x |
| TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC | 4 | Implement | implementer | 1539.798 | 68.0 | 22.6x |
| TCK-20260824-WOUND-PENALTY-FORMULA-WIRING | 1 | Scope | ticket-scoper | 91.483 | 4.0 | 22.6x |
| TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS | 1 | Scope | claude | 90.441 | 4.0 | 22.3x |
| TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE | 8 | Test | test-scoper | 1402.414 | 64.8 | 21.7x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 1 | Scope | ticket-scoper | 86.801 | 4.0 | 21.4x |
| TCK-20260831-POPULATION-COHORT-SEEDING | 8 | Test | test-scoper | 1343.054 | 64.8 | 20.7x |
| TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING | 1 | Scope | orchestrator | 81.003 | 4.0 | 20.0x |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | 5 | Test | test-scoper | 1262.373 | 64.8 | 19.5x |
| TCK-20260904-BASH-SECRET-SCAN-HOOK | 1 | Scope | ticket-scoper | 75.87100000000001 | 4.0 | 18.7x |
| TCK-20260822-SEMANTIC-ENTITY-INDEX | 1 | Scope | ticket-scoper | 73.905 | 4.0 | 18.3x |
| TCK-20260822-SEMANTIC-ENTITY-INDEX | 1 | Scope | ticket-scoper | 73.905 | 4.0 | 18.3x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 2 | Investigate | investigator | 1279.258 | 70.7 | 18.1x |
| TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE | 1 | Scope | claude | 72.729 | 4.0 | 18.0x |
| TCK-20260831-READINESS-SPEED-FORMULA | 1 | Scope | ticket-scoper | 71.67099999999999 | 4.0 | 17.7x |
| TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY | 1 | Scope | claude | 71.366 | 4.0 | 17.6x |
| TCK-20260904-SHADOW-REVIEWER-LOGGING | 1 | Scope | claude | 70.971 | 4.0 | 17.5x |
| TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM | 7 | Verify | done-checker | 1139.361 | 65.4 | 17.4x |
| TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT | 1 | Scope | orchestrator | 69.434 | 4.0 | 17.2x |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | 1 | Scope | ticket-scoper | 69.419 | 4.0 | 17.2x |
| TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION | 1 | Scope | ticket-scoper | 68.72800000000001 | 4.0 | 17.0x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 9 | Architecture-Verify | architecture-reviewer | 932.0260000000001 | 55.1 | 16.9x |
| TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE | 1 | Scope | ticket-scoper | 68.155 | 4.0 | 16.8x |
| TCK-20260822-PAID-INFO-INDEX-RETROFIT | 1 | Scope | ticket-scoper | 68.126 | 4.0 | 16.8x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 1 | Scope | ticket-scoper | 67.777 | 4.0 | 16.7x |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 1 | Scope | ticket-scoper | 67.288 | 4.0 | 16.6x |
| TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING | 1 | Scope | ticket-scoper | 66.769 | 4.0 | 16.5x |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | 6 | Review | architecture-reviewer | 975.631 | 59.4 | 16.4x |
| TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR | 1 | Scope | ticket-scoper | 66.42699999999999 | 4.0 | 16.4x |
| TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM | 1 | Scope | ticket-scoper | 66.247 | 4.0 | 16.4x |
| TCK-20260823-CI-STEP-SUMMARY-REPORTING | 4 | Scope | ticket-scoper | 65.654 | 4.0 | 16.2x |
| TCK-20260831-POPULATION-COHORT-SEEDING | 1 | Scope | ticket-scoper | 65.215 | 4.0 | 16.1x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 8 | Architecture-Verify | architecture-reviewer | 887.236 | 55.1 | 16.1x |
| TCK-20260824-ALLOCATE-AP-BRANCH-DECISION | 1 | Scope | ticket-scoper | 64.99600000000001 | 4.0 | 16.1x |
| TCK-20260824-LIFE-STAGE-TRANSITIONS | 1 | Scope | ticket-scoper | 64.916 | 4.0 | 16.0x |
| TCK-20260822-GUARD-SCAN-INDEX-RETROFIT | 1 | Scope | ticket-scoper | 64.702 | 4.0 | 16.0x |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 1 | Scope | ticket-scoper | 64.346 | 4.0 | 15.9x |
| TCK-20260831-SPECIES-INTELLIGENCE-TIER | 1 | Scope | ticket-scoper | 64.112 | 4.0 | 15.8x |
| TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION | 1 | Scope | ticket-scoper | 64.019 | 4.0 | 15.8x |
| TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK | 1 | Scope | ticket-scoper | 64.009 | 4.0 | 15.8x |
| TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC | 1 | Scope | ticket-scoper | 63.88 | 4.0 | 15.8x |
| TCK-20260824-WIRE-ORPHANED-MECHANISMS | 1 | Scope | ticket-scoper | 63.88 | 4.0 | 15.8x |
| TCK-20260824-DEFAULT-HEIR-ASSIGNMENT | 1 | Scope | ticket-scoper | 63.813 | 4.0 | 15.8x |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 1 | Scope | ticket-scoper | 63.44 | 4.0 | 15.7x |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 5 | Test | test-scoper | 1009.152 | 64.8 | 15.6x |
| TCK-20260831-RACE-RELATIONS-MATRIX | 1 | Scope | ticket-scoper | 62.967 | 4.0 | 15.6x |
| TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING | 1 | Scope | ticket-scoper | 62.809 | 4.0 | 15.5x |
| TCK-20260831-HABIT-BIAS-WIRING | 1 | Scope | ticket-scoper | 62.733000000000004 | 4.0 | 15.5x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 10 | Implement | implementer | 1054.0149999999999 | 68.0 | 15.5x |
| TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC | 1 | Scope | ticket-scoper | 62.071 | 4.0 | 15.3x |
| TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT | 1 | Scope | ticket-scoper | 61.903999999999996 | 4.0 | 15.3x |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 1 | Scope | ticket-scoper | 61.848 | 4.0 | 15.3x |
| TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ | 1 | Scope | ticket-scoper | 61.733000000000004 | 4.0 | 15.3x |
| TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA | 1 | Scope | ticket-scoper | 61.293 | 4.0 | 15.1x |
| TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE | 1 | Scope | ticket-scoper | 60.974000000000004 | 4.0 | 15.1x |
| TCK-20260824-TACTICAL-WOUND-SCAR-WIRING | 1 | Scope | ticket-scoper | 60.567 | 4.0 | 15.0x |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | 1 | Scope | ticket-scoper | 59.97 | 4.0 | 14.8x |
| TCK-20260831-METAMORPHIC-LAB-PILOT | 1 | Scope | ticket-scoper | 59.757 | 4.0 | 14.8x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 1 | Scope | ticket-scoper | 59.641 | 4.0 | 14.7x |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 1 | Scope | ticket-scoper | 59.612 | 4.0 | 14.7x |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 1 | Scope | ticket-scoper | 59.516999999999996 | 4.0 | 14.7x |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | 1 | Scope | ticket-scoper | 59.466 | 4.0 | 14.7x |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 1 | Scope | ticket-scoper | 59.328 | 4.0 | 14.7x |
| TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS | 1 | Scope | ticket-scoper | 59.209 | 4.0 | 14.6x |
| TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION | 1 | Scope | ticket-scoper | 59.035 | 4.0 | 14.6x |
| TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION | 1 | Scope | ticket-scoper | 58.991 | 4.0 | 14.6x |
| TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE | 1 | Scope | ticket-scoper | 58.938 | 4.0 | 14.6x |
| TCK-20260824-AFFECTION-CONTRACT-GATE | 1 | Scope | ticket-scoper | 58.87 | 4.0 | 14.5x |
| TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS | 1 | Scope | ticket-scoper | 58.702 | 4.0 | 14.5x |
| TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | 1 | Scope | ticket-scoper | 58.652 | 4.0 | 14.5x |
| TCK-20260824-WOUND-THRESHOLD-DECISION | 1 | Scope | ticket-scoper | 58.606 | 4.0 | 14.5x |
| TCK-20260831-TRUST-GATED-TEACHING | 1 | Scope | ticket-scoper | 58.539 | 4.0 | 14.5x |
| TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES | 1 | Scope | ticket-scoper | 58.504 | 4.0 | 14.5x |
| TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC | 1 | Scope | ticket-scoper | 58.177 | 4.0 | 14.4x |
| TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC | 1 | Scope | ticket-scoper | 58.123 | 4.0 | 14.4x |
| TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC | 1 | Scope | ticket-scoper | 57.856 | 4.0 | 14.3x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 1 | Scope | ticket-scoper | 57.819 | 4.0 | 14.3x |
| TCK-20260831-CAPABILITY-DRIVEN-TARGETING | 1 | Scope | ticket-scoper | 57.725 | 4.0 | 14.3x |
| TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION | 1 | Scope | ticket-scoper | 57.514 | 4.0 | 14.2x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 1 | Scope | orchestrator | 57.432 | 4.0 | 14.2x |
| TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING | 1 | Scope | ticket-scoper | 57.425 | 4.0 | 14.2x |
| TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH | 1 | Scope | ticket-scoper | 57.251 | 4.0 | 14.1x |
| TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT | 9 | Parity | parity-updater | 860.895 | 61.2 | 14.1x |
| TCK-20260824-ROUTE-KIND-COUNT-FIX | 1 | Scope | ticket-scoper | 56.828 | 4.0 | 14.0x |
| TCK-20260831-CLAN-STATE-SCHEMA | 1 | Scope | ticket-scoper | 56.738 | 4.0 | 14.0x |
| TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED | 1 | Scope | ticket-scoper | 56.727000000000004 | 4.0 | 14.0x |
| TCK-20260824-WOUND-HEALING-DECISION | 1 | Scope | ticket-scoper | 56.519 | 4.0 | 14.0x |
| TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION | 1 | Scope | ticket-scoper | 56.405 | 4.0 | 13.9x |
| TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC | 4 | Test | test-scoper | 899.635 | 64.8 | 13.9x |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | 6 | Implement | implementer | 944.649 | 68.0 | 13.9x |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 5 | Test | test-scoper | 897.868 | 64.8 | 13.9x |
| TCK-20260830-HOTFIX-WORLD-EMERGENCE-VESTIGIAL-GATE-CLEANUP | 1 | Scope | ticket-scoper | 55.926 | 4.0 | 13.8x |
| TCK-20260831-ITEM-INSTANCE-HISTORY | 1 | Scope | ticket-scoper | 55.875 | 4.0 | 13.8x |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 10 | Test | test-scoper | 890.664 | 64.8 | 13.8x |
| TCK-20260824-OCCUPATION-CHANGE-TRIGGER | 1 | Scope | ticket-scoper | 55.655 | 4.0 | 13.8x |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | 1 | Scope | ticket-scoper | 55.571 | 4.0 | 13.7x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 1 | Scope | ticket-scoper | 55.074 | 4.0 | 13.6x |
| TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH | 1 | Scope | ticket-scoper | 55.052 | 4.0 | 13.6x |
| TCK-20260831-CREATURE-TERRITORY-LIFECYCLE | 1 | Scope | ticket-scoper | 55.022999999999996 | 4.0 | 13.6x |
| TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE | 1 | Scope | ticket-scoper | 55.012 | 4.0 | 13.6x |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 1 | Scope | ticket-scoper | 54.975 | 4.0 | 13.6x |
| TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE | 2 | Scope | ticket-scoper | 54.968 | 4.0 | 13.6x |
| TCK-20260823-LIVE-TEST-API-KEY-AUTH | 2 | Scope | ticket-scoper | 54.816 | 4.0 | 13.5x |
| TCK-20260831-CLASS-TIER-BRANCHING | 1 | Scope | ticket-scoper | 54.792 | 4.0 | 13.5x |
| TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH | 1 | Scope | ticket-scoper | 53.926 | 4.0 | 13.3x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 5 | Implement | implementer | 857.049 | 68.0 | 12.6x |
| TCK-20260831-READINESS-SPEED-FORMULA | 6 | Review-Recheck | architecture-reviewer | 4738.2 | 379.8 | 12.5x |
| TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL | 5 | Implement | claude | 845.559 | 68.0 | 12.4x |
| TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION | 5 | Implement | implementer | 840.549 | 68.0 | 12.4x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 5 | Implement | implementer | 821.265 | 68.0 | 12.1x |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 8 | Test | test-scoper | 773.48 | 64.8 | 11.9x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 11 | Verify | done-checker | 777.943 | 65.4 | 11.9x |
| TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE | 5 | Implement | implementer | 763.065 | 68.0 | 11.2x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 9 | Document-Update | orchestrator | 704.941 | 63.9 | 11.0x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 9 | Test | test-scoper | 703.523 | 64.8 | 10.9x |
| TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT | 3 | Document-Update | doc-updater | 688.707 | 63.9 | 10.8x |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | 9 | Test | test-scoper | 690.6030000000001 | 64.8 | 10.7x |
| TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST | 1 | Scope | ticket-scoper | 42.694 | 4.0 | 10.5x |
| TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT | 1 | Scope | ticket-scoper | 42.152 | 4.0 | 10.4x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 7 | Architecture-Verify | claude | 566.404 | 55.1 | 10.3x |
| TCK-20260824-ALLOCATE-AP-BRANCH-DECISION | 9 | Test | test-scoper | 662.3530000000001 | 64.8 | 10.2x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 8 | Architecture-Verify | architecture-reviewer | 560.8199999999999 | 55.1 | 10.2x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 7 | Document-Update | doc-updater | 649.592 | 63.9 | 10.2x |
| TCK-20260826-PARITY-FACTION-CANONICAL-SCAN | 8 | Test | test-scoper | 643.742 | 64.8 | 9.9x |
| TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE | 9 | Parity | claude | 589.681 | 61.2 | 9.6x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 8 | Architecture-Verify | architecture-reviewer | 530.2429999999999 | 55.1 | 9.6x |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 1 | Investigate | investigator | 658.818 | 70.7 | 9.3x |
| TCK-20260821-VISUAL-CONNECTIVITY-METRIC | 4 | Implement | implementer | 625.849 | 68.0 | 9.2x |
| TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND | 3 | Implement | implementer | 607.7080000000001 | 68.0 | 8.9x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 9 | Test | test-scoper | 553.405 | 64.8 | 8.5x |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | 6 | Parity | parity-updater | 512.8969999999999 | 61.2 | 8.4x |
| TCK-20260831-POPULATION-COHORT-SEEDING | 11 | Parity | parity-updater | 504.449 | 61.2 | 8.2x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 4 | Review | architecture-reviewer | 489.023 | 59.4 | 8.2x |
| TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | 4 | Implement | implementer | 550.8340000000001 | 68.0 | 8.1x |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 8 | Test | test-scoper | 489.211 | 64.8 | 7.6x |
| TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | 9 | Verify | done-checker | 486.354 | 65.4 | 7.4x |
| TCK-20260824-WIRE-ORPHANED-MECHANISMS | 6 | Implement | implementer | 505.486 | 68.0 | 7.4x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 6 | Implement | implementer | 504.101 | 68.0 | 7.4x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 6 | Implement | implementer | 500.89 | 68.0 | 7.4x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 6 | Implement | implementer | 495.392 | 68.0 | 7.3x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 9 | Document-Update-Gate | orchestrator | 466.647 | 64.2 | 7.3x |
| TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK | 2 | Test | test-scoper | 459.51300000000003 | 64.8 | 7.1x |
| TCK-20260822-SCAN-POLICY-DOC-FIX | 8 | Test | test-scoper | 440.457 | 64.8 | 6.8x |
| TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL | 6 | Implement | implementer | 461.325 | 68.0 | 6.8x |
| TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD | 6 | Implement | implementer | 457.979 | 68.0 | 6.7x |
| TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE | 8 | Test | test-scoper | 426.543 | 64.8 | 6.6x |
| TCK-20260831-ROLE-MODEL-IMITATION | 5 | Implement | implementer | 444.687 | 68.0 | 6.5x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 4 | Review | architecture-reviewer | 382.003 | 59.4 | 6.4x |
| TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ | 2 | Investigate | investigator | 449.495 | 70.7 | 6.4x |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 2 | Implement | implementer | 431.76800000000003 | 68.0 | 6.3x |
| TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK | 1 | Implement | implementer | 430.128 | 68.0 | 6.3x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 10 | Test | test-scoper | 407.92400000000004 | 64.8 | 6.3x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 7 | Implement | implementer | 428.213 | 68.0 | 6.3x |
| TCK-20260824-RETRO-METRIC-CAVEATS | 9 | Parity | parity-updater | 378.788 | 61.2 | 6.2x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 7 | Architecture-Verify | architecture-reviewer | 338.946 | 55.1 | 6.1x |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 5 | Review | architecture-reviewer | 361.331 | 59.4 | 6.1x |
| TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP | 3 | Implement | implementer | 412.552 | 68.0 | 6.1x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 5 | Implement | implementer | 410.161 | 68.0 | 6.0x |
| TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE | 5 | Document-Update | doc-updater | 381.0 | 63.9 | 6.0x |
| TCK-20260831-HABIT-BIAS-WIRING | 10 | Test | test-scoper | 385.283 | 64.8 | 5.9x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 3 | Plan | planner | 372.27500000000003 | 62.9 | 5.9x |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 12 | Verify | done-checker | 384.844 | 65.4 | 5.9x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 3 | Plan | planner | 369.498 | 62.9 | 5.9x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 6 | Document-Update | doc-updater | 371.293 | 63.9 | 5.8x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 4 | Review | architecture-reviewer | 343.091 | 59.4 | 5.8x |
| TCK-20260904-SHADOW-REVIEWER-LOGGING | 5 | Verify | claude | 371.81 | 65.4 | 5.7x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 8 | Test | test-scoper | 367.235 | 64.8 | 5.7x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 4 | Review | architecture-reviewer | 334.027 | 59.4 | 5.6x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 6 | Document-Update | doc-updater | 356.392 | 63.9 | 5.6x |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 6 | Implement | implementer | 371.541 | 68.0 | 5.5x |
| TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP | 4 | Review | architecture-reviewer | 315.929 | 59.4 | 5.3x |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 6 | Document-Update | doc-updater | 338.238 | 63.9 | 5.3x |
| TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX | 4 | Review | architecture-reviewer | 313.03000000000003 | 59.4 | 5.3x |
| TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE | 2 | Investigate | investigator | 369.344 | 70.7 | 5.2x |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 7 | Implement | implementer | 350.039 | 68.0 | 5.1x |
| TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | 5 | Implement | implementer | 349.419 | 68.0 | 5.1x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 11 | Parity | parity-updater | 313.924 | 61.2 | 5.1x |
| TCK-20260823-HTTP-API-KEY-AUTH | 5 | Implement | implementer | 349.009 | 68.0 | 5.1x |
| TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR | 5 | Implement | implementer | 339.855 | 68.0 | 5.0x |
| TCK-20260823-CI-STEP-SUMMARY-REPORTING | 11 | Test | test-scoper | 322.669 | 64.8 | 5.0x |
| TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION | 5 | Implement | implementer | 333.476 | 68.0 | 4.9x |
| TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION | 5 | Document-Update | doc-updater | 304.637 | 63.9 | 4.8x |
| TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION | 5 | Document-Update | doc-updater | 303.841 | 63.9 | 4.8x |
| TCK-20260907-FILTERED-REPLAY-EVAL-PILOT | 6 | Implement | implementer | 320.658 | 68.0 | 4.7x |
| TCK-20260831-CAPABILITY-DRIVEN-TARGETING | 8 | Test | test-scoper | 304.187 | 64.8 | 4.7x |
| TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST | 5 | Implement | implementer | 317.60400000000004 | 68.0 | 4.7x |
| TCK-20260831-READINESS-SPEED-FORMULA | 9 | Architecture-Verify | architecture-reviewer | 247.949 | 55.1 | 4.5x |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 6 | Implement | implementer | 305.28200000000004 | 68.0 | 4.5x |
| TCK-20260824-RETRO-METRIC-CAVEATS | 5 | Implement | implementer | 302.65200000000004 | 68.0 | 4.4x |
| TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD | 7 | Implement | implementer | 302.369 | 68.0 | 4.4x |
| TCK-20260831-CAPABILITY-DRIVEN-TARGETING | 5 | Implement | implementer | 298.219 | 68.0 | 4.4x |
| TCK-20260831-METAMORPHIC-LAB-PILOT | 5 | Implement | implementer | 293.745 | 68.0 | 4.3x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 8 | Architecture-Verify | architecture-reviewer | 237.89600000000002 | 55.1 | 4.3x |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | 8 | Test | test-scoper | 279.326 | 64.8 | 4.3x |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 5 | Implement | implementer | 292.608 | 68.0 | 4.3x |
| TCK-20260824-WIRE-ORPHANED-MECHANISMS | 9 | Test | test-scoper | 278.111 | 64.8 | 4.3x |
| TCK-20260821-WORLD-RENDER-CORE | 4 | Implement | implementer | 290.661 | 68.0 | 4.3x |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | 8 | Verify | done-checker | 279.326 | 65.4 | 4.3x |
| TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET | 8 | Implement | implementer | 288.981 | 68.0 | 4.2x |
| TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX | 5 | Implement | claude | 286.221 | 68.0 | 4.2x |
| TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT | 5 | Implement | implementer | 285.171 | 68.0 | 4.2x |
| TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING | 4 | Implement | implementer | 279.211 | 68.0 | 4.1x |
| TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING | 7 | Implement | implementer | 274.375 | 68.0 | 4.0x |
| TCK-20260902-HOTFIX-INFRA-324-STALE-LINE-CITATION | 1 | Scope | orchestrator | 16.224 | 4.0 | 4.0x |
| TCK-20260824-AFFECTION-CONTRACT-GATE | 5 | Document-Update | doc-updater | 253.687 | 63.9 | 4.0x |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | 15 | Verify | done-checker | 259.157 | 65.4 | 4.0x |
| TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX | 10 | Verify | claude | 259.081 | 65.4 | 4.0x |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 6 | Verify | done-checker | 256.095 | 65.4 | 3.9x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 10 | Test-Cleanup-Checkpoint | orchestrator | 102.00200000000001 | 26.4 | 3.9x |
| TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL | 4 | Review | claude | 229.423 | 59.4 | 3.9x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 4 | Review | architecture-reviewer | 228.594 | 59.4 | 3.8x |
| TCK-20260831-ITEM-INSTANCE-HISTORY | 9 | Architecture-Verify | architecture-reviewer | 211.915 | 55.1 | 3.8x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 4 | Review | claude | 228.336 | 59.4 | 3.8x |
| TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS | 1 | Implement | implementer | 260.461 | 68.0 | 3.8x |
| TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE | 5 | Document-Update | doc-updater | 241.711 | 63.9 | 3.8x |
| TCK-20260823-LIVE-TEST-API-KEY-AUTH | 9 | Test | test-scoper | 242.702 | 64.8 | 3.7x |
| TCK-20260905-FAME-DERIVER-LEGEND-FACT | 8 | Test | claude | 242.673 | 64.8 | 3.7x |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 4 | Review | architecture-reviewer | 220.77100000000002 | 59.4 | 3.7x |
| TCK-20260831-POPULATION-COHORT-SEEDING | 5 | Implement | implementer | 251.596 | 68.0 | 3.7x |
| TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC | 8 | Test | test-scoper | 236.237 | 64.8 | 3.6x |
| TCK-20260824-ALLOCATE-AP-BRANCH-DECISION | 5 | Implement | implementer | 245.76500000000001 | 68.0 | 3.6x |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | 7 | Implement | implementer | 244.066 | 68.0 | 3.6x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 2 | Investigate | investigator | 251.595 | 70.7 | 3.6x |
| TCK-20260824-OCCUPATION-CHANGE-TRIGGER | 5 | Document-Update | doc-updater | 225.427 | 63.9 | 3.5x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 4 | Review | architecture-reviewer | 209.253 | 59.4 | 3.5x |
| TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA | 5 | Implement | implementer | 239.318 | 68.0 | 3.5x |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 5 | Document-Update | doc-updater | 224.764 | 63.9 | 3.5x |
| TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT | 2 | Implement | implementer | 238.476 | 68.0 | 3.5x |
| TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE | 1 | Scope | claude | 14.092 | 4.0 | 3.5x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 7 | Architecture-Verify | architecture-reviewer | 190.28900000000002 | 55.1 | 3.5x |
| TCK-20260831-HABIT-BIAS-WIRING | 7 | Implement | implementer | 232.91400000000002 | 68.0 | 3.4x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 3 | Plan | planner | 215.294 | 62.9 | 3.4x |
| TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC | 7 | Implement | implementer | 232.82 | 68.0 | 3.4x |
| TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING | 5 | Document-Update | doc-updater | 217.873 | 63.9 | 3.4x |
| TCK-20260902-CLASSHALL-DEAD-CODE | 2 | Implement | implementer | 230.746 | 68.0 | 3.4x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 5 | Review | architecture-reviewer | 201.013 | 59.4 | 3.4x |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 9 | Test | test-scoper | 217.81900000000002 | 64.8 | 3.4x |
| TCK-20260821-VISUAL-AGENT-REVIEW | 6 | Implement | implementer | 228.186 | 68.0 | 3.4x |
| TCK-20260912-WORKING-LOG-APPEND-HELPER | 8 | Implement | implementer | 224.601 | 68.0 | 3.3x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 10 | Verify | done-checker | 212.822 | 65.4 | 3.3x |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 10 | Verify | done-checker | 211.204 | 65.4 | 3.2x |
| TCK-20260823-CI-STEP-SUMMARY-REPORTING | 8 | Document-Update | doc-updater | 206.434 | 63.9 | 3.2x |
| TCK-20260831-TRUST-GATED-TEACHING | 5 | Implement | implementer | 218.484 | 68.0 | 3.2x |
| TCK-20260824-WOUND-HEALING-DECISION | 5 | Implement | implementer | 218.198 | 68.0 | 3.2x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 11 | Verify | done-checker | 209.279 | 65.4 | 3.2x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 11 | Test | test-scoper | 206.873 | 64.8 | 3.2x |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 6 | Implement | implementer | 215.981 | 68.0 | 3.2x |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | 5 | Implement | implementer | 215.929 | 68.0 | 3.2x |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 7 | Architecture-Verify | architecture-reviewer | 174.132 | 55.1 | 3.2x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 6 | Document-Update | doc-updater | 201.603 | 63.9 | 3.2x |
| TCK-20260831-POPULATION-COHORT-SEEDING | 12 | Verify | done-checker | 205.887 | 65.4 | 3.1x |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 5 | Review | planner | 186.527 | 59.4 | 3.1x |
| TCK-20260821-WS-ENTITY-DELTA-BROADCAST | 5 | Implement | implementer | 212.81400000000002 | 68.0 | 3.1x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 10 | Test-Cleanup-Checkpoint | orchestrator | 82.502 | 26.4 | 3.1x |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 5 | Implement | implementer | 212.099 | 68.0 | 3.1x |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 8 | Test | test-scoper | 200.573 | 64.8 | 3.1x |
| TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS | 8 | Test | test-scoper | 198.862 | 64.8 | 3.1x |
| TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE | 2 | Investigate | investigator | 217.08100000000002 | 70.7 | 3.1x |
| TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP | 5 | Document-Update | doc-updater | 195.911 | 63.9 | 3.1x |
| TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT | 5 | Implement | implementer | 208.239 | 68.0 | 3.1x |
| TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED | 4 | Test | test-scoper | 197.766 | 64.8 | 3.1x |
| TCK-20260831-CREATURE-TERRITORY-LIFECYCLE | 8 | Test | test-scoper | 195.767 | 64.8 | 3.0x |
| TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | 8 | Test | test-scoper | 195.744 | 64.8 | 3.0x |

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
| Retrieval event count | 35 | 0 |
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

**Total:** 1661

### Raw Investigation (Read) Calls

**Total:** 12370
**Read-to-search ratio:** 7.4473

## Tool Safety Audit

### Search-Before-Grep Compliance (Investigate Phase)

_Only the orchestrating run's own direct tools.jsonl rows are visible to this detector — a dispatched sub-agent's (e.g. `investigator`) own search/grep calls are not attributed back to this pair, so a 'non-compliant' pair may reflect an orchestrator-level incidental call rather than the real investigation's own behavior. The true compliance rate for delegated investigation work is unknown and plausibly higher than the rate below._

**Compliance rate:** 77.9% (109/140 Investigate-phase calls)

### Parity Ledger Write-Safety

**`docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build` call:** 15
**Unsafe `parity_index.py build` invocations (real repo path):** 95

### Read-Count Correlation (Search-Before-Grep Compliance)

| Group | Pairs | Median Read count | Avg Read count |
|---|---|---|---|
| Compliant | 109 | 14.0 | 13.5 |
| Non-compliant | 31 | 9.0 | 15.3 |

## Parity Index Read-Path Usage

**`entry`/`impact`/`health` call count:** 4/54682 Bash rows scanned

_Counts tools.jsonl rows where tool == "Bash" and input_summary matches parity_index.py followed immediately by entry, impact, or health (path-anchored, so a filename mention alone — e.g. test_parity_index.py, --help, `git log -- ... parity_index.py`, `sed -n '1,60p' tools/parity_index.py` — never counts). bash_rows_scanned is the total Bash-tool row population this detector ran against (the section's own 'N' denominator). Confirmed 0 real call sites as of TCK-20260731-PARITY-READPATH-GATE's Gate A review (reviewed GO, not yet wired into any real workflow call site) — this is the expected, correct value until a future ticket adds a real entry/impact/health call site, not a bug._

## Skill Usage

### Per-Skill Invocation Counts (This Period)

| Skill | Invocations |
|---|---|
| agent-monitoring-retro | 4 |
| artifact-design | 3 |
| claude-api | 2 |
| combat-mechanics | 1 |
| create-tickets | 5 |
| graphify | 13 |
| implement-epic | 2 |
| implement-ticket | 10 |
| run | 1 |
| workflow-authoring | 5 |

**Total:** 46

_Derived from tools.jsonl's literal `tool` field, filtered to `tool == 'Skill'`, with the skill name extracted from `input_summary` via regex (r\"'skill':\s*'([^']*)'\") — never json.loads(), since input_summary is a Python dict-repr string, not JSON. Records where the regex finds no match are counted under `unparseable`, never silently dropped. `unattributed` covers Skill invocations with no run_id (interactive, outside any workflow run). Distinct from generate_retro.py's tag_breakdown_skill aggregate — this is a raw per-skill invocation count, not a tag-driven gate-hit count._

### Zero-Invocation Flags (All-Time, 14-Day Grace Period)

**Flagged (confirmed age past grace period):** api-design-principles, architecture, backend-testing, observability, progression-entities, simq-dev, systems-economy
**Flagged (unknown age, no `date_added`):** debugging-strategies, doc-coauthoring, frontend-design, prompt-builder, python-performance-optimization, python-testing-patterns, test-driven-development

_All-time (never period-scoped) cross-reference of the real .claude/skills/*/SKILL.md catalog against build_skill_usage_section(tools)'s per_skill counts. A skill with any nonzero invocation count is never flagged, regardless of age. Of the remaining zero-invocation skills: `flagged_stale` requires a real, parseable `date_added` older than the 14-day grace period — a confirmed-age signal. `flagged_unknown_age` covers skills with no (or unparseable) `date_added` and zero invocations — an honest, lower-certainty signal, not proof of staleness, since no authorship date can be established. This fail-open policy on missing date_added is deliberate: it is what makes backend-testing's real pre-TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED state (no date_added field at all) correctly flaggable, per TCK-20260810-SKILL-USAGE-RETRO-TRACKING's AC2._

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

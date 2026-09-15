# Agent Monitoring Retro — Last 14 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 249 |
| Completed (DONE) | 233 (93%) |
| Gate failures | 15 |
| Avg duration | 169 min |
| Avg agents per run | 7.3 |
| Total agent calls | 1861 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| BLOCKED | 11 | 4% |
| NEEDS_CHANGES | 3 | 1% |
| NEEDS_HUMAN_INPUT | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 3 |
| governance_conflict | 1 |
| scope_larger_than_anticipated | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 1 | 100% | 0 |
| architecture | 45 | 91% | 4 |
| cognition | 24 | 79% | 5 |
| combat | 7 | 85% | 1 |
| content | 36 | 91% | 2 |
| core | 2 | 100% | 0 |
| economy | 6 | 100% | 0 |
| engine | 5 | 100% | 0 |
| faction | 5 | 100% | 0 |
| feature-flags | 2 | 100% | 0 |
| governance | 10 | 100% | 0 |
| grand-strategy | 1 | 100% | 0 |
| hud | 1 | 100% | 0 |
| information | 5 | 80% | 1 |
| lifecycle | 14 | 100% | 0 |
| mcp | 9 | 100% | 0 |
| observability | 9 | 100% | 0 |
| progression | 1 | 100% | 0 |
| rendering | 1 | 100% | 0 |
| self-model | 6 | 50% | 3 |
| simulation-quality | 30 | 90% | 3 |
| social | 21 | 100% | 0 |
| strategy | 13 | 100% | 0 |
| temporal | 1 | 100% | 0 |
| testing | 31 | 93% | 2 |
| world | 27 | 92% | 2 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| api-design | 2 | N/A — no gate implemented |
| debugging | 2 | N/A — no gate implemented |
| performance | 9 | N/A — no gate implemented |
| security | 3 | 2 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 9 | 1 | 8 | 100% |
| hotfix | 54 | 0 | 54 | 100% |
| n/a | 7 | 0 | 7 | 100% |
| standard | 179 | 0 | 164 | 91% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| architecture-reviewer | 139 | 105 | 10 | 12 | 12 |
| claude | 970 | 841 | 1 | 13 | 115 |
| concern-investigator | 1 | 1 | 0 | 0 | 0 |
| context-packet-wrapper | 1 | 1 | 0 | 0 | 0 |
| create-tickets | 6 | 6 | 0 | 0 | 0 |
| doc-updater | 59 | 59 | 0 | 0 | 0 |
| done-checker | 76 | 60 | 7 | 9 | 0 |
| finalizer | 47 | 47 | 0 | 0 | 0 |
| implement-ticket | 12 | 12 | 0 | 0 | 0 |
| implementer | 63 | 63 | 0 | 0 | 0 |
| investigate:C1 | 4 | 4 | 0 | 0 | 0 |
| investigate:C10 | 1 | 1 | 0 | 0 | 0 |
| investigate:C11 | 1 | 1 | 0 | 0 | 0 |
| investigate:C12 | 1 | 1 | 0 | 0 | 0 |
| investigate:C13 | 1 | 1 | 0 | 0 | 0 |
| investigate:C14 | 1 | 1 | 0 | 0 | 0 |
| investigate:C15 | 1 | 1 | 0 | 0 | 0 |
| investigate:C2 | 4 | 4 | 0 | 0 | 0 |
| investigate:C3 | 3 | 3 | 0 | 0 | 0 |
| investigate:C4 | 2 | 2 | 0 | 0 | 0 |
| investigate:C5 | 1 | 0 | 0 | 0 | 1 |
| investigate:C6 | 1 | 1 | 0 | 0 | 0 |
| investigate:C7 | 1 | 1 | 0 | 0 | 0 |
| investigate:C8 | 1 | 0 | 0 | 1 | 0 |
| investigate:C9 | 1 | 1 | 0 | 0 | 0 |
| investigate:D1 | 1 | 1 | 0 | 0 | 0 |
| investigate:D2 | 1 | 1 | 0 | 0 | 0 |
| investigate:D3 | 1 | 1 | 0 | 0 | 0 |
| investigator | 59 | 49 | 0 | 0 | 10 |
| link-epic | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 142 | 128 | 5 | 0 | 9 |
| parity-updater | 51 | 43 | 0 | 0 | 8 |
| planner | 68 | 58 | 0 | 0 | 10 |
| security-reviewer | 5 | 2 | 0 | 0 | 3 |
| structure | 6 | 6 | 0 | 0 | 0 |
| test-scoper | 60 | 55 | 5 | 0 | 0 |
| ticket-scoper | 66 | 66 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 69 | 63 | 0 | 0 | 6 |
| Comprehend | 7 | 7 | 0 | 0 | 0 |
| Document-Update | 75 | 74 | 0 | 0 | 1 |
| Document-Update-Gate | 6 | 6 | 0 | 0 | 0 |
| Finalize | 232 | 227 | 0 | 3 | 2 |
| Implement | 220 | 212 | 0 | 1 | 7 |
| Investigate | 138 | 124 | 1 | 2 | 11 |
| Link | 3 | 3 | 0 | 0 | 0 |
| Parity | 197 | 86 | 0 | 1 | 110 |
| Parity-Gate | 4 | 4 | 0 | 0 | 0 |
| Plan | 99 | 88 | 0 | 1 | 10 |
| Plan-Fix | 2 | 2 | 0 | 0 | 0 |
| Retrieval | 1 | 1 | 0 | 0 | 0 |
| Review | 96 | 68 | 10 | 12 | 6 |
| Review-Recheck | 3 | 3 | 0 | 0 | 0 |
| Scope | 205 | 205 | 0 | 0 | 0 |
| Security-Review | 12 | 2 | 0 | 0 | 10 |
| Structure | 7 | 7 | 0 | 0 | 0 |
| Test | 212 | 201 | 5 | 1 | 5 |
| Test-Cleanup-Checkpoint | 6 | 6 | 0 | 0 | 0 |
| Verify | 237 | 212 | 12 | 13 | 0 |
| Verify-Recheck | 3 | 2 | 0 | 1 | 0 |
| Verify-Recheck2 | 1 | 1 | 0 | 0 | 0 |
| Write | 26 | 26 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 62 | 9743.8 | 157.2 |
| Comprehend | 1 | 174.4 | 174.4 |
| Document-Update | 65 | 7372.8 | 113.4 |
| Document-Update-Gate | 6 | 728.0 | 121.3 |
| Finalize | 113 | 3520.4 | 31.2 |
| Implement | 106 | 13638.7 | 128.7 |
| Investigate | 81 | 4787.4 | 59.1 |
| Link | 1 | 0.0 | 0.0 |
| Parity | 90 | 5088.2 | 56.5 |
| Parity-Gate | 4 | 0.0 | 0.0 |
| Plan | 78 | 3996.4 | 51.2 |
| Plan-Fix | 2 | 122.5 | 61.3 |
| Review | 86 | 9037.1 | 105.1 |
| Review-Recheck | 3 | 4885.0 | 1628.3 |
| Scope | 97 | 5621.4 | 58.0 |
| Security-Review | 12 | 954.8 | 79.6 |
| Structure | 1 | 0.0 | 0.0 |
| Test | 100 | 12173.0 | 121.7 |
| Test-Cleanup-Checkpoint | 6 | 237.3 | 39.5 |
| Verify | 115 | 5351.8 | 46.5 |
| Verify-Recheck | 3 | 280.6 | 93.5 |
| Verify-Recheck2 | 1 | 235.1 | 235.1 |
| Write | 2 | 0.0 | 0.0 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 124 | 19856.9 | 160.1 |
| claude | 291 | 13230.6 | 45.5 |
| create-tickets | 1 | 174.4 | 174.4 |
| doc-updater | 53 | 6325.6 | 119.4 |
| done-checker | 66 | 4958.0 | 75.1 |
| finalizer | 47 | 3056.5 | 65.0 |
| implement-ticket | 7 | 0.0 | 0.0 |
| implementer | 57 | 12061.2 | 211.6 |
| investigate:C1 | 1 | 54.2 | 54.2 |
| investigate:C2 | 1 | 115.3 | 115.3 |
| investigator | 53 | 4060.5 | 76.6 |
| link-epic | 1 | 0.0 | 0.0 |
| orchestrator | 125 | 3428.5 | 27.4 |
| parity-updater | 45 | 3524.6 | 78.3 |
| planner | 60 | 3864.7 | 64.4 |
| security-reviewer | 5 | 129.4 | 25.9 |
| structure | 1 | 0.0 | 0.0 |
| test-scoper | 54 | 11293.6 | 209.1 |
| ticket-scoper | 43 | 1815.0 | 42.2 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 98 |

## Slow Runs (> 30 min)

| run_id | duration | active | idle | final_status |
|---|---|---|---|---|
| FOLDER-tickets-todos-ai-first-hardening-h1-h2-followon | 3841 min | 0 min | 3841 min | DONE |
| FOLDER-tickets-todos-ai-first-hardening-h0-governance-guardrail | 1165 min | 0 min | 1165 min | DONE |
| TCK-20260912-WORKING-LOG-APPEND-HELPER | 1086 min | 0 min | 1337 min | DONE |
| TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE | 1016 min | 0 min | 1015 min | DONE |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 977 min | 0 min | 977 min | DONE |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 828 min | 91 min | 737 min | DONE |
| TCK-20260904-INHERITED-REPUTATION-SEED | 569 min | 1 min | 568 min | DONE |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 462 min | 0 min | 462 min | DONE |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 462 min | 0 min | 462 min | DONE |
| TCK-20260902-PLACE-MIGRATION-RECALIBRATION | 385 min | 0 min | 385 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M4-BEYOND-CITY-EPIC | 204 min | 2 min | 202 min | DONE |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 202 min | 41 min | 161 min | DONE |
| TCK-20260831-READINESS-SPEED-FORMULA | 148 min | 44 min | 103 min | DONE |
| TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT | 147 min | 0 min | 147 min | DONE |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 147 min | 0 min | 147 min | DONE |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 143 min | 54 min | 89 min | DONE |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 123 min | 123 min | 0 min | DONE |
| TCK-20260903-CLAN-LIFECYCLE-SUCCESSION | 111 min | 0 min | 111 min | DONE |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 103 min | 103 min | 0 min | DONE |
| TCK-20260903-ECONOMIC-VACANCY-SIGNAL | 99 min | 0 min | 99 min | DONE |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 98 min | 0 min | 98 min | DONE |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 93 min | 57 min | 35 min | DONE |
| TCK-20260903-INFORMATION-HUB-ACCUMULATION | 93 min | 0 min | 93 min | DONE |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 89 min | 0 min | 89 min | DONE |
| TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE | 89 min | 37 min | 51 min | DONE |
| TCK-20260902-WORLDCOMPILER-PLACE-WIRING | 88 min | 0 min | 88 min | DONE |
| TCK-20260902-PARITY-TEST-PATH-GAP | 86 min | 41 min | 45 min | DONE |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 85 min | 0 min | 85 min | DONE |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 83 min | 0 min | 83 min | DONE |
| TCK-20260905-CHRONICLE-FIDELITY-DRIFT | 79 min | 0 min | 79 min | DONE |
| TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION | 74 min | 35 min | 39 min | DONE |
| TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP | 74 min | 0 min | 74 min | DONE |
| CREATE-TICKETS-AI-FIRST-HARDENING-EPICS | 67 min | 0 min | 67 min | DONE |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 66 min | 66 min | 0 min | DONE |
| TCK-20260831-ROLE-MODEL-IMITATION | 65 min | 65 min | 0 min | DONE |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 64 min | 64 min | 0 min | DONE |
| TCK-20260831-TRUST-GATED-TEACHING | 60 min | 60 min | 0 min | DONE |
| TCK-20260904-SPECIES-CORE-SCHEMA-RENAME | 60 min | 15 min | 45 min | DONE |
| TCK-20260902-ASPECT-TERM-CLEANUP | 56 min | 56 min | 0 min | DONE |
| TCK-20260906-CI-FRONTEND-PATH-FILTER | 55 min | 0 min | 417 min | DONE |
| TCK-20260831-SPECIES-INTELLIGENCE-TIER | 53 min | 53 min | 0 min | DONE |
| TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP | 50 min | 0 min | 50 min | DONE |
| TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT | 49 min | 0 min | 49 min | DONE |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | 42 min | 42 min | 0 min | DONE |
| TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS | 42 min | 0 min | 419 min | DONE |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 41 min | 41 min | 0 min | DONE |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 39 min | 39 min | 0 min | DONE |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 39 min | 0 min | 39 min | DONE |
| TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE | 35 min | 0 min | 35 min | DONE |
| TCK-20260825-METADATA-API-BACKEND-MISSING | 35 min | 0 min | 211 min | DONE |
| TCK-20260902-HARVEST-LOOT-TEST-COVERAGE | 33 min | 33 min | 0 min | DONE |

_38 of the runs above spend at least half their reported duration idle (gaps ≥ 30 min between phase transitions, e.g. waiting on human review) rather than in active work — see `active`/`idle` columns; "slow" here does not mean "took a long time to actively work on."_

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Duration outliers (by tier)

| run_id | tier | duration_s | tier median | ratio | active | idle |
|---|---|---|---|---|---|---|
| FOLDER-tickets-todos-ai-first-hardening-h1-h2-followon | epic | 230499 | 300 | 768.3x | 0 min | 3841 min |
| FOLDER-tickets-todos-ai-first-hardening-h0-governance-guardrail | epic | 69900 | 300 | 233.0x | 0 min | 1165 min |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M4-BEYOND-CITY-EPIC | n/a | 12280 | 898 | 13.7x | 2 min | 202 min |
| TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD | epic | 1800 | 300 | 6.0x | 0 min | 30 min |
| TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY | epic | 1800 | 300 | 6.0x | 0 min | 390 min |
| CREATE-TICKETS-AI-FIRST-HARDENING-EPICS | n/a | 4049 | 898 | 4.5x | 0 min | 67 min |

_6 of the duration outliers above spend at least half their reported duration idle rather than in active work — see `active`/`idle` columns; a large ratio here does not mean "took unusually long to actively work on."_

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX | 1 | Scope | claude | 862.641 | 14.1 | 61.2x |
| TCK-20260831-READINESS-SPEED-FORMULA | 6 | Review-Recheck | architecture-reviewer | 4738.2 | 93.3 | 50.8x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 6 | Review | architecture-reviewer | 2336.572 | 62.4 | 37.4x |
| TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST | 7 | Architecture-Verify | architecture-reviewer | 1788.286 | 56.0 | 31.9x |
| TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY | 6 | Architecture-Verify | claude | 1593.737 | 56.0 | 28.5x |
| TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE | 1 | Scope | claude | 360.141 | 14.1 | 25.6x |
| TCK-20260902-ASPECT-TERM-CLEANUP | 5 | Test | test-scoper | 1547.051 | 63.3 | 24.4x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 8 | Document-Update | doc-updater | 1483.53 | 66.7 | 22.2x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 2 | Investigate | investigator | 1279.258 | 62.7 | 20.4x |
| TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE | 1 | Scope | claude | 285.16200000000003 | 14.1 | 20.2x |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | 5 | Test | test-scoper | 1262.373 | 63.3 | 19.9x |
| TCK-20260825-METADATA-API-BACKEND-MISSING | 1 | Scope | claude | 238.752 | 14.1 | 16.9x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 9 | Architecture-Verify | architecture-reviewer | 932.0260000000001 | 56.0 | 16.6x |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 5 | Test | test-scoper | 1009.152 | 63.3 | 15.9x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 8 | Architecture-Verify | architecture-reviewer | 887.236 | 56.0 | 15.8x |
| TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS | 1 | Scope | claude | 206.951 | 14.1 | 14.7x |
| TCK-20260907-FILTERED-REPLAY-EVAL-PILOT | 1 | Scope | ticket-scoper | 206.79500000000002 | 14.1 | 14.7x |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 5 | Test | test-scoper | 897.868 | 63.3 | 14.2x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 5 | Implement | implementer | 857.049 | 60.7 | 14.1x |
| TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL | 5 | Implement | claude | 845.559 | 60.7 | 13.9x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 5 | Implement | implementer | 821.265 | 60.7 | 13.5x |
| TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE | 5 | Implement | implementer | 763.065 | 60.7 | 12.6x |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 8 | Test | test-scoper | 773.48 | 63.3 | 12.2x |
| TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN | 1 | Scope | orchestrator | 163.589 | 14.1 | 11.6x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 9 | Test | test-scoper | 703.523 | 63.3 | 11.1x |
| TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP | 1 | Scope | orchestrator | 154.248 | 14.1 | 10.9x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 9 | Document-Update | orchestrator | 704.941 | 66.7 | 10.6x |
| TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE | 1 | Scope | claude | 148.718 | 14.1 | 10.6x |
| TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT | 3 | Document-Update | doc-updater | 688.707 | 66.7 | 10.3x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 7 | Architecture-Verify | claude | 566.404 | 56.0 | 10.1x |
| TCK-20260908-HOTFIX-OWNERSHIP-LIFECYCLE-DOC-STALE-PRESHIP-GUARD | 1 | Scope | orchestrator | 140.72 | 14.1 | 10.0x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 1 | Scope | claude | 138.034 | 14.1 | 9.8x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 8 | Architecture-Verify | architecture-reviewer | 530.2429999999999 | 56.0 | 9.5x |
| TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS | 1 | Scope | claude | 127.416 | 14.1 | 9.0x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 6 | Implement | implementer | 504.101 | 60.7 | 8.3x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 6 | Implement | implementer | 495.392 | 60.7 | 8.2x |
| TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP | 1 | Scope | orchestrator | 114.68 | 14.1 | 8.1x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 1 | Scope | ticket-scoper | 111.029 | 14.1 | 7.9x |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 8 | Test | test-scoper | 489.211 | 63.3 | 7.7x |
| TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL | 1 | Scope | claude | 107.419 | 14.1 | 7.6x |
| TCK-20260831-ROLE-MODEL-IMITATION | 5 | Implement | implementer | 444.687 | 60.7 | 7.3x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 9 | Document-Update-Gate | orchestrator | 466.647 | 64.2 | 7.3x |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 2 | Implement | implementer | 431.76800000000003 | 60.7 | 7.1x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 7 | Implement | implementer | 428.213 | 60.7 | 7.0x |
| TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL | 1 | Scope | claude | 97.28800000000001 | 14.1 | 6.9x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 5 | Implement | implementer | 410.161 | 60.7 | 6.8x |
| TCK-20260904-HOTFIX-WORKFLOW-META-CONFORMANCE-SHARD-AWARENESS | 1 | Scope | claude | 94.46000000000001 | 14.1 | 6.7x |
| TCK-20260909-KGMCP-DOC-STATUS-SWEEP | 1 | Scope | ticket-scoper | 93.202 | 14.1 | 6.6x |
| TCK-20260831-ROLE-MODEL-IMITATION | 1 | Scope | ticket-scoper | 92.42699999999999 | 14.1 | 6.6x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 10 | Test | test-scoper | 407.92400000000004 | 63.3 | 6.4x |
| TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS | 1 | Scope | claude | 90.441 | 14.1 | 6.4x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 3 | Plan | planner | 372.27500000000003 | 60.3 | 6.2x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 1 | Scope | ticket-scoper | 86.801 | 14.1 | 6.2x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 3 | Plan | planner | 369.498 | 60.3 | 6.1x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 4 | Review | architecture-reviewer | 382.003 | 62.4 | 6.1x |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 6 | Implement | implementer | 371.541 | 60.7 | 6.1x |
| TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | 5 | Implement | implementer | 349.419 | 60.7 | 5.8x |
| TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING | 1 | Scope | orchestrator | 81.003 | 14.1 | 5.7x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 6 | Document-Update | doc-updater | 371.293 | 66.7 | 5.6x |
| TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION | 5 | Implement | implementer | 333.476 | 60.7 | 5.5x |
| TCK-20260904-BASH-SECRET-SCAN-HOOK | 1 | Scope | ticket-scoper | 75.87100000000001 | 14.1 | 5.4x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 4 | Review | architecture-reviewer | 334.027 | 62.4 | 5.4x |
| TCK-20260907-FILTERED-REPLAY-EVAL-PILOT | 6 | Implement | implementer | 320.658 | 60.7 | 5.3x |
| TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST | 5 | Implement | implementer | 317.60400000000004 | 60.7 | 5.2x |
| TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE | 1 | Scope | claude | 72.729 | 14.1 | 5.2x |
| TCK-20260831-READINESS-SPEED-FORMULA | 1 | Scope | ticket-scoper | 71.67099999999999 | 14.1 | 5.1x |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 6 | Document-Update | doc-updater | 338.238 | 66.7 | 5.1x |
| TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY | 1 | Scope | claude | 71.366 | 14.1 | 5.1x |
| TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP | 4 | Review | architecture-reviewer | 315.929 | 62.4 | 5.1x |
| TCK-20260904-SHADOW-REVIEWER-LOGGING | 1 | Scope | claude | 70.971 | 14.1 | 5.0x |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 6 | Implement | implementer | 305.28200000000004 | 60.7 | 5.0x |
| TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT | 1 | Scope | orchestrator | 69.434 | 14.1 | 4.9x |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 5 | Implement | implementer | 292.608 | 60.7 | 4.8x |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 1 | Scope | ticket-scoper | 67.288 | 14.1 | 4.8x |
| TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX | 5 | Implement | claude | 286.221 | 60.7 | 4.7x |
| TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT | 5 | Implement | implementer | 285.171 | 60.7 | 4.7x |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 1 | Scope | ticket-scoper | 64.346 | 14.1 | 4.6x |
| TCK-20260831-SPECIES-INTELLIGENCE-TIER | 1 | Scope | ticket-scoper | 64.112 | 14.1 | 4.5x |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 1 | Scope | ticket-scoper | 63.44 | 14.1 | 4.5x |
| TCK-20260831-READINESS-SPEED-FORMULA | 9 | Architecture-Verify | architecture-reviewer | 247.949 | 56.0 | 4.4x |
| TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT | 1 | Scope | ticket-scoper | 61.903999999999996 | 14.1 | 4.4x |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 1 | Scope | ticket-scoper | 61.848 | 14.1 | 4.4x |
| TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA | 1 | Scope | ticket-scoper | 61.293 | 14.1 | 4.3x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 8 | Architecture-Verify | architecture-reviewer | 237.89600000000002 | 56.0 | 4.2x |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 1 | Scope | ticket-scoper | 59.612 | 14.1 | 4.2x |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 1 | Scope | ticket-scoper | 59.328 | 14.1 | 4.2x |
| TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE | 1 | Scope | ticket-scoper | 58.938 | 14.1 | 4.2x |
| TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS | 1 | Scope | ticket-scoper | 58.702 | 14.1 | 4.2x |
| TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | 1 | Scope | ticket-scoper | 58.652 | 14.1 | 4.2x |
| TCK-20260831-TRUST-GATED-TEACHING | 1 | Scope | ticket-scoper | 58.539 | 14.1 | 4.2x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 1 | Scope | ticket-scoper | 57.819 | 14.1 | 4.1x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 1 | Scope | orchestrator | 57.432 | 14.1 | 4.1x |
| TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA | 5 | Implement | implementer | 239.318 | 60.7 | 3.9x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 1 | Scope | ticket-scoper | 55.074 | 14.1 | 3.9x |
| TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH | 1 | Scope | ticket-scoper | 55.052 | 14.1 | 3.9x |
| TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE | 1 | Scope | ticket-scoper | 55.012 | 14.1 | 3.9x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 10 | Test-Cleanup-Checkpoint | orchestrator | 102.00200000000001 | 26.4 | 3.9x |
| TCK-20260905-FAME-DERIVER-LEGEND-FACT | 8 | Test | claude | 242.673 | 63.3 | 3.8x |
| TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH | 1 | Scope | ticket-scoper | 53.926 | 14.1 | 3.8x |
| TCK-20260902-CLASSHALL-DEAD-CODE | 2 | Implement | implementer | 230.746 | 60.7 | 3.8x |
| TCK-20260912-WORKING-LOG-APPEND-HELPER | 8 | Implement | implementer | 224.601 | 60.7 | 3.7x |
| TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL | 4 | Review | claude | 229.423 | 62.4 | 3.7x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 4 | Review | architecture-reviewer | 228.594 | 62.4 | 3.7x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 4 | Review | claude | 228.336 | 62.4 | 3.7x |
| TCK-20260831-TRUST-GATED-TEACHING | 5 | Implement | implementer | 218.484 | 60.7 | 3.6x |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 4 | Review | architecture-reviewer | 220.77100000000002 | 62.4 | 3.5x |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 5 | Implement | implementer | 212.099 | 60.7 | 3.5x |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 9 | Test | test-scoper | 217.81900000000002 | 63.3 | 3.4x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 7 | Architecture-Verify | architecture-reviewer | 190.28900000000002 | 56.0 | 3.4x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 4 | Review | architecture-reviewer | 209.253 | 62.4 | 3.4x |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 6 | Implement | implementer | 200.14600000000002 | 60.7 | 3.3x |
| TCK-20260905-CHRONICLE-FIDELITY-DRIFT | 5 | Implement | implementer | 196.341 | 60.7 | 3.2x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 5 | Review | architecture-reviewer | 201.013 | 62.4 | 3.2x |
| TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS | 8 | Test | test-scoper | 198.862 | 63.3 | 3.1x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 10 | Test-Cleanup-Checkpoint | orchestrator | 82.502 | 26.4 | 3.1x |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 7 | Architecture-Verify | architecture-reviewer | 174.132 | 56.0 | 3.1x |
| TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | 8 | Test | test-scoper | 195.744 | 63.3 | 3.1x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 6 | Document-Update | doc-updater | 201.603 | 66.7 | 3.0x |

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
| Retrieval event count | 1 | 0 |
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

**Total:** 858

### Raw Investigation (Read) Calls

**Total:** 4938
**Read-to-search ratio:** 5.7552

## Tool Safety Audit

### Search-Before-Grep Compliance (Investigate Phase)

_Only the orchestrating run's own direct tools.jsonl rows are visible to this detector — a dispatched sub-agent's (e.g. `investigator`) own search/grep calls are not attributed back to this pair, so a 'non-compliant' pair may reflect an orchestrator-level incidental call rather than the real investigation's own behavior. The true compliance rate for delegated investigation work is unknown and plausibly higher than the rate below._

**Compliance rate:** 72.5% (37/51 Investigate-phase calls)

### Parity Ledger Write-Safety

**`docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build` call:** 0
**Unsafe `parity_index.py build` invocations (real repo path):** 33

### Read-Count Correlation (Search-Before-Grep Compliance)

| Group | Pairs | Median Read count | Avg Read count |
|---|---|---|---|
| Compliant | 37 | 13.0 | 12.9 |
| Non-compliant | 14 | 6.5 | 7.6 |

## Parity Index Read-Path Usage

**`entry`/`impact`/`health` call count:** 0/21870 Bash rows scanned

_Counts tools.jsonl rows where tool == "Bash" and input_summary matches parity_index.py followed immediately by entry, impact, or health (path-anchored, so a filename mention alone — e.g. test_parity_index.py, --help, `git log -- ... parity_index.py`, `sed -n '1,60p' tools/parity_index.py` — never counts). bash_rows_scanned is the total Bash-tool row population this detector ran against (the section's own 'N' denominator). Confirmed 0 real call sites as of TCK-20260731-PARITY-READPATH-GATE's Gate A review (reviewed GO, not yet wired into any real workflow call site) — this is the expected, correct value until a future ticket adds a real entry/impact/health call site, not a bug._

## Skill Usage

### Per-Skill Invocation Counts (This Period)

| Skill | Invocations |
|---|---|
| claude-api | 2 |
| combat-mechanics | 1 |
| create-tickets | 1 |
| graphify | 6 |
| implement-ticket | 3 |
| run | 1 |
| workflow-authoring | 5 |

**Total:** 19

_Derived from tools.jsonl's literal `tool` field, filtered to `tool == 'Skill'`, with the skill name extracted from `input_summary` via regex (r\"'skill':\s*'([^']*)'\") — never json.loads(), since input_summary is a Python dict-repr string, not JSON. Records where the regex finds no match are counted under `unparseable`, never silently dropped. `unattributed` covers Skill invocations with no run_id (interactive, outside any workflow run). Distinct from generate_retro.py's tag_breakdown_skill aggregate — this is a raw per-skill invocation count, not a tag-driven gate-hit count._

### Zero-Invocation Flags (All-Time, 14-Day Grace Period)

**Flagged (confirmed age past grace period):** api-design-principles, architecture, backend-testing, observability, progression-entities, simq-dev, systems-economy
**Flagged (unknown age, no `date_added`):** debugging-strategies, doc-coauthoring, frontend-design, prompt-builder, python-performance-optimization, python-testing-patterns, test-driven-development

_All-time (never period-scoped) cross-reference of the real .claude/skills/*/SKILL.md catalog against build_skill_usage_section(tools)'s per_skill counts. A skill with any nonzero invocation count is never flagged, regardless of age. Of the remaining zero-invocation skills: `flagged_stale` requires a real, parseable `date_added` older than the 14-day grace period — a confirmed-age signal. `flagged_unknown_age` covers skills with no (or unparseable) `date_added` and zero invocations — an honest, lower-certainty signal, not proof of staleness, since no authorship date can be established. This fail-open policy on missing date_added is deliberate: it is what makes backend-testing's real pre-TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED state (no date_added field at all) correctly flaggable, per TCK-20260810-SKILL-USAGE-RETRO-TRACKING's AC2._

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

### Deep review — 2026-09-15 (`agent-working-design`)

Written after the 2026-09-11→15 agent-infrastructure batch closed (PRs #194, #197, #199, #201 all
merged). Numbers below were derived directly from the sharded `agent-monitoring/data/*/` JSONL
corpus, **not** from `monitoring.db` (last built 2026-09-13 and documented as going stale), and
cross-checked against this report's own generated sections.

**Read the generated report above with one correction in mind.** `make agent-monitoring-retro`
defaults to the current ISO week — that run covered **16 runs / 94 events**, against **249 runs /
1,861 events** for the real 14-day window. Anyone reading `RETRO-2026-W38.md` alone will
understate the period by more than an order of magnitude. This file (`--days 14`) is the correct
instrument for a fortnightly review.

#### Throughput and outcomes

| Metric | Value |
|---|---|
| Runs | 249 (233 DONE, 93%) |
| Events | 1,861 |
| Tool calls | 50,696 |
| Ticket closures (working_log, September) | 329 — 321 DONE, 10 BLOCKED |
| Tier mix | standard 174, hotfix 54, epic 9 |

Week over week the DONE rate **fell**: W37 97% (137/141) → W38 89% (97/109), with gate failures
rising from 3 to 12 (BLOCKED 2→9, NEEDS_CHANGES 0→3). That is worth watching rather than alarming —
W38 is when this batch deliberately pointed gates at agent infrastructure, and a gate that starts
catching things looks exactly like a regression in this table.

#### Where work actually fails

Failure is concentrated in two phases and effectively absent elsewhere:

| Phase | Total | Failed | Rate |
|---|---|---|---|
| Review | 97 | 10 | **10.3%** |
| Verify | 233 | 12 | 5.2% |
| Test | 209 | 5 | 2.4% |
| Implement / Scope / Finalize / Plan / Parity | 940 | 0 | 0.0% |

**Review's failures are still the same root cause `agent_definition_gap_audit_2026-08-04.md`
identified and its August fix targeted**: planners asserting facts about existing code without
verifying them ("plan falsely claimed `test_docs_coverage_hotfix_is_na` stays unmodified", "Step 5
rests on a disproven claim", "investigation.md undercounts the dict as 10 entries", "misattributes
INFRA-278"). That audit's own deferred check was six weeks overdue; it was run on 2026-09-14 and
its finding is recorded in that document's addendum. Verify's three targeted sub-patterns did
close — its failures have relocated to `Files Changed` / sibling-path disclosure omissions, a class
nobody has tried to fix.

Encouragingly, the daily trend ends clean: **zero failed events on 2026-09-12, -13 and -14**,
including a 171-event day.

#### Data quality — the largest finding, and it caps every cost number here

- **23.7% of tool rows (12,033 / 50,696) carry no `run_id` and no phase.** It is the *same* rows
  missing both. Every per-phase and per-agent spend figure in this report is therefore computed on
  ~76% of real volume.
- **`cost_proxy_score` is present on only 30.5% of events (579 / 1,897).** The Spend-Proxy tables
  above are a ranking, not a total.
- Both trace to the same cause: `.claude/current_run` is a single shared sidecar across concurrent
  sessions (`project_sidecar_cross_session_contamination`). With several sessions running at once
  all week, unattributed rows are the expected outcome, not an anomaly.
- **34 September closures have no run record at all**, clustered on 2026-09-02→05 (4/13/14/3 by
  day) — one hand-orchestrated batch, not steady leakage. Same gap as
  `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE`.
- **`make agent-monitoring-validate` currently fails** — 19 runs marked DONE with no working_log
  entry. All are June-era (`TCK-20260619-*`, `TCK-20260629-SIMQ-*`), so historical, but the gate is
  red today and a reader should know that before trusting any integrity claim.
- **9 of 2,013 working_log rows (0.4%) do not match the 6-column schema** — 7, 8 and 9 fields.
  Cause is unescaped commas in the *title* field ("Clan lifecycle -- joining, leaving, and
  succession-on-death"), shifting every later column. Any status-based query silently misreads
  them; this review hit exactly that.
- **55 events and 66 runs carry an unusable `ts`**; `agent-monitoring/data/unknown-week/` holds 34
  rows. The runs are entirely W24–W27 (June), so the 14-day window is **not** deflated by them.
- Three non-canonical agent values persist: `orchestrator` (144 events, first seen 2026-06-22 —
  long-lived, and the registered literal is `implement-ticket-orchestrator`), `concern-investigator`
  (6), `context-packet-wrapper` (1).

#### How the work is actually being done

**`claude` accounts for 970 of ~1,900 events — over half.** This pipeline is now majority
hand-orchestration rather than dispatched subagents, and `claude` is a *registered* identity for
exactly that (`TCK-20260808-AGENT-MONITORING-CLAUDE-VOCAB-REGISTRATION`), not drift. That matters
for interpreting everything above: the hand-orchestrated path is the one where the monitoring
sidecar is weakest and where the done-checker gate was, until 2026-09-14, unreachable at all
(`TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`).

Caller-level agent mix, from 1,183 subagent transcripts (`agentType` in `.meta.json`) — note this
is **not** `tools.jsonl`'s `agent` field, which carries the pipeline identity from the sidecar:
architecture-reviewer 199, done-checker 125, fork 104, implementer 100, planner 100,
ticket-scoper 95, general-purpose 92, test-scoper 83, investigator 77, doc-updater 73.

Tool mix is overwhelmingly shell: **Bash 33,419 (66%)**, Read 7,389, Edit 4,590, Write 1,828,
Agent 971, `search_docs` 362. Median 309 tool calls per run (p90 664).

#### Duration — read the idle column

18 runs exceeded 2h, median 42 min over the 89 runs with a nonzero `duration_s`. But the report's
own Outliers section is right to caveat this: the two largest (`FOLDER-...-h1-h2-followon` at 64.0h
and `...-h0-governance-guardrail` at 19.4h) are **epic folder aggregates spanning a whole batch**,
and show `0 min active / 3841 min idle` and `0 min active / 1165 min idle`. They are not 64-hour
executions. The genuine single-ticket outliers are `TCK-20260912-WORKING-LOG-APPEND-HELPER` (18.1h)
and `TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE` (16.9h).

#### Cross-confirmations worth keeping

- The Skill Usage section independently re-flags `frontend-design` and `prompt-builder` as
  zero-invocation — the same two skills the 2026-07-03 infrastructure audit named, and which were
  re-verified still-present and still-unevaluated on 2026-09-14. Ten weeks, unchanged.
- Search-before-grep compliance reads 72.5%, and the section correctly discloses that a dispatched
  sub-agent's own calls are invisible to the detector, so the real rate is unknown and plausibly
  higher. That disclosure is the difference between a measurement and a number.
- The retro generator itself surfaced two non-canonical tiers (`epic_batch`, `epic-batch`) and three
  `tools.jsonl` rows skipped for a pre-schema shape (`tools_used` array).

#### Proposed actions, in leverage order

1. **Fix the sidecar attribution gap.** At 23.7% unattributed tool rows and 30.5% cost coverage, the
   spend tables cannot answer "what does a ticket cost". This is the single change that would make
   the rest of this report trustworthy.
2. **Close the Review root cause** — the planner still has no instruction to verify factual claims
   about current code against real source. Named in the August audit, measurably still live.
3. **Fix the working_log title-field quoting** so the 0.4% malformed rows stop corrupting
   status queries.
4. **Decide the 34 uncovered closures** — backfill or accept, but record which.
5. **Make `--days 14` (or `--week`) the default cadence for a fortnightly review**, or note
   prominently in `RETRO-<week>.md` that it is a one-week slice.

_No finding here was taken from an agent report without re-deriving it. Two of this session's own
intermediate figures were wrong and are corrected above: a ticket count derived from file mtimes
(meaningless after branch switching) and a closure/run gap of ~100 that was really 34._

#### Addendum — `index.md` reports numbers that disagree with the reports it links to

Found while writing this review, and it is the same shape as everything else catalogued above, so
it belongs here rather than in a session transcript.

`agent-monitoring/retro/index.md` currently shows:

| Row | Index claims | The linked report itself says |
|---|---|---|
| `LAST14D` | 0 runs, 0 DONE, 0 failures | **249 runs, 233 DONE** |
| `ALL` | 1609 runs, 1383 DONE | **1149 runs, 962 DONE (83%)** |

Cause is in `generate_retro.py::_update_index` (:1885-1925). Every row's numbers are computed from
the **live corpus at generation time**, never from the report the row links to:

```python
week_runs = all_runs if name == "ALL" else runs_by_week.get(name, [])
```

- `runs_by_week` is keyed by **ISO week string**. `"LAST14D"` is not an ISO week, so the lookup
  misses and the row is filled with zeros. There is an explicit special case for `"ALL"` and none
  for any other non-week scope, so **every `--days N` report indexes as 0**.

  This is not new and was not first exposed by this file. All three period reports in the repo
  today index as zero while their own bodies report real work, and two of them have been committed
  since 2026-09-06 — nine days of an index stating there is nothing there:

  | Report | Index row | Report body |
  |---|---|---|
  | `RETRO-LAST7D.md` (tracked, 2026-09-06) | 0 runs | **69 runs** |
  | `RETRO-LAST14D.md` (this file) | 0 runs | **249 runs** |
  | `RETRO-LAST28D.md` (tracked, 2026-09-06) | 0 runs | **300 runs** |
- The `ALL` row uses the unfiltered `all_runs` (1609), while `RETRO-ALL.md`'s own body reports 1149
  after `main()`'s filtering. Same label, two populations.

Because the index never parses the reports, it cannot notice the disagreement — it silently prints
a different number next to the document that contradicts it. A reader opening `index.md` first (the
obvious entry point) sees "LAST14D: 0 runs" and would reasonably conclude the fortnight was empty.

Not fixed here — this review is read-only with respect to the tooling. Worth a ticket, and worth
noting that it makes **13** distinct mechanisms found in this arc that exist, have tests or an
official-looking surface, and do not report what they appear to.

### Duplicate run records corrected — 2026-09-15 (`agent-working-implementer`,
### `TCK-20260915-DUPLICATE-RUN-RECORDS`)

This report's own headline (**249 runs, 233 DONE, 93%**) was measured against raw, undeduplicated
`runs.jsonl` rows. Investigated and found: `writeMonitoring()` fires at every gate exit point
within one continuous execution, correctly keeping one stable `(run_id, execution_id, start_ts)`
identity across every call — a session that continues past a gate failure (fixes it, keeps going)
legitimately produces multiple `runs.jsonl` rows for that one real execution (`NEEDS_CHANGES` →
`DOD_BLOCKED` → `DONE`, each a real checkpoint, confirmed by correlating a sample group's shared
`execution_id` against its own `events.jsonl` timeline). This is **not** noise; it is accurate
audit-trail data that a naive `len(runs)` count was never designed to collapse.

All-time corpus: 66 duplicate-key groups, of which 63 (95%) are this legitimate shape, 2 are
ambiguous-but-plausible epic-batch continuations, and exactly **1** is a confirmed genuine
accidental duplicate (a hand-typed `record_run.py --data` invocation, identifiable by its
non-standard `-final`-suffixed `execution_id`, most likely run twice with the same copy-pasted
argument). Fixed with a dedupe-on-read utility
(`tools/agent-monitoring/run_dedup.py::dedupe_to_latest_per_execution`), now wired into
`generate_retro.py`'s report generation for every window (`--days`, `--all`, weekly), and a
narrow ratchet check (`make duplicate-run-record-check`, ceiling 1) watching only the genuinely-
ambiguous bucket, not the healthy-continuation majority.

**This period's own corrected figures**: only 2 of the 66 all-time duplicate groups fall inside
this 14-day window (1 legitimate continuation, 1 the confirmed accidental duplicate) — the
correction is real but small:

| | Raw (as reported above) | Deduplicated |
|---|---|---|
| Total runs | 249 | **247** |
| DONE | 233 | **232** |
| Gate failures | 15 | **14** |
| DONE rate | 93.6% | **93.9%** |

Future report generations (`generate_retro.py`'s CLI, not the raw import path used to compute this
correction without regenerating the file — see below) will render these deduplicated figures
directly, with an inline note when raw and deduplicated counts differ.

**A hazard hit while producing this very note, recorded so it does not recur**: running
`generate_retro.py --days 14` to check the fix would have unconditionally overwritten this file,
destroying every hand-authored section above (including this one and the "Deep review" section) —
confirmed the hard way with a real `git diff` showing 177 deleted lines before reverting it. Every
number in this section was instead computed by importing `_load_runs_and_events()`/
`compute_retro_metrics()`/`generate()` directly and calling them without touching
`RETRO_DIR`/writing a file. Anyone verifying this correction later should do the same, not re-run
the CLI against this path.

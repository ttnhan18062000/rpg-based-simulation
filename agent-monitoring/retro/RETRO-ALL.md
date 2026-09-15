# Agent Monitoring Retro — All Time

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 1532 |
| Completed (DONE) | 1385 (90%) |
| Gate failures | 99 |
| Avg duration | 168 min |
| Avg agents per run | 6.8 |
| Total agent calls | 10623 |

_Note: 1614 raw `runs.jsonl` rows in this window collapsed to 1532 real executions after deduplicating gate-checkpoint rows that share one `(run_id, execution_id, start_ts)` identity (TCK-20260915-DUPLICATE-RUN-RECORDS) — the counts above are the deduplicated figures._

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| BLOCKED | 14 | 0% |
| completed | 12 | 0% |
| NEEDS_HUMAN_INPUT | 11 | 0% |
| success | 10 | 0% |
| None | 10 | 0% |
| DOD_BLOCKED | 10 | 0% |
| complete | 8 | 0% |
| done | 4 | 0% |
| CONFLICTS_DETECTED | 4 | 0% |
| NEEDS_CHANGES | 3 | 0% |
| DONE_NO_TICKET | 2 | 0% |
| STOPPED_BY_USER | 2 | 0% |
| TESTS_FAILED | 2 | 0% |
| INPROGRESS | 1 | 0% |
| ALL_SCOPED | 1 | 0% |
| STOPPED_FOR_HUMAN_INPUT | 1 | 0% |
| VERIFY_WRITE_CYCLE_EVIDENCE | 1 | 0% |
| BACKLOG | 1 | 0% |
| NEEDS_TICKET | 1 | 0% |
| ANCHORS_STILL_FAILING | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 116 |
| needs_changes | 18 |
| conflicts_detected | 6 |
| no_behavior_change | 6 |
| DOD_BLOCKED | 3 |
| architecture_violation | 3 |
| plan_needs_changes | 3 |
| needs_human_input | 2 |
| DOC_STALENESS_BLOCKED | 1 |
| FRONTMATTER_INVALID | 1 |
| operational_mistake | 1 |
| documentation_accuracy | 1 |
| transient_infra_error | 1 |
| new_open_question_discovered | 1 |
| governance_conflict | 1 |
| scope_larger_than_anticipated | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| adventure | 18 | 100% | 0 |
| agency | 6 | 100% | 0 |
| architecture | 66 | 89% | 5 |
| cognition | 66 | 89% | 7 |
| combat | 51 | 94% | 3 |
| content | 44 | 93% | 2 |
| core | 2 | 100% | 0 |
| dashboard | 29 | 93% | 1 |
| ecology | 2 | 100% | 0 |
| economy | 15 | 93% | 1 |
| engine | 49 | 97% | 1 |
| faction | 21 | 100% | 0 |
| feature-flags | 28 | 96% | 1 |
| governance | 10 | 100% | 0 |
| grade-thresholds | 3 | 66% | 1 |
| grand-strategy | 2 | 100% | 0 |
| hud | 2 | 100% | 0 |
| information | 17 | 76% | 4 |
| lifecycle | 13 | 100% | 0 |
| live-map | 1 | 100% | 0 |
| mcp | 49 | 85% | 0 |
| observability | 127 | 96% | 4 |
| progression | 26 | 100% | 0 |
| rendering | 8 | 87% | 0 |
| resource | 1 | 100% | 0 |
| resource-registry | 3 | 100% | 0 |
| self-model | 12 | 66% | 4 |
| simulation-quality | 197 | 95% | 7 |
| social | 40 | 92% | 3 |
| stasis | 3 | 100% | 0 |
| strategy | 23 | 95% | 1 |
| temporal | 1 | 100% | 0 |
| testing | 143 | 88% | 8 |
| visualization | 10 | 90% | 0 |
| websocket | 8 | 100% | 0 |
| world | 98 | 93% | 4 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| api-design | 16 | N/A — no gate implemented |
| debugging | 14 | N/A — no gate implemented |
| performance | 35 | N/A — no gate implemented |
| security | 16 | 12 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 133 | 31 | 91 | 89% |
| epic-batch | 1 | 0 | 1 | 100% |
| epic_batch | 1 | 1 | 0 | 0% |
| hotfix | 314 | 0 | 298 | 94% |
| n/a | 44 | 0 | 44 | 100% |
| standard | 1018 | 0 | 936 | 91% |
| unknown | 21 | 0 | 15 | 71% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| ? | 258 | 0 | 0 | 0 | 0 |
| advisory-checks | 4 | 4 | 0 | 0 | 0 |
| anchor-updater | 3 | 2 | 1 | 0 | 0 |
| architecture-reviewer | 1240 | 907 | 152 | 37 | 144 |
| claude | 1472 | 1338 | 2 | 15 | 117 |
| claude-fork-direct | 12 | 12 | 0 | 0 | 0 |
| claude-orchestrator | 2 | 2 | 0 | 0 | 0 |
| claude-sonnet | 9 | 9 | 0 | 0 | 0 |
| claude-sonnet-4-6 | 16 | 16 | 0 | 0 | 0 |
| cleanup-checkpoint | 4 | 4 | 0 | 0 | 0 |
| concern-investigator | 8 | 8 | 0 | 0 | 0 |
| consolidation | 1 | 1 | 0 | 0 | 0 |
| context-packet-wrapper | 59 | 59 | 0 | 0 | 0 |
| coordinator | 1 | 1 | 0 | 0 | 0 |
| create-tickets | 49 | 48 | 1 | 0 | 0 |
| doc-syncer | 2 | 2 | 0 | 0 | 0 |
| doc-updater | 317 | 316 | 0 | 0 | 1 |
| doc-writer | 2 | 2 | 0 | 0 | 0 |
| dod-verifier | 1 | 1 | 0 | 0 | 0 |
| done-checker | 875 | 707 | 143 | 25 | 0 |
| drift-classifier | 3 | 3 | 0 | 0 | 0 |
| epic-closure | 1 | 1 | 0 | 0 | 0 |
| epic-coordinator | 7 | 7 | 0 | 0 | 0 |
| epic-discoverer | 1 | 1 | 0 | 0 | 0 |
| epic-loop | 1 | 1 | 0 | 0 | 0 |
| epic-orchestrator | 2 | 2 | 0 | 0 | 0 |
| epic-reporter | 1 | 1 | 0 | 0 | 0 |
| epic-runner | 1 | 1 | 0 | 0 | 0 |
| finalizer | 603 | 603 | 0 | 0 | 0 |
| general-purpose | 1 | 1 | 0 | 0 | 0 |
| hotfix-agent | 5 | 5 | 0 | 0 | 0 |
| implement | 1 | 1 | 0 | 0 | 0 |
| implement-epic | 27 | 27 | 0 | 0 | 0 |
| implement-epic-orchestrator | 1 | 1 | 0 | 0 | 0 |
| implement-ticket | 437 | 419 | 13 | 0 | 0 |
| implement-ticket-orchestrator | 152 | 151 | 0 | 0 | 1 |
| implementer | 836 | 825 | 8 | 2 | 1 |
| investigate:C1 | 36 | 35 | 1 | 0 | 0 |
| investigate:C10 | 3 | 3 | 0 | 0 | 0 |
| investigate:C11 | 2 | 2 | 0 | 0 | 0 |
| investigate:C12 | 2 | 2 | 0 | 0 | 0 |
| investigate:C13 | 2 | 2 | 0 | 0 | 0 |
| investigate:C14 | 2 | 2 | 0 | 0 | 0 |
| investigate:C15 | 2 | 2 | 0 | 0 | 0 |
| investigate:C2 | 31 | 30 | 1 | 0 | 0 |
| investigate:C3 | 30 | 29 | 1 | 0 | 0 |
| investigate:C4 | 24 | 23 | 1 | 0 | 0 |
| investigate:C5 | 17 | 15 | 1 | 0 | 1 |
| investigate:C6 | 10 | 10 | 0 | 0 | 0 |
| investigate:C7 | 7 | 7 | 0 | 0 | 0 |
| investigate:C8 | 5 | 4 | 0 | 1 | 0 |
| investigate:C9 | 3 | 3 | 0 | 0 | 0 |
| investigate:D1 | 1 | 1 | 0 | 0 | 0 |
| investigate:D2 | 1 | 1 | 0 | 0 | 0 |
| investigate:D3 | 1 | 1 | 0 | 0 | 0 |
| investigate:direct | 1 | 1 | 0 | 0 | 0 |
| investigator | 651 | 564 | 2 | 2 | 83 |
| link-epic | 19 | 18 | 0 | 0 | 1 |
| main | 6 | 6 | 0 | 0 | 0 |
| manual-hotfix | 3 | 3 | 0 | 0 | 0 |
| orchestrator | 501 | 455 | 5 | 1 | 40 |
| orchestrator-audit | 1 | 1 | 0 | 0 | 0 |
| orchestrator-fix | 3 | 3 | 0 | 0 | 0 |
| parity-checker | 3 | 3 | 0 | 0 | 0 |
| parity-updater | 628 | 473 | 3 | 0 | 152 |
| plan-expander | 1 | 1 | 0 | 0 | 0 |
| plan-fixer | 8 | 8 | 0 | 0 | 0 |
| planner | 671 | 565 | 2 | 21 | 83 |
| planner+implementer | 1 | 1 | 0 | 0 | 0 |
| reviewer | 4 | 4 | 0 | 0 | 0 |
| scope-agent | 9 | 9 | 0 | 0 | 0 |
| scoper | 4 | 4 | 0 | 0 | 0 |
| security-reviewer | 17 | 10 | 1 | 0 | 6 |
| self-doc-update | 1 | 1 | 0 | 0 | 0 |
| self-parity | 1 | 1 | 0 | 0 | 0 |
| self-review | 2 | 2 | 0 | 0 | 0 |
| self-test | 1 | 1 | 0 | 0 | 0 |
| self-verify | 2 | 1 | 1 | 0 | 0 |
| structure | 39 | 39 | 0 | 0 | 0 |
| test-runner | 2 | 2 | 0 | 0 | 0 |
| test-scoper | 650 | 627 | 19 | 2 | 2 |
| tester | 4 | 4 | 0 | 0 | 0 |
| ticket-scoper | 763 | 757 | 6 | 0 | 0 |
| verifier | 2 | 2 | 0 | 0 | 0 |
| workflow | 11 | 11 | 0 | 0 | 0 |
| write-sequence | 5 | 5 | 0 | 0 | 0 |
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
| ? | 177 | 0 | 0 | 0 | 0 |
| Architecture-Verify | 499 | 407 | 18 | 10 | 64 |
| Architecture-Verify-Recheck | 1 | 1 | 0 | 0 | 0 |
| Clarification | 1 | 0 | 0 | 1 | 0 |
| Classify Drift | 4 | 4 | 0 | 0 | 0 |
| Comprehend | 42 | 42 | 0 | 0 | 0 |
| Discover | 9 | 9 | 0 | 0 | 0 |
| Doc-Staleness-Gate | 2 | 2 | 0 | 0 | 0 |
| Document-Update | 366 | 364 | 0 | 0 | 2 |
| Document-Update-Gate | 6 | 6 | 0 | 0 | 0 |
| Epic | 1 | 1 | 0 | 0 | 0 |
| Finalize | 1121 | 1103 | 0 | 3 | 2 |
| Fix | 1 | 1 | 0 | 0 | 0 |
| Implement | 1338 | 1295 | 18 | 3 | 7 |
| Implement+Finalize | 4 | 4 | 0 | 0 | 0 |
| Implement-extension | 1 | 1 | 0 | 0 | 0 |
| Investigate | 989 | 892 | 9 | 4 | 84 |
| Investigate+Plan+Implement | 1 | 1 | 0 | 0 | 0 |
| Investigate-Deepen | 1 | 1 | 0 | 0 | 0 |
| Link | 21 | 20 | 0 | 0 | 1 |
| Parity | 908 | 609 | 4 | 1 | 289 |
| Parity Check | 3 | 3 | 0 | 0 | 0 |
| Parity-Gate | 4 | 4 | 0 | 0 | 0 |
| Plan | 757 | 650 | 2 | 22 | 83 |
| Plan+Implement | 1 | 1 | 0 | 0 | 0 |
| Plan-Fix | 4 | 4 | 0 | 0 | 0 |
| Recalibrate | 4 | 4 | 0 | 0 | 0 |
| Report | 25 | 25 | 0 | 0 | 0 |
| Retrieval | 59 | 59 | 0 | 0 | 0 |
| Review | 809 | 568 | 134 | 27 | 80 |
| Review-Recheck | 5 | 5 | 0 | 0 | 0 |
| Scope | 949 | 934 | 6 | 0 | 0 |
| Security-Review | 24 | 10 | 1 | 0 | 13 |
| Smoke-Test | 1 | 1 | 0 | 0 | 0 |
| Structure | 43 | 43 | 0 | 0 | 0 |
| Sync Docs | 3 | 3 | 0 | 0 | 0 |
| Test | 1002 | 962 | 20 | 4 | 7 |
| Test-Cleanup-Checkpoint | 6 | 6 | 0 | 0 | 0 |
| Update Anchors | 4 | 3 | 1 | 0 | 0 |
| Verify | 1110 | 929 | 151 | 30 | 0 |
| Verify-Recheck | 5 | 4 | 0 | 1 | 0 |
| Verify-Recheck2 | 1 | 1 | 0 | 0 | 0 |
| Verify-fix | 2 | 2 | 0 | 0 | 0 |
| Write | 195 | 195 | 0 | 0 | 0 |
| child-ticket-creation | 2 | 2 | 0 | 0 | 0 |
| context-search | 2 | 2 | 0 | 0 | 0 |
| data-runs-clean-checkpoint | 4 | 4 | 0 | 0 | 0 |
| discover | 1 | 0 | 0 | 0 | 0 |
| doc-staleness-gate | 13 | 13 | 0 | 0 | 0 |
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

_Computed over 60.2% of this window's events (6392 of 10623 scored) — see TCK-20260915-SIDECAR-ATTRIBUTION-GAP for why the rest lack a `cost_proxy_score`._

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 450 | 31959.7 | 71.0 |
| Architecture-Verify-Recheck | 1 | 86.5 | 86.5 |
| Comprehend | 1 | 174.4 | 174.4 |
| Doc-Staleness-Gate | 2 | 0.0 | 0.0 |
| Document-Update | 356 | 22492.0 | 63.2 |
| Document-Update-Gate | 6 | 728.0 | 121.3 |
| Finalize | 688 | 39334.4 | 57.2 |
| Fix | 1 | 55.3 | 55.3 |
| Implement | 684 | 141992.3 | 207.6 |
| Implement-extension | 1 | 0.0 | 0.0 |
| Investigate | 547 | 123453.5 | 225.7 |
| Investigate-Deepen | 1 | 0.0 | 0.0 |
| Link | 1 | 0.0 | 0.0 |
| Parity | 570 | 22918.7 | 40.2 |
| Parity-Gate | 4 | 0.0 | 0.0 |
| Plan | 525 | 24012.1 | 45.7 |
| Plan-Fix | 4 | 236.6 | 59.1 |
| Report | 2 | 0.0 | 0.0 |
| Review | 565 | 33349.8 | 59.0 |
| Review-Recheck | 5 | 5887.0 | 1177.4 |
| Scope | 549 | 49303.6 | 89.8 |
| Security-Review | 24 | 1411.8 | 58.8 |
| Structure | 1 | 0.0 | 0.0 |
| Test | 634 | 60789.2 | 95.9 |
| Test-Cleanup-Checkpoint | 6 | 237.3 | 39.5 |
| Verify | 737 | 45017.1 | 61.1 |
| Verify-Recheck | 5 | 602.4 | 120.5 |
| Verify-Recheck2 | 1 | 235.1 | 235.1 |
| Verify-fix | 2 | 0.0 | 0.0 |
| Write | 2 | 0.0 | 0.0 |
| data-runs-clean-checkpoint | 4 | 0.0 | 0.0 |
| doc-staleness-gate | 13 | 0.0 | 0.0 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| advisory-checks | 4 | 0.0 | 0.0 |
| architecture-reviewer | 964 | 66156.1 | 68.6 |
| claude | 736 | 27113.5 | 36.8 |
| claude-fork-direct | 3 | 0.0 | 0.0 |
| claude-orchestrator | 2 | 0.0 | 0.0 |
| cleanup-checkpoint | 4 | 0.0 | 0.0 |
| create-tickets | 1 | 174.4 | 174.4 |
| doc-updater | 311 | 21166.7 | 68.1 |
| done-checker | 656 | 43863.0 | 66.9 |
| epic-orchestrator | 1 | 0.0 | 0.0 |
| finalizer | 402 | 36481.7 | 90.8 |
| general-purpose | 1 | 0.0 | 0.0 |
| implement-epic-orchestrator | 1 | 0.0 | 0.0 |
| implement-ticket | 8 | 0.0 | 0.0 |
| implement-ticket-orchestrator | 144 | 15.0 | 0.1 |
| implementer | 544 | 140816.7 | 258.9 |
| investigate:C1 | 1 | 54.2 | 54.2 |
| investigate:C2 | 1 | 115.3 | 115.3 |
| investigator | 444 | 116553.6 | 262.5 |
| link-epic | 1 | 0.0 | 0.0 |
| orchestrator | 429 | 4008.3 | 9.3 |
| parity-updater | 430 | 20930.4 | 48.7 |
| planner | 462 | 23069.6 | 49.9 |
| security-reviewer | 17 | 586.3 | 34.5 |
| self-doc-update | 1 | 0.0 | 0.0 |
| self-parity | 1 | 0.0 | 0.0 |
| self-review | 2 | 0.0 | 0.0 |
| self-test | 1 | 0.0 | 0.0 |
| self-verify | 2 | 0.0 | 0.0 |
| structure | 1 | 0.0 | 0.0 |
| test-scoper | 449 | 58545.6 | 130.4 |
| ticket-scoper | 368 | 44626.6 | 121.3 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 258 |
| Truncated (>200 chars) | 166 |

## Slow Runs (> 30 min)

| run_id | duration | active | idle | final_status |
|---|---|---|---|---|
| TCK-20260702-OBSISO-EPIC | 48074 min | 0 min | 48074 min | DONE |
| TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC | 10688 min | 0 min | 10688 min | BACKLOG |
| FOLDER-tickets-todos-ai-first-hardening-h1-h2-followon | 3841 min | 0 min | 3841 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M3-FAMILY-SPECIES-EPIC | 3327 min | 0 min | 3327 min | DONE |
| FOLDER-tickets-todos-adventure-cognition-merge | 1912 min | 0 min | 1911 min | DONE |
| EPIC-TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC | 1801 min | 0 min | 1801 min | DONE |
| FOLDER-tickets-todos-ai-first-hardening-h0-governance-guardrail | 1165 min | 0 min | 1165 min | DONE |
| TCK-20260912-WORKING-LOG-APPEND-HELPER | 1086 min | 0 min | 1337 min | DONE |
| TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE | 1016 min | 0 min | 1015 min | DONE |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 977 min | 0 min | 977 min | DONE |
| FOLDER-tickets-todos-simq-scoring-improvement | 839 min | 0 min | 1008 min | STOPPED_BY_USER |
| FOLDER-tickets-todos-simq-roadmap-phase2-depth-social | 830 min | 0 min | 830 min | DONE |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 828 min | 15 min | 813 min | DONE |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 828 min | 91 min | 737 min | DONE |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 760 min | 31 min | 728 min | DONE |
| TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP | 630 min | 51 min | 578 min | DONE |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 613 min | 42 min | 571 min | DONE |
| FOLDER-tickets-todos-progress-timeline | 603 min | 0 min | 603 min | DONE |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | 585 min | 8 min | 576 min | DONE |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | 580 min | 14 min | 565 min | DONE |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | 576 min | 37 min | 539 min | DONE |
| TCK-20260904-INHERITED-REPUTATION-SEED | 569 min | 1 min | 568 min | DONE |
| EPIC-TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC | 548 min | 0 min | 548 min | DONE |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 541 min | 0 min | 707 min | STOPPED_BY_USER |
| FOLDER-tickets-todos-semantic-entity-index | 532 min | 16 min | 516 min | DONE |
| TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD | 500 min | 60 min | 440 min | DONE |
| TCK-20260824-ROLLOUT-FLAG-DECISIONS | 494 min | 19 min | 479 min | DONE |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 484 min | 60 min | 424 min | DONE |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 483 min | 55 min | 427 min | DONE |
| TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC | 480 min | 0 min | 480 min | DONE |
| EPIC-TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC | 476 min | 0 min | 476 min | DONE |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | 475 min | 27 min | 447 min | DONE |
| TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE | 470 min | 5 min | 465 min | DONE |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 462 min | 0 min | 462 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 440 min | 0 min | 695 min | DOD_BLOCKED |
| TCK-20260801-CODEX-REALREPO-PILOT-HARNESS | 440 min | 15 min | 425 min | DONE |
| FOLDER-tickets-todos-simq-roadmap-phase3-depth-faction-information | 434 min | 0 min | 434 min | DONE |
| TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP | 434 min | 51 min | 383 min | DONE |
| TCK-20260719-TAG-COLLISION-DEDUP | 429 min | 9 min | 420 min | DONE |
| TCK-20260720-PROGRESS-TIMELINE-VIEW | 427 min | 77 min | 350 min | DONE |
| FOLDER-cognition-adventure-eligibility | 416 min | 0 min | 416 min | DONE |
| TCK-20260822-GUARD-SCAN-INDEX-RETROFIT | 400 min | 35 min | 365 min | DONE |
| TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG | 399 min | 0 min | 399 min | DONE |
| TCK-20260811-REGION-STABILIZATION-GOAL-SCORER | 396 min | 75 min | 320 min | DONE |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 396 min | 64 min | 331 min | DONE |
| TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP | 390 min | 28 min | 362 min | DONE |
| TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE | 386 min | 0 min | 904 min | DONE |
| TCK-20260902-PLACE-MIGRATION-RECALIBRATION | 385 min | 0 min | 385 min | DONE |
| EPIC-TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC | 383 min | 0 min | 383 min | DONE |
| TCK-20260821-LIVE-MAP-PERF-VALIDATION | 379 min | 108 min | 271 min | DONE |
| TCK-20260802-STORED-ARTIFACT-KIND | 373 min | 27 min | 345 min | DONE |
| TCK-20260720-TIMELINE-RANGE-CONTROL | 369 min | 59 min | 310 min | DONE |
| TCK-20260831-RACE-RELATIONS-MATRIX | 360 min | 47 min | 312 min | DONE |
| TCK-20260804-AGENT-DEF-GAP-FIXES | 329 min | 149 min | 180 min | DONE |
| TCK-20260824-OCCUPATION-CHANGE-TRIGGER | 329 min | 60 min | 268 min | DONE |
| TCK-20260721-MONITORING-WRITER-UNIFICATION | 325 min | 28 min | 297 min | DONE |
| EPIC-TCK-20260721-PROVIDER-AGNOSTIC-EPIC | 323 min | 0 min | 323 min | DONE |
| EPIC-TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC | 321 min | 0 min | 514 min | DONE |
| TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | 314 min | 75 min | 238 min | DONE |
| TCK-20260731-CODEX-PILOT-EXECUTOR | 295 min | 0 min | 295 min | DONE |
| TCK-20260804-EXPANSION-RATE-WIRING | 284 min | 89 min | 195 min | DONE |
| TCK-20260730-CODEX-RUNTIME-SHADOW | 282 min | 35 min | 247 min | DONE |
| TCK-20260718-AGENTOPS-STATS-BOARD-EPIC | 275 min | 0 min | 275 min | DONE |
| TCK-20260811-ADVENTURE-GOAL-SCORER | 266 min | 105 min | 161 min | DONE |
| TCK-20260817-STATE-DESIGN-PRIORITY-ORDER | 264 min | 0 min | 396 min | DONE |
| TCK-20260710-SIMQ-DEPTH-FACTION | 261 min | 22 min | 238 min | DONE |
| EPIC-TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC | 260 min | 0 min | 260 min | DONE |
| EPIC-TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC | 256 min | 3 min | 253 min | DONE |
| FOLDER-tickets-todos-simq-roadmap-phase0-reliability-foundation | 256 min | 0 min | 256 min | DONE |
| TCK-20260825-HOTFIX-EXEC-IDENTITY-TEST-SIDECAR-STALENESS | 252 min | 0 min | 252 min | DONE |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | 248 min | 0 min | 983 min | DONE |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | 248 min | 86 min | 162 min | DONE |
| EPIC-TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC | 242 min | 0 min | 242 min | DONE |
| EPIC-TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC | 236 min | 0 min | 236 min | DONE |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 235 min | 113 min | 122 min | DONE |
| FOLDER-tickets-todos-context-retrieval-phase3 | 231 min | 0 min | 230 min | DONE |
| FOLDER-tickets-todos-context-retrieval-phase5 | 228 min | 20 min | 208 min | DONE |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | 224 min | 38 min | 186 min | DONE |
| FOLDER-tickets-todos-tag-registry-redesign | 224 min | 0 min | 759 min | DONE |
| TCK-20260721-MONITORING-WRITER-DECISION | 223 min | 6 min | 216 min | DONE |
| TCK-20260811-MULTI-STEP-PLANNING-DESIGN | 211 min | 38 min | 173 min | DONE |
| TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING | 206 min | 43 min | 162 min | DONE |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 204 min | 95 min | 109 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M4-BEYOND-CITY-EPIC | 204 min | 2 min | 202 min | DONE |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 202 min | 41 min | 161 min | DONE |
| TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION | 196 min | 62 min | 134 min | DONE |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | 176 min | 55 min | 121 min | DONE |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 173 min | 48 min | 125 min | DONE |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | 173 min | 64 min | 108 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard-ui-fixes | 173 min | 0 min | 173 min | DONE |
| TCK-20260821-WS-ENTITY-DELTA-BROADCAST | 173 min | 173 min | 0 min | DONE |
| FOLDER-tickets-todos-agent-monitoring-derived-index | 172 min | 0 min | 172 min | DONE |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 171 min | 28 min | 142 min | DONE |
| TCK-20260821-PHASED-LOADING-STATE-MACHINE | 164 min | 124 min | 40 min | DONE |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 163 min | 40 min | 123 min | DONE |
| TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS | 158 min | 101 min | 57 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M1-QUICK-WINS-EPIC | 154 min | 30 min | 124 min | DONE |
| TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE | 153 min | 89 min | 64 min | DONE |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 152 min | 45 min | 107 min | DONE |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 149 min | 0 min | 707 min | DONE |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | 149 min | 76 min | 72 min | DONE |
| TCK-20260831-READINESS-SPEED-FORMULA | 148 min | 44 min | 103 min | DONE |
| TCK-20260718-AGENTOPS-STATS-API | 148 min | 19 min | 129 min | DONE |
| TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE | 148 min | 6 min | 141 min | DONE |
| TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT | 147 min | 0 min | 147 min | DONE |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 147 min | 22 min | 124 min | DONE |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 147 min | 0 min | 147 min | DONE |
| TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING | 146 min | 98 min | 48 min | DONE |
| TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION | 145 min | 60 min | 85 min | DONE |
| TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE | 144 min | 4 min | 139 min | DONE |
| FOLDER-tickets-todos-world-grammar-semantic-constraints | 144 min | 0 min | 144 min | DONE |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 143 min | 54 min | 89 min | DONE |
| TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT | 141 min | 52 min | 88 min | DONE |
| TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE | 140 min | 90 min | 49 min | DONE |
| TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS | 136 min | 7 min | 129 min | DONE |
| TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE | 135 min | 135 min | 0 min | DONE |
| TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT | 131 min | 69 min | 62 min | DONE |
| TCK-20260718-RETRO-STATS-REFACTOR | 130 min | 10 min | 120 min | DONE |
| FOLDER-tickets-todos-context-retrieval-phase4 | 130 min | 22 min | 107 min | DONE |
| FOLDER-tickets-todos-agent-ops-dashboard | 127 min | 0 min | 254 min | DONE |
| TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS | 127 min | 127 min | 0 min | DONE |
| FOLDER-tickets-todos-context-efficient-retrieval | 126 min | 12 min | 114 min | EPIC_SCOPED |
| FOLDER-tickets-todos-simq-scoring-improvement | 124 min | 0 min | 874 min | DONE |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 123 min | 123 min | 0 min | DONE |
| TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE | 122 min | 76 min | 46 min | DONE |
| TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE | 121 min | 61 min | 59 min | DONE |
| TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER | 121 min | 50 min | 71 min | DONE |
| TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE | 120 min | 120 min | 0 min | DONE |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | 119 min | 62 min | 57 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | 119 min | 39 min | 80 min | DONE |
| TCK-20260816-KGMCP-P4-PARITY-ADAPTER | 115 min | 73 min | 42 min | DONE |
| TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE | 115 min | 80 min | 35 min | DONE |
| TCK-20260809-COMBAT-ACTIONSTYLE-WIRING | 115 min | 50 min | 65 min | DONE |
| TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND | 112 min | 51 min | 60 min | DONE |
| TCK-20260903-CLAN-LIFECYCLE-SUCCESSION | 111 min | 0 min | 111 min | DONE |
| TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION | 110 min | 55 min | 55 min | DONE |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | 109 min | 12 min | 96 min | DONE |
| TCK-20260721-ORCHESTRATION-CONTRACT-CORE | 109 min | 36 min | 73 min | DONE |
| TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE | 107 min | 68 min | 38 min | DONE |
| TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT | 106 min | 106 min | 0 min | DONE |
| TCK-20260702-OBSISO-ISOLATION-PROOF | 106 min | 52 min | 54 min | DONE |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 106 min | 62 min | 43 min | DONE |
| TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY | 105 min | 45 min | 60 min | DONE |
| FOLDER-tickets-todos-placement-legality | 104 min | 0 min | 104 min | DONE |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 104 min | 104 min | 0 min | DONE |
| TCK-20260831-ITEM-INSTANCE-HISTORY | 103 min | 53 min | 49 min | DONE |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 103 min | 103 min | 0 min | DONE |
| TCK-20260717-GANTT-TIME-AXIS | 103 min | 27 min | 75 min | DONE |
| TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING | 102 min | 60 min | 41 min | DONE |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | 102 min | 68 min | 33 min | DONE |
| TCK-20260823-HTTP-API-KEY-AUTH | 101 min | 60 min | 41 min | DONE |
| TCK-20260812-COMMITTED-INTENTION-SEQUENCE | 100 min | 52 min | 48 min | DONE |
| TCK-20260903-ECONOMIC-VACANCY-SIGNAL | 99 min | 0 min | 99 min | DONE |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 98 min | 0 min | 98 min | DONE |
| FOLDER-tickets-todos-simq-roadmap-phase1-process-hardening | 98 min | 0 min | 98 min | DONE |
| TCK-20260824-WIRE-ORPHANED-MECHANISMS | 98 min | 50 min | 47 min | DONE |
| TCK-20260831-POPULATION-COHORT-SEEDING | 97 min | 59 min | 38 min | DONE |
| TCK-20260729-HYBRID-RETRIEVAL-FUSION | 95 min | 65 min | 30 min | DONE |
| TCK-20260702-OBSISO-TRACE-ASYNC | 95 min | 50 min | 44 min | DONE |
| TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION | 95 min | 95 min | 0 min | DONE |
| TCK-20260822-SEMANTIC-ENTITY-INDEX | 94 min | 94 min | 0 min | DONE |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 93 min | 57 min | 35 min | DONE |
| TCK-20260702-OBSISO-BROKER-CONFIG | 93 min | 93 min | 0 min | DONE |
| TCK-20260903-INFORMATION-HUB-ACCUMULATION | 93 min | 0 min | 93 min | DONE |
| TCK-20260721-CODEX-REPLAY-PARITY | 91 min | 13 min | 78 min | DONE |
| TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING | 90 min | 55 min | 34 min | DONE |
| TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE | 90 min | 60 min | 30 min | DONE |
| TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE | 90 min | 15 min | 75 min | DONE |
| TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING | 90 min | 0 min | 90 min | DONE |
| FOLDER-tickets-todos-epic-scope-orphan-cleanup | 89 min | 0 min | 89 min | DONE |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | 89 min | 15 min | 73 min | DONE |
| TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL | 89 min | 53 min | 36 min | DONE |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 89 min | 0 min | 89 min | DONE |
| TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE | 89 min | 37 min | 51 min | DONE |
| TCK-20260804-SKILL-DRIFT-DETECTION | 89 min | 89 min | 0 min | DONE |
| TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC | 88 min | 55 min | 33 min | DONE |
| TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET | 88 min | 26 min | 62 min | DONE |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 88 min | 50 min | 37 min | DONE |
| TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING | 88 min | 88 min | 0 min | DONE |
| TCK-20260902-WORLDCOMPILER-PLACE-WIRING | 88 min | 0 min | 88 min | DONE |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 88 min | 56 min | 31 min | DONE |
| TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET | 87 min | 87 min | 0 min | DONE |
| TCK-20260720-TAG-TOUCHPOINT-CLEANUP | 87 min | 87 min | 0 min | DONE |
| TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD | 86 min | 0 min | 338 min | DONE |
| TCK-20260902-PARITY-TEST-PATH-GAP | 86 min | 41 min | 45 min | DONE |
| TCK-20260718-STATS-TAB-FRONTEND | 86 min | 48 min | 38 min | DONE |
| TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC | 86 min | 86 min | 0 min | DONE |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 85 min | 0 min | 85 min | DONE |
| TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY | 85 min | 55 min | 30 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-PROGRESS-TIMELINE | 84 min | 2 min | 81 min | DONE |
| TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY | 83 min | 83 min | 0 min | DONE |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 83 min | 0 min | 83 min | DONE |
| TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER | 82 min | 82 min | 0 min | DONE |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 81 min | 26 min | 55 min | DONE |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 81 min | 81 min | 0 min | DONE |
| TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT | 81 min | 43 min | 37 min | DONE |
| TCK-20260728-EVAL-FIXTURE-REPAIR | 80 min | 46 min | 33 min | DOD_BLOCKED |
| TCK-20260905-CHRONICLE-FIDELITY-DRIFT | 79 min | 0 min | 79 min | DONE |
| TCK-20260730-CODEX-POSTTOOL-ADAPTER | 79 min | 37 min | 41 min | DONE |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 78 min | 78 min | 0 min | DONE |
| TCK-20260801-CODEX-LIVE-TRANSPORT | 78 min | 48 min | 30 min | DONE |
| TCK-20260730-CLAUDE-EXECUTION-IDENTITY | 78 min | 78 min | 0 min | DONE |
| TCK-20260718-GLOSSARY-TOOLTIPS-EPIC | 78 min | 0 min | 78 min | DONE |
| TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT | 77 min | 77 min | 0 min | DONE |
| TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD | 76 min | 76 min | 0 min | DONE |
| FOLDER-tickets-todos-simq-pillar-lifecycle-depth | 76 min | 76 min | 0 min | DONE |
| TCK-20260716-AGENTOPS-REPLAY-TIMELINE | 75 min | 31 min | 44 min | DONE |
| TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD | 75 min | 0 min | 75 min | DONE |
| TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON | 75 min | 0 min | 75 min | DONE |
| TCK-20260824-LIFE-STAGE-TRANSITIONS | 74 min | 37 min | 37 min | DONE |
| TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION | 74 min | 35 min | 39 min | DONE |
| TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP | 74 min | 0 min | 74 min | DONE |
| TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS | 73 min | 18 min | 55 min | DONE |
| TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS | 72 min | 72 min | 0 min | DONE |
| TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION | 72 min | 72 min | 0 min | DONE |
| TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING | 71 min | 71 min | 0 min | DONE |
| EPIC-TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC | 70 min | 70 min | 0 min | DONE |
| SIMQ-AUDIT-20260811T111151Z | 70 min | 5 min | 64 min | ANCHORS_STILL_FAILING |
| TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL | 70 min | 70 min | 0 min | DONE |
| TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT | 70 min | 0 min | 105 min | DONE |
| TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER | 70 min | 5 min | 65 min | BLOCKED |
| TCK-20260815-KGMCP-P1-FAILOPEN-TESTS | 69 min | 69 min | 0 min | DONE |
| TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC | 69 min | 69 min | 0 min | DONE |
| TCK-20260720-SKILL-MAPPING-DEDUP | 68 min | 68 min | 0 min | DONE |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 67 min | 67 min | 0 min | DONE |
| CREATE-TICKETS-AI-FIRST-HARDENING-EPICS | 67 min | 0 min | 67 min | DONE |
| TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON | 67 min | 67 min | 0 min | DONE |
| TCK-20260810-SKILL-USAGE-RETRO-TRACKING | 67 min | 67 min | 0 min | DONE |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 66 min | 66 min | 0 min | DONE |
| TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY | 66 min | 7 min | 59 min | DONE |
| TCK-20260824-ALLOCATE-AP-BRANCH-DECISION | 65 min | 65 min | 0 min | DONE |
| TCK-20260821-WORLD-RENDER-CORE | 65 min | 29 min | 35 min | DONE |
| TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR | 65 min | 65 min | 0 min | DONE |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 65 min | 30 min | 34 min | DONE |
| TCK-20260802-DOC-UPDATE-DISCIPLINE | 65 min | 65 min | 0 min | DONE |
| TCK-20260831-ROLE-MODEL-IMITATION | 65 min | 65 min | 0 min | DONE |
| TCK-20260821-REST-MAP-STATIC-STATS | 65 min | 65 min | 0 min | DONE |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 64 min | 64 min | 0 min | DONE |
| TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION | 64 min | 64 min | 0 min | DONE |
| TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION | 63 min | 63 min | 0 min | DONE |
| TCK-20260826-PARITY-FACTION-CANONICAL-SCAN | 63 min | 63 min | 0 min | DONE |
| TCK-20260824-AFFECTION-CONTRACT-GATE | 63 min | 63 min | 0 min | DOD_BLOCKED |
| TCK-20260720-TAG-RELEVANCE-VERIFY | 63 min | 63 min | 0 min | DONE |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 63 min | 63 min | 0 min | DONE |
| TCK-20260731-PARITY-READPATH-GATE | 62 min | 62 min | 0 min | DONE |
| TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING | 62 min | 62 min | 0 min | DONE |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 62 min | 30 min | 31 min | DONE |
| TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE | 62 min | 62 min | 0 min | DONE |
| FOLDER-tickets-todos-context-retrieval-phase2 | 61 min | 61 min | 0 min | DONE |
| TCK-20260718-STATUS-DRIFT-REPAIR | 61 min | 61 min | 0 min | DONE |
| TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH | 60 min | 60 min | 0 min | DONE |
| TCK-20260729-DETERMINISTIC-CODE-INDEX | 60 min | 60 min | 0 min | DONE |
| TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING | 60 min | 60 min | 0 min | DONE |
| TCK-20260831-TRUST-GATED-TEACHING | 60 min | 60 min | 0 min | DONE |
| TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING | 60 min | 60 min | 0 min | DONE |
| TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION | 60 min | 60 min | 0 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-SIMQ-SCORING-IMPROVEMENT-ROADMAP | 60 min | 60 min | 0 min | DONE |
| TCK-20260731-PARITY-INDEX-IMPORTER | 60 min | 0 min | 1659 min | DONE |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 60 min | 60 min | 0 min | DONE |
| EPIC-TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE5-EPIC | 60 min | 2 min | 57 min | DONE |
| TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP | 60 min | 30 min | 30 min | DONE |
| TCK-20260904-SPECIES-CORE-SCHEMA-RENAME | 60 min | 15 min | 45 min | DONE |
| TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY | 59 min | 13 min | 46 min | DONE |
| TCK-20260831-HABIT-BIAS-WIRING | 59 min | 59 min | 0 min | DONE |
| TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY | 59 min | 59 min | 0 min | DONE |
| SIMQ-AUDIT-20260807T142932Z | 59 min | 59 min | 0 min | DONE_NO_TICKET |
| TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP | 59 min | 59 min | 0 min | DONE |
| TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT | 59 min | 59 min | 0 min | DONE |
| TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY | 59 min | 59 min | 0 min | DONE |
| TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY | 58 min | 58 min | 0 min | DONE |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 58 min | 58 min | 0 min | DONE |
| TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD | 58 min | 58 min | 0 min | DONE |
| TCK-20260825-LIVE-VERIFICATION-TOOLING | 58 min | 18 min | 40 min | DONE |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 57 min | 0 min | 323 min | DOD_BLOCKED |
| TCK-20260806-PUSH-CUTOVER-PHASE2 | 57 min | 57 min | 0 min | DONE |
| TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT | 57 min | 57 min | 0 min | DONE |
| TCK-20260821-VISUAL-AGENT-REVIEW | 57 min | 57 min | 0 min | DONE |
| TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW | 57 min | 10 min | 47 min | DONE |
| TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING | 57 min | 57 min | 0 min | DONE |
| TCK-20260720-ECHARTS-PHASE-PALETTE | 57 min | 57 min | 0 min | DONE |
| TCK-20260902-ASPECT-TERM-CLEANUP | 56 min | 56 min | 0 min | DONE |
| TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION | 55 min | 55 min | 0 min | DONE |
| TCK-20260806-PUSH-SHADOW-VALIDATION-PERF | 55 min | 20 min | 34 min | DONE |
| TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF | 55 min | 55 min | 0 min | DONE |
| TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES | 55 min | 55 min | 0 min | DONE |
| TCK-20260906-CI-FRONTEND-PATH-FILTER | 55 min | 0 min | 417 min | DONE |
| TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION | 54 min | 54 min | 0 min | DONE |
| TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC | 54 min | 54 min | 0 min | DONE |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 54 min | 54 min | 0 min | DONE |
| TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT | 54 min | 0 min | 54 min | DONE |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 54 min | 54 min | 0 min | DONE |
| TCK-20260815-KGMCP-P1-BASELINE-COMPARISON | 54 min | 54 min | 0 min | DONE |
| TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS | 54 min | 54 min | 0 min | DONE |
| TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP | 54 min | 54 min | 0 min | DONE |
| TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE | 53 min | 53 min | 0 min | DONE |
| TCK-20260831-SPECIES-INTELLIGENCE-TIER | 53 min | 53 min | 0 min | DONE |
| TCK-20260730-PROVIDER-HOOK-POLICY | 53 min | 53 min | 0 min | DONE |
| TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC | 53 min | 53 min | 0 min | DONE |
| TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET | 52 min | 0 min | 52 min | DONE |
| TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE | 52 min | 20 min | 32 min | DONE |
| TCK-20260710-EPIC-STALENESS-CHECK | 52 min | 52 min | 0 min | DONE |
| TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE | 52 min | 52 min | 0 min | DONE |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 51 min | 51 min | 0 min | DONE |
| TCK-20260814-KGMCP-MEASUREMENT-BASELINE | 51 min | 0 min | 421 min | DONE |
| TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS | 51 min | 51 min | 0 min | DONE |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 51 min | 51 min | 0 min | DONE |
| TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC | 51 min | 51 min | 0 min | DONE |
| TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS | 51 min | 51 min | 0 min | DONE |
| TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT | 51 min | 51 min | 0 min | DONE |
| TCK-20260819-SKILL-STALENESS-SOFT-WARNING | 51 min | 51 min | 0 min | DONE |
| TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP | 51 min | 51 min | 0 min | DONE |
| TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY | 50 min | 50 min | 0 min | DONE |
| TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC | 50 min | 50 min | 0 min | DONE |
| TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION | 50 min | 50 min | 0 min | DONE |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | 50 min | 50 min | 0 min | DONE |
| TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS | 50 min | 50 min | 0 min | DONE |
| TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP | 50 min | 50 min | 0 min | DONE |
| TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP | 50 min | 0 min | 50 min | DONE |
| TCK-20260814-KGMCP-CONTRACT-SCHEMAS | 49 min | 49 min | 0 min | DONE |
| TCK-20260716-PLACELEGAL-HARDLAW | 49 min | 49 min | 0 min | DONE |
| TCK-20260815-KGMCP-P1-QUERY-ROUTER | 49 min | 49 min | 0 min | DONE |
| TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT | 49 min | 0 min | 49 min | DONE |
| TCK-20260824-TACTICAL-WOUND-SCAR-WIRING | 48 min | 48 min | 0 min | DONE |
| TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON | 48 min | 48 min | 0 min | DONE |
| TCK-20260831-CAPABILITY-DRIVEN-TARGETING | 48 min | 48 min | 0 min | DONE |
| TCK-20260831-CREATURE-TERRITORY-LIFECYCLE | 48 min | 48 min | 0 min | DONE |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 48 min | 48 min | 0 min | DONE |
| TCK-20260727-CODEX-SKILL-COMPANION-ASSETS | 48 min | 14 min | 33 min | DONE |
| TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC | 48 min | 48 min | 0 min | DONE |
| TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE | 47 min | 47 min | 0 min | DONE |
| TCK-20260721-CODEX-REPLAY-PROOF | 47 min | 16 min | 31 min | DONE |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | 47 min | 47 min | 0 min | DOD_BLOCKED |
| TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION | 47 min | 47 min | 0 min | DONE |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 47 min | 47 min | 0 min | DONE |
| TCK-20260711-EPIC-SCOPE-ORPHAN-FIX | 47 min | 47 min | 0 min | DONE |
| TCK-20260810-STATUS-DRIFT-CHECK-WIRING | 46 min | 46 min | 0 min | DONE |
| TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR | 46 min | 46 min | 0 min | DONE |
| TCK-20260729-RETRIEVAL-RETRO-VIEWS | 46 min | 46 min | 0 min | DONE |
| TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION | 45 min | 45 min | 0 min | DONE |
| TCK-20260804-SKILL-JS-PHASE-SYNC | 45 min | 45 min | 0 min | DONE |
| TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP | 45 min | 45 min | 0 min | DONE |
| TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION | 45 min | 45 min | 0 min | DONE |
| TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP | 45 min | 0 min | 45 min | DONE |
| TCK-20260710-FEATURE-FLAGS-GUIDE | 44 min | 44 min | 0 min | DONE |
| TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT | 44 min | 44 min | 0 min | DONE |
| TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG | 43 min | 43 min | 0 min | DONE |
| TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION | 43 min | 43 min | 0 min | DONE |
| TCK-20260821-VISUAL-GRADE-SCORER | 43 min | 43 min | 0 min | DONE |
| TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES | 43 min | 43 min | 0 min | DONE |
| TCK-20260824-DEFAULT-HEIR-ASSIGNMENT | 43 min | 43 min | 0 min | DONE |
| TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER | 43 min | 43 min | 0 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-LIVE-MAP-RECONNECTION-EPIC | 42 min | 42 min | 0 min | DONE |
| TCK-20260831-CLASS-TIER-BRANCHING | 42 min | 42 min | 0 min | DONE |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | 42 min | 42 min | 0 min | DONE |
| TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP | 42 min | 42 min | 0 min | DONE |
| TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS | 42 min | 0 min | 419 min | DONE |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 41 min | 41 min | 0 min | DONE |
| TCK-20260821-VISUAL-QUALITY-CALIBRATION | 41 min | 41 min | 0 min | DONE |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 41 min | 0 min | 140 min | DONE |
| TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG | 41 min | 41 min | 0 min | DONE |
| TCK-20260824-WOUND-THRESHOLD-DECISION | 41 min | 41 min | 0 min | DONE |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 41 min | 41 min | 0 min | DONE |
| TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH | 41 min | 41 min | 0 min | DONE |
| TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP | 41 min | 3 min | 37 min | DONE |
| TCK-20260823-LIVE-TEST-API-KEY-AUTH | 40 min | 40 min | 0 min | DONE |
| TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX | 40 min | 40 min | 0 min | DONE |
| TCK-20260824-RETRO-METRIC-CAVEATS | 40 min | 5 min | 35 min | DONE |
| TCK-20260718-STATUS-SUFFIX-TRIM | 40 min | 40 min | 0 min | DONE |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 40 min | 40 min | 0 min | DONE |
| TCK-20260805-SKILL-GATE-CONVERSION-DECISION | 40 min | 40 min | 0 min | DONE |
| TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED | 40 min | 40 min | 0 min | DONE |
| TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG | 40 min | 40 min | 0 min | DONE |
| TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD | 40 min | 0 min | 40 min | DONE |
| TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION | 40 min | 0 min | 40 min | DONE |
| TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING | 40 min | 40 min | 0 min | DONE |
| TCK-20260818-STANDARD-DASHBOARD-STATS-TABLES-SEARCH-SORT-PAGE | 40 min | 0 min | 40 min | DONE |
| TCK-20260731-PARITY-IMPACT-PROOF | 39 min | 39 min | 0 min | DONE |
| TCK-20260824-WOUND-HEALING-DECISION | 39 min | 6 min | 32 min | NEEDS_HUMAN_INPUT |
| TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM | 39 min | 39 min | 0 min | DONE |
| TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION | 39 min | 3 min | 35 min | DONE |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 39 min | 39 min | 0 min | DONE |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 39 min | 0 min | 39 min | DONE |
| TCK-20260731-CODEX-EXECUTION-IDENTITY-TAG-SWEEP | 38 min | 38 min | 0 min | DONE |
| TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE | 38 min | 38 min | 0 min | DONE |
| TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION | 38 min | 38 min | 0 min | DONE |
| CREATE-TICKETS-DOCS-PLANS-WORLD-GENERATION-ORGANIC-TERRAIN-EPIC | 38 min | 38 min | 0 min | DONE |
| TCK-20260821-VISUAL-QUALITY-DOCS | 38 min | 38 min | 0 min | DONE |
| TCK-20260729-SHADOW-PACKET-CALL-SITE | 38 min | 0 min | 140 min | DONE |
| TCK-20260805-PROGRESSION-ENTITIES-SKILL | 38 min | 38 min | 0 min | DONE |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 37 min | 37 min | 0 min | DONE |
| TCK-20260720-TAG-CATEGORY-REGISTRY | 37 min | 37 min | 0 min | DONE |
| TCK-20260822-PAID-INFO-INDEX-RETROFIT | 37 min | 37 min | 0 min | DONE |
| TCK-20260821-VISUAL-SHAPE-METRIC | 37 min | 37 min | 0 min | DONE |
| TCK-20260821-VISUAL-VARIANTS-METRIC | 36 min | 36 min | 0 min | DONE |
| TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION | 36 min | 36 min | 0 min | DONE |
| TCK-20260824-WOUND-HEALING-DECISION | 36 min | 4 min | 32 min | DONE |
| TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK | 36 min | 36 min | 0 min | DONE |
| TCK-20260823-CI-STEP-SUMMARY-REPORTING | 36 min | 0 min | 102 min | DONE |
| TCK-20260802-CONTEXT-KIND-PRIORITY | 36 min | 36 min | 0 min | DONE |
| TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION | 36 min | 36 min | 0 min | DONE |
| TCK-20260729-RETRIEVAL-CACHE-LEVELS | 35 min | 35 min | 0 min | DONE |
| TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE | 35 min | 35 min | 0 min | DONE |
| TCK-20260717-TICKETS-TAG-SEARCH | 35 min | 35 min | 0 min | DONE |
| TCK-20260802-EXACT-LOOKUP-CONVENTION | 35 min | 35 min | 0 min | DONE |
| TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION | 35 min | 35 min | 0 min | DONE |
| TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY | 35 min | 35 min | 0 min | DONE |
| TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY | 35 min | 35 min | 0 min | DONE |
| TCK-20260805-SECURITY-GATE-FIRING-MONITOR | 35 min | 35 min | 0 min | DONE |
| TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT | 35 min | 0 min | 104 min | DONE |
| TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION | 35 min | 35 min | 0 min | DONE |
| TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP | 35 min | 35 min | 0 min | DONE |
| TCK-20260807-QUEST-EVENT-PUSH-MIGRATION | 35 min | 35 min | 0 min | DONE |
| TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS | 35 min | 35 min | 0 min | DONE |
| TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY | 35 min | 35 min | 0 min | DONE |
| TCK-20260817-STANDARD-SIMQ-NARRATIVE-ANCHOR-RECALIBRATION-FRONTIER-BATCH | 35 min | 0 min | 35 min | DONE |
| TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE | 35 min | 0 min | 35 min | DONE |
| TCK-20260825-METADATA-API-BACKEND-MISSING | 35 min | 0 min | 211 min | DONE |
| TCK-20260821-VISUAL-CONNECTIVITY-METRIC | 34 min | 34 min | 0 min | DONE |
| TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX | 34 min | 34 min | 0 min | DONE |
| TCK-20260729-SHADOW-BASELINE-COMPARISON | 34 min | 34 min | 0 min | DONE |
| TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP | 33 min | 33 min | 0 min | DONE |
| TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION | 33 min | 33 min | 0 min | DONE |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 33 min | 0 min | 280 min | TESTS_FAILED |
| TCK-20260902-HARVEST-LOOT-TEST-COVERAGE | 33 min | 33 min | 0 min | DONE |
| TCK-20260805-OBSERVABILITY-SKILL | 33 min | 33 min | 0 min | DONE |
| TCK-20260805-SIMQ-DEV-SKILL | 33 min | 33 min | 0 min | DONE |
| TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION | 33 min | 33 min | 0 min | DONE |
| TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE | 32 min | 32 min | 0 min | DONE |
| TCK-20260729-CONTEXT-PACKET-ASSEMBLY | 32 min | 32 min | 0 min | DONE |
| TCK-20260720-TAG-CORPUS-REPAIR-SWEEP | 32 min | 32 min | 0 min | DONE |
| TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION | 32 min | 32 min | 0 min | DONE |
| TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK | 32 min | 32 min | 0 min | DONE |
| TCK-20260713-MONITORING-SQLITE-INDEX | 31 min | 31 min | 0 min | DONE |
| TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT | 31 min | 31 min | 0 min | DONE |
| TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK | 31 min | 0 min | 31 min | DONE |
| TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND | 31 min | 0 min | 31 min | DONE |
| TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE | 31 min | 31 min | 0 min | DONE |
| TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION | 31 min | 31 min | 0 min | DONE |
| TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ | 31 min | 31 min | 0 min | DONE |
| TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE | 31 min | 31 min | 0 min | DONE |
| SIMQ-AUDIT-20260810T032558Z | 31 min | 31 min | 0 min | NEEDS_TICKET |
| TCK-20260731-PARITY-INDEX-BASELINE | 31 min | 0 min | 3017 min | DONE |
| TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH | 31 min | 31 min | 0 min | DONE |
| TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX | 31 min | 31 min | 0 min | DONE |
| TCK-20260809-STALE-DOCS-AI-BRAIN-ARCHITECTURE-AUDIT | 31 min | 31 min | 0 min | DONE |
| TCK-20260721-BASELINE-MONITORING-MANIFEST | 30 min | 30 min | 0 min | DONE |
| TCK-20260728-RETRIEVAL-BASELINE-METRICS | 30 min | 30 min | 0 min | DONE |
| TCK-20260809-MONITORING-ZERO-DURATION-COMBAT-RUNS-HOTFIX | 30 min | 0 min | 30 min | DONE |

_203 of the runs above spend at least half their reported duration idle (gaps ≥ 30 min between phase transitions, e.g. waiting on human review) rather than in active work — see `active`/`idle` columns; "slow" here does not mean "took a long time to actively work on."_

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Duration outliers (by tier)

| run_id | tier | duration_s | tier median | ratio | active | idle |
|---|---|---|---|---|---|---|
| TCK-20260702-OBSISO-EPIC | epic | 2884452 | 7611 | 379.0x | 0 min | 48074 min |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M3-FAMILY-SPECIES-EPIC | n/a | 199620 | 898 | 222.3x | 0 min | 3327 min |
| TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC | epic | 641310 | 7611 | 84.3x | 0 min | 10688 min |
| TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE | hotfix | 28259 | 677 | 41.7x | 5 min | 465 min |
| TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG | hotfix | 23963 | 677 | 35.4x | 0 min | 399 min |
| FOLDER-tickets-todos-ai-first-hardening-h1-h2-followon | epic | 230499 | 7611 | 30.3x | 0 min | 3841 min |
| TCK-20260912-WORKING-LOG-APPEND-HELPER | standard | 65164 | 2182 | 29.9x | 0 min | 1337 min |
| TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE | standard | 60960 | 2182 | 27.9x | 0 min | 1015 min |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | standard | 58672 | 2182 | 26.9x | 0 min | 977 min |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | standard | 49729 | 2182 | 22.8x | 15 min | 813 min |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | standard | 49716 | 2182 | 22.8x | 91 min | 737 min |
| TCK-20260825-HOTFIX-EXEC-IDENTITY-TEST-SIDECAR-STALENESS | hotfix | 15137 | 677 | 22.4x | 0 min | 252 min |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | standard | 45628 | 2182 | 20.9x | 31 min | 728 min |
| TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP | standard | 37834 | 2182 | 17.3x | 51 min | 578 min |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36832 | 2182 | 16.9x | 42 min | 571 min |
| TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP | standard | 35107 | 2182 | 16.1x | 8 min | 576 min |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | standard | 34806 | 2182 | 16.0x | 14 min | 565 min |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | standard | 34600 | 2182 | 15.9x | 37 min | 539 min |
| TCK-20260904-INHERITED-REPUTATION-SEED | standard | 34172 | 2182 | 15.7x | 1 min | 568 min |
| FOLDER-tickets-todos-adventure-cognition-merge | epic | 114727 | 7611 | 15.1x | 0 min | 1911 min |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | standard | 32485 | 2182 | 14.9x | 0 min | 707 min |
| EPIC-TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC | epic | 108078 | 7611 | 14.2x | 0 min | 1801 min |
| TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD | standard | 30000 | 2182 | 13.7x | 60 min | 440 min |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M4-BEYOND-CITY-EPIC | n/a | 12280 | 898 | 13.7x | 2 min | 202 min |
| TCK-20260824-ROLLOUT-FLAG-DECISIONS | standard | 29694 | 2182 | 13.6x | 19 min | 479 min |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | standard | 29073 | 2182 | 13.3x | 60 min | 424 min |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | standard | 28991 | 2182 | 13.3x | 55 min | 427 min |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | standard | 28516 | 2182 | 13.1x | 27 min | 447 min |
| TCK-20260717-CSS-LAYER-PADDING-FIX | hotfix | 8827 | 677 | 13.0x | 22 min | 124 min |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | standard | 27777 | 2182 | 12.7x | 0 min | 462 min |
| TCK-20260801-CODEX-REALREPO-PILOT-HARNESS | standard | 26413 | 2182 | 12.1x | 15 min | 425 min |
| TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS | hotfix | 8185 | 677 | 12.1x | 7 min | 129 min |
| TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP | standard | 26088 | 2182 | 12.0x | 51 min | 383 min |
| TCK-20260719-TAG-COLLISION-DEDUP | standard | 25786 | 2182 | 11.8x | 9 min | 420 min |
| TCK-20260720-PROGRESS-TIMELINE-VIEW | standard | 25634 | 2182 | 11.7x | 77 min | 350 min |
| FOLDER-cognition-adventure-eligibility | standard | 25009 | 2182 | 11.5x | 0 min | 416 min |
| TCK-20260822-GUARD-SCAN-INDEX-RETROFIT | standard | 24039 | 2182 | 11.0x | 35 min | 365 min |
| TCK-20260811-REGION-STABILIZATION-GOAL-SCORER | standard | 23794 | 2182 | 10.9x | 75 min | 320 min |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | standard | 23793 | 2182 | 10.9x | 64 min | 331 min |
| TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP | standard | 23400 | 2182 | 10.7x | 28 min | 362 min |
| TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE | standard | 23162 | 2182 | 10.6x | 0 min | 904 min |
| TCK-20260902-PLACE-MIGRATION-RECALIBRATION | standard | 23100 | 2182 | 10.6x | 0 min | 385 min |
| TCK-20260821-LIVE-MAP-PERF-VALIDATION | standard | 22740 | 2182 | 10.4x | 108 min | 271 min |
| CREATE-TICKETS-DOCS-PLANS-RPG-DESIGN-ROADMAP-RPG-M1-QUICK-WINS-EPIC | n/a | 9289 | 898 | 10.3x | 30 min | 124 min |
| TCK-20260802-STORED-ARTIFACT-KIND | standard | 22385 | 2182 | 10.3x | 27 min | 345 min |
| TCK-20260720-TIMELINE-RANGE-CONTROL | standard | 22182 | 2182 | 10.2x | 59 min | 310 min |
| TCK-20260831-RACE-RELATIONS-MATRIX | standard | 21613 | 2182 | 9.9x | 47 min | 312 min |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | hotfix | 6560 | 677 | 9.7x | 12 min | 96 min |
| FOLDER-tickets-todos-ai-first-hardening-h0-governance-guardrail | epic | 69900 | 7611 | 9.2x | 0 min | 1165 min |
| TCK-20260804-AGENT-DEF-GAP-FIXES | standard | 19762 | 2182 | 9.1x | 149 min | 180 min |
| TCK-20260824-OCCUPATION-CHANGE-TRIGGER | standard | 19745 | 2182 | 9.0x | 60 min | 268 min |
| TCK-20260721-MONITORING-WRITER-UNIFICATION | standard | 19540 | 2182 | 9.0x | 28 min | 297 min |
| TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | standard | 18867 | 2182 | 8.6x | 75 min | 238 min |
| TCK-20260731-CODEX-PILOT-EXECUTOR | standard | 17701 | 2182 | 8.1x | 0 min | 295 min |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-STATS-BOARD | n/a | 7189 | 898 | 8.0x | 39 min | 80 min |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | hotfix | 5381 | 677 | 7.9x | 15 min | 73 min |
| TCK-20260804-EXPANSION-RATE-WIRING | standard | 17081 | 2182 | 7.8x | 89 min | 195 min |
| TCK-20260730-CODEX-RUNTIME-SHADOW | standard | 16974 | 2182 | 7.8x | 35 min | 247 min |
| TCK-20260811-ADVENTURE-GOAL-SCORER | standard | 16005 | 2182 | 7.3x | 105 min | 161 min |
| TCK-20260817-STATE-DESIGN-PRIORITY-ORDER | standard | 15845 | 2182 | 7.3x | 0 min | 396 min |
| TCK-20260710-SIMQ-DEPTH-FACTION | standard | 15661 | 2182 | 7.2x | 22 min | 238 min |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | standard | 14925 | 2182 | 6.8x | 0 min | 983 min |
| TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP | standard | 14911 | 2182 | 6.8x | 86 min | 162 min |
| TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD | hotfix | 4617 | 677 | 6.8x | 76 min | 0 min |
| FOLDER-tickets-todos-simq-scoring-improvement | epic | 50386 | 7611 | 6.6x | 0 min | 1008 min |
| FOLDER-tickets-todos-simq-roadmap-phase2-depth-social | epic | 49832 | 7611 | 6.5x | 0 min | 830 min |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | standard | 14139 | 2182 | 6.5x | 113 min | 122 min |
| TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION | hotfix | 4353 | 677 | 6.4x | 72 min | 0 min |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | standard | 13482 | 2182 | 6.2x | 38 min | 186 min |
| TCK-20260721-MONITORING-WRITER-DECISION | standard | 13426 | 2182 | 6.2x | 6 min | 216 min |
| TCK-20260811-MULTI-STEP-PLANNING-DESIGN | standard | 12676 | 2182 | 5.8x | 38 min | 173 min |
| TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING | standard | 12385 | 2182 | 5.7x | 43 min | 162 min |
| CREATE-TICKETS-DOCS-PLANS-AGENT-OPS-DASHBOARD-PROPOSAL-PROGRESS-TIMELINE | n/a | 5066 | 898 | 5.6x | 2 min | 81 min |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | standard | 12296 | 2182 | 5.6x | 95 min | 109 min |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | standard | 12161 | 2182 | 5.6x | 41 min | 161 min |
| TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE | hotfix | 3721 | 677 | 5.5x | 62 min | 0 min |
| TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION | standard | 11810 | 2182 | 5.4x | 62 min | 134 min |
| TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY | hotfix | 3587 | 677 | 5.3x | 13 min | 46 min |
| TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP | hotfix | 3569 | 677 | 5.3x | 59 min | 0 min |
| TCK-20260820-HOTFIX-PHANTOM-TESTCONTAINERS-DEPENDENCY | hotfix | 3536 | 677 | 5.2x | 58 min | 0 min |
| TCK-20260825-LIVE-VERIFICATION-TOOLING | hotfix | 3480 | 677 | 5.1x | 18 min | 40 min |
| TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW | hotfix | 3436 | 677 | 5.1x | 10 min | 47 min |
| TCK-20260902-ASPECT-TERM-CLEANUP | hotfix | 3406 | 677 | 5.0x | 56 min | 0 min |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | standard | 10587 | 2182 | 4.9x | 55 min | 121 min |
| TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT | hotfix | 3264 | 677 | 4.8x | 0 min | 54 min |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | standard | 10434 | 2182 | 4.8x | 48 min | 125 min |
| TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM | standard | 10411 | 2182 | 4.8x | 64 min | 108 min |
| TCK-20260821-WS-ENTITY-DELTA-BROADCAST | standard | 10390 | 2182 | 4.8x | 173 min | 0 min |
| FOLDER-tickets-todos-progress-timeline | epic | 36205 | 7611 | 4.8x | 0 min | 603 min |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | standard | 10261 | 2182 | 4.7x | 28 min | 142 min |
| TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC | hotfix | 3183 | 677 | 4.7x | 53 min | 0 min |
| TCK-20260821-PHASED-LOADING-STATE-MACHINE | standard | 9840 | 2182 | 4.5x | 124 min | 40 min |
| CREATE-TICKETS-AI-FIRST-HARDENING-EPICS | n/a | 4049 | 898 | 4.5x | 0 min | 67 min |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | standard | 9827 | 2182 | 4.5x | 40 min | 123 min |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | hotfix | 3027 | 677 | 4.5x | 50 min | 0 min |
| TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS | standard | 9530 | 2182 | 4.4x | 101 min | 57 min |
| EPIC-TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC | epic | 32893 | 7611 | 4.3x | 0 min | 548 min |
| TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE | standard | 9237 | 2182 | 4.2x | 89 min | 64 min |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | hotfix | 2849 | 677 | 4.2x | 47 min | 0 min |
| FOLDER-tickets-todos-semantic-entity-index | epic | 31978 | 7611 | 4.2x | 16 min | 516 min |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | standard | 9141 | 2182 | 4.2x | 45 min | 107 min |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | standard | 8978 | 2182 | 4.1x | 0 min | 707 min |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | standard | 8960 | 2182 | 4.1x | 76 min | 72 min |
| TCK-20260831-READINESS-SPEED-FORMULA | standard | 8916 | 2182 | 4.1x | 44 min | 103 min |
| TCK-20260718-AGENTOPS-STATS-API | standard | 8913 | 2182 | 4.1x | 19 min | 129 min |
| TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE | standard | 8889 | 2182 | 4.1x | 6 min | 141 min |
| TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT | standard | 8844 | 2182 | 4.1x | 0 min | 147 min |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | standard | 8826 | 2182 | 4.0x | 0 min | 147 min |
| CREATE-TICKETS-DOCS-PLANS-SIMQ-SCORING-IMPROVEMENT-ROADMAP | n/a | 3626 | 898 | 4.0x | 60 min | 0 min |
| TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING | standard | 8792 | 2182 | 4.0x | 98 min | 48 min |
| TCK-20260804-SKILL-JS-PHASE-SYNC | hotfix | 2702 | 677 | 4.0x | 45 min | 0 min |
| TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION | standard | 8700 | 2182 | 4.0x | 60 min | 85 min |
| TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE | standard | 8660 | 2182 | 4.0x | 4 min | 139 min |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | standard | 8599 | 2182 | 3.9x | 54 min | 89 min |
| TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT | standard | 8478 | 2182 | 3.9x | 52 min | 88 min |
| TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE | standard | 8426 | 2182 | 3.9x | 90 min | 49 min |
| TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES | hotfix | 2589 | 677 | 3.8x | 43 min | 0 min |
| TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC | epic | 28800 | 7611 | 3.8x | 0 min | 480 min |
| EPIC-TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC | epic | 28607 | 7611 | 3.8x | 0 min | 476 min |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | hotfix | 2534 | 677 | 3.7x | 42 min | 0 min |
| TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE | standard | 8109 | 2182 | 3.7x | 135 min | 0 min |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | hotfix | 2505 | 677 | 3.7x | 41 min | 0 min |
| TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG | hotfix | 2471 | 677 | 3.6x | 41 min | 0 min |
| TCK-20260823-LIVE-TEST-API-KEY-AUTH | hotfix | 2459 | 677 | 3.6x | 40 min | 0 min |
| TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX | hotfix | 2457 | 677 | 3.6x | 40 min | 0 min |
| TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT | standard | 7902 | 2182 | 3.6x | 69 min | 62 min |
| TCK-20260824-RETRO-METRIC-CAVEATS | hotfix | 2450 | 677 | 3.6x | 5 min | 35 min |
| TCK-20260718-RETRO-STATS-REFACTOR | standard | 7836 | 2182 | 3.6x | 10 min | 120 min |
| TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS | standard | 7654 | 2182 | 3.5x | 127 min | 0 min |
| FOLDER-tickets-todos-agent-ops-dashboard | epic | 26444 | 7611 | 3.5x | 0 min | 695 min |
| TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM | hotfix | 2352 | 677 | 3.5x | 39 min | 0 min |
| TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION | hotfix | 2351 | 677 | 3.5x | 3 min | 35 min |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | hotfix | 2351 | 677 | 3.5x | 39 min | 0 min |
| FOLDER-tickets-todos-simq-roadmap-phase3-depth-faction-information | epic | 26096 | 7611 | 3.4x | 0 min | 434 min |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | standard | 7395 | 2182 | 3.4x | 123 min | 0 min |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | hotfix | 2278 | 677 | 3.4x | 37 min | 0 min |
| TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE | standard | 7341 | 2182 | 3.4x | 76 min | 46 min |
| TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE | standard | 7294 | 2182 | 3.3x | 61 min | 59 min |
| TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER | standard | 7291 | 2182 | 3.3x | 50 min | 71 min |
| TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE | standard | 7200 | 2182 | 3.3x | 120 min | 0 min |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | standard | 7192 | 2182 | 3.3x | 62 min | 57 min |
| TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK | hotfix | 2195 | 677 | 3.2x | 36 min | 0 min |
| TCK-20260816-KGMCP-P4-PARITY-ADAPTER | standard | 6944 | 2182 | 3.2x | 73 min | 42 min |
| TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE | standard | 6911 | 2182 | 3.2x | 80 min | 35 min |
| TCK-20260809-COMBAT-ACTIONSTYLE-WIRING | standard | 6900 | 2182 | 3.2x | 50 min | 65 min |
| TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND | standard | 6750 | 2182 | 3.1x | 51 min | 60 min |
| TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX | hotfix | 2077 | 677 | 3.1x | 34 min | 0 min |
| TCK-20260903-CLAN-LIFECYCLE-SUCCESSION | standard | 6672 | 2182 | 3.1x | 0 min | 111 min |
| EPIC-TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC | epic | 23030 | 7611 | 3.0x | 0 min | 383 min |
| TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION | standard | 6600 | 2182 | 3.0x | 55 min | 55 min |
| TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP | hotfix | 2037 | 677 | 3.0x | 33 min | 0 min |
| TCK-20260721-ORCHESTRATION-CONTRACT-CORE | standard | 6554 | 2182 | 3.0x | 36 min | 73 min |

_112 of the duration outliers above spend at least half their reported duration idle rather than in active work — see `active`/`idle` columns; a large ratio here does not mean "took unusually long to actively work on."_

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 2 | Implement | implementer | 28601.745 | 10.2 | 2809.0x |
| TCK-20260710-SIMQ-DEPTH-FACTION | 5 | Implement | implementer | 14058.238 | 10.2 | 1380.7x |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | 8 | Test | test-scoper | 4614.366 | 3.6 | 1281.6x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 5 | Implement | implementer | 6415.868 | 10.2 | 630.1x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 7 | Test | test-scoper | 2222.629 | 3.6 | 617.3x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 7 | Test | test-scoper | 2101.762 | 3.6 | 583.7x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 2 | Investigate | investigator | 34837.628 | 63.0 | 553.4x |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | 5 | Implement | implementer | 5392.113 | 10.2 | 529.6x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 5 | Implement | implementer | 4994.127 | 10.2 | 490.5x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 2 | Investigate | investigator | 28601.745 | 63.0 | 454.3x |
| TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES | 8 | Test | test-scoper | 1566.065 | 3.6 | 435.0x |
| TCK-20260902-ASPECT-TERM-CLEANUP | 5 | Test | test-scoper | 1547.051 | 3.6 | 429.7x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 7 | Test | test-scoper | 1478.29 | 3.6 | 410.6x |
| TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE | 8 | Test | test-scoper | 1402.414 | 3.6 | 389.5x |
| TCK-20260831-POPULATION-COHORT-SEEDING | 8 | Test | test-scoper | 1343.054 | 3.6 | 373.0x |
| TCK-20260710-SIMQ-DEPTH-SOCIAL | 5 | Implement | implementer | 3589.04 | 10.2 | 352.5x |
| TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT | 5 | Test | test-scoper | 1262.373 | 3.6 | 350.6x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 6 | Implement | implementer | 3227.086 | 10.2 | 316.9x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 7 | Test | test-scoper | 1099.442 | 3.6 | 305.4x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 5 | Implement | implementer | 3104.991 | 10.2 | 304.9x |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 5 | Test | test-scoper | 1009.152 | 3.6 | 280.3x |
| TCK-20260717-CSS-LAYER-PADDING-FIX | 7 | Test | test-scoper | 957.445 | 3.6 | 265.9x |
| TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC | 4 | Test | test-scoper | 899.635 | 3.6 | 249.9x |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 5 | Test | test-scoper | 897.868 | 3.6 | 249.4x |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 10 | Test | test-scoper | 890.664 | 3.6 | 247.4x |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 8 | Test | test-scoper | 773.48 | 3.6 | 214.8x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 9 | Test | test-scoper | 703.523 | 3.6 | 195.4x |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | 9 | Test | test-scoper | 690.6030000000001 | 3.6 | 191.8x |
| TCK-20260824-ALLOCATE-AP-BRANCH-DECISION | 9 | Test | test-scoper | 662.3530000000001 | 3.6 | 184.0x |
| TCK-20260826-PARITY-FACTION-CANONICAL-SCAN | 8 | Test | test-scoper | 643.742 | 3.6 | 178.8x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 5 | Implement | implementer | 1676.257 | 10.2 | 164.6x |
| TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE | 4 | Test | claude | 554.6370000000001 | 3.6 | 154.0x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 9 | Test | test-scoper | 553.405 | 3.6 | 153.7x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 7 | Test | test-scoper | 547.336 | 3.6 | 152.0x |
| TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC | 4 | Implement | implementer | 1539.798 | 10.2 | 151.2x |
| TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION | 7 | Test | test-scoper | 531.985 | 3.6 | 147.8x |
| TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP | 4 | Implement | implementer | 1450.566 | 10.2 | 142.5x |
| TCK-20260821-NOISE-FILL-SCHEMA | 4 | Implement | implementer | 1394.259 | 10.2 | 136.9x |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 8 | Test | test-scoper | 489.211 | 3.6 | 135.9x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 2 | Investigate | investigator | 8243.029 | 63.0 | 130.9x |
| TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK | 2 | Test | test-scoper | 459.51300000000003 | 3.6 | 127.6x |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | 8 | Test | test-scoper | 456.055 | 3.6 | 126.7x |
| TCK-20260822-SCAN-POLICY-DOC-FIX | 8 | Test | test-scoper | 440.457 | 3.6 | 122.3x |
| TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE | 8 | Test | test-scoper | 426.543 | 3.6 | 118.5x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 10 | Test | test-scoper | 407.92400000000004 | 3.6 | 113.3x |
| TCK-20260720-TAG-TOUCHPOINT-CLEANUP | 8 | Test | test-scoper | 402.391 | 3.6 | 111.8x |
| TCK-20260831-HABIT-BIAS-WIRING | 10 | Test | test-scoper | 385.283 | 3.6 | 107.0x |
| TCK-20260720-TAG-RELEVANCE-VERIFY | 7 | Test | test-scoper | 379.201 | 3.6 | 105.3x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Implement | implementer | 1059.236 | 10.2 | 104.0x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 10 | Implement | implementer | 1054.0149999999999 | 10.2 | 103.5x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 8 | Test | test-scoper | 367.235 | 3.6 | 102.0x |
| TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE | 9 | Test | test-scoper | 357.856 | 3.6 | 99.4x |
| TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX | 3 | Test | claude | 350.51300000000003 | 3.6 | 97.4x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 7 | Test | test-scoper | 347.36 | 3.6 | 96.5x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 7 | Test | test-scoper | 347.264 | 3.6 | 96.4x |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | 6 | Implement | implementer | 944.649 | 10.2 | 92.8x |
| TCK-20260823-CI-STEP-SUMMARY-REPORTING | 11 | Test | test-scoper | 322.669 | 3.6 | 89.6x |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 3 | Test | test-scoper | 311.175 | 3.6 | 86.4x |
| TCK-20260831-CAPABILITY-DRIVEN-TARGETING | 8 | Test | test-scoper | 304.187 | 3.6 | 84.5x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 5 | Implement | implementer | 857.049 | 10.2 | 84.2x |
| TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL | 5 | Implement | claude | 845.559 | 10.2 | 83.0x |
| TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION | 5 | Implement | implementer | 840.549 | 10.2 | 82.6x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 5 | Implement | implementer | 821.265 | 10.2 | 80.7x |
| TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION | 5 | Implement | implementer | 796.2280000000001 | 10.2 | 78.2x |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | 8 | Test | test-scoper | 279.326 | 3.6 | 77.6x |
| TCK-20260824-WIRE-ORPHANED-MECHANISMS | 9 | Test | test-scoper | 278.111 | 3.6 | 77.2x |
| TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE | 5 | Implement | implementer | 763.065 | 10.2 | 74.9x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 7 | Test | test-scoper | 254.593 | 3.6 | 70.7x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 2 | Investigate | investigator | 4360.288 | 63.0 | 69.3x |
| TCK-20260717-GANTT-TIME-AXIS | 2 | Investigate | investigator | 4330.635 | 63.0 | 68.8x |
| TCK-20260728-EVAL-FIXTURE-REPAIR | 5 | Implement | implementer | 694.696 | 10.2 | 68.2x |
| TCK-20260823-LIVE-TEST-API-KEY-AUTH | 9 | Test | test-scoper | 242.702 | 3.6 | 67.4x |
| TCK-20260905-FAME-DERIVER-LEGEND-FACT | 8 | Test | claude | 242.673 | 3.6 | 67.4x |
| TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON | 8 | Test | test-scoper | 239.639 | 3.6 | 66.6x |
| TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT | 5 | Implement | implementer | 668.4110000000001 | 10.2 | 65.6x |
| TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC | 8 | Test | test-scoper | 236.237 | 3.6 | 65.6x |
| TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE | 11 | Test | test-scoper | 231.733 | 3.6 | 64.4x |
| TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION | 5 | Implement | implementer | 650.801 | 10.2 | 63.9x |
| TCK-20260816-KGMCP-P4-PARITY-ADAPTER | 6 | Implement | implementer | 632.9590000000001 | 10.2 | 62.2x |
| TCK-20260821-VISUAL-CONNECTIVITY-METRIC | 4 | Implement | implementer | 625.849 | 10.2 | 61.5x |
| TCK-20260716-AGENTOPS-TICKETS-VIEW | 5 | Implement | implementer | 619.269 | 10.2 | 60.8x |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 9 | Test | test-scoper | 217.81900000000002 | 3.6 | 60.5x |
| TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND | 3 | Implement | implementer | 607.7080000000001 | 10.2 | 59.7x |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | 9 | Architecture-Verify | architecture-reviewer | 3171.214 | 53.9 | 58.9x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 11 | Test | test-scoper | 206.873 | 3.6 | 57.5x |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 8 | Test | test-scoper | 200.573 | 3.6 | 55.7x |
| TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING | 5 | Implement | implementer | 565.566 | 10.2 | 55.5x |
| TCK-20260720-TAG-RELEVANCE-VERIFY | 5 | Implement | implementer | 564.591 | 10.2 | 55.4x |
| TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS | 8 | Test | test-scoper | 198.862 | 3.6 | 55.2x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 7 | Implement | implementer | 559.772 | 10.2 | 55.0x |
| TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED | 4 | Test | test-scoper | 197.766 | 3.6 | 54.9x |
| TCK-20260831-CREATURE-TERRITORY-LIFECYCLE | 8 | Test | test-scoper | 195.767 | 3.6 | 54.4x |
| TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | 8 | Test | test-scoper | 195.744 | 3.6 | 54.4x |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | 4 | Implement | implementer | 552.434 | 10.2 | 54.3x |
| TCK-20260815-KGMCP-P1-BASELINE-COMPARISON | 8 | Test | test-scoper | 194.86 | 3.6 | 54.1x |
| TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | 4 | Implement | implementer | 550.8340000000001 | 10.2 | 54.1x |
| TCK-20260710-SIMQ-DEPTH-INFORMATION | 5 | Implement | implementer | 546.789 | 10.2 | 53.7x |
| TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC | 7 | Test | test-scoper | 190.599 | 3.6 | 52.9x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 5 | Implement | implementer | 528.578 | 10.2 | 51.9x |
| TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX | 3 | Test | claude | 184.498 | 3.6 | 51.2x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 7 | Test | test-scoper | 183.068 | 3.6 | 50.8x |
| TCK-20260717-TICKETS-TAG-SEARCH | 7 | Test | test-scoper | 181.619 | 3.6 | 50.4x |
| TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD | 13 | Test | test-scoper | 179.39100000000002 | 3.6 | 49.8x |
| TCK-20260824-WIRE-ORPHANED-MECHANISMS | 6 | Implement | implementer | 505.486 | 10.2 | 49.6x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 6 | Implement | implementer | 504.101 | 10.2 | 49.5x |
| TCK-20260902-PARITY-TEST-PATH-GAP | 8 | Test | test-scoper | 177.913 | 3.6 | 49.4x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 6 | Implement | implementer | 500.89 | 10.2 | 49.2x |
| TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING | 9 | Test | test-scoper | 175.897 | 3.6 | 48.9x |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 5 | Implement | implementer | 495.92 | 10.2 | 48.7x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 6 | Implement | implementer | 495.392 | 10.2 | 48.7x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 8 | Test | test-scoper | 174.803 | 3.6 | 48.5x |
| TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT | 8 | Test | test-scoper | 171.892 | 3.6 | 47.7x |
| TCK-20260824-HOTFIX-GHA-NODE20-DEPRECATION-BUMP | 8 | Test | test-scoper | 170.349 | 3.6 | 47.3x |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 5 | Implement | implementer | 478.353 | 10.2 | 47.0x |
| TCK-20260824-OCCUPATION-CHANGE-TRIGGER | 8 | Test | test-scoper | 167.538 | 3.6 | 46.5x |
| TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS | 7 | Implement | implementer | 472.934 | 10.2 | 46.4x |
| TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL | 7 | Test | claude | 166.886 | 3.6 | 46.4x |
| TCK-20260815-KGMCP-P1-FAILOPEN-TESTS | 5 | Implement | implementer | 471.369 | 10.2 | 46.3x |
| TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING | 7 | Test | test-scoper | 164.481 | 3.6 | 45.7x |
| TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL | 6 | Implement | implementer | 461.325 | 10.2 | 45.3x |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 6 | Implement | implementer | 460.449 | 10.2 | 45.2x |
| TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD | 6 | Implement | implementer | 457.979 | 10.2 | 45.0x |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | 10 | Test | test-scoper | 160.836 | 3.6 | 44.7x |
| TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON | 6 | Implement | implementer | 450.051 | 10.2 | 44.2x |
| TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE | 8 | Test | test-scoper | 158.336 | 3.6 | 44.0x |
| TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP | 9 | Test | test-scoper | 158.255 | 3.6 | 44.0x |
| TCK-20260831-ROLE-MODEL-IMITATION | 5 | Implement | implementer | 444.687 | 10.2 | 43.7x |
| TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP | 5 | Implement | implementer | 433.838 | 10.2 | 42.6x |
| TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH | 9 | Test | test-scoper | 153.09 | 3.6 | 42.5x |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 2 | Implement | implementer | 431.76800000000003 | 10.2 | 42.4x |
| TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK | 1 | Implement | implementer | 430.128 | 10.2 | 42.2x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 7 | Test | test-scoper | 151.651 | 3.6 | 42.1x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 7 | Implement | implementer | 428.213 | 10.2 | 42.1x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 6 | Review | architecture-reviewer | 2336.572 | 55.8 | 41.9x |
| TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION | 7 | Test | test-scoper | 149.662 | 3.6 | 41.6x |
| TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC | 10 | Test | test-scoper | 146.977 | 3.6 | 40.8x |
| TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP | 3 | Implement | implementer | 412.552 | 10.2 | 40.5x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 5 | Implement | implementer | 410.161 | 10.2 | 40.3x |
| TCK-20260831-TRUST-GATED-TEACHING | 8 | Test | test-scoper | 142.919 | 3.6 | 39.7x |
| TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP | 2 | Test | test-scoper | 141.554 | 3.6 | 39.3x |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 9 | Test | test-scoper | 141.17700000000002 | 3.6 | 39.2x |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | 11 | Test | test-scoper | 140.71300000000002 | 3.6 | 39.1x |
| TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY | 3 | Test | orchestrator | 139.543 | 3.6 | 38.8x |
| TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING | 8 | Test | test-scoper | 139.036 | 3.6 | 38.6x |
| TCK-20260907-FILTERED-REPLAY-EVAL-PILOT | 10 | Test | test-scoper | 137.136 | 3.6 | 38.1x |
| TCK-20260814-KGMCP-MEASUREMENT-BASELINE | 9 | Test | test-scoper | 135.501 | 3.6 | 37.6x |
| TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE | 15 | Test | test-scoper | 135.476 | 3.6 | 37.6x |
| TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP | 8 | Test | test-scoper | 134.06900000000002 | 3.6 | 37.2x |
| TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT | 8 | Test | test-scoper | 134.063 | 3.6 | 37.2x |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 5 | Implement | implementer | 374.292 | 10.2 | 36.8x |
| TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE | 6 | Implement | implementer | 371.541 | 10.2 | 36.5x |
| TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5 | 6 | Implement | implementer | 370.776 | 10.2 | 36.4x |
| TCK-20260905-CHRONICLE-FIDELITY-DRIFT | 8 | Test | test-scoper | 131.083 | 3.6 | 36.4x |
| TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST | 8 | Test | test-scoper | 128.365 | 3.6 | 35.7x |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 5 | Implement | implementer | 360.303 | 10.2 | 35.4x |
| TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY | 8 | Test | test-scoper | 126.717 | 3.6 | 35.2x |
| TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING | 11 | Test | test-scoper | 126.24000000000001 | 3.6 | 35.1x |
| TCK-20260816-KGMCP-P4-PARITY-ADAPTER | 9 | Test | test-scoper | 125.316 | 3.6 | 34.8x |
| TCK-20260730-CLAUDE-EXECUTION-IDENTITY | 7 | Test | test-scoper | 124.211 | 3.6 | 34.5x |
| TCK-20260831-CLASS-TIER-BRANCHING | 8 | Test | test-scoper | 124.112 | 3.6 | 34.5x |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 7 | Implement | implementer | 350.039 | 10.2 | 34.4x |
| TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE | 5 | Implement | implementer | 349.419 | 10.2 | 34.3x |
| TCK-20260823-HTTP-API-KEY-AUTH | 5 | Implement | implementer | 349.009 | 10.2 | 34.3x |
| TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT | 8 | Test | test-scoper | 123.31700000000001 | 3.6 | 34.2x |
| TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR | 10 | Test | test-scoper | 122.426 | 3.6 | 34.0x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 9 | Test | test-scoper | 122.359 | 3.6 | 34.0x |
| TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP | 8 | Test | test-scoper | 121.892 | 3.6 | 33.9x |
| TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE | 4 | Implement | implementer | 343.65200000000004 | 10.2 | 33.8x |
| TCK-20260904-SHADOW-REVIEWER-LOGGING | 3 | Test | claude | 121.081 | 3.6 | 33.6x |
| TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY | 8 | Implement | implementer | 342.032 | 10.2 | 33.6x |
| TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR | 5 | Implement | implementer | 339.855 | 10.2 | 33.4x |
| TCK-20260720-TAG-TOUCHPOINT-CLEANUP | 5 | Implement | implementer | 339.211 | 10.2 | 33.3x |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 8 | Test | test-scoper | 119.72 | 3.6 | 33.3x |
| TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST | 7 | Architecture-Verify | architecture-reviewer | 1788.286 | 53.9 | 33.2x |
| TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION | 2 | Implement | implementer | 337.025 | 10.2 | 33.1x |
| TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER | 4 | Test | test-scoper | 118.744 | 3.6 | 33.0x |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 8 | Test | test-scoper | 118.628 | 3.6 | 32.9x |
| TCK-20260817-STATE-DESIGN-PRIORITY-ORDER | 1 | Investigate | investigator | 2067.306 | 63.0 | 32.8x |
| TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION | 5 | Implement | implementer | 333.476 | 10.2 | 32.8x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 3 | Test | test-scoper | 116.939 | 3.6 | 32.5x |
| TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS | 2 | Implement | implementer | 326.196 | 10.2 | 32.0x |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | 2 | Implement | implementer | 325.528 | 10.2 | 32.0x |
| TCK-20260823-HTTP-API-KEY-AUTH | 11 | Test | test-scoper | 114.50999999999999 | 3.6 | 31.8x |
| TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL | 11 | Test | test-scoper | 114.366 | 3.6 | 31.8x |
| TCK-20260830-HOTFIX-WORLD-EMERGENCE-VESTIGIAL-GATE-CLEANUP | 8 | Test | test-scoper | 113.565 | 3.6 | 31.5x |
| TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON | 5 | Implement | implementer | 320.983 | 10.2 | 31.5x |
| TCK-20260907-FILTERED-REPLAY-EVAL-PILOT | 6 | Implement | implementer | 320.658 | 10.2 | 31.5x |
| TCK-20260815-KGMCP-P1-FAILOPEN-TESTS | 8 | Test | test-scoper | 113.213 | 3.6 | 31.4x |
| TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING | 10 | Test | test-scoper | 113.075 | 3.6 | 31.4x |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | 7 | Test | test-scoper | 112.67500000000001 | 3.6 | 31.3x |
| TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST | 5 | Implement | implementer | 317.60400000000004 | 10.2 | 31.2x |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 9 | Test | test-scoper | 112.225 | 3.6 | 31.2x |
| TCK-20260824-AFFECTION-CONTRACT-GATE | 8 | Test | test-scoper | 112.116 | 3.6 | 31.1x |
| TCK-20260815-KGMCP-P1-QUERY-ROUTER | 8 | Test | test-scoper | 111.79599999999999 | 3.6 | 31.1x |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 7 | Test | test-scoper | 111.578 | 3.6 | 31.0x |
| TCK-20260814-KGMCP-MEASUREMENT-BASELINE | 6 | Implement | implementer | 315.509 | 10.2 | 31.0x |
| TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE | 6 | Implement | implementer | 306.03999999999996 | 10.2 | 30.1x |
| TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION | 6 | Implement | implementer | 305.28200000000004 | 10.2 | 30.0x |
| TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT | 6 | Implement | implementer | 303.60699999999997 | 10.2 | 29.8x |
| TCK-20260824-RETRO-METRIC-CAVEATS | 5 | Implement | implementer | 302.65200000000004 | 10.2 | 29.7x |
| TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD | 7 | Implement | implementer | 302.369 | 10.2 | 29.7x |
| TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY | 6 | Architecture-Verify | claude | 1593.737 | 53.9 | 29.6x |
| TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE | 7 | Test | test-scoper | 106.477 | 3.6 | 29.6x |
| TCK-20260831-CAPABILITY-DRIVEN-TARGETING | 5 | Implement | implementer | 298.219 | 10.2 | 29.3x |
| TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING | 8 | Test | test-scoper | 105.22200000000001 | 3.6 | 29.2x |
| TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD | 13 | Test | test-scoper | 104.846 | 3.6 | 29.1x |
| TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING | 8 | Test | test-scoper | 104.313 | 3.6 | 29.0x |
| TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR | 8 | Test | test-scoper | 104.053 | 3.6 | 28.9x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 7 | Test | test-scoper | 103.999 | 3.6 | 28.9x |
| TCK-20260831-METAMORPHIC-LAB-PILOT | 5 | Implement | implementer | 293.745 | 10.2 | 28.8x |
| TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING | 8 | Test | test-scoper | 103.68299999999999 | 3.6 | 28.8x |
| TCK-20260904-AGENT-TOOL-USAGE-BASELINE | 5 | Implement | implementer | 292.608 | 10.2 | 28.7x |
| TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE | 8 | Test | test-scoper | 103.092 | 3.6 | 28.6x |
| TCK-20260821-WORLD-RENDER-CORE | 4 | Implement | implementer | 290.661 | 10.2 | 28.5x |
| TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET | 8 | Implement | implementer | 288.981 | 10.2 | 28.4x |
| TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING | 5 | Implement | implementer | 287.656 | 10.2 | 28.3x |
| TCK-20260717-TICKETS-TABLE-PAGINATION | 5 | Implement | implementer | 286.954 | 10.2 | 28.2x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 5 | Implement | implementer | 286.615 | 10.2 | 28.1x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 5 | Implement | implementer | 286.615 | 10.2 | 28.1x |
| TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX | 5 | Implement | claude | 286.221 | 10.2 | 28.1x |
| TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT | 5 | Implement | implementer | 285.171 | 10.2 | 28.0x |
| TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING | 4 | Implement | implementer | 279.211 | 10.2 | 27.4x |
| TCK-20260902-PARITY-TEST-PATH-GAP | 9 | Test | test-scoper | 97.922 | 3.6 | 27.2x |
| TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA | 8 | Test | test-scoper | 97.809 | 3.6 | 27.2x |
| TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING | 7 | Implement | implementer | 274.375 | 10.2 | 26.9x |
| TCK-20260821-REST-MAP-STATIC-STATS | 8 | Test | test-scoper | 95.261 | 3.6 | 26.5x |
| TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD | 9 | Test | test-scoper | 95.03 | 3.6 | 26.4x |
| TCK-20260815-KGMCP-P1-BASELINE-COMPARISON | 5 | Implement | implementer | 266.524 | 10.2 | 26.2x |
| TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT | 7 | Test | test-scoper | 93.45 | 3.6 | 26.0x |
| TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE | 12 | Implement | implementer | 263.728 | 10.2 | 25.9x |
| TCK-20260831-ITEM-INSTANCE-HISTORY | 10 | Test | test-scoper | 93.02600000000001 | 3.6 | 25.8x |
| TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION | 7 | Test | test-scoper | 92.717 | 3.6 | 25.8x |
| TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION | 4 | Test | test-scoper | 92.146 | 3.6 | 25.6x |
| TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS | 1 | Implement | implementer | 260.461 | 10.2 | 25.6x |
| TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION | 8 | Test | test-scoper | 91.436 | 3.6 | 25.4x |
| TCK-20260717-TICKETS-TAG-SEARCH | 5 | Implement | implementer | 258.501 | 10.2 | 25.4x |
| TCK-20260803-BRAINSTORM-SKILL-STALE-PATH | 7 | Test | test-scoper | 91.322 | 3.6 | 25.4x |
| TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD | 9 | Test | test-scoper | 90.962 | 3.6 | 25.3x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 8 | Document-Update | doc-updater | 1483.53 | 58.7 | 25.3x |
| TCK-20260731-PARITY-READPATH-GATE | 6 | Implement | implementer | 256.03700000000003 | 10.2 | 25.1x |
| TCK-20260731-PARITY-READPATH-GATE | 8 | Test | test-scoper | 90.428 | 3.6 | 25.1x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 9 | Test | test-scoper | 90.37700000000001 | 3.6 | 25.1x |
| TCK-20260831-POPULATION-COHORT-SEEDING | 5 | Implement | implementer | 251.596 | 10.2 | 24.7x |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 6 | Implement | implementer | 250.403 | 10.2 | 24.6x |
| TCK-20260811-ADVENTURE-GOAL-SCORER | 9 | Test | test-scoper | 88.482 | 3.6 | 24.6x |
| TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING | 5 | Implement | implementer | 247.204 | 10.2 | 24.3x |
| TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK | 1 | Implement | claude | 245.972 | 10.2 | 24.2x |
| TCK-20260824-ALLOCATE-AP-BRANCH-DECISION | 8 | Test | test-scoper | 86.975 | 3.6 | 24.2x |
| TCK-20260821-VISUAL-QUALITY-DOCS | 10 | Test | test-scoper | 86.96000000000001 | 3.6 | 24.2x |
| TCK-20260824-ALLOCATE-AP-BRANCH-DECISION | 5 | Implement | implementer | 245.76500000000001 | 10.2 | 24.1x |
| TCK-20260731-PARITY-IMPACT-PROOF | 7 | Test | test-scoper | 86.709 | 3.6 | 24.1x |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | 7 | Implement | implementer | 244.066 | 10.2 | 24.0x |
| TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC | 8 | Test | test-scoper | 86.21600000000001 | 3.6 | 23.9x |
| TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS | 5 | Implement | implementer | 242.763 | 10.2 | 23.8x |
| TCK-20260716-AGENTOPS-DASHBOARD-BACKEND | 7 | Test | test-scoper | 85.703 | 3.6 | 23.8x |
| TCK-20260831-CLAN-STATE-SCHEMA | 8 | Test | test-scoper | 85.501 | 3.6 | 23.7x |
| TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA | 5 | Implement | implementer | 239.318 | 10.2 | 23.5x |
| TCK-20260821-WS-ENTITY-DELTA-BROADCAST | 9 | Test | test-scoper | 84.49000000000001 | 3.6 | 23.5x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 7 | Test | test-scoper | 84.336 | 3.6 | 23.4x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 7 | Test | test-scoper | 84.336 | 3.6 | 23.4x |
| TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT | 2 | Implement | implementer | 238.476 | 10.2 | 23.4x |
| TCK-20260831-SPECIES-INTELLIGENCE-TIER | 10 | Test | test-scoper | 84.303 | 3.6 | 23.4x |
| TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION | 8 | Test | test-scoper | 84.09700000000001 | 3.6 | 23.4x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 10 | Test | test-scoper | 83.39699999999999 | 3.6 | 23.2x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 9 | Test | test-scoper | 83.16 | 3.6 | 23.1x |
| TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION | 8 | Test | test-scoper | 82.656 | 3.6 | 23.0x |
| TCK-20260718-STATUS-SUFFIX-TRIM | 7 | Test | test-scoper | 82.504 | 3.6 | 22.9x |
| TCK-20260831-HABIT-BIAS-WIRING | 7 | Implement | implementer | 232.91400000000002 | 10.2 | 22.9x |
| TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC | 7 | Implement | implementer | 232.82 | 10.2 | 22.9x |
| TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION | 8 | Test | test-scoper | 82.327 | 3.6 | 22.9x |
| TCK-20260731-PARITY-INDEX-BASELINE | 17 | Test | test-scoper | 82.164 | 3.6 | 22.8x |
| TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE | 8 | Test | test-scoper | 82.123 | 3.6 | 22.8x |
| TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT | 8 | Test | test-scoper | 82.10900000000001 | 3.6 | 22.8x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 8 | Test | test-scoper | 81.991 | 3.6 | 22.8x |
| TCK-20260824-DEFAULT-HEIR-ASSIGNMENT | 10 | Test | test-scoper | 81.887 | 3.6 | 22.7x |
| TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP | 6 | Test | test-scoper | 81.725 | 3.6 | 22.7x |
| TCK-20260902-CLASSHALL-DEAD-CODE | 2 | Implement | implementer | 230.746 | 10.2 | 22.7x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 9 | Test | test-scoper | 81.461 | 3.6 | 22.6x |
| TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION | 10 | Test | test-scoper | 81.32300000000001 | 3.6 | 22.6x |
| TCK-20260821-VISUAL-AGENT-REVIEW | 6 | Implement | implementer | 228.186 | 10.2 | 22.4x |
| TCK-20260717-GANTT-TIME-AXIS | 7 | Test | test-scoper | 80.578 | 3.6 | 22.4x |
| TCK-20260812-COMMITTED-INTENTION-SEQUENCE | 4 | Implement | implementer | 226.88400000000001 | 10.2 | 22.3x |
| TCK-20260819-HOTFIX-PARITY-BASELINE-DEAD-INFRA-DRIFT | 3 | Test | test-scoper | 80.17699999999999 | 3.6 | 22.3x |
| TCK-20260821-VISUAL-GRADE-SCORER | 10 | Test | test-scoper | 80.11 | 3.6 | 22.2x |
| TCK-20260712-WORKFLOW-FRICTION-FIXES | 5 | Implement | implementer | 225.843 | 10.2 | 22.2x |
| TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX | 8 | Test | claude | 79.672 | 3.6 | 22.1x |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 8 | Test | test-scoper | 79.593 | 3.6 | 22.1x |
| TCK-20260912-WORKING-LOG-APPEND-HELPER | 8 | Implement | implementer | 224.601 | 10.2 | 22.1x |
| TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE | 3 | Implement | claude | 224.512 | 10.2 | 22.0x |
| TCK-20260728-RETRIEVAL-BASELINE-METRICS | 7 | Test | test-scoper | 79.292 | 3.6 | 22.0x |
| TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5 | 9 | Test | test-scoper | 79.137 | 3.6 | 22.0x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 2 | Investigate | investigator | 1383.699 | 63.0 | 22.0x |
| TCK-20260831-CREATURE-TERRITORY-LIFECYCLE | 11 | Test | test-scoper | 78.47800000000001 | 3.6 | 21.8x |
| TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING | 8 | Test | test-scoper | 78.462 | 3.6 | 21.8x |
| TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH | 8 | Test | test-scoper | 78.373 | 3.6 | 21.8x |
| TCK-20260810-D22-DORMANT-WIRING-AUDIT | 3 | Test | test-scoper | 78.278 | 3.6 | 21.7x |
| TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH | 8 | Test | test-scoper | 78.077 | 3.6 | 21.7x |
| TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION | 6 | Implement | implementer | 220.164 | 10.2 | 21.6x |
| TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL | 7 | Implement | implementer | 220.05700000000002 | 10.2 | 21.6x |
| TCK-20260831-TRUST-GATED-TEACHING | 5 | Implement | implementer | 218.484 | 10.2 | 21.5x |
| TCK-20260810-SKILL-USAGE-RETRO-TRACKING | 10 | Test | test-scoper | 77.238 | 3.6 | 21.5x |
| TCK-20260824-WOUND-HEALING-DECISION | 5 | Implement | implementer | 218.198 | 10.2 | 21.4x |
| TCK-20260729-SHADOW-BASELINE-COMPARISON | 7 | Test | test-scoper | 76.931 | 3.6 | 21.4x |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 9 | Test | test-scoper | 76.72800000000001 | 3.6 | 21.3x |
| TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS | 3 | Test | test-scoper | 76.493 | 3.6 | 21.2x |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 6 | Implement | implementer | 215.981 | 10.2 | 21.2x |
| TCK-20260824-LEAD-CONTRADICTION-WIRING | 5 | Implement | implementer | 215.929 | 10.2 | 21.2x |
| TCK-20260821-VISUAL-QUALITY-CALIBRATION | 10 | Test | test-scoper | 76.292 | 3.6 | 21.2x |
| TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT | 9 | Test | test-scoper | 76.214 | 3.6 | 21.2x |
| TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL | 10 | Test | test-scoper | 75.96000000000001 | 3.6 | 21.1x |
| TCK-20260730-CODEX-RUNTIME-SHADOW | 5 | Implement | implementer | 214.54500000000002 | 10.2 | 21.1x |
| TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS | 9 | Test | implementer | 75.72800000000001 | 3.6 | 21.0x |
| TCK-20260731-PARITY-INDEX-IMPORTER | 8 | Test | test-scoper | 75.366 | 3.6 | 20.9x |
| TCK-20260821-WS-ENTITY-DELTA-BROADCAST | 5 | Implement | implementer | 212.81400000000002 | 10.2 | 20.9x |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 8 | Test | test-scoper | 75.084 | 3.6 | 20.9x |
| TCK-20260904-CAPABILITY-ENVELOPE-BASELINE | 5 | Implement | implementer | 212.099 | 10.2 | 20.8x |
| TCK-20260815-KGMCP-P1-QUERY-ROUTER | 5 | Implement | implementer | 211.516 | 10.2 | 20.8x |
| TCK-20260824-WOUND-PENALTY-FORMULA-WIRING | 7 | Test | test-scoper | 74.67699999999999 | 3.6 | 20.7x |
| TCK-20260819-SKILL-STALENESS-SOFT-WARNING | 9 | Test | test-scoper | 74.642 | 3.6 | 20.7x |
| TCK-20260822-SEMANTIC-ENTITY-INDEX | 11 | Test | test-scoper | 74.577 | 3.6 | 20.7x |
| TCK-20260824-WOUND-THRESHOLD-DECISION | 8 | Test | test-scoper | 73.999 | 3.6 | 20.6x |
| TCK-20260824-WOUND-HEALING-DECISION | 9 | Test | test-scoper | 73.994 | 3.6 | 20.6x |
| TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT | 7 | Test | test-scoper | 73.864 | 3.6 | 20.5x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 5 | Implement | implementer | 208.463 | 10.2 | 20.5x |
| TCK-20260821-VISUAL-AGENT-REVIEW | 10 | Test | test-scoper | 73.669 | 3.6 | 20.5x |
| TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT | 5 | Implement | implementer | 208.239 | 10.2 | 20.5x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 2 | Investigate | investigator | 1279.258 | 63.0 | 20.3x |
| TCK-20260730-CODEX-POSTTOOL-ADAPTER | 7 | Test | test-scoper | 72.992 | 3.6 | 20.3x |
| TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS | 11 | Test | test-scoper | 72.884 | 3.6 | 20.2x |
| TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC | 8 | Test | test-scoper | 72.625 | 3.6 | 20.2x |
| TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE | 9 | Test | test-scoper | 72.599 | 3.6 | 20.2x |
| TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE | 7 | Test | test-scoper | 72.292 | 3.6 | 20.1x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 9 | Test | test-scoper | 71.584 | 3.6 | 19.9x |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 7 | Test | test-scoper | 71.53999999999999 | 3.6 | 19.9x |
| TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS | 8 | Test | test-scoper | 71.445 | 3.6 | 19.8x |
| TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC | 5 | Implement | implementer | 201.066 | 10.2 | 19.7x |
| TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP | 8 | Test | test-scoper | 70.849 | 3.6 | 19.7x |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 6 | Implement | implementer | 200.14600000000002 | 10.2 | 19.7x |
| TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE | 11 | Test | test-scoper | 70.735 | 3.6 | 19.6x |
| TCK-20260822-GUARD-SCAN-INDEX-RETROFIT | 8 | Test | test-scoper | 70.535 | 3.6 | 19.6x |
| TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE | 6 | Test | test-scoper | 70.242 | 3.6 | 19.5x |
| TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM | 7 | Verify | done-checker | 1139.361 | 58.4 | 19.5x |
| TCK-20260831-RACE-RELATIONS-MATRIX | 10 | Test | test-scoper | 70.077 | 3.6 | 19.5x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 5 | Implement | implementer | 197.676 | 10.2 | 19.4x |
| TCK-20260822-SEMANTIC-ENTITY-INDEX | 8 | Implement | implementer | 196.678 | 10.2 | 19.3x |
| TCK-20260905-CHRONICLE-FIDELITY-DRIFT | 5 | Implement | implementer | 196.341 | 10.2 | 19.3x |
| TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT | 3 | Implement | implementer | 196.24 | 10.2 | 19.3x |
| TCK-20260730-CODEX-POSTTOOL-ADAPTER | 5 | Implement | implementer | 195.752 | 10.2 | 19.2x |
| TCK-20260730-PROVIDER-HOOK-POLICY | 5 | Implement | implementer | 195.486 | 10.2 | 19.2x |
| TCK-20260904-CLAN-REPUTATION-ASSOCIATION | 10 | Test | test-scoper | 69.111 | 3.6 | 19.2x |
| TCK-20260812-COMMITTED-INTENTION-SEQUENCE | 7 | Test | test-scoper | 68.962 | 3.6 | 19.2x |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 8 | Test | test-scoper | 68.923 | 3.6 | 19.1x |
| TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP | 2 | Test | test-scoper | 68.821 | 3.6 | 19.1x |
| TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION | 8 | Test | test-scoper | 68.725 | 3.6 | 19.1x |
| TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX | 7 | Test | test-scoper | 68.467 | 3.6 | 19.0x |
| TCK-20260720-TAG-CATEGORY-REGISTRY | 7 | Test | test-scoper | 68.39 | 3.6 | 19.0x |
| TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION | 9 | Test | test-scoper | 68.307 | 3.6 | 19.0x |
| TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE | 3 | Test | test-scoper | 68.143 | 3.6 | 18.9x |
| TCK-20260823-LIVE-TEST-API-KEY-AUTH | 6 | Implement | implementer | 192.402 | 10.2 | 18.9x |
| TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON | 9 | Test | test-scoper | 67.768 | 3.6 | 18.8x |
| TCK-20260821-VISUAL-VARIANTS-METRIC | 9 | Test | test-scoper | 67.684 | 3.6 | 18.8x |
| TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN | 4 | Test | test-scoper | 67.656 | 3.6 | 18.8x |
| TCK-20260728-CONTEXT-PACKET-SCHEMA | 7 | Test | test-scoper | 67.55 | 3.6 | 18.8x |
| TCK-20260821-NOISE-FILL-SCHEMA | 9 | Verify | done-checker | 1094.077 | 58.4 | 18.7x |
| TCK-20260730-CODEX-RUNTIME-SHADOW | 7 | Test | test-scoper | 67.343 | 3.6 | 18.7x |
| TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET | 11 | Test | test-scoper | 67.15 | 3.6 | 18.7x |
| TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX | 7 | Test | test-scoper | 66.867 | 3.6 | 18.6x |
| TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION | 3 | Test | test-scoper | 66.816 | 3.6 | 18.6x |
| TCK-20260731-PARITY-INDEX-BASELINE | 15 | Implement | implementer | 188.94299999999998 | 10.2 | 18.6x |
| TCK-20260729-SHADOW-BASELINE-COMPARISON | 5 | Implement | implementer | 188.252 | 10.2 | 18.5x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 7 | Test | test-scoper | 66.412 | 3.6 | 18.4x |
| TCK-20260716-AGENTOPS-BUILD-SERVE | 7 | Test | test-scoper | 66.372 | 3.6 | 18.4x |
| TCK-20260824-TACTICAL-WOUND-SCAR-WIRING | 8 | Test | test-scoper | 66.314 | 3.6 | 18.4x |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | 11 | Test | test-scoper | 66.244 | 3.6 | 18.4x |
| TCK-20260716-AGENTOPS-ACTIVITY-GANTT | 1 | Implement | implementer | 187.02 | 10.2 | 18.4x |
| TCK-20260728-CODE-TEST-INDEX-BOUNDARIES | 7 | Test | test-scoper | 66.04599999999999 | 3.6 | 18.3x |
| TCK-20260810-SKILL-USAGE-RETRO-TRACKING | 7 | Implement | implementer | 186.76999999999998 | 10.2 | 18.3x |
| TCK-20260831-READINESS-SPEED-FORMULA | 10 | Test | test-scoper | 65.945 | 3.6 | 18.3x |
| TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION | 8 | Test | test-scoper | 65.64 | 3.6 | 18.2x |
| TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION | 9 | Test | test-scoper | 65.383 | 3.6 | 18.2x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 6 | Verify | done-checker | 1060.682 | 58.4 | 18.2x |
| TCK-20260728-PHASE0-PREREQ-CONFIRMATION | 7 | Test | test-scoper | 65.30799999999999 | 3.6 | 18.1x |
| TCK-20260824-LIFE-STAGE-TRANSITIONS | 8 | Test | test-scoper | 65.301 | 3.6 | 18.1x |
| TCK-20260731-PARITY-IMPACT-PROOF | 5 | Implement | implementer | 184.36 | 10.2 | 18.1x |
| TCK-20260730-PROVIDER-HOOK-POLICY | 7 | Test | test-scoper | 64.932 | 3.6 | 18.0x |
| TCK-20260822-PAID-INFO-INDEX-RETROFIT | 8 | Test | test-scoper | 64.879 | 3.6 | 18.0x |
| TCK-20260802-STORED-ARTIFACT-KIND | 6 | Implement | implementer | 183.32 | 10.2 | 18.0x |
| TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY | 7 | Test | claude | 64.771 | 3.6 | 18.0x |
| TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH | 8 | Test | test-scoper | 64.745 | 3.6 | 18.0x |
| TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION | 8 | Test | test-scoper | 64.711 | 3.6 | 18.0x |
| TCK-20260802-CONTEXT-KIND-PRIORITY | 8 | Test | test-scoper | 64.432 | 3.6 | 17.9x |
| TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE | 9 | Test | test-scoper | 64.32 | 3.6 | 17.9x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 8 | Test | claude | 64.31 | 3.6 | 17.9x |
| TCK-20260802-EXACT-LOOKUP-CONVENTION | 8 | Test | test-scoper | 64.174 | 3.6 | 17.8x |
| TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD | 9 | Implement | implementer | 181.324 | 10.2 | 17.8x |
| TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION | 4 | Test | test-scoper | 63.881 | 3.6 | 17.7x |
| TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE | 9 | Test | test-scoper | 63.612 | 3.6 | 17.7x |
| TCK-20260902-ENTITIES-DOC-REWRITE | 8 | Test | test-scoper | 63.546 | 3.6 | 17.6x |
| TCK-20260821-VISUAL-GRADE-SCORER | 6 | Implement | implementer | 179.647 | 10.2 | 17.6x |
| TCK-20260902-HARVEST-LOOT-TEST-COVERAGE | 8 | Test | test-scoper | 63.055 | 3.6 | 17.5x |
| TCK-20260717-GANTT-TIME-AXIS | 5 | Implement | implementer | 178.142 | 10.2 | 17.5x |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | 6 | Review | architecture-reviewer | 975.631 | 55.8 | 17.5x |
| TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS | 5 | Implement | implementer | 177.86599999999999 | 10.2 | 17.5x |
| TCK-20260729-SHADOW-PACKET-CALL-SITE | 11 | Test | test-scoper | 62.883 | 3.6 | 17.5x |
| TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ | 8 | Test | test-scoper | 62.831 | 3.6 | 17.5x |
| TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT | 4 | Test | test-scoper | 62.731 | 3.6 | 17.4x |
| TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG | 7 | Test | test-scoper | 62.548 | 3.6 | 17.4x |
| TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION | 10 | Test | test-scoper | 62.402 | 3.6 | 17.3x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 9 | Test | test-scoper | 62.395 | 3.6 | 17.3x |
| TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION | 8 | Test | test-scoper | 62.386 | 3.6 | 17.3x |
| TCK-20260904-DOC-COVERAGE-REVERSE-CHECK | 9 | Architecture-Verify | architecture-reviewer | 932.0260000000001 | 53.9 | 17.3x |
| TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS | 8 | Test | test-scoper | 62.265 | 3.6 | 17.3x |
| TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK | 7 | Test | test-scoper | 61.84 | 3.6 | 17.2x |
| TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION | 8 | Test | test-scoper | 61.836 | 3.6 | 17.2x |
| TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT | 3 | Test | test-scoper | 61.828 | 3.6 | 17.2x |
| TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE | 8 | Test | test-scoper | 61.755 | 3.6 | 17.2x |
| TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT | 7 | Test | test-scoper | 61.678 | 3.6 | 17.1x |
| TCK-20260814-KGMCP-CONTRACT-SCHEMAS | 5 | Implement | implementer | 174.095 | 10.2 | 17.1x |
| TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT | 6 | Test | test-scoper | 61.561 | 3.6 | 17.1x |
| TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS | 8 | Test | test-scoper | 61.41 | 3.6 | 17.1x |
| TCK-20260821-VISUAL-SHAPE-METRIC | 5 | Implement | implementer | 173.623 | 10.2 | 17.1x |
| TCK-20260728-DEFAULT-PACKET-CRITERIA | 7 | Test | test-scoper | 61.311 | 3.6 | 17.0x |
| TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK | 8 | Test | test-scoper | 61.039 | 3.6 | 17.0x |
| TCK-20260728-EVAL-FIXTURE-REPAIR | 7 | Test | test-scoper | 61.012 | 3.6 | 16.9x |
| TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS | 5 | Implement | implementer | 172.53199999999998 | 10.2 | 16.9x |
| TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF | 8 | Test | test-scoper | 60.953 | 3.6 | 16.9x |
| TCK-20260902-CLASSHALL-DEAD-CODE | 5 | Test | test-scoper | 60.927 | 3.6 | 16.9x |
| TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION | 9 | Test | test-scoper | 60.916 | 3.6 | 16.9x |
| TCK-20260824-ROUTE-KIND-COUNT-FIX | 8 | Test | test-scoper | 60.875 | 3.6 | 16.9x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 8 | Test | test-scoper | 60.762 | 3.6 | 16.9x |
| TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER | 9 | Test | test-scoper | 60.68 | 3.6 | 16.9x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 8 | Test | test-scoper | 60.552 | 3.6 | 16.8x |
| TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS | 2 | Test | test-scoper | 60.446 | 3.6 | 16.8x |
| TCK-20260717-TICKET-TITLE-PARSE-FIX | 7 | Test | test-scoper | 60.38 | 3.6 | 16.8x |
| TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH | 7 | Test | test-scoper | 60.38 | 3.6 | 16.8x |
| TCK-20260728-RETRIEVAL-RETENTION-REDACTION | 7 | Test | test-scoper | 60.263 | 3.6 | 16.7x |
| TCK-20260810-STATUS-DRIFT-CHECK-WIRING | 8 | Test | test-scoper | 60.248 | 3.6 | 16.7x |
| TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING | 10 | Test | test-scoper | 60.191 | 3.6 | 16.7x |
| TCK-20260716-AGENTOPS-REPLAY-TIMELINE | 7 | Test | test-scoper | 60.15 | 3.6 | 16.7x |
| TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER | 5 | Implement | implementer | 170.019 | 10.2 | 16.7x |
| TCK-20260814-KGMCP-CONTRACT-SCHEMAS | 8 | Test | test-scoper | 60.097 | 3.6 | 16.7x |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 9 | Verify | done-checker | 973.098 | 58.4 | 16.7x |
| TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT | 8 | Test | test-scoper | 59.838 | 3.6 | 16.6x |
| TCK-20260720-TAG-CORPUS-REPAIR-SWEEP | 7 | Test | test-scoper | 59.786 | 3.6 | 16.6x |
| TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT | 2 | Implement | implementer | 168.466 | 10.2 | 16.5x |
| TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE | 3 | Implement | claude | 167.96 | 10.2 | 16.5x |
| TCK-20260713-SIMQ-EVAL-PROFILE-BUG | 7 | Test | test-scoper | 59.359 | 3.6 | 16.5x |
| TCK-20260811-REGION-STABILIZATION-GOAL-SCORER | 10 | Test | test-scoper | 59.338 | 3.6 | 16.5x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 8 | Architecture-Verify | architecture-reviewer | 887.236 | 53.9 | 16.5x |
| TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE | 6 | Implement | implementer | 167.643 | 10.2 | 16.5x |
| TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK | 3 | Test | test-scoper | 59.242 | 3.6 | 16.5x |
| TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY | 7 | Test | test-scoper | 59.135 | 3.6 | 16.4x |
| TCK-20260711-DOC-STALENESS-GATE-CHECK | 7 | Test | test-scoper | 59.094 | 3.6 | 16.4x |
| TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY | 9 | Test | test-scoper | 58.932 | 3.6 | 16.4x |
| TCK-20260720-TAG-CATEGORY-REGISTRY | 5 | Implement | implementer | 166.32 | 10.2 | 16.3x |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 9 | Test | test-scoper | 58.796 | 3.6 | 16.3x |
| TCK-20260824-DEFAULT-HEIR-ASSIGNMENT | 7 | Implement | implementer | 166.005 | 10.2 | 16.3x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 10 | Test | test-scoper | 58.427 | 3.6 | 16.2x |
| TCK-20260810-STATUS-DRIFT-CHECK-WIRING | 5 | Implement | implementer | 165.191 | 10.2 | 16.2x |
| TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC | 4 | Implement | implementer | 164.959 | 10.2 | 16.2x |
| TCK-20260831-CREATURE-TERRITORY-LIFECYCLE | 5 | Implement | implementer | 163.715 | 10.2 | 16.1x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 7 | Test | test-scoper | 57.646 | 3.6 | 16.0x |
| TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING | 9 | Test | test-scoper | 57.488 | 3.6 | 16.0x |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | 7 | Test | test-scoper | 57.358 | 3.6 | 15.9x |
| TCK-20260716-PLACELEGAL-HARDLAW | 2 | Investigate | investigator | 1001.508 | 63.0 | 15.9x |
| TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY | 9 | Test | test-scoper | 57.258 | 3.6 | 15.9x |
| TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE | 8 | Test | claude | 57.132 | 3.6 | 15.9x |
| TCK-20260824-WOUND-THRESHOLD-DECISION | 5 | Implement | implementer | 160.893 | 10.2 | 15.8x |
| TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH | 5 | Implement | implementer | 160.349 | 10.2 | 15.7x |
| TCK-20260902-HARVEST-LOOT-TEST-COVERAGE | 5 | Implement | implementer | 159.445 | 10.2 | 15.7x |
| TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX | 10 | Test | test-scoper | 56.376 | 3.6 | 15.7x |
| TCK-20260826-PARITY-FACTION-CANONICAL-SCAN | 5 | Implement | implementer | 159.21 | 10.2 | 15.6x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 4 | Review | architecture-reviewer | 869.171 | 55.8 | 15.6x |
| TCK-20260902-SCHEMA4-DIVERGENCE-NOTE | 5 | Test | test-scoper | 56.022 | 3.6 | 15.6x |
| TCK-20260731-PARITY-INDEX-IMPORTER | 6 | Implement | implementer | 157.78 | 10.2 | 15.5x |
| TCK-20260710-SIMQ-DEPTH-FACTION | 7 | Test | test-scoper | 55.653 | 3.6 | 15.5x |
| TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT | 8 | Test | test-scoper | 55.574 | 3.6 | 15.4x |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 8 | Implement | implementer | 157.032 | 10.2 | 15.4x |
| TCK-20260720-TAG-CORPUS-REPAIR-SWEEP | 5 | Implement | implementer | 156.747 | 10.2 | 15.4x |
| TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK | 5 | Implement | implementer | 156.593 | 10.2 | 15.4x |
| TCK-20260720-SKILL-MAPPING-DEDUP | 3 | Plan | planner | 883.876 | 57.9 | 15.3x |
| TCK-20260831-CLASS-TIER-BRANCHING | 5 | Implement | implementer | 155.369 | 10.2 | 15.3x |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 7 | Test | test-scoper | 54.906 | 3.6 | 15.2x |
| TCK-20260821-REST-MAP-STATIC-STATS | 5 | Implement | implementer | 153.55599999999998 | 10.2 | 15.1x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 7 | Test | test-scoper | 54.255 | 3.6 | 15.1x |
| TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS | 3 | Test | claude | 54.194 | 3.6 | 15.1x |
| TCK-20260711-EPIC-SCOPE-ORPHAN-FIX | 7 | Test | test-scoper | 54.127 | 3.6 | 15.0x |
| TCK-20260821-WOLF-DEN-NOISE-MIGRATION | 4 | Implement | implementer | 152.644 | 10.2 | 15.0x |
| TCK-20260712-WORKFLOW-FRICTION-FIXES | 7 | Test | test-scoper | 53.941 | 3.6 | 15.0x |
| TCK-20260729-SHADOW-PACKET-CALL-SITE | 9 | Implement | implementer | 151.937 | 10.2 | 14.9x |
| TCK-20260831-ROLE-MODEL-IMITATION | 8 | Test | test-scoper | 53.661 | 3.6 | 14.9x |
| TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH | 7 | Test | test-scoper | 53.534 | 3.6 | 14.9x |
| TCK-20260902-ASPECT-TERM-CLEANUP | 2 | Implement | implementer | 151.214 | 10.2 | 14.9x |
| TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT | 4 | Implement | implementer | 149.95499999999998 | 10.2 | 14.7x |
| TCK-20260824-LIFE-STAGE-TRANSITIONS | 5 | Implement | implementer | 149.39 | 10.2 | 14.7x |
| TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS | 6 | Implement | implementer | 148.64499999999998 | 10.2 | 14.6x |
| TCK-20260821-COMPILER-NOISE-FILL | 4 | Implement | implementer | 147.923 | 10.2 | 14.5x |
| TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION | 6 | Implement | implementer | 147.872 | 10.2 | 14.5x |
| TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH | 5 | Implement | implementer | 147.747 | 10.2 | 14.5x |
| TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH | 5 | Implement | implementer | 146.888 | 10.2 | 14.4x |
| TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING | 5 | Implement | implementer | 146.288 | 10.2 | 14.4x |
| TCK-20260817-ENGINE-LIVENESS-HEALTH-EPIC | 5 | Implement | implementer | 143.75 | 10.2 | 14.1x |
| TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS | 1 | Investigate | claude | 888.051 | 63.0 | 14.1x |
| TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED | 2 | Implement | implementer | 140.74599999999998 | 10.2 | 13.8x |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 1 | Investigate | investigator | 860.991 | 63.0 | 13.7x |
| TCK-20260811-REGION-STABILIZATION-GOAL-SCORER | 5 | Implement | implementer | 137.94 | 10.2 | 13.5x |
| TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT | 5 | Implement | implementer | 137.85500000000002 | 10.2 | 13.5x |
| TCK-20260821-VISUAL-DENSITY-METRIC | 4 | Implement | implementer | 137.651 | 10.2 | 13.5x |
| TCK-20260821-VISUAL-QUALITY-CALIBRATION | 6 | Implement | implementer | 137.436 | 10.2 | 13.5x |
| TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION | 1 | Implement | implementer | 136.50799999999998 | 10.2 | 13.4x |
| TCK-20260717-DASHBOARD-RESPONSIVE-LAYOUT | 5 | Implement | implementer | 135.764 | 10.2 | 13.3x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 11 | Verify | done-checker | 777.943 | 58.4 | 13.3x |
| TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC | 2 | Implement | implementer | 135.001 | 10.2 | 13.3x |
| TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION | 4 | Implement | implementer | 131.233 | 10.2 | 12.9x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 2 | Investigate | investigator | 802.218 | 63.0 | 12.7x |
| TCK-20260819-HOTFIX-RNG-BOUNDARY-VIOLATION-BACKOFF-JITTER | 2 | Implement | implementer | 129.32999999999998 | 10.2 | 12.7x |
| TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF | 7 | Implement | implementer | 128.361 | 10.2 | 12.6x |
| TCK-20260909-KGMCP-DOC-STATUS-SWEEP | 5 | Implement | implementer | 127.762 | 10.2 | 12.5x |
| TCK-20260831-READINESS-SPEED-FORMULA | 6 | Review-Recheck | architecture-reviewer | 4738.2 | 379.8 | 12.5x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 5 | Implement | claude | 126.792 | 10.2 | 12.5x |
| TCK-20260728-RETRIEVAL-BASELINE-METRICS | 5 | Implement | implementer | 126.405 | 10.2 | 12.4x |
| TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF | 5 | Implement | implementer | 125.21900000000001 | 10.2 | 12.3x |
| TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT | 5 | Implement | implementer | 124.873 | 10.2 | 12.3x |
| TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY | 5 | Implement | implementer | 124.09700000000001 | 10.2 | 12.2x |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 6 | Implement | implementer | 123.887 | 10.2 | 12.2x |
| TCK-20260728-CODE-TEST-INDEX-BOUNDARIES | 5 | Implement | implementer | 123.32600000000001 | 10.2 | 12.1x |
| TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC | 5 | Implement | implementer | 123.245 | 10.2 | 12.1x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 9 | Document-Update | orchestrator | 704.941 | 58.7 | 12.0x |
| TCK-20260821-VISUAL-QUALITY-DOCS | 5 | Implement | implementer | 121.932 | 10.2 | 12.0x |
| TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK | 2 | Implement | implementer | 121.201 | 10.2 | 11.9x |
| TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE | 5 | Implement | implementer | 119.856 | 10.2 | 11.8x |
| TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT | 3 | Document-Update | doc-updater | 688.707 | 58.7 | 11.7x |
| TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD | 6 | Implement | implementer | 118.78999999999999 | 10.2 | 11.7x |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 6 | Implement | implementer | 118.71600000000001 | 10.2 | 11.7x |
| TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP | 1 | Implement | implementer | 118.345 | 10.2 | 11.6x |
| TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY | 2 | Plan | claude | 660.87 | 57.9 | 11.4x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 6 | Implement | implementer | 115.72 | 10.2 | 11.4x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 4 | Review | architecture-reviewer | 630.599 | 55.8 | 11.3x |
| TCK-20260821-VISUAL-VARIANTS-METRIC | 4 | Implement | implementer | 113.994 | 10.2 | 11.2x |
| TCK-20260716-AGENTOPS-REPLAY-TIMELINE | 5 | Implement | implementer | 113.679 | 10.2 | 11.2x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 7 | Document-Update | doc-updater | 649.592 | 58.7 | 11.1x |
| TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY | 5 | Implement | implementer | 112.24000000000001 | 10.2 | 11.0x |
| TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP | 1 | Investigate | claude | 692.077 | 63.0 | 11.0x |
| TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING | 5 | Implement | implementer | 110.953 | 10.2 | 10.9x |
| TCK-20260802-EXACT-LOOKUP-CONVENTION | 6 | Implement | implementer | 109.482 | 10.2 | 10.8x |
| TCK-20260902-PARITY-TEST-PATH-GAP | 5 | Implement | implementer | 109.39699999999999 | 10.2 | 10.7x |
| TCK-20260819-SKILL-STALENESS-SOFT-WARNING | 6 | Implement | implementer | 109.378 | 10.2 | 10.7x |
| TCK-20260718-STATUS-SUFFIX-TRIM | 5 | Implement | implementer | 107.964 | 10.2 | 10.6x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 7 | Architecture-Verify | claude | 566.404 | 53.9 | 10.5x |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 1 | Investigate | investigator | 658.818 | 63.0 | 10.5x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 8 | Architecture-Verify | architecture-reviewer | 560.8199999999999 | 53.9 | 10.4x |
| TCK-20260802-CONTEXT-KIND-PRIORITY | 6 | Implement | implementer | 105.063 | 10.2 | 10.3x |
| TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE | 5 | Implement | implementer | 105.062 | 10.2 | 10.3x |
| TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP | 1 | Implement | implementer | 102.398 | 10.2 | 10.1x |
| TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY | 4 | Implement | implementer | 101.724 | 10.2 | 10.0x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 5 | Implement | implementer | 101.637 | 10.2 | 10.0x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 6 | Architecture-Verify | architecture-reviewer | 535.464 | 53.9 | 9.9x |
| TCK-20260717-TICKET-TITLE-PARSE-FIX | 5 | Implement | implementer | 100.239 | 10.2 | 9.8x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 8 | Architecture-Verify | architecture-reviewer | 530.2429999999999 | 53.9 | 9.8x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 2 | Investigate | investigator | 617.064 | 63.0 | 9.8x |
| TCK-20260728-RETRIEVAL-RETENTION-REDACTION | 5 | Implement | implementer | 99.47 | 10.2 | 9.8x |
| TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH | 5 | Test | test-scoper | 35.097 | 3.6 | 9.7x |
| TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION | 1 | Investigate | claude | 602.912 | 63.0 | 9.6x |
| TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS | 4 | Implement | claude | 96.44 | 10.2 | 9.5x |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 5 | Implement | implementer | 94.65 | 10.2 | 9.3x |
| TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE | 6 | Implement | implementer | 94.248 | 10.2 | 9.3x |
| TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE | 1 | Investigate | investigator | 581.595 | 63.0 | 9.2x |
| TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS | 2 | Implement | implementer | 93.606 | 10.2 | 9.2x |
| TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING | 5 | Implement | implementer | 92.543 | 10.2 | 9.1x |
| TCK-20260902-ENTITIES-DOC-REWRITE | 5 | Implement | implementer | 91.74000000000001 | 10.2 | 9.0x |
| TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY | 5 | Implement | implementer | 91.563 | 10.2 | 9.0x |
| TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE | 9 | Implement | implementer | 90.568 | 10.2 | 8.9x |
| TCK-20260831-CLAN-STATE-SCHEMA | 5 | Implement | implementer | 89.616 | 10.2 | 8.8x |
| TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS | 6 | Implement | implementer | 89.31 | 10.2 | 8.8x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 4 | Review | architecture-reviewer | 489.023 | 55.8 | 8.8x |
| TCK-20260728-PHASE0-PREREQ-CONFIRMATION | 5 | Implement | implementer | 89.054 | 10.2 | 8.7x |
| TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS | 5 | Implement | implementer | 88.84100000000001 | 10.2 | 8.7x |
| TCK-20260711-EPIC-SCOPE-ORPHAN-FIX | 5 | Implement | implementer | 88.785 | 10.2 | 8.7x |
| TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE | 7 | Implement | implementer | 87.57300000000001 | 10.2 | 8.6x |
| TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS | 5 | Implement | implementer | 87.432 | 10.2 | 8.6x |
| TCK-20260811-ADVENTURE-GOAL-SCORER | 6 | Implement | implementer | 86.708 | 10.2 | 8.5x |
| TCK-20260815-KGMCP-P1-QUERY-ROUTER | 10 | Verify | done-checker | 496.00100000000003 | 58.4 | 8.5x |
| TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH | 5 | Implement | implementer | 86.049 | 10.2 | 8.5x |
| TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT | 5 | Implement | implementer | 85.747 | 10.2 | 8.4x |
| TCK-20260817-RUNTIMEMODE-BENCH-SCOPING | 9 | Verify | done-checker | 486.354 | 58.4 | 8.3x |
| TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE | 6 | Implement | implementer | 83.561 | 10.2 | 8.2x |
| TCK-20260821-PRESENT-MAP-STATIC | 5 | Implement | implementer | 82.94200000000001 | 10.2 | 8.1x |
| TCK-20260713-SIMQ-RAWSCORE-PERSIST | 2 | Investigate | investigator | 512.132 | 63.0 | 8.1x |
| TCK-20260728-CONTEXT-PACKET-SCHEMA | 5 | Implement | implementer | 82.291 | 10.2 | 8.1x |
| TCK-20260810-D22-DORMANT-WIRING-AUDIT | 1 | Implement | implementer | 82.099 | 10.2 | 8.1x |
| TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK | 1 | Investigate | claude | 503.72700000000003 | 63.0 | 8.0x |
| TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX | 5 | Implement | implementer | 81.195 | 10.2 | 8.0x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 7 | Implement | implementer | 80.843 | 10.2 | 7.9x |
| TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION | 6 | Implement | implementer | 80.483 | 10.2 | 7.9x |
| TCK-20260822-PAID-INFO-INDEX-RETROFIT | 5 | Implement | implementer | 80.26 | 10.2 | 7.9x |
| TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE | 1 | Implement | implementer | 79.892 | 10.2 | 7.8x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 5 | Implement | implementer | 79.79599999999999 | 10.2 | 7.8x |
| TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE | 5 | Implement | implementer | 79.35900000000001 | 10.2 | 7.8x |
| TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS | 9 | Architecture-Verify | architecture-reviewer | 419.68600000000004 | 53.9 | 7.8x |
| TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH | 5 | Implement | implementer | 79.291 | 10.2 | 7.8x |
| TCK-20260728-DEFAULT-PACKET-CRITERIA | 5 | Implement | implementer | 79.218 | 10.2 | 7.8x |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | 7 | Architecture-Verify | architecture-reviewer | 415.861 | 53.9 | 7.7x |
| TCK-20260831-READINESS-SPEED-FORMULA | 7 | Implement | implementer | 78.344 | 10.2 | 7.7x |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 5 | Implement | implementer | 78.334 | 10.2 | 7.7x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 2 | Investigate | investigator | 482.209 | 63.0 | 7.7x |
| TCK-20260822-GUARD-SCAN-INDEX-RETROFIT | 5 | Implement | implementer | 77.952 | 10.2 | 7.7x |
| TCK-20260831-RACE-RELATIONS-MATRIX | 7 | Implement | implementer | 77.303 | 10.2 | 7.6x |
| TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION | 1 | Investigate | claude | 476.866 | 63.0 | 7.6x |
| TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME | 2 | Investigate | investigator | 475.986 | 63.0 | 7.6x |
| TCK-20260831-ITEM-INSTANCE-HISTORY | 7 | Implement | implementer | 76.431 | 10.2 | 7.5x |
| TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION | 1 | Implement | implementer | 76.169 | 10.2 | 7.5x |
| TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING | 6 | Implement | implementer | 75.836 | 10.2 | 7.4x |
| TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT | 5 | Implement | implementer | 75.768 | 10.2 | 7.4x |
| TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE | 5 | Implement | claude | 75.569 | 10.2 | 7.4x |
| TCK-20260816-KGMCP-P4-PARITY-ADAPTER | 11 | Verify | done-checker | 433.202 | 58.4 | 7.4x |
| TCK-20260814-KGMCP-PRESCAN-MANDATE-INSTRUCTION-DRAFT | 5 | Implement | implementer | 75.26599999999999 | 10.2 | 7.4x |
| TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS | 5 | Implement | implementer | 75.06700000000001 | 10.2 | 7.4x |
| TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP | 8 | Implement | implementer | 74.765 | 10.2 | 7.3x |
| TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN | 2 | Implement | implementer | 74.201 | 10.2 | 7.3x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 9 | Document-Update-Gate | orchestrator | 466.647 | 64.2 | 7.3x |
| TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION | 6 | Implement | implementer | 73.748 | 10.2 | 7.2x |
| TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP | 5 | Implement | implementer | 73.644 | 10.2 | 7.2x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 5 | Implement | implementer | 73.504 | 10.2 | 7.2x |
| TCK-20260817-STATE-DESIGN-PRIORITY-ORDER | 4 | Implement | implementer | 73.11 | 10.2 | 7.2x |
| TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP | 5 | Implement | implementer | 72.997 | 10.2 | 7.2x |
| TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ | 2 | Investigate | investigator | 449.495 | 63.0 | 7.1x |
| TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK | 5 | Implement | implementer | 71.631 | 10.2 | 7.0x |
| TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET | 3 | Test | claude | 25.292 | 3.6 | 7.0x |
| TCK-20260710-SIMQ-DEPTH-FACTION | 2 | Investigate | investigator | 438.081 | 63.0 | 7.0x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 4 | Review | architecture-reviewer | 382.003 | 55.8 | 6.8x |
| TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX | 6 | Implement | implementer | 69.127 | 10.2 | 6.8x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 5 | Implement | implementer | 69.126 | 10.2 | 6.8x |
| TCK-20260717-AGENTOPS-DASHBOARD-DOCS | 5 | Implement | implementer | 68.977 | 10.2 | 6.8x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 8 | Implement | implementer | 68.906 | 10.2 | 6.8x |
| TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-PUSH-SHAPER-EVENTS | 1 | Investigate | claude | 425.931 | 63.0 | 6.8x |
| TCK-20260902-SCHEMA4-DIVERGENCE-NOTE | 2 | Implement | implementer | 68.759 | 10.2 | 6.8x |
| TCK-20260822-WORLD-GRAMMAR-REACHABILITY-VALIDATOR | 6 | Implement | implementer | 68.72 | 10.2 | 6.7x |
| TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION | 5 | Implement | implementer | 68.52 | 10.2 | 6.7x |
| TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP | 6 | Document-Update | doc-updater | 394.943 | 58.7 | 6.7x |
| TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT | 6 | Implement | implementer | 68.338 | 10.2 | 6.7x |
| TCK-20260904-BASH-SECRET-SCAN-HOOK | 5 | Implement | implementer | 67.687 | 10.2 | 6.6x |
| TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME | 2 | Investigate | investigator | 416.131 | 63.0 | 6.6x |
| TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION | 12 | Verify | done-checker | 384.844 | 58.4 | 6.6x |
| TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE | 9 | Architecture-Verify | architecture-reviewer | 354.638 | 53.9 | 6.6x |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 2 | Plan | planner | 380.951 | 57.9 | 6.6x |
| TCK-20260730-CLAUDE-EXECUTION-IDENTITY | 5 | Implement | implementer | 66.678 | 10.2 | 6.5x |
| TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ | 5 | Implement | implementer | 66.416 | 10.2 | 6.5x |
| TCK-20260824-ROUTE-KIND-COUNT-FIX | 5 | Implement | implementer | 66.12700000000001 | 10.2 | 6.5x |
| TCK-20260824-HOTFIX-COLLECTONLY-CLASS-NORMALIZE | 5 | Document-Update | doc-updater | 381.0 | 58.7 | 6.5x |
| TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP | 11 | Verify | done-checker | 378.865 | 58.4 | 6.5x |
| TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE | 4 | Test | claude | 23.337 | 3.6 | 6.5x |
| TCK-20260824-TACTICAL-WOUND-SCAR-WIRING | 6 | Implement | implementer | 65.958 | 10.2 | 6.5x |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 5 | Review | architecture-reviewer | 361.331 | 55.8 | 6.5x |
| TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG | 4 | Implement | implementer | 65.759 | 10.2 | 6.5x |
| TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION | 2 | Investigate | claude | 405.94100000000003 | 63.0 | 6.4x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 3 | Plan | planner | 372.27500000000003 | 57.9 | 6.4x |
| TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP | 1 | Investigate | investigator | 403.29900000000004 | 63.0 | 6.4x |
| TCK-20260824-WOUND-PENALTY-FORMULA-WIRING | 5 | Implement | implementer | 65.21600000000001 | 10.2 | 6.4x |
| TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-LIVE-DIFF-FALSE-POSITIVE | 2 | Implement | implementer | 65.197 | 10.2 | 6.4x |
| TCK-20260803-BRAINSTORM-SKILL-STALE-PATH | 6 | Implement | implementer | 65.011 | 10.2 | 6.4x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 3 | Plan | planner | 369.498 | 57.9 | 6.4x |
| TCK-20260728-EVAL-FIXTURE-REPAIR | 9 | Verify | done-checker | 372.169 | 58.4 | 6.4x |
| TCK-20260904-SHADOW-REVIEWER-LOGGING | 5 | Verify | claude | 371.81 | 58.4 | 6.4x |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 6 | Implement | implementer | 64.75399999999999 | 10.2 | 6.4x |
| TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER | 5 | Implement | implementer | 64.66499999999999 | 10.2 | 6.4x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 6 | Document-Update | doc-updater | 371.293 | 58.7 | 6.3x |
| TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL | 5 | Implement | claude | 64.22 | 10.2 | 6.3x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 7 | Architecture-Verify | architecture-reviewer | 338.946 | 53.9 | 6.3x |
| TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION | 1 | Implement | implementer | 63.846000000000004 | 10.2 | 6.3x |
| TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX | 6 | Implement | implementer | 63.181 | 10.2 | 6.2x |
| TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP | 6 | Architecture-Verify | architecture-reviewer | 333.693 | 53.9 | 6.2x |
| TCK-20260811-MULTI-STEP-PLANNING-DESIGN | 5 | Implement | implementer | 62.937 | 10.2 | 6.2x |
| TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE | 1 | Implement | implementer | 62.698 | 10.2 | 6.2x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 4 | Review | architecture-reviewer | 343.091 | 55.8 | 6.1x |
| TCK-20260802-STORED-ARTIFACT-KIND | 7 | Implement | implementer | 62.345 | 10.2 | 6.1x |
| TCK-20260821-WS-ENTITY-DELTA-BROADCAST | 6 | Implement | implementer | 62.036 | 10.2 | 6.1x |
| TCK-20260816-HOTFIX-KGMCP-LOCAL-DATA-BOOTSTRAP-DOCS | 2 | Implement | implementer | 62.031 | 10.2 | 6.1x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 6 | Document-Update | doc-updater | 356.392 | 58.7 | 6.1x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 6 | Implement | implementer | 61.558 | 10.2 | 6.0x |
| TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH | 5 | Implement | implementer | 61.229 | 10.2 | 6.0x |
| TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION | 6 | Implement | implementer | 61.136 | 10.2 | 6.0x |
| TCK-20260823-HOTFIX-INVESTIGATOR-EXCLUDED-DOC-BULLET-TEMPLATE-GAP | 2 | Implement | implementer | 61.098 | 10.2 | 6.0x |
| TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING | 6 | Implement | implementer | 60.956 | 10.2 | 6.0x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 4 | Review | architecture-reviewer | 334.027 | 55.8 | 6.0x |
| TCK-20260711-DOC-STALENESS-GATE-CHECK | 5 | Implement | implementer | 60.481 | 10.2 | 5.9x |
| TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE | 3 | Test | test-scoper | 21.301000000000002 | 3.6 | 5.9x |
| TCK-20260824-TOWN-CENTER-POINTER-FIX | 8 | Implement | implementer | 60.097 | 10.2 | 5.9x |
| TCK-20260904-SHADOW-REVIEWER-LOGGING | 2 | Implement | claude | 59.925 | 10.2 | 5.9x |
| TCK-20260822-QUEST-OPPORTUNITY-PREEMIT-VALIDATION | 6 | Implement | implementer | 59.891 | 10.2 | 5.9x |
| TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE | 2 | Investigate | investigator | 369.344 | 63.0 | 5.9x |
| TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY | 5 | Implement | claude | 59.545 | 10.2 | 5.8x |
| TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM | 3 | Implement | implementer | 59.192 | 10.2 | 5.8x |
| TCK-20260817-STANDARD-BALANCE-REGRESSION-STALE-SCORING-WEIGHT | 5 | Implement | orchestrator | 59.069 | 10.2 | 5.8x |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 6 | Document-Update | doc-updater | 338.238 | 58.7 | 5.8x |
| TCK-20260710-TOWN-COUNCIL-HAZARD-DA | 2 | Investigate | investigator | 360.99 | 63.0 | 5.7x |
| TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION | 6 | Implement | implementer | 58.123 | 10.2 | 5.7x |
| TCK-20260710-CURRENT-RUN-SIDECAR-BASH | 5 | Implement | implementer | 58.018 | 10.2 | 5.7x |
| TCK-20260814-KGMCP-CONTRACT-SCHEMAS | 11 | Implement | implementer | 57.766 | 10.2 | 5.7x |
| TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX | 1 | Investigate | investigator | 356.40500000000003 | 63.0 | 5.7x |
| TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP | 4 | Review | architecture-reviewer | 315.929 | 55.8 | 5.7x |
| TCK-20260831-SPECIES-INTELLIGENCE-TIER | 7 | Implement | implementer | 57.557 | 10.2 | 5.7x |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 8 | Architecture-Verify | architecture-reviewer | 303.845 | 53.9 | 5.6x |
| TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX | 4 | Review | architecture-reviewer | 313.03000000000003 | 55.8 | 5.6x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 5 | Implement | implementer | 56.725 | 10.2 | 5.6x |
| TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK | 6 | Implement | implementer | 55.765 | 10.2 | 5.5x |
| TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT | 2 | Plan | planner | 315.48 | 57.9 | 5.4x |
| TCK-20260902-HOTFIX-PARITY-WORLD-DYNAMICS-ID-BASELINE-DRIFT | 2 | Implement | implementer | 55.022 | 10.2 | 5.4x |
| TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT | 1 | Investigate | investigator | 338.936 | 63.0 | 5.4x |
| TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE | 5 | Implement | implementer | 54.079 | 10.2 | 5.3x |
| TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION | 2 | Implement | implementer | 53.643 | 10.2 | 5.3x |
| TCK-20260823-CI-STEP-SUMMARY-REPORTING | 9 | Implement | implementer | 53.188 | 10.2 | 5.2x |
| TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON | 11 | Verify | done-checker | 304.471 | 58.4 | 5.2x |
| TCK-20260831-CREATURE-TERRITORY-LIFECYCLE | 9 | Implement | implementer | 52.855 | 10.2 | 5.2x |
| TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE | 9 | Verify | done-checker | 303.037 | 58.4 | 5.2x |
| TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION | 5 | Document-Update | doc-updater | 304.637 | 58.7 | 5.2x |
| TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION | 5 | Document-Update | doc-updater | 303.841 | 58.7 | 5.2x |
| TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD | 4 | Review | claude | 286.722 | 55.8 | 5.1x |
| TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION | 12 | Verify | claude | 298.722 | 58.4 | 5.1x |
| TCK-20260714-DATA-RUNS-VERIFY-REGEN | 2 | Investigate | investigator | 319.704 | 63.0 | 5.1x |
| TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE | 2 | Investigate | claude | 318.337 | 63.0 | 5.1x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 9 | Verify | done-checker | 293.789 | 58.4 | 5.0x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 10 | Verify | done-checker | 289.145 | 58.4 | 4.9x |
| TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS | 2 | Review | implementer | 268.87 | 55.8 | 4.8x |
| TCK-20260820-EXPERIMENTS-PLACEMENT-INTEGRITY-CLEANUP | 8 | Verify | done-checker | 279.326 | 58.4 | 4.8x |
| TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE | 11 | Verify | claude | 275.48199999999997 | 58.4 | 4.7x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 260.409 | 55.8 | 4.7x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 260.409 | 55.8 | 4.7x |
| TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS | 2 | Plan | planner | 268.87 | 57.9 | 4.6x |
| TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS | 2 | Implement | claude | 47.152 | 10.2 | 4.6x |
| TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION | 1 | Investigate | investigator | 291.056 | 63.0 | 4.6x |
| TCK-20260831-READINESS-SPEED-FORMULA | 9 | Architecture-Verify | architecture-reviewer | 247.949 | 53.9 | 4.6x |
| TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP | 3 | Implement | implementer | 45.728 | 10.2 | 4.5x |
| TCK-20260710-HAZARD-KIND-CORPUS-WIDE | 10 | Verify | done-checker | 259.841 | 58.4 | 4.4x |
| TCK-20260817-DEAD-INFRA-REMOVAL-EPIC | 15 | Verify | done-checker | 259.157 | 58.4 | 4.4x |
| TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX | 10 | Verify | claude | 259.081 | 58.4 | 4.4x |
| TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH | 2 | Investigate | investigator | 278.746 | 63.0 | 4.4x |
| TCK-20260904-OWNERSHIP-LIFECYCLE-DOC | 8 | Architecture-Verify | architecture-reviewer | 237.89600000000002 | 53.9 | 4.4x |
| TCK-20260901-HOTFIX-ENTITY-LEDGER-PARITY-BASELINE-DRIFT | 6 | Verify | done-checker | 256.095 | 58.4 | 4.4x |
| TCK-20260711-EPIC-SCOPE-ORPHAN-FIX | 9 | Verify | done-checker | 252.345 | 58.4 | 4.3x |
| TCK-20260824-AFFECTION-CONTRACT-GATE | 5 | Document-Update | doc-updater | 253.687 | 58.7 | 4.3x |
| TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP | 8 | Architecture-Verify | architecture-reviewer | 232.44400000000002 | 53.9 | 4.3x |
| TCK-20260717-GANTT-TIME-AXIS | 6 | Architecture-Verify | architecture-reviewer | 232.32 | 53.9 | 4.3x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 2 | Investigate | investigator | 271.207 | 63.0 | 4.3x |
| TCK-20260717-TICKETS-TAG-SEARCH | 9 | Verify | done-checker | 247.557 | 58.4 | 4.2x |
| TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE | 17 | Verify | done-checker | 245.342 | 58.4 | 4.2x |
| TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE | 5 | Document-Update | doc-updater | 241.711 | 58.7 | 4.1x |
| TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL | 4 | Review | claude | 229.423 | 55.8 | 4.1x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 4 | Review | architecture-reviewer | 228.594 | 55.8 | 4.1x |
| TCK-20260904-WORKING-LOG-CSV-PARSER | 4 | Review | claude | 228.336 | 55.8 | 4.1x |
| TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY | 2 | Investigate | claude | 252.69 | 63.0 | 4.0x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 2 | Investigate | investigator | 251.595 | 63.0 | 4.0x |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 4 | Review | architecture-reviewer | 220.77100000000002 | 55.8 | 4.0x |
| TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION | 1 | Investigate | investigator | 248.818 | 63.0 | 4.0x |
| TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK | 1 | Investigate | claude | 248.793 | 63.0 | 4.0x |
| TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE | 15 | Verify | done-checker | 230.469 | 58.4 | 3.9x |
| TCK-20260831-ITEM-INSTANCE-HISTORY | 9 | Architecture-Verify | architecture-reviewer | 211.915 | 53.9 | 3.9x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 10 | Test-Cleanup-Checkpoint | orchestrator | 102.00200000000001 | 26.4 | 3.9x |
| TCK-20260824-OCCUPATION-CHANGE-TRIGGER | 5 | Document-Update | doc-updater | 225.427 | 58.7 | 3.8x |
| TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE | 2 | Investigate | claude | 240.983 | 63.0 | 3.8x |
| TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD | 2 | Implement | claude | 38.969 | 10.2 | 3.8x |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 5 | Document-Update | doc-updater | 224.764 | 58.7 | 3.8x |
| TCK-20260904-COST-PROXY-EPIC-TICKETS | 4 | Review | architecture-reviewer | 209.253 | 55.8 | 3.7x |
| TCK-20260816-KGMCP-P4-PARITY-ADAPTER | 12 | Verify | done-checker | 219.001 | 58.4 | 3.7x |
| TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE | 11 | Verify | done-checker | 218.014 | 58.4 | 3.7x |
| TCK-20260824-GRIEF-NEMESIS-REACHABILITY | 3 | Plan | planner | 215.294 | 57.9 | 3.7x |
| TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT | 11 | Verify | done-checker | 216.851 | 58.4 | 3.7x |
| TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING | 5 | Document-Update | doc-updater | 217.873 | 58.7 | 3.7x |
| TCK-20260711-DOC-STALENESS-GATE-CHECK | 9 | Verify | done-checker | 214.347 | 58.4 | 3.7x |
| TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS | 10 | Verify | done-checker | 212.822 | 58.4 | 3.6x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 4 | Review | architecture-reviewer | 202.994 | 55.8 | 3.6x |
| TCK-20260824-RELATIONSHIP-ROLE-FIELD | 10 | Verify | done-checker | 211.204 | 58.4 | 3.6x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 5 | Review | architecture-reviewer | 201.013 | 55.8 | 3.6x |
| TCK-20260904-INHERITED-REPUTATION-SEED | 11 | Verify | done-checker | 209.279 | 58.4 | 3.6x |
| TCK-20260904-REPUTATION-LOCALITY-SCOPE | 7 | Architecture-Verify | architecture-reviewer | 190.28900000000002 | 53.9 | 3.5x |
| TCK-20260831-POPULATION-COHORT-SEEDING | 12 | Verify | done-checker | 205.887 | 58.4 | 3.5x |
| TCK-20260823-CI-STEP-SUMMARY-REPORTING | 8 | Document-Update | doc-updater | 206.434 | 58.7 | 3.5x |
| TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE | 2 | Investigate | investigator | 220.452 | 63.0 | 3.5x |
| TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT | 1 | Investigate | investigator | 220.446 | 63.0 | 3.5x |
| TCK-20260730-PROVIDER-HOOK-POLICY | 2 | Investigate | investigator | 219.3 | 63.0 | 3.5x |
| TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE | 2 | Investigate | investigator | 217.08100000000002 | 63.0 | 3.4x |
| TCK-20260904-TEST-SCOPER-HANG-GUARD | 6 | Document-Update | doc-updater | 201.603 | 58.7 | 3.4x |
| TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP | 2 | Investigate | investigator | 214.788 | 63.0 | 3.4x |
| TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE | 1 | Investigate | claude | 214.196 | 63.0 | 3.4x |
| TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY | 2 | Investigate | investigator | 211.216 | 63.0 | 3.4x |
| TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION | 5 | Review | planner | 186.527 | 55.8 | 3.3x |
| TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP | 5 | Document-Update | doc-updater | 195.911 | 58.7 | 3.3x |
| TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG | 2 | Plan | claude | 192.453 | 57.9 | 3.3x |
| TCK-20260730-CLAUDE-EXECUTION-IDENTITY | 3 | Plan | planner | 192.387 | 57.9 | 3.3x |
| TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE | 13 | Verify | done-checker | 193.411 | 58.4 | 3.3x |
| TCK-20260713-SIMQ-SCORE-CEILING-FIX | 4 | Review | architecture-reviewer | 184.09 | 55.8 | 3.3x |
| TCK-20260815-KGMCP-P1-BASELINE-COMPARISON | 10 | Verify | done-checker | 192.136 | 58.4 | 3.3x |
| TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE | 2 | Review | implementer | 181.614 | 55.8 | 3.3x |
| TCK-20260719-LIVE-PHASE-AGENT-LABEL | 9 | Verify | done-checker | 189.63 | 58.4 | 3.2x |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 7 | Architecture-Verify | architecture-reviewer | 174.132 | 53.9 | 3.2x |
| TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC | 3 | Review | architecture-reviewer | 175.284 | 55.8 | 3.1x |
| TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING | 5 | Document-Update | doc-updater | 184.426 | 58.7 | 3.1x |
| TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE | 2 | Plan | planner | 181.614 | 57.9 | 3.1x |
| TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE | 10 | Test-Cleanup-Checkpoint | orchestrator | 82.502 | 26.4 | 3.1x |
| TCK-20260730-CLAUDE-EXECUTION-IDENTITY | 4 | Review | architecture-reviewer | 172.874 | 55.8 | 3.1x |
| TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION | 4 | Review | architecture-reviewer | 172.18 | 55.8 | 3.1x |
| TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP | 6 | Test | test-scoper | 10.997 | 3.6 | 3.1x |
| TCK-20260831-READINESS-SPEED-FORMULA | 4 | Review | architecture-reviewer | 169.064 | 55.8 | 3.0x |
| TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE | 8 | Architecture-Verify | architecture-reviewer | 161.685 | 53.9 | 3.0x |

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
| Retrieval event count | 59 | 0 |
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

**Total:** 4618

### Raw Investigation (Read) Calls

**Total:** 41011
**Read-to-search ratio:** 8.8807

## Tool Safety Audit

### Search-Before-Grep Compliance (Investigate Phase)

_Only the orchestrating run's own direct tools.jsonl rows are visible to this detector — a dispatched sub-agent's (e.g. `investigator`) own search/grep calls are not attributed back to this pair, so a 'non-compliant' pair may reflect an orchestrator-level incidental call rather than the real investigation's own behavior. The true compliance rate for delegated investigation work is unknown and plausibly higher than the rate below._

**Compliance rate:** 70.7% (270/382 Investigate-phase calls)

### Parity Ledger Write-Safety

**`docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build` call:** 35
**Unsafe `parity_index.py build` invocations (real repo path):** 150

### Read-Count Correlation (Search-Before-Grep Compliance)

| Group | Pairs | Median Read count | Avg Read count |
|---|---|---|---|
| Compliant | 270 | 13.0 | 13.7 |
| Non-compliant | 112 | 9.0 | 15.0 |

## Parity Index Read-Path Usage

**`entry`/`impact`/`health` call count:** 4/142317 Bash rows scanned

_Counts tools.jsonl rows where tool == "Bash" and input_summary matches parity_index.py followed immediately by entry, impact, or health (path-anchored, so a filename mention alone — e.g. test_parity_index.py, --help, `git log -- ... parity_index.py`, `sed -n '1,60p' tools/parity_index.py` — never counts). bash_rows_scanned is the total Bash-tool row population this detector ran against (the section's own 'N' denominator). Confirmed 0 real call sites as of TCK-20260731-PARITY-READPATH-GATE's Gate A review (reviewed GO, not yet wired into any real workflow call site) — this is the expected, correct value until a future ticket adds a real entry/impact/health call site, not a bug._

## Skill Usage

### Per-Skill Invocation Counts (This Period)

| Skill | Invocations |
|---|---|
| agent-monitoring-retro | 26 |
| artifact-design | 6 |
| brainstorming | 5 |
| claude-api | 3 |
| claude-in-chrome | 3 |
| cognition-strategy | 1 |
| combat-mechanics | 1 |
| create-tickets | 39 |
| dataviz | 3 |
| fewer-permission-prompts | 2 |
| graphify | 87 |
| implement-epic | 23 |
| implement-ticket | 88 |
| run | 3 |
| simq-audit | 8 |
| update-config | 2 |
| workflow-authoring | 5 |

**Total:** 305

_Derived from tools.jsonl's literal `tool` field, filtered to `tool == 'Skill'`, with the skill name extracted from `input_summary` via regex (r\"'skill':\s*'([^']*)'\") — never json.loads(), since input_summary is a Python dict-repr string, not JSON. Records where the regex finds no match are counted under `unparseable`, never silently dropped. `unattributed` covers Skill invocations with no run_id (interactive, outside any workflow run). Distinct from generate_retro.py's tag_breakdown_skill aggregate — this is a raw per-skill invocation count, not a tag-driven gate-hit count._

### Zero-Invocation Flags (All-Time, 14-Day Grace Period)

**Flagged (confirmed age past grace period):** api-design-principles, architecture, backend-testing, observability, progression-entities, simq-dev, systems-economy
**Flagged (unknown age, no `date_added`):** debugging-strategies, doc-coauthoring, frontend-design, prompt-builder, python-performance-optimization, python-testing-patterns, test-driven-development

_All-time (never period-scoped) cross-reference of the real .claude/skills/*/SKILL.md catalog against build_skill_usage_section(tools)'s per_skill counts. A skill with any nonzero invocation count is never flagged, regardless of age. Of the remaining zero-invocation skills: `flagged_stale` requires a real, parseable `date_added` older than the 14-day grace period — a confirmed-age signal. `flagged_unknown_age` covers skills with no (or unparseable) `date_added` and zero invocations — an honest, lower-certainty signal, not proof of staleness, since no authorship date can be established. This fail-open policy on missing date_added is deliberate: it is what makes backend-testing's real pre-TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED state (no date_added field at all) correctly flaggable, per TCK-20260810-SKILL-USAGE-RETRO-TRACKING's AC2._

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

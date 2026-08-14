# Agent Monitoring Retro — Last 7 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 69 |
| Completed (DONE) | 44 (63%) |
| Gate failures | 23 |
| Avg duration | 91 min |
| Avg agents per run | 5.7 |
| Total agent calls | 400 |

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| NEEDS_CHANGES | 8 | 11% |
| DOD_BLOCKED | 6 | 8% |
| NEEDS_HUMAN_INPUT | 4 | 5% |
| CONFLICTS_DETECTED | 3 | 4% |
| TESTS_FAILED | 2 | 2% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 7 |
| needs_changes | 5 |
| conflicts_detected | 3 |
| DOC_STALENESS_BLOCKED | 1 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| dashboard | 6 | 50% | 2 |
| observability | 14 | 71% | 4 |
| simulation-quality | 1 | 100% | 0 |
| testing | 21 | 52% | 10 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| security | 8 | 7 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 2 | 1 | 1 | 100% |
| hotfix | 18 | 0 | 15 | 83% |
| n/a | 2 | 0 | 2 | 100% |
| standard | 47 | 0 | 26 | 55% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| architecture-reviewer | 63 | 45 | 11 | 4 | 3 |
| claude | 8 | 8 | 0 | 0 | 0 |
| context-packet-wrapper | 2 | 2 | 0 | 0 | 0 |
| create-tickets | 4 | 4 | 0 | 0 | 0 |
| doc-updater | 8 | 8 | 0 | 0 | 0 |
| done-checker | 43 | 35 | 7 | 1 | 0 |
| finalizer | 33 | 33 | 0 | 0 | 0 |
| implementer | 35 | 34 | 1 | 0 | 0 |
| investigate:C1 | 5 | 5 | 0 | 0 | 0 |
| investigate:C2 | 3 | 3 | 0 | 0 | 0 |
| investigate:C3 | 3 | 3 | 0 | 0 | 0 |
| investigate:C4 | 1 | 1 | 0 | 0 | 0 |
| investigator | 28 | 24 | 0 | 1 | 3 |
| link-epic | 4 | 4 | 0 | 0 | 0 |
| orchestrator | 9 | 9 | 0 | 0 | 0 |
| parity-updater | 31 | 20 | 0 | 0 | 11 |
| planner | 31 | 23 | 0 | 5 | 3 |
| security-reviewer | 2 | 2 | 0 | 0 | 0 |
| structure | 5 | 5 | 0 | 0 | 0 |
| test-scoper | 34 | 32 | 2 | 0 | 0 |
| ticket-scoper | 46 | 43 | 3 | 0 | 0 |
| write-sequence | 2 | 2 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 28 | 23 | 3 | 2 | 0 |
| Comprehend | 5 | 5 | 0 | 0 | 0 |
| Document-Update | 8 | 8 | 0 | 0 | 0 |
| Finalize | 39 | 39 | 0 | 0 | 0 |
| Implement | 37 | 36 | 1 | 0 | 0 |
| Investigate | 40 | 36 | 0 | 1 | 3 |
| Link | 4 | 4 | 0 | 0 | 0 |
| Parity | 31 | 20 | 0 | 0 | 11 |
| Plan | 31 | 23 | 0 | 5 | 3 |
| Retrieval | 2 | 2 | 0 | 0 | 0 |
| Review | 35 | 22 | 8 | 2 | 3 |
| Scope | 41 | 38 | 3 | 0 | 0 |
| Security-Review | 2 | 2 | 0 | 0 | 0 |
| Structure | 5 | 5 | 0 | 0 | 0 |
| Test | 38 | 36 | 2 | 0 | 0 |
| Verify | 43 | 35 | 7 | 1 | 0 |
| Write | 11 | 11 | 0 | 0 | 0 |

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 28 | 729.9 | 26.1 |
| Document-Update | 8 | 0.0 | 0.0 |
| Finalize | 39 | 1531.4 | 39.3 |
| Implement | 37 | 2146.6 | 58.0 |
| Investigate | 27 | 998.7 | 37.0 |
| Parity | 31 | 406.7 | 13.1 |
| Plan | 31 | 1009.1 | 32.6 |
| Review | 35 | 781.7 | 22.3 |
| Scope | 40 | 621.6 | 15.5 |
| Security-Review | 2 | 0.0 | 0.0 |
| Test | 38 | 1344.6 | 35.4 |
| Verify | 43 | 1979.7 | 46.0 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 63 | 1511.5 | 24.0 |
| claude | 7 | 0.0 | 0.0 |
| doc-updater | 8 | 0.0 | 0.0 |
| done-checker | 43 | 1979.7 | 46.0 |
| finalizer | 33 | 1531.4 | 46.4 |
| implementer | 35 | 2146.6 | 61.3 |
| investigator | 27 | 998.7 | 37.0 |
| orchestrator | 9 | 0.0 | 0.0 |
| parity-updater | 31 | 406.7 | 13.1 |
| planner | 31 | 1009.1 | 32.6 |
| security-reviewer | 2 | 0.0 | 0.0 |
| test-scoper | 34 | 1344.6 | 39.5 |
| ticket-scoper | 36 | 621.6 | 17.3 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 1 |

## Slow Runs (> 30 min)

| run_id | duration | final_status |
|---|---|---|
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 613 min | DONE |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 610 min | NEEDS_CHANGES |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 603 min | NEEDS_CHANGES |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | 592 min | NEEDS_CHANGES |
| TCK-20260801-CODEX-REALREPO-PILOT-HARNESS | 440 min | DONE |
| TCK-20260802-STORED-ARTIFACT-KIND | 373 min | DONE |
| TCK-20260731-CODEX-PILOT-EXECUTOR | 295 min | DONE |
| TCK-20260804-EXPANSION-RATE-WIRING | 284 min | DONE |
| TCK-20260702-OBSISO-ISOLATION-PROOF | 106 min | DONE |
| TCK-20260702-OBSISO-TRACE-ASYNC | 95 min | DONE |
| TCK-20260702-OBSISO-BROKER-CONFIG | 93 min | DONE |
| TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC | 86 min | DONE |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 81 min | DONE |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 78 min | DONE |
| TCK-20260801-CODEX-LIVE-TRANSPORT | 78 min | DONE |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 76 min | DOD_BLOCKED |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 72 min | DOD_BLOCKED |
| TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY | 66 min | DONE |
| TCK-20260802-DOC-UPDATE-DISCIPLINE | 65 min | DONE |
| TCK-20260731-PARITY-READPATH-GATE | 62 min | DONE |
| TCK-20260731-PARITY-INDEX-IMPORTER | 60 min | DONE |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 51 min | DONE |
| TCK-20260804-SKILL-JS-PHASE-SYNC | 45 min | DONE |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 44 min | DOD_BLOCKED |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 41 min | DONE |
| TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX | 40 min | DONE |
| TCK-20260731-PARITY-IMPACT-PROOF | 39 min | DONE |
| TCK-20260802-CONTEXT-KIND-PRIORITY | 36 min | DONE |
| TCK-20260802-EXACT-LOOKUP-CONVENTION | 35 min | DONE |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 33 min | DOD_BLOCKED |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 33 min | TESTS_FAILED |
| TCK-20260731-PARITY-INDEX-BASELINE | 31 min | DONE |

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Duration outliers (by tier)

| run_id | tier | duration_s | tier median | ratio |
|---|---|---|---|---|
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36832 | 2581.0 | 14.3x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36615 | 2581.0 | 14.2x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 36222 | 2581.0 | 14.0x |
| TCK-20260801-CODEX-PILOT-ORCHESTRATION | standard | 35563 | 2581.0 | 13.8x |
| TCK-20260801-CODEX-REALREPO-PILOT-HARNESS | standard | 26413 | 2581.0 | 10.2x |
| TCK-20260802-STORED-ARTIFACT-KIND | standard | 22385 | 2581.0 | 8.7x |
| TCK-20260804-SKILL-JS-PHASE-SYNC | hotfix | 2702 | 325.0 | 8.3x |
| TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX | hotfix | 2457 | 325.0 | 7.6x |
| TCK-20260731-CODEX-PILOT-EXECUTOR | standard | 17701 | 2581.0 | 6.9x |
| TCK-20260804-EXPANSION-RATE-WIRING | standard | 17081 | 2581.0 | 6.6x |
| TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE | hotfix | 1764 | 325.0 | 5.4x |
| TCK-20260730-PROGRESS-TIMELINE-VIEW-HOTFIX | hotfix | 1500 | 325.0 | 4.6x |
| TCK-20260804-PLANS-EXPERIMENTS-SWEEP | hotfix | 1090 | 325.0 | 3.4x |

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 10 | Verify | done-checker | 147.07999999999998 | 3.7 | 39.5x |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 11 | Verify | done-checker | 140.046 | 3.7 | 37.7x |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 10 | Verify | done-checker | 138.61599999999999 | 3.7 | 37.3x |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 9 | Verify | done-checker | 125.309 | 3.7 | 33.7x |
| TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX | 9 | Verify | done-checker | 119.905 | 3.7 | 32.2x |
| TCK-20260731-PARITY-READPATH-GATE | 10 | Verify | done-checker | 115.46600000000001 | 3.7 | 31.0x |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 8 | Verify | done-checker | 115.212 | 3.7 | 31.0x |
| TCK-20260731-PARITY-IMPACT-PROOF | 9 | Verify | done-checker | 112.25999999999999 | 3.7 | 30.2x |
| TCK-20260731-PARITY-INDEX-BASELINE | 19 | Verify | done-checker | 85.90100000000001 | 3.7 | 23.1x |
| TCK-20260802-EXACT-LOOKUP-CONVENTION | 10 | Verify | done-checker | 83.506 | 3.7 | 22.5x |
| TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE | 8 | Verify | done-checker | 81.139 | 3.7 | 21.8x |
| TCK-20260731-PARITY-INDEX-IMPORTER | 10 | Verify | done-checker | 80.375 | 3.7 | 21.6x |
| TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE | 11 | Verify | done-checker | 79.461 | 3.7 | 21.4x |
| TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION | 11 | Verify | done-checker | 75.504 | 3.7 | 20.3x |
| TCK-20260803-DOCS-STRUCTURE-AUDIT | 9 | Verify | done-checker | 72.937 | 3.7 | 19.6x |
| TCK-20260803-RETRO-TOOL-SAFETY-AUDIT | 12 | Verify | done-checker | 71.39 | 3.7 | 19.2x |
| TCK-20260802-CONTEXT-KIND-PRIORITY | 10 | Verify | done-checker | 70.357 | 3.7 | 18.9x |
| TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX | 10 | Verify | done-checker | 66.045 | 3.7 | 17.8x |
| TCK-20260803-DOC-UPDATER-CORE-WIRING | 10 | Verify | done-checker | 65.912 | 3.7 | 17.7x |
| TCK-20260802-STORED-ARTIFACT-KIND | 11 | Verify | done-checker | 65.601 | 3.7 | 17.6x |
| TCK-20260803-BRAINSTORM-SKILL-STALE-PATH | 8 | Verify | done-checker | 63.993 | 3.7 | 17.2x |

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
| Retrieval event count | 2 | 0 |
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

**Compliance rate:** 85.7% (12/14 Investigate-phase calls)

### Parity Ledger Write-Safety

**`docs/parity_ledger/*.yaml` write violations:** 14
**Unsafe `parity_index.py build` invocations (real repo path):** 1

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

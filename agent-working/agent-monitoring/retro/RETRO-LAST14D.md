# Agent Monitoring Retro — Last 14 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 370 |
| Completed (DONE) | 358 (96%) |
| Gate failures | 8 |
| Avg duration | 82 min |
| Avg agents per run | 6.3 |
| Total agent calls | 2327 |

**By execution mode**

| Mode | Runs | DONE | Avg duration |
|---|---|---|---|
| Pipeline | 9 | 3 (33%) | 61 min |
| Hand-closed | 274 | 269 (98%) | 132 min |
| Native workflow | 3 | 2 (66%) | 17 min |
| Unlabelled (pre-field) | 84 | 84 (100%) | 49 min |

_Note: 372 raw `runs.jsonl` rows in this window collapsed to 370 real executions after deduplicating gate-checkpoint rows that share one `(run_id, execution_id, start_ts)` identity (TCK-20260915-DUPLICATE-RUN-RECORDS) — the counts above are the deduplicated figures._

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| NEEDS_HUMAN_INPUT | 3 | 0% |
| WORKFLOW_ERROR | 2 | 0% |
| TESTS_FAILED | 1 | 0% |
| NOTHING_TO_DO | 1 | 0% |
| NATIVE_GATE_SITES_UNPORTED | 1 | 0% |

## Reason Codes

| Reason | Count |
|---|---|
| dod_condition_failed | 3 |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| architecture | 69 | 100% | 0 |
| cognition | 7 | 100% | 0 |
| combat | 16 | 87% | 2 |
| content | 3 | 100% | 0 |
| core | 1 | 100% | 0 |
| delivery | 35 | 97% | 0 |
| economy | 3 | 33% | 2 |
| engine | 18 | 100% | 0 |
| faction | 4 | 50% | 2 |
| governance | 31 | 93% | 0 |
| lifecycle | 8 | 100% | 0 |
| live-map | 17 | 100% | 0 |
| mcp | 20 | 100% | 0 |
| observability | 19 | 94% | 1 |
| progression | 3 | 100% | 0 |
| rendering | 3 | 100% | 0 |
| resource | 3 | 33% | 2 |
| simulation-quality | 9 | 100% | 0 |
| social | 4 | 100% | 0 |
| strategy | 5 | 100% | 0 |
| testing | 93 | 97% | 2 |
| world | 30 | 96% | 1 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| performance | 29 | N/A — no gate implemented |
| security | 4 | 0 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 21 | 4 | 16 | 94% |
| hotfix | 105 | 0 | 103 | 98% |
| n/a | 4 | 0 | 4 | 100% |
| standard | 240 | 0 | 235 | 97% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| architecture-reviewer | 31 | 24 | 1 | 0 | 6 |
| architecture-reviewer-shadow | 6 | 6 | 0 | 0 | 0 |
| claude | 2037 | 1684 | 0 | 0 | 353 |
| context-packet-wrapper | 6 | 6 | 0 | 0 | 0 |
| create-tickets | 4 | 4 | 0 | 0 | 0 |
| doc-updater | 14 | 14 | 0 | 0 | 0 |
| done-checker | 19 | 13 | 6 | 0 | 0 |
| finalizer | 13 | 13 | 0 | 0 | 0 |
| implement-epic | 1 | 1 | 0 | 0 | 0 |
| implement-ticket | 2 | 2 | 0 | 0 | 0 |
| implement-ticket-orchestrator | 3 | 0 | 3 | 0 | 0 |
| implementer | 71 | 65 | 0 | 0 | 6 |
| investigate:C1 | 4 | 4 | 0 | 0 | 0 |
| investigate:C2 | 3 | 3 | 0 | 0 | 0 |
| investigate:C3 | 3 | 3 | 0 | 0 | 0 |
| investigate:C4 | 2 | 2 | 0 | 0 | 0 |
| investigate:C5 | 1 | 1 | 0 | 0 | 0 |
| investigate:C6 | 1 | 1 | 0 | 0 | 0 |
| investigator | 19 | 15 | 0 | 0 | 4 |
| link-epic | 2 | 2 | 0 | 0 | 0 |
| parity-updater | 13 | 6 | 0 | 0 | 7 |
| planner | 20 | 11 | 0 | 5 | 4 |
| structure | 4 | 4 | 0 | 0 | 0 |
| test-scoper | 18 | 13 | 5 | 0 | 0 |
| ticket-scoper | 28 | 28 | 0 | 0 | 0 |
| write-sequence | 2 | 2 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 29 | 20 | 0 | 0 | 9 |
| Comprehend | 4 | 4 | 0 | 0 | 0 |
| Discover | 1 | 1 | 0 | 0 | 0 |
| Document-Update | 22 | 16 | 0 | 0 | 6 |
| Finalize | 354 | 354 | 0 | 0 | 0 |
| Implement | 347 | 327 | 0 | 0 | 20 |
| Investigate | 87 | 82 | 0 | 0 | 5 |
| Link | 2 | 2 | 0 | 0 | 0 |
| Parity | 324 | 35 | 0 | 0 | 289 |
| Plan | 60 | 50 | 0 | 5 | 5 |
| Retrieval | 6 | 6 | 0 | 0 | 0 |
| Review | 24 | 11 | 1 | 0 | 12 |
| Scope | 358 | 350 | 3 | 0 | 5 |
| Security-Review | 10 | 0 | 0 | 0 | 10 |
| Structure | 4 | 4 | 0 | 0 | 0 |
| Test | 345 | 321 | 5 | 0 | 19 |
| Verify | 337 | 331 | 6 | 0 | 0 |
| Write | 13 | 13 | 0 | 0 | 0 |

_Computed over 12.8% of this window's events (299 of 2327 scored) — see TCK-20260915-SIDECAR-ATTRIBUTION-GAP for why the rest lack a `cost_proxy_score`._

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 14 | 652.9 | 46.6 |
| Comprehend | 4 | 690.8 | 172.7 |
| Discover | 1 | 0.0 | 0.0 |
| Document-Update | 15 | 6166.4 | 411.1 |
| Finalize | 15 | 962.3 | 64.2 |
| Implement | 30 | 8534.3 | 284.5 |
| Investigate | 42 | 1530.2 | 36.4 |
| Link | 2 | 2.9 | 1.4 |
| Parity | 14 | 459.4 | 32.8 |
| Plan | 29 | 1306.7 | 45.1 |
| Review | 15 | 682.1 | 45.5 |
| Scope | 57 | 4377.9 | 76.8 |
| Structure | 4 | 314.4 | 78.6 |
| Test | 23 | 4282.2 | 186.2 |
| Verify | 21 | 1356.3 | 64.6 |
| Write | 13 | 3.0 | 0.2 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 29 | 1335.0 | 46.0 |
| claude | 82 | 5214.7 | 63.6 |
| create-tickets | 4 | 690.8 | 172.7 |
| doc-updater | 14 | 6115.8 | 436.8 |
| done-checker | 19 | 1300.2 | 68.4 |
| finalizer | 13 | 962.3 | 74.0 |
| implement-epic | 1 | 0.0 | 0.0 |
| implement-ticket | 2 | 0.0 | 0.0 |
| implement-ticket-orchestrator | 3 | 0.0 | 0.0 |
| implementer | 15 | 8356.2 | 557.1 |
| investigate:C1 | 4 | 0.0 | 0.0 |
| investigate:C2 | 3 | 0.0 | 0.0 |
| investigate:C3 | 3 | 0.0 | 0.0 |
| investigate:C4 | 2 | 0.0 | 0.0 |
| investigate:C5 | 1 | 0.0 | 0.0 |
| investigate:C6 | 1 | 0.0 | 0.0 |
| investigator | 17 | 1062.5 | 62.5 |
| link-epic | 2 | 2.9 | 1.4 |
| parity-updater | 13 | 459.2 | 35.3 |
| planner | 19 | 819.6 | 43.1 |
| structure | 4 | 314.4 | 78.6 |
| test-scoper | 18 | 3893.8 | 216.3 |
| ticket-scoper | 28 | 791.2 | 28.3 |
| write-sequence | 2 | 3.0 | 1.5 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 43 |

## Slow Runs (> 30 min)

| run_id | duration | active | idle | final_status |
|---|---|---|---|---|
| TCK-20261003-AGENT-WORKING-ROOT-MOVE | 454 min | 0 min | 454 min | DONE |
| TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION | 353 min | 89 min | 263 min | DONE |
| TCK-20261004-REMOVE-THE-DORMANT-PARTY-COMMAND-METHOD | 207 min | 0 min | 207 min | DONE |
| TCK-20261004-BIBLE-07-DESCRIBES-PARTY-COMMAND-BEHAVIOUR-THAT-NEVER-OCCURS | 207 min | 0 min | 207 min | DONE |
| TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT | 207 min | 0 min | 207 min | DONE |
| TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION | 207 min | 0 min | 207 min | DONE |
| TCK-20261004-GENERATOR-AUTHORS-UNASSEMBLABLE-COMPOSITION-ON-REGION-ID-COLLISION | 206 min | 0 min | 206 min | DONE |
| TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP | 189 min | 0 min | 189 min | DONE |
| FOLDER-tickets-todos-systemic-world-first-wave | 130 min | 0 min | 130 min | DONE |
| TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE | 102 min | 67 min | 35 min | DONE |
| TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP | 96 min | 0 min | 189 min | TESTS_FAILED |
| TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING | 67 min | 67 min | 0 min | DONE |
| TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY | 55 min | 55 min | 0 min | DONE |
| TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE | 52 min | 52 min | 0 min | DONE |
| TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION | 46 min | 46 min | 0 min | DONE |
| TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP | 46 min | 46 min | 0 min | DONE |
| TCK-20260924-M2-MAPPING-DRIFT-DETECTION | 45 min | 8 min | 37 min | DONE |
| TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP | 36 min | 36 min | 0 min | DONE |
| TCK-20260923-STATUS-VOCABULARY-RECONCILIATION | 32 min | 32 min | 0 min | DONE |

_11 of the runs above spend at least half their reported duration idle (gaps ≥ 30 min between phase transitions, e.g. waiting on human review) rather than in active work — see `active`/`idle` columns; "slow" here does not mean "took a long time to actively work on."_

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION | 12 | Parity | parity-updater | 100.38 | 0.1 | 1024.3x |
| TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION | 9 | Parity | parity-updater | 96.858 | 0.1 | 988.3x |
| TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION | 8 | Implement | implementer | 5859.419 | 7.8 | 748.2x |
| TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE | 10 | Parity | parity-updater | 68.733 | 0.1 | 701.4x |
| TCK-20260924-M2-MAPPING-DRIFT-DETECTION | 9 | Parity | parity-updater | 66.376 | 0.1 | 677.3x |
| TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT | 12 | Parity | parity-updater | 65.82300000000001 | 0.1 | 671.7x |
| TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE | 9 | Parity | parity-updater | 60.984 | 0.1 | 622.3x |
| TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP | 11 | Implement | implementer | 1133.679 | 7.8 | 144.8x |
| TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP | 6 | Document-Update | doc-updater | 4629.581 | 67.7 | 68.4x |
| TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING | 5 | Implement | implementer | 483.557 | 7.8 | 61.7x |
| TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE | 5 | Implement | implementer | 382.107 | 7.8 | 48.8x |
| TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT | 2 | Investigate | claude | 205.38 | 5.2 | 39.8x |
| TCK-20260924-M2-MAPPING-DRIFT-DETECTION | 5 | Implement | implementer | 291.619 | 7.8 | 37.2x |
| TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE | 2 | Investigate | investigator | 168.303 | 5.2 | 32.6x |
| TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK | 2 | Investigate | claude | 145.195 | 5.2 | 28.1x |
| TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY | 5 | Implement | implementer | 205.861 | 7.8 | 26.3x |
| TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE | 2 | Investigate | investigator | 94.543 | 5.2 | 18.3x |
| TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION | 2 | Investigate | investigator | 89.49600000000001 | 5.2 | 17.3x |
| TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION | 2 | Investigate | investigator | 89.333 | 5.2 | 17.3x |
| TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY | 2 | Investigate | investigator | 82.616 | 5.2 | 16.0x |
| TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING | 2 | Investigate | investigator | 79.82300000000001 | 5.2 | 15.5x |
| TCK-20260924-M2-MAPPING-DRIFT-DETECTION | 2 | Investigate | investigator | 78.029 | 5.2 | 15.1x |
| TCK-20260923-STATUS-VOCABULARY-RECONCILIATION | 2 | Investigate | investigator | 76.174 | 5.2 | 14.8x |
| TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT | 5 | Investigate | investigator | 70.30799999999999 | 5.2 | 13.6x |
| TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT | 2 | Investigate | investigator | 59.52 | 5.2 | 11.5x |
| TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP | 5 | Investigate | investigator | 59.005 | 5.2 | 11.4x |
| TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP | 2 | Investigate | investigator | 57.961 | 5.2 | 11.2x |
| TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING | 8 | Test | test-scoper | 887.085 | 79.6 | 11.1x |
| TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP | 8 | Investigate | investigator | 57.345 | 5.2 | 11.1x |
| TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT | 1 | Scope | claude | 469.63800000000003 | 53.4 | 8.8x |
| TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE | 8 | Test | test-scoper | 665.8000000000001 | 79.6 | 8.4x |
| TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP | 1 | Scope | claude | 437.466 | 53.4 | 8.2x |
| TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS | 4 | Test | test-scoper | 606.643 | 79.6 | 7.6x |
| TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS | 2 | Investigate | claude | 38.905 | 5.2 | 7.5x |
| TCK-20261003-PATH-MAP-INDEX-REBUILD-COMMANDS | 5 | Implement | claude | 53.985 | 7.8 | 6.9x |
| TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP | 9 | Test | test-scoper | 530.85 | 79.6 | 6.7x |
| TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX | 1 | Scope | claude | 304.51599999999996 | 53.4 | 5.7x |
| TCK-20260928-MONITORING-LOADER-CWD-RELATIVE-PATHS | 1 | Scope | claude | 287.387 | 53.4 | 5.4x |
| TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS | 1 | Scope | claude | 270.89099999999996 | 53.4 | 5.1x |
| TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY | 2 | Investigate | claude | 23.024 | 5.2 | 4.5x |
| TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE | 10 | Verify | done-checker | 291.788 | 67.7 | 4.3x |
| TCK-20260914-BOSS-KINDS-OBSERVABILITY-CONSTANT-DRIFT | 8 | Document-Update | doc-updater | 284.655 | 67.7 | 4.2x |
| TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION | 11 | Test | test-scoper | 324.743 | 79.6 | 4.1x |
| TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC | 1 | Scope | claude | 211.972 | 53.4 | 4.0x |
| TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE | 5 | Document-Update | doc-updater | 262.915 | 67.7 | 3.9x |
| TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE | 12 | Finalize | finalizer | 245.804 | 66.7 | 3.7x |
| TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE | 1 | Scope | claude | 193.221 | 53.4 | 3.6x |
| TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT | 1 | Scope | claude | 187.88 | 53.4 | 3.5x |
| TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION | 5 | Document-Update | doc-updater | 231.185 | 67.7 | 3.4x |
| TCK-20260923-STATUS-VOCABULARY-RECONCILIATION | 5 | Document-Update | doc-updater | 212.418 | 67.7 | 3.1x |
| TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE | 2 | Investigate | claude | 15.521 | 5.2 | 3.0x |

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
| Retrieval event count | 6 | 0 |
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

**Total:** 334

### Raw Investigation (Read) Calls

**Total:** 765
**Read-to-search ratio:** 2.2904

## Tool Safety Audit

### Search-Before-Grep Compliance (Investigate Phase)

_Only the orchestrating run's own direct tools.jsonl rows are visible to this detector — a dispatched sub-agent's (e.g. `investigator`) own search/grep calls are not attributed back to this pair, so a 'non-compliant' pair may reflect an orchestrator-level incidental call rather than the real investigation's own behavior. The true compliance rate for delegated investigation work is unknown and plausibly higher than the rate below._

**Compliance rate:** 75.0% (18/24 Investigate-phase calls)

### Parity Ledger Write-Safety

**`docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build` call:** 0
**Unsafe `parity_index.py build` invocations (real repo path):** 2

### Read-Count Correlation (Search-Before-Grep Compliance)

| Group | Pairs | Median Read count | Avg Read count |
|---|---|---|---|
| Compliant | 18 | 2.5 | 6.2 |
| Non-compliant | 6 | 2.0 | 5.0 |

## Parity Index Read-Path Usage

**`entry`/`impact`/`health` call count:** 0/4576 Bash rows scanned

_Counts tools.jsonl rows where tool == "Bash" and input_summary matches parity_index.py followed immediately by entry, impact, or health (path-anchored, so a filename mention alone — e.g. test_parity_index.py, --help, `git log -- ... parity_index.py`, `sed -n '1,60p' tools/parity_index.py` — never counts). bash_rows_scanned is the total Bash-tool row population this detector ran against (the section's own 'N' denominator). Confirmed 0 real call sites as of TCK-20260731-PARITY-READPATH-GATE's Gate A review (reviewed GO, not yet wired into any real workflow call site) — this is the expected, correct value until a future ticket adds a real entry/impact/health call site, not a bug._

## Skill Usage

### Zero-Invocation Flags (All-Time, 14-Day Grace Period)

**Covered by another channel (zero `Skill`-tool calls does not mean unused):**
- `api-design-principles` — tag-driven routing via tag 'api-design' (tag_registry.py::get_skill_mapping())
- `debugging-strategies` — tag-driven routing via tag 'debugging' (tag_registry.py::get_skill_mapping())
- `python-performance-optimization` — tag-driven routing via tag 'performance' (tag_registry.py::get_skill_mapping())

**Flagged (confirmed age past grace period):** architecture, backend-testing, observability, progression-entities, simq-dev, systems-economy
**Flagged (unknown age, no `date_added`):** doc-coauthoring, frontend-design, prompt-builder, python-testing-patterns, test-driven-development

_All-time (never period-scoped) cross-reference of the real .claude/skills/*/SKILL.md catalog against build_skill_usage_section(tools)'s per_skill counts. A skill with any nonzero invocation count is never flagged, regardless of age. A zero count here means only 'not invoked as a Skill tool call' -- it does NOT mean unused: a skill named in tag_registry.py::get_skill_mapping() (tag-driven routing) is reported separately as `covered_by_other_channel`, with the covering channel named, and is never counted toward either flag below -- a capability delivered by agent dispatch, phase-prompt enrichment, or an unconditional test guard reads as zero forever under this tool-only count, so flagging it as stale/unused would be wrong regardless of age. Of the remaining, genuinely-uncovered zero-invocation skills: `flagged_stale` requires a real, parseable `date_added` older than the 14-day grace period — a confirmed-age signal. `flagged_unknown_age` covers skills with no (or unparseable) `date_added` and zero invocations — an honest, lower-certainty signal, not proof of staleness, since no authorship date can be established. This fail-open policy on missing date_added is deliberate: it is what makes backend-testing's real pre-TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED state (no date_added field at all) correctly flaggable, per TCK-20260810-SKILL-USAGE-RETRO-TRACKING's AC2._

## Session-Layer Measures

_Headline metric and batch latency from `docs/plans/agent_infrastructure/session_layer_working_process.md` section 11. Counts are repeated instructions, never decisions, design feedback or requirements. `sample` is the conservative prompt tagger (under-counts); `tally` is the owner's own line per batch._

### Manual orchestration actions

| category | sample | tally |
|---|---|---|
| role reminder | 0 | 0 |
| routing correction | 0 | 0 |
| manual wake | 0 | 0 |
| worktree correction | 0 | 0 |
| boundary reminder | 0 | 0 |
| handover recovery | 0 | 0 |

Total: 0. Per-batch: tally with `manual_actions.py tally <category> --batch <id>`.

### Runs by session role

| session_role | runs |
|---|---|
| unresolved | 370 |

_`unresolved` = no binding names the session (plain session) or the record predates `session_role`._

### `role_boundary` warnings (advisory)

None in this period.

### Batch latency

Not computed for this report. Pass `--latency-prs <N> ...` to derive implementation, finalization and cycle time from merged PRs (`unknown` when a timestamp is unavailable, never zero).

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

### Deep review — 2026-09-15 (`agent-working-design`)

Written after the 2026-09-11→15 agent-infrastructure batch closed (PRs #194, #197, #199, #201 all
merged). Numbers below were derived directly from the sharded `agent-working/agent-monitoring/data/*/` JSONL
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
- **55 events and 66 runs carry an unusable `ts`**; `agent-working/agent-monitoring/data/unknown-week/` holds 34
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

`agent-working/agent-monitoring/retro/index.md` currently shows:

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

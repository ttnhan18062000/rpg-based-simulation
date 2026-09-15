# Agent Monitoring Retro — Last 7 Days

---

## Run Summary

| Metric | Value |
|---|---|
| Total runs | 107 |
| Completed (DONE) | 98 (91%) |
| Gate failures | 9 |
| Avg duration | 258 min |
| Avg agents per run | 6.4 |
| Total agent calls | 702 |

_Note: 108 raw `runs.jsonl` rows in this window collapsed to 107 real executions after deduplicating gate-checkpoint rows that share one `(run_id, execution_id, start_ts)` identity (TCK-20260915-DUPLICATE-RUN-RECORDS) — the counts above are the deduplicated figures._

## Gate Failure Breakdown

| Gate | Count | % of runs |
|---|---|---|
| BLOCKED | 7 | 6% |
| NEEDS_CHANGES | 2 | 1% |

## Tag Breakdown — Subsystem/Topic

| Tag | Runs | DONE rate | Gate failures |
|---|---|---|---|
| architecture | 26 | 96% | 1 |
| cognition | 22 | 77% | 5 |
| combat | 4 | 75% | 1 |
| content | 8 | 100% | 0 |
| economy | 1 | 100% | 0 |
| engine | 2 | 100% | 0 |
| faction | 1 | 100% | 0 |
| feature-flags | 1 | 100% | 0 |
| governance | 5 | 100% | 0 |
| grand-strategy | 1 | 100% | 0 |
| information | 4 | 75% | 1 |
| mcp | 7 | 100% | 0 |
| observability | 7 | 100% | 0 |
| rendering | 1 | 100% | 0 |
| self-model | 6 | 50% | 3 |
| simulation-quality | 6 | 100% | 0 |
| social | 6 | 100% | 0 |
| strategy | 3 | 100% | 0 |
| testing | 11 | 81% | 2 |
| world | 16 | 100% | 0 |

## Tag Breakdown — Process/Skill-signal

| Tag | Runs | Gate Hits |
|---|---|---|
| api-design | 2 | N/A — no gate implemented |
| performance | 7 | N/A — no gate implemented |
| security | 1 | 1 |

## Tier Distribution

| Tier | Count | Scoped | DONE count | DONE rate |
|---|---|---|---|---|
| epic | 1 | 0 | 1 | 100% |
| hotfix | 28 | 0 | 28 | 100% |
| n/a | 1 | 0 | 1 | 100% |
| standard | 77 | 0 | 68 | 88% |

## Agent Status Distribution

| Agent | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| architecture-reviewer | 21 | 15 | 4 | 2 | 0 |
| claude | 591 | 505 | 0 | 7 | 79 |
| create-tickets | 1 | 1 | 0 | 0 | 0 |
| doc-updater | 6 | 6 | 0 | 0 | 0 |
| done-checker | 10 | 9 | 0 | 1 | 0 |
| finalizer | 7 | 7 | 0 | 0 | 0 |
| implementer | 8 | 8 | 0 | 0 | 0 |
| investigate:C1 | 1 | 1 | 0 | 0 | 0 |
| investigate:C2 | 1 | 1 | 0 | 0 | 0 |
| investigator | 8 | 4 | 0 | 0 | 4 |
| link-epic | 1 | 1 | 0 | 0 | 0 |
| orchestrator | 18 | 13 | 0 | 0 | 5 |
| parity-updater | 4 | 4 | 0 | 0 | 0 |
| planner | 8 | 4 | 0 | 0 | 4 |
| security-reviewer | 1 | 1 | 0 | 0 | 0 |
| structure | 1 | 1 | 0 | 0 | 0 |
| test-scoper | 5 | 5 | 0 | 0 | 0 |
| ticket-scoper | 10 | 10 | 0 | 0 | 0 |

## Phase Status Distribution

| Phase | Calls | ok | failed | blocked | skipped |
|---|---|---|---|---|---|
| Architecture-Verify | 12 | 12 | 0 | 0 | 0 |
| Comprehend | 1 | 1 | 0 | 0 | 0 |
| Document-Update | 12 | 11 | 0 | 0 | 1 |
| Finalize | 103 | 101 | 0 | 2 | 0 |
| Implement | 100 | 93 | 0 | 1 | 6 |
| Investigate | 31 | 26 | 0 | 1 | 4 |
| Link | 1 | 1 | 0 | 0 | 0 |
| Parity | 91 | 18 | 0 | 0 | 73 |
| Plan | 17 | 13 | 0 | 0 | 4 |
| Review | 18 | 12 | 4 | 2 | 0 |
| Scope | 105 | 105 | 0 | 0 | 0 |
| Security-Review | 3 | 1 | 0 | 0 | 2 |
| Structure | 1 | 1 | 0 | 0 | 0 |
| Test | 100 | 97 | 0 | 1 | 2 |
| Verify | 105 | 102 | 0 | 3 | 0 |
| Write | 2 | 2 | 0 | 0 | 0 |

_Computed over 21.7% of this window's events (152 of 702 scored) — see TCK-20260915-SIDECAR-ATTRIBUTION-GAP for why the rest lack a `cost_proxy_score`._

## Spend Proxy — By Phase

| Phase | Events scored | Total | Avg |
|---|---|---|---|
| Architecture-Verify | 11 | 2593.0 | 235.7 |
| Comprehend | 1 | 174.4 | 174.4 |
| Document-Update | 10 | 799.0 | 79.9 |
| Finalize | 11 | 642.9 | 58.4 |
| Implement | 15 | 3207.6 | 213.8 |
| Investigate | 14 | 694.1 | 49.6 |
| Link | 1 | 0.0 | 0.0 |
| Parity | 11 | 778.6 | 70.8 |
| Plan | 12 | 490.0 | 40.8 |
| Review | 18 | 1442.8 | 80.2 |
| Scope | 17 | 1764.0 | 103.8 |
| Security-Review | 3 | 0.0 | 0.0 |
| Structure | 1 | 0.0 | 0.0 |
| Test | 13 | 1662.9 | 127.9 |
| Verify | 12 | 1635.5 | 136.3 |
| Write | 2 | 0.0 | 0.0 |

## Spend Proxy — By Agent

| Agent | Events scored | Total | Avg |
|---|---|---|---|
| architecture-reviewer | 21 | 1590.1 | 75.7 |
| claude | 41 | 7004.9 | 170.9 |
| create-tickets | 1 | 174.4 | 174.4 |
| doc-updater | 6 | 674.5 | 112.4 |
| done-checker | 10 | 1376.4 | 137.6 |
| finalizer | 7 | 511.7 | 73.1 |
| implementer | 8 | 1855.7 | 232.0 |
| investigate:C1 | 1 | 54.2 | 54.2 |
| investigate:C2 | 1 | 115.3 | 115.3 |
| investigator | 8 | 199.7 | 25.0 |
| link-epic | 1 | 0.0 | 0.0 |
| orchestrator | 18 | 202.5 | 11.2 |
| parity-updater | 4 | 486.2 | 121.6 |
| planner | 8 | 125.9 | 15.7 |
| security-reviewer | 1 | 0.0 | 0.0 |
| structure | 1 | 0.0 | 0.0 |
| test-scoper | 5 | 1344.4 | 268.9 |
| ticket-scoper | 10 | 169.1 | 16.9 |

## Summary Quality

| Issue | Count |
|---|---|
| Empty summary (current schema) | 0 |
| Legacy-format records (summary field not applicable) | 0 |
| Truncated (>200 chars) | 62 |

## Slow Runs (> 30 min)

| run_id | duration | active | idle | final_status |
|---|---|---|---|---|
| TCK-20260912-WORKING-LOG-APPEND-HELPER | 1086 min | 0 min | 1337 min | DONE |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 828 min | 91 min | 737 min | DONE |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 123 min | 123 min | 0 min | DONE |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 103 min | 103 min | 0 min | DONE |
| TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE | 89 min | 37 min | 51 min | DONE |
| TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION | 74 min | 35 min | 39 min | DONE |

_4 of the runs above spend at least half their reported duration idle (gaps ≥ 30 min between phase transitions, e.g. waiting on human review) rather than in active work — see `active`/`idle` columns; "slow" here does not mean "took a long time to actively work on."_

## Outliers

_Flags a value more than 3x its group's median — a relative visibility signal, not an absolute threshold like Slow Runs above, and not a claim about *why* the value is high._

### Cost-proxy-score outliers (by phase)

| run_id | seq | phase | agent | cost_proxy_score | phase median | ratio |
|---|---|---|---|---|---|---|
| TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY | 6 | Architecture-Verify | claude | 1593.737 | 81.6 | 19.5x |
| TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX | 1 | Scope | claude | 862.641 | 71.4 | 12.1x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 9 | Test | test-scoper | 703.523 | 68.9 | 10.2x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 11 | Verify | done-checker | 777.943 | 83.4 | 9.3x |
| TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL | 5 | Implement | claude | 845.559 | 127.8 | 6.6x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 10 | Test | test-scoper | 407.92400000000004 | 68.9 | 5.9x |
| TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2 | 6 | Document-Update | doc-updater | 338.238 | 66.9 | 5.1x |
| TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL | 3 | Plan | claude | 133.71 | 30.1 | 4.4x |
| TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT | 6 | Implement | implementer | 504.101 | 127.8 | 3.9x |
| TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS | 3 | Plan | claude | 109.352 | 30.1 | 3.6x |
| TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT | 7 | Implement | implementer | 428.213 | 127.8 | 3.4x |
| TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL | 4 | Review | claude | 229.423 | 71.5 | 3.2x |
| TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX | 10 | Verify | claude | 259.081 | 83.4 | 3.1x |

## Search & Investigation Effort

### Search Calls (Follow-Up Search Tooling)

**Total:** 281

### Raw Investigation (Read) Calls

**Total:** 1081
**Read-to-search ratio:** 3.847

## Tool Safety Audit

### Search-Before-Grep Compliance (Investigate Phase)

_Only the orchestrating run's own direct tools.jsonl rows are visible to this detector — a dispatched sub-agent's (e.g. `investigator`) own search/grep calls are not attributed back to this pair, so a 'non-compliant' pair may reflect an orchestrator-level incidental call rather than the real investigation's own behavior. The true compliance rate for delegated investigation work is unknown and plausibly higher than the rate below._

**Compliance rate:** 0.0% (0/8 Investigate-phase calls)

### Parity Ledger Write-Safety

**`docs/parity_ledger/*.yaml` edits co-occurring with a same-run `parity_index.py build` call:** 0
**Unsafe `parity_index.py build` invocations (real repo path):** 7

### Read-Count Correlation (Search-Before-Grep Compliance)

| Group | Pairs | Median Read count | Avg Read count |
|---|---|---|---|
| Compliant | 0 | n/a | n/a |
| Non-compliant | 8 | 6.0 | 4.9 |

## Parity Index Read-Path Usage

**`entry`/`impact`/`health` call count:** 0/6419 Bash rows scanned

_Counts tools.jsonl rows where tool == "Bash" and input_summary matches parity_index.py followed immediately by entry, impact, or health (path-anchored, so a filename mention alone — e.g. test_parity_index.py, --help, `git log -- ... parity_index.py`, `sed -n '1,60p' tools/parity_index.py` — never counts). bash_rows_scanned is the total Bash-tool row population this detector ran against (the section's own 'N' denominator). Confirmed 0 real call sites as of TCK-20260731-PARITY-READPATH-GATE's Gate A review (reviewed GO, not yet wired into any real workflow call site) — this is the expected, correct value until a future ticket adds a real entry/impact/health call site, not a bug._

## Skill Usage

### Zero-Invocation Flags (All-Time, 14-Day Grace Period)

**Flagged (confirmed age past grace period):** api-design-principles, architecture, backend-testing, observability, progression-entities, simq-dev, systems-economy
**Flagged (unknown age, no `date_added`):** debugging-strategies, doc-coauthoring, frontend-design, prompt-builder, python-performance-optimization, python-testing-patterns, test-driven-development

_All-time (never period-scoped) cross-reference of the real .claude/skills/*/SKILL.md catalog against build_skill_usage_section(tools)'s per_skill counts. A skill with any nonzero invocation count is never flagged, regardless of age. Of the remaining zero-invocation skills: `flagged_stale` requires a real, parseable `date_added` older than the 14-day grace period — a confirmed-age signal. `flagged_unknown_age` covers skills with no (or unparseable) `date_added` and zero invocations — an honest, lower-certainty signal, not proof of staleness, since no authorship date can be established. This fail-open policy on missing date_added is deliberate: it is what makes backend-testing's real pre-TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED state (no date_added field at all) correctly flaggable, per TCK-20260810-SKILL-USAGE-RETRO-TRACKING's AC2._

## Notes

_Fill in after reviewing the report above. What patterns stand out? What to improve?_

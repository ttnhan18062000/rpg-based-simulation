---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS
phase: open
date: 2026-10-16
tags: [performance, benchmarking]
---

# TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS

## Title
A benchmark record carries a real engine working-set figure from a separate, untimed, collector-on memory pass

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This is the follow-up the owner chose ("(a) Close + follow-up", 2026-10-16, via lead-planner) when `TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE` closed with its AC1 NOT MET.

That ticket added after-collect and after-`malloc_trim` RSS readings, taken after the timed window. On `simq_corpus_frontier_extended` (1000 ticks, `PERF_512MB_LOCAL`, canonical) the record now reads 311 MB after trim, against 1702 MB before. That figure is still an upper bound. The latency window runs with the collector disabled, and the garbage freed at the end leaves fragmented arenas that `malloc_trim(0)` cannot fully release.

A diagnostic run of the same world with the collector ON gave 106 MB after trim (+5.6 MB over warm-up), and tracemalloc traced 26 MB retained over 1100 ticks. Live-block growth was the same with the collector off and on. So the engine's working set is about 106 MB, but no benchmark record carries that figure.

## Scope
1. **A separate memory pass.** For a benchmark record, run a second pass that is untimed and kept apart from the latency window. It uses the same scenario, seed and RunSpec tick counts, with the collector left enabled. At the end it collects, trims and reads RSS, live blocks and `gc.get_stats()` collected. The latency window, `protocol.gc_disabled` and every timed field are unchanged.
2. **Where the pass runs.** The plan chooses, with its reason: either a fresh process (cleanest; the arenas aren't shared with the timed pass) or the same process after the timed pass (cheaper; the plan then shows the timed pass's retained arenas don't leak into the reading). Default: fresh process.
3. **Cost control.** The pass roughly doubles a memory-carrying run's wall time. Run it opt-in per record or per tool (`rerun_baselines.py`, the corpus records), or for the corpus and memory-relevant records by default. The plan states which, and how a record says whether the pass ran.
4. **Record fields.** Add optional `memory_mb` keys for the pass (e.g. `working_set_mb`, `working_set_delta_mb`, `working_set_basis`), with a MINOR schema bump. `rss_over_declared` moves to the working-set basis when it is present; the record says which basis was used. It stays report-only (OD-8). The schema doc edit is P1: the owner approves it.
5. **Tests.** The pass runs with the collector enabled, outside every timed span. The timed fields are byte-identical with and without the pass. With a fake kernel making cyclic garbage per tick, the pass's working-set delta is small while the old `rss_delta` is large. The pass's absence leaves the record valid.

## Out of Scope
- Any change to the latency protocol, the tripwire RunSpecs, `NOISE_BUDGET` or compare thresholds.
- Breaking the engine's reference cycles (rpg, #593).
- The pydantic/uuid retained-growth candidate (#593 note; rpg's).
- Any `src/` change outside `src/perf/`. Any memory gate (OD-8).

## Acceptance Criteria
- AC1: On `simq_corpus_frontier_extended` (the same RunSpec as the ledger line), a record carries the working-set reading from the pass, and its value matches the collector-on diagnostic (106 MB after trim, `TCK-20261015-...` investigation) within an error the plan states before the run. One local run is enough as evidence; it is not a baseline promotion.
- AC2: The timed fields of a record are unchanged by the pass (test, plus one real record compared with and without the pass).
- AC3: The declared-memory ratio uses the working-set basis when it is present and says so; it stays report-only (test).
- AC4: The owner approves the schema doc change before the merge; the ledger's two corpus rows get the working-set figure.
- AC5: Resource rule: one heavy run at a time, under the systemd-run memory cap; lead-planner is told before any run over about 3 GB.

## Related Tickets
- TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE (closed with AC1 NOT MET; owner decision (a)), TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION (#597, §5 as corrected), TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (#591)

## Related Docs
- docs/performance/tick_cost_growth.md §5, docs/performance/benchmark_identity_schema.md, docs/performance/baseline_invalidation_ledger.md, docs/performance/perf_baseline_policy.md (OD-8)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE/ (investigation, rss_diagnose.py), once that ticket closes

## Related Code Areas
- src/perf/bench_harness.py, src/perf/benchmark_record.py, tools/perf/rerun_baselines.py, tests/unit/perf/test_bench_harness_memory.py

## Assumptions / Open Questions
- Fresh process vs same process is the plan's choice (scope 2), with the default being a fresh process.
- Whether the pass should also run in the nightly tripwire lane: no, unless testing-planner asks for it.

## Implementation Notes
(empty until the plan)

## Test Summary
(empty until implementation)

## Files Changed
(empty until implementation)

## Completion Summary
(empty until close)

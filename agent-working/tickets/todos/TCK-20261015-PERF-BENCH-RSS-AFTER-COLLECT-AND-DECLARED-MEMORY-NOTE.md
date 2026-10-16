---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE
phase: open
date: 2026-10-15
tags: [performance, benchmarking]
---

# TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE

## Title
A benchmark record's memory describes the engine, not the harness's disabled collector, and carries a report-only note against the profile's declared memory

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION` (#597, `docs/performance/tick_cost_growth.md` §5) found that T08's "RSS over the profile" (`simq_corpus_frontier_extended` 1703 MB, `frontier_marches` 1568 MB, on `PERF_512MB_LOCAL`, which declares 512 MB) is a harness artefact. `BenchHarness.run_benchmark` (`src/perf/bench_harness.py:122-151`) calls `gc.collect()` and then `gc.disable()` for the whole sampling window. The engine makes about 1230 container objects of cyclic garbage per tick. With the collector off, RSS grows +1.42 MB per tick; with it on, +0.14 MB. 1.42 x 1100 ticks is about the recorded 1587 MB `rss_delta`. The engine's working set is about 110-130 MB.

The collector is disabled deliberately, to keep collector pauses out of the latency samples, so the latency protocol stays as it is. The memory fields are the part that is wrong: `mem_rss_mb` / `rss_high_water` / `rss_delta` report uncollected garbage. Nothing compares RSS with the profile's declared `ram_mb` outside LIVE.

## Scope
1. **Memory measured after collection.** Keep `gc.disable()` for the latency window, unchanged. Add an engine-memory reading that excludes uncollected garbage. Preferred: at the end of the sampling window, re-enable the collector, run `gc.collect()`, and read RSS once (`rss_after_collect_mb`). Also read it before the window, after the existing `gc.collect()`, so the growth over the window is a collected-to-collected delta. If a short extra gc-on pass is cheaper and clearer, the plan may choose it instead, with the reason. Freed-but-retained malloc arenas mean RSS does not always shrink after a collect. The plan states how that is handled (for example, also record `tracemalloc`'s current size, or state the limit).
2. **Keep the old fields, say what they mean.** `mem_rss_mb.{avg,max,delta}`, `rss_high_water` and `rss_delta` keep their values for comparability with existing records. Their documentation says they include garbage the collector was told not to collect. New records carry the new fields alongside them.
3. **Declared-memory note (report-only, OD-8).** Record `rss_after_collect_mb / profile ram_mb` in the benchmark record as a note. When it is above 1.0, the record's report says so. It is never a gate, never fails a run and never blocks a promotion.
4. **Schema and docs.** Add the field(s) to `docs/performance/benchmark_identity_schema.md` (P1: the owner approves the schema edit) and bump the record schema version if the schema rules require it. Update the T08 ledger lines for the two corpus records in `docs/performance/baseline_invalidation_ledger.md`: their RSS is harness garbage, not engine memory.
5. **Tests.** A unit test that a run with a synthetic garbage-making tick (cycles per tick) reports a large `rss_delta` but a small after-collect delta. A test that the latency window still runs with the collector disabled (the protocol is unchanged). A test that the note is report-only: a ratio above 1.0 changes no exit code and no promotion decision.

## Out of Scope
- Breaking the engine's reference cycles (rpg: `tick_cost_growth.md` §7 item 5, on #593).
- Any change to the latency protocol, `protocol.gc_disabled`, or the tripwire.
- Any `src/` change outside `src/perf/`.
- A memory gate of any kind (OD-8: report-only until the full lift).

## Acceptance Criteria
- AC1: New benchmark records carry an after-collect RSS reading and its growth over the window, and their values on `simq_corpus_frontier_extended` are of the order of the engine working set (about 100-200 MB), not 1.5 GB. One local re-run is enough as evidence. It is not a baseline promotion.
- AC2: The old RSS fields are unchanged in value and documented as including uncollected garbage.
- AC3: The declared-memory ratio is recorded and reported, and it is proven by test to be report-only.
- AC4: The schema doc change is approved by the owner before the merge. The ledger notes are updated.
- AC5: The latency samples' protocol is unchanged (test).
- AC6: Resource rule: one heavy run at a time, under the systemd-run memory cap, and lead-planner is told before any run over about 3 GB.

## Related Tickets
- TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION (#597, finding §5), TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (#591, the 1.7 GB records), TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES

## Related Docs
- docs/performance/tick_cost_growth.md §5, docs/performance/benchmark_identity_schema.md, docs/performance/baseline_invalidation_ledger.md, docs/performance/perf_baseline_policy.md (OD-8)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION/evidence.md (gc on/off pair)

## Related Code Areas
- src/perf/bench_harness.py (run_benchmark, the result dict at :180-203 and :275-276), src/perf/benchmark_record.py, tools/perf/rerun_baselines.py

## Assumptions / Open Questions
- A1: Starts after #597 merges (its doc and evidence are the reference).
- Q1 (for the plan): is the after-collect reading at the end of the window enough, or is a periodic in-window reading needed? The investigation's linear growth suggests the end reading is enough.

## Implementation Notes
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(to be filled)

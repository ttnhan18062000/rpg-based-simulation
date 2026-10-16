---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE
phase: done
date: 2026-10-15
tags: [performance, benchmarking]
---

# TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE

## Title
A benchmark record's memory describes the engine, not the harness's disabled collector, and carries a report-only note against the profile's declared memory

## Status
DONE

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
`src/perf/bench_harness.py`: after the pre-window `gc.collect()` the harness reads RSS (untrimmed) and `sys.getallocatedblocks()`; the sampled loop and `gc.disable()` are untouched. After `wall_end_ts` and `cpu_end` (outside both timed spans) it runs `gc.collect()`, reads RSS, calls `malloc_trim(0)` (guarded ctypes; true whenever the call was made, whatever it returned) and reads RSS again. The finally still owns the collector's state. New optional `memory_mb` keys (schema 1.2): `rss_before_window_mb`, `rss_after_collect_mb`, `rss_after_trim_mb`, `rss_trim_delta_mb`, `allocated_blocks_delta`, `gc_collected_objects` (the `gc.get_stats()` collected total), `gc_collect_s`, `declared_ram_mb`, `rss_over_declared` (= `rss_after_trim_mb / max_ram_mb`, or `rss_after_collect_mb / max_ram_mb` where no trim, flagged by `rss_over_declared_basis_trim` 1.0 / 0.0), `peak_rss_over_declared`. The result dict keeps its legacy keys (a test pins them). Report-only: no gate, no `compare` or `promote` input.
Diagnosis on the way: the first 1000-tick record's after-collect RSS equalled the high-water mark (1702 MB) because the freed garbage stays mapped; 200-tick runs (collector on/off, canonical/pinned, no harness, tracemalloc, malloc_trim; `rss_diagnose.py`) named the cause; `malloc_trim(0)` took 402 MB to 125.6 MB. `tick_cost_growth.md` section 5 corrected. Trim is taken only after the clocks, never before the window (page faults would enter the sampled ticks). The quiet-host spin (4.3x on identical work) and the crowded_frontier discard are recorded in the T08-NOISY ticket.

## Test Summary
`tests/unit/perf/test_bench_harness_memory.py` (18 tests): garbage-making fake tick (old `rss_delta` large, after-collect delta small, `gc_collected_objects` large); old fields and the result dict's keys unchanged; the declared ratio against two profiles and the basis flag; ordering (tick, clock stop, end collect, one trim, shutdown; no trim before a sampled tick; the collector's state after `run_benchmark` equals its state before, enabled and disabled); protocol unchanged and the tripwire RunSpecs pinned at 10 + 50; a failing memory reader never fails a run; report-only for `compare` and `promote`; 1.1 against 1.2 records compare as one version, MAJOR 2.0 still INCONCLUSIVE, a 1.1 record round-trips; no trim means no trim keys and basis 0.0; `_malloc_trim` never raises and a stub libc returning 0 still counts as a trim. Mutation checks: end collect before the clocks, trim before the window, and `bool(malloc_trim(0))` each fail the matching test. `tests/unit/perf` 275 passed; mypy gate rc=0; `codebase.health check` rc=0 (0 new, 0 worse); wall-clock inventory regenerated and its sync tests pass.

## Files Changed
- src/perf/bench_harness.py, src/perf/benchmark_record.py (SCHEMA_VERSION 1.2)
- tests/unit/perf/test_bench_harness_memory.py (new), tests/unit/perf/test_benchmark_record.py
- docs/performance/benchmark_identity_schema.md (schema 1.2 text, PENDING OWNER APPROVAL), docs/performance/baseline_invalidation_ledger.md, docs/performance/tick_cost_growth.md (section 5 correction), docs/performance/wall_clock_inventory.md and .json (regenerated)
- agent-working/stored_artifacts/TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE/ (investigation.md, plan.md, test_plan.md, rss_diagnose.py)
Commits on `perf-t08-noisy-baselines`: 5b1413535, 62809b22a, 133a46e37, 781781c3b, 24ff9ba89, f609d49e0. Raw run data: `reports/perf/rss_evidence/` (git-ignored).

## Completion Summary
**AC1 NOT MET, closed on the owner's decision "(a) Close + follow-up" (2026-10-16, through lead-planner).** AC1 asked for after-collect values of the order of 100-200 MB on `simq_corpus_frontier_extended`; the record reads **311.0 MB after trim** (1701.9 MB after the plain collect; old fields 1687.6 / 1589.0 MB unchanged). That figure is an upper bound: the collector-on diagnostic (not the harness) reads **106.2 MB** after trim (+5.6 MB over warm-up, same +211.7k live blocks), and tracemalloc traces **26.0 MB** at the end of 1000 ticks with the collector on. The 311 MB is collector-off allocator fragmentation the trim cannot fully release, so this design cannot give the record a working-set figure. The AC1 text is unchanged. Follow-up: `TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS` (an untimed collector-on pass).
- AC2 met: old fields unchanged in value (the 1000-tick runs reproduce 1687.4 / 1587.3 and 1687.6 / 1589.0) and documented as including uncollected garbage (`_build_record` docstring, schema text); tests: `test_the_result_dict_and_the_old_memory_keys_are_unchanged`.
- AC3 met: the ratio is recorded (0.61 on the trimmed reading, 3.30 for the peak) and report-only by test (`test_the_ratio_is_report_only_for_compare_and_promotion`, `test_a_failure_reading_the_new_keys_never_fails_the_run`).
- AC4: ledger notes updated (three readings side by side, AC1 recorded as not met). **Schema text (62809b22a and 781781c3b) awaits the owner's approval in the batch PR. AC4 is complete only on that approval, and the merge waits for it.**
- AC5 met: the latency protocol is unchanged (`test_the_protocol_is_unchanged`, the ordering test with the collector state before and after, the tripwire RunSpecs pinned at 10 + 50).
- AC6 followed: one heavy run at a time under `MemoryMax=3G`, quiet window checked, no run over 3 GB (the process peak was 1.70 GB).
Corrections found on the way: `tick_cost_growth.md` section 5's "sample RSS after an explicit collect" proposal does not work without a trim; the unreachable-object count puzzle is explained by the first generation-0 collection after `gc.enable()` (1.34 M objects collected).

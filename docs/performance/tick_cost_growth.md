---
status: active
layer: performance
authority: P2
audience: developer
tags: [performance, benchmarking, regression]
---

# Where the tick cost grew, and what to fix first (TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION)

**Status: PROVISIONAL evidence.** Measurement only: nothing in `src/` outside `src/perf/` was changed. Every number comes from one run on one loaded development VM (6 vCPU, 1-minute load 1.2 to 6.4, `py-spy` at 250 Hz), so **absolute milliseconds are inflated** (about 2x a CI runner) and **the comparisons below are phase shares within a run**, which a uniform sampling overhead does not bias. `py-spy` overhead is not resolvable below the roughly 18 % run-to-run noise of this host (measured: 0.94 and 1.04 at 250 Hz, `investigation.md` in the ticket's artifacts). Nothing here is a baseline or a capacity claim.

## 1. What was held fixed

| contract | how (no `src/` edit) | holds fixed | still moves |
|---|---|---|---|
| **pinned** (the reference) | `Kernel(..., governor=PinnedNormalGovernor())` | the RuntimeMode (always NORMAL) | other wall-clock inputs outside `audit_mode`: the mid-tick budget throttle's wall-clock reading (report-only since DEV-014), the queue and worker wall-clock signals, the scheduler's tick-time inputs |
| canonical | `canonical_variant(PROD_LARGE)` | the governor reads a modelled cost, so the mode sequence is host-independent | the measured tick ms (telemetry) |
| live | the profile as `profile_tick.py` ran before | nothing | the governor |
| audit | `audit_mode: True` | NORMAL, but **adds** fingerprint and dirty-set work | used only to see what audit adds |

Tools: `python3 tools/perf/profile_tick.py --scenario <s> --entities <n> --contract <c> [--world <corpus world>]` (the `--contract`, `--world` and `--sampler none` options and a peak-RSS field were added for this ticket), `tools/perf/profile_diff.py`, and a standalone runner for old trees. Each profile's `phases.md` records commit, host cores, loadavg, contract and (for `pinned`) the sentence "pinned fixes the RuntimeMode only". Profiles use `no_replay` and `no_frame_pacing`, like the benchmark harness.

**The contract barely changes the work:** for the same scenario the pinned, canonical and live mean ticks agree within 4 to 12 % (strategic_100: 615, 604, 639 ms; idle_100: 126, 125, 119 ms), so the growth is not a governor artefact. Under canonical, `mixed_200`, `strategic_100` and `movement` at 500 and above leave NORMAL (CONSTRAINED or SURVIVAL), which is the T08 finding; `movement_2000` canonical shows `resolution_overhead` at 40 % (4583 ms) against 13 % pinned, a mode effect I did not investigate.

## 2. Per-scenario phase table (pinned contract; mean ms per tick and share of the tick)

| scenario | mean tick | top phases |
|---|---|---|
| `idle_100` | 126 ms | combat_engagement 43 ms (34 %), collection 33 ms (26 %), resolution_overhead 33 ms (26 %) |
| `combat_10` (`--entities 20`, 10 against 10) | 51 ms | combat_engagement 12 ms (23 %), collection 10 ms (20 %), cooperation 10 ms (19 %) |
| `mixed_200` (140 entities) | 233 ms | cooperation 72 ms (31 %), combat_engagement 50 ms (21 %), resolution_overhead 38 ms (16 %) |
| `strategic_100` | 615 ms | cooperation 365 ms (59 %), resolution_overhead 94 ms (15 %), combat_engagement 48 ms (8 %) |
| `movement_100` / `500` / `1000` / `2000` | 160 / 1611 / 5590 / 10323 ms | combat_engagement 35 % / 61 % / 65 % / 71 % (55 / 989 / 3632 / 7279 ms) |
| corpus `frontier_extended`, ticks 4 to 33 | 105 ms | resolution_overhead 22 %, cooperation 21 %, collection 16 %, advancement 16 % |
| corpus `frontier_extended`, ticks 604 to 643 | 130 ms | **advancement 40 % (52 ms)**, cooperation 16 %, collection 14 % |
| corpus `frontier_marches`, ticks 4 to 33 / 604 to 643 | 107 / 114 ms | cooperation 31 % then advancement 45 % (51 ms) |

`combat_engagement` and `cooperation` are per-entity-pair costs that grow with the population; the corpus worlds change shape with run length because the **event recorder** takes over (section 3, H3). The idle floor is 4.1 ms in May (`20f773dee`) and about 110 ms now; the 30-phase tick has a fixed cost of that order even for idle entities.

**movement scaling.** Whole-tick exponent 1.44 (100 to 500) then 1.80 (500 to 1000); `combat_engagement` 1.80 then 1.88; 1000 to 2000 is about 1.0 for the tick (10 ticks, one run each: rough). A pinned 5000-entity tick is therefore between about 25 s and about 100 s on this host. **No 5000-entity profile was run** (a 33-tick profile would take about an hour). The held ticket's 3.2 s at 5000 entities is not reproducible here (that ticket itself records 3.2 s on one box and 16 s on another for identical code): `build_movement_state` is the same grid builder at `132bf09ca` and today, `combat_engagement` is 2.2 to 3.5 s at 1000 entities in every tree from `132bf09ca` on, and the scale to quote is the curve above.

## 3. Hotspots, ranked, with evidence and the call to rpg

Evidence is the share of all samples whose stack contains the function (inclusive) in `profile.folded`; raw files are under `reports/perf/tick_cost/` (git-ignored) and summarised in the ticket's `investigation.md`.

| rank | where | share | legitimate work or waste | expected saving |
|---|---|---|---|---|
| **H1** | `is_hostile_compat` (`faction.py:206/207/226`) to `project_relation` (`relation.py:75/76/190`), called per entity pair from `CombatEngagementPhase._consider` (`phase.py:310`) and `candidate_selector._adjacent_hostile` / `hostility.perceived_hostile` | 29 to 62 % of the tick in synthetic scenarios (36 % at `idle_100`, 59 % at `movement_1000`); 6 to 20 % in corpus worlds; self-time of the two functions is about 43 % at `movement_500` | **Waste.** The relation of two factions does not change within a tick, yet it is recomputed for every pair, including idle pairs with no line of sight; exponent about 1.8 to 1.9 in entity count | cache the relation per (faction pair, generation) or precompute a faction-pair matrix, and test spatial adjacency before hostility: most of the 35 to 65 % that `combat_engagement` takes in the synthetic scenarios |
| **H2** | `cooperation/providers.py:53 get_candidates` (and `identity_resolver.resolve`, 2 to 15 %) | 43 to 61 % of `strategic_100`, 27 % of `mixed_200`, 10 to 27 % of corpus worlds | **Mostly waste** (a per-entity candidate enumeration rebuilt every tick; #394 already fixed the pending-offer lookup, this is the next cost in the same phase) | index the candidate source once per tick; the largest remaining cost of `strategic_100` (365 ms of 615 ms) |
| **H3** | `EventRecorder.record` (`src/observability/event_recorder.py:213-216`): when the in-memory buffer is full (`max_events` = 5000) **every recorded event scans the whole buffer** to find the lowest-severity oldest event to evict, then `list.pop(index)` | 42.5 % of all samples (53 % inclusive for `_phase_observability`) in the late corpus profile; it is the whole growth of `advancement` from 16 % to 40 to 45 % | **Waste** (O(buffer) per event once the buffer is full; the buffer fills after about 5000 events, so it hits every long run) | O(1) eviction: per-severity deques or a ring buffer; about 40 to 50 ms per tick (35 to 40 %) in long-running corpus worlds |
| **H4** | pydantic model construction on hot internal events (`pydantic/main.py:250 __init__`: 2 to 14 %) and `observability/event_shapers.py` (1 to 6 %) | up to 14 % of `strategic_100` | **Probably waste** (validated construction of events the engine itself just produced) | `model_construct` for internal events, 5 to 10 % on event-heavy ticks |
| **H5** | `resolution_overhead` (12 to 33 % of every tick) | `StrategicIntelligenceSystem.fused_strategic_pass` (`pipeline.py:393`, the `strategic_intelligence` run_phase): 92 to 99.4 % of the residual in every counterfactual run (see "H5 attribution" below) | **Unattributed work, not overhead:** `refine`'s Phase 7 timer is started at `pipeline.py:386` and `t_start` is assigned again at `:431` for the `faction_sentiment` block, so `costs["final_integrity"]` (`:461`) times only `:431-461` (0.1 to 0.33 ms) and the strategic, lifecycle, groups and capacity work before it falls into the residual | rpg: one line (a distinct variable for the faction_sentiment timer) in `src/engine/pipeline.py`; expected effect: `final_integrity` reports the real time and `resolution_overhead` falls to the true dispatch cost; no tick gets cheaper (reported phase costs move, the total is unchanged) |
| **H6** | `spatial_query.nearby_entities` and `cognition.filter_saliency` | 10 % each at `movement_1000` | likely legitimate (the neighbourhood query), but quadratic without a spatial index | not estimated |
| **H7** | cyclic garbage: about 1230 container objects per tick survive in reference cycles (gc object count 118k with the collector on, 242k with it off after 100 ticks) | not a CPU share | **Waste** (see section 5) | fewer cycles per tick lowers collector cost and the memory the benchmark harness accumulates |

**What is legitimate work and what budget it needs (input to the option (i) decision, not the decision).** Under the pinned contract on this loaded host the tick costs are idle_100 126 ms, movement_100 160 ms, mixed_200 233 ms, strategic_100 615 ms, corpus worlds 105 to 130 ms; the PROD profiles budget 50 to 100 ms per tick. Two projections, each from measured shares and an assumed saving (not a measurement after a fix): `strategic_100` (615 ms) would be about 615 x (1 - 0.59 x 0.7 - 0.30 x 0.5) = about 270 ms, where 0.59 is the share of the cooperation phase (H2, assumed 70 % saved) and 0.30 is the share of the hostility relation, H1 (about 32 % of the tick inclusive, assumed 50 % saved; H1 and H2 overlap a little, so this is an optimistic figure); H3 is about zero in `strategic_100`. The late corpus tick (130 ms) would be about 130 x (1 - 0.425) = about 75 ms, from H3 alone (42.5 % of the tick assumed removed): the legitimate work is well below the current tick, so a larger canonical budget for work that is mostly waste would price the waste in. These are projections from shares, not measurements after a fix.

### H5 attribution (`TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION`, 2026-10-16)
**Cause, proven by counterfactual, not by samples alone.** The folded stacks of five #597 profiles (`movement_1000` pinned and canonical, `strategic_100`, `idle_100`, `mixed_200`) replayed with the kernel's own timer accounting put 93 to 99 % of the residual on `pipeline.py:393` (`fused_strategic_pass`). A process-local timer wrapped around that call (no `src/` edit, wrapper inert: identical end-state fingerprints on the deterministic runs, 0.3 microseconds per tick) then measured, per tick and against the same run's `resolution_overhead`:

| scenario (contract, commit 9accca4ad) | `fused_strategic_pass` ms | `resolution_overhead` ms | residual |
|---|---|---|---|
| idle_100 pinned | 25.5 | 26.3 | 2.9 % |
| strategic_100 pinned | 55.2 | 60.2 | 8.3 % |
| movement_500 pinned / canonical | 125.2 / 248.0 | 127.6 / 249.7 | 1.9 % / 0.7 % |
| movement_1000 pinned / canonical | 345.0 / 564.2 | 348.7 / 567.8 | 1.1 % / 0.6 % |

**Ranked: (1) `fused_strategic_pass`, 92 to 99.4 % of the residual in every run; (2) everything else together (result sorting, update building, `refine` prologue and merges), 0.6 to 8 %.** Nothing else is large enough to name.

**The canonical jump at `movement_2000`** (`resolution_overhead` 40 % under canonical against 13 % pinned): in the `movement` runs the strategic pass costs 1.6 to 2.0 times as much under canonical, which is in SURVIVAL for every measured tick (248 against 125 ms at `movement_500`, 564 against 345 ms at `movement_1000`); it is not unattributed bookkeeping. **But the mode alone does not explain it:** on the corpus world `frontier_extended` (canonical, 1100 ticks crossing NORMAL, CONSTRAINED, DEGRADED and SURVIVAL, one process) the median wrapped strategic pass is flat across the modes, 12.7, 12.4, 13.1 and 13.0 ms, while the tick's wall time doubles (60 to 124 ms); the pass is 13.6 of 15.6 ms of `resolution_overhead` there (residual 12.9 %). So what makes the `movement` strategic pass costlier under canonical than pinned is **not established**: candidates (untested) are that the two contracts do not evolve the same world, or a property of the `movement` scenario. The growth of the tick in SURVIVAL on the corpus world is outside `fused_strategic_pass`. 15 to 20 measured ticks per `movement` run; `movement_2000` itself was not run.

**For rpg (through lead, the #593 hand-off):** fix the shadowed `t_start` (the timer fix above). The earlier suggestion to look at what `fused_strategic_pass` does differently under SURVIVAL is withdrawn: the corpus run does not show a mode effect in the pass.

## 4. The three held cost tickets, from the call-site evidence

* **`TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`**: `fingerprint` appears in **0.0 %** of the samples of every non-audit profile and in **3.5 %** under `audit_mode` (strategic_100). Recommendation: **update, not close**: not a material tick cost with replay off; the profiles run `no_replay`, so the `kernel.py:664` path under `replay_allowed` is untested here.
* **`TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED`**: `decision_trace` frames are **0.0 to 1.4 %** of the tick-thread stacks (stacks are filtered to those containing the measured tick loop, so a writer thread's own frames are not counted). Recommendation: **close as not a tick cost** (perf-planner checks the close).
* **`TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`**: **confirmed**, at 100 to 2000 entities, as H1; the fix stays with rpg Lane B; `combat_engagement` first appears between `c84352465` (none) and `132bf09ca` (2.2 s at 1000 entities, full tree) and stays at 2.2 to 3.5 s since.

## 5. Memory: the RSS "over the profile" is a harness artefact

T08 recorded `simq_corpus_frontier_extended` at 1703 MB and `frontier_marches` at 1568 MB on `PERF_512MB_LOCAL` (declares 512 MB). **Cause: `BenchHarness` runs the sampled ticks with `gc.disable()` (`bench_harness.py`, the `protocol.gc_disabled` field), and the engine produces cyclic garbage every tick.** Same world, same kernel, 100 ticks after 30 warmup ticks, tool `tracemalloc` and a gc on/off pair: gc **on** RSS 95 to 109 MB (+0.14 MB per tick, 86 ms/tick); gc **off** RSS 95 to 237 MB (+1.42 MB per tick, 101 ms/tick). 1.42 MB x 1100 ticks = about 1560 MB, the recorded `rss_delta` of 1587 MB. The profiled process without the harness stayed at 127 MB after 640 ticks. So the engine's working set is about 110 to 130 MB; **the 1.7 GB is garbage the collector was told not to collect**, and is not engine memory. (`tracemalloc` attributed only about 24 MB of Python allocations at the end; the rest of the growth is cycle garbage held by freed-but-uncollected containers and malloc arenas, so the gc experiment, not the allocation table, is the evidence. memray was not needed and not installed.) Nothing in `BenchHarness`, `compare()` or the governor under the canonical contract compares RSS with a profile's declared `ram_mb` (the memory guard exists only under LIVE). **Proposal (perf-owned, not built here, to be filed):** record `rss_high_water / ram_mb` in the benchmark record as a note (never a gate, OD-8), and either sample RSS after an explicit `gc.collect()` or stop disabling the collector for memory records, so a record's RSS describes the engine and not the harness. **Correction (`TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE`, 2026-10-16): the explanation stands, the "sample RSS after an explicit `gc.collect()`" proposal does not work.** A first after-collect reading on the 1100-tick `simq_corpus_frontier_extended` run stayed at 1702 MB, because the freed cyclic garbage's memory stays mapped in the allocator. 200-tick runs on the same world (same kernel call shape as the harness, `PERF_512MB_LOCAL`) separate the causes: collector off, RSS grows +285 MB (canonical) and +292 MB (pinned, NORMAL only) and is 402 MB after an end collect; collector on, +9 and +11.5 MB; no `BenchHarness` at all with the collector on, +3 MB; so the growth is the disabled collector, not the mode and not the harness's history list. `tracemalloc` saw a 324.6 MB Python peak during the window and 11.1 MB at its end (RSS minus traced: 431 MB): the garbage was freed and RSS did not fall. **`malloc_trim(0)` after the collect took RSS from 402 MB to 125.6 MB** (99.6 MB at the end of warm-up), which is the engine's working set. The benchmark record now carries `rss_after_trim_mb` for that reason (schema 1.2).

## 6. Then versus now (one run each, same runner, live contract, full trees, `movement` 1000, load 3.5 to 6)

| tree | mean tick ms | combat_engagement | resolution_overhead | cooperation |
|---|---|---|---|---|
| 2026-05-15 `20f773dee` | 333 | none (pre-hostility) | one `resolution` bucket 292 | none |
| `c84352465` | 1068 | none | 383 | 382 |
| `132bf09ca` | 5323 | 2174 | 2704 | 358 |
| 2026-10-06 `d135dd6be` | 6919 | 2227 | 3903 | 339 |
| 2026-10-14 `dc9b63c99` | 4452 | 3477 | 246 | n/r |
| today (this branch at `32242fdb7`, engine `src/` identical to main `2dabff8c1`) | 3880 | 2506 | 842 | n/r |

(n/r: not recorded; the cooperation phase was not among the top four phases of those two runs.)

`resolution_overhead` fell between October trees because DEV-017 stopped double counting the refine sub-phases, so totals before and after DEV-017 are not comparable; shares of the corrected accounting are. The first old-tree runs of this investigation used `src/` only and ran the engine's legacy content fallback; that reading ("5x growth since 2026-10-06") was withdrawn.

## 7. Ranked hand-off for rpg (#593)

1. **`EventRecorder.record` eviction** (`src/observability/event_recorder.py:209-222`): replace the per-event full scan with O(1) eviction. Largest single saving in long runs (35 to 40 % of the tick). Note that the all-CRITICAL branch (buffer full of CRITICAL events) also does `self.events.pop(0)`, which is O(n) on a list, so the O(1) design (per-severity deques or a ring buffer) must cover both paths.
2. **Hostility relation** (`faction.py` `is_hostile_compat`, `relation.py` `project_relation`, callers `combat_engagement/phase.py:310`, `engine/candidate_selector.py`, `engine/hostility.py`): memoise per faction pair per generation and gate by adjacency. Largest in dense and idle scenarios (30 to 60 % of the tick).
3. **Cooperation candidates** (`domains/cooperation/providers.py:53`, `entities/identity_resolver.py resolve`): per-tick index. 40 to 60 % of `strategic_100`.
4. **Event construction** (pydantic `__init__` in `observability/event_shapers.py`): skip validation for engine-made events. 5 to 10 %.
5. **Cycle garbage per tick** (about 1230 objects): find the reference cycles (events or closures) and break them.
6. perf-owned, not rpg: the declared-memory note and the gc-disabled RSS (section 5); a corpus-world profile with warmup of 600 ticks should be part of any future tick-cost baseline, because early ticks hide H3.

## 8. Limits of this evidence

One run per profile, a loaded host (load 1.2 to 6.4, other sessions' suites running), `py-spy` sampling (shares, not ms), 30 to 40 measured ticks (10 at 2000 entities), pinned fixes the mode only, `no_replay` profiles (replay-on costs are not measured), the movement 5000 point not run, `resolution_overhead` not broken down, old trees run under the live contract and compared by share. Re-measure on a quiet host before quoting a millisecond.

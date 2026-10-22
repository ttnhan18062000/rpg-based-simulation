---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, determinism, audit]
---

# Port-leak audit: what §5 of the engine execution modes proposal claims, and what the code does

**Status:** audit, advisory; **revised 2026-10-22 after perf-planner and lead-planner review** (clock row, F1, F2, F3, F5). Read-only: every claim below is from reading code at `main` **`b281d0c3d`**; no run, profile
or hash experiment was made. A claim that reading cannot settle is marked `UNVERIFIED (needs run)` with the run that would
settle it. Written by `architecture-implementer` for ticket `TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT`, dispatched by
`architecture-planner` (approval: issue #715, comment 6345579717). Source list:
[engine_execution_modes_proposal.md](engine_execution_modes_proposal.md) §5.

**Impact classes.** `M1-now`: breaks Mode 1 determinism or the final hash today, on a path a certified run can take.
`M2`: only once replay is off or the Mode 2 fast path is used. `M3+`: only under parallel, process-pooled or relaxed
execution. Owners: `rpg-planner` (`src/**` semantics) or `perf-planner` (engine runtime, hash scheme).

## 1. Summary

| # | port | §5 claim | verdict | class |
|---|---|---|---|---|
| 1 | clock | wall-clock pacing and timers | **Partly refuted.** Pacing and timers reach telemetry only. The real leak is the *default* `LIVE` signal contract: measured wall-clock picks the runtime mode, and the mode changes scheduling | M1-now (unless fixed budgets: `audit_mode` or pinned NORMAL) |
| 2a | random | `base_seed=0` on restore | **Confirmed**, and worse than the code comment says: stateless draws read `_base_seed` | M1-now (restore path only) |
| 2b | random | salted `hash()` at `military_conflict.py:339` | **Confirmed**; result lands in hashed `groups` | M1-now (cross-process) |
| 2c | random | (not in §5) | **New:** salted `hash()` at `perception/filter.py:88,97` | M1-now provisional, reach UNVERIFIED |
| 3 | process scope | seven named singletons | **Confirmed, with one correction and two additions.** None reaches the hash; one is a hazard in a pool | M3+ |
| 4 | state store and hash | hash omits six fields | **Confirmed for all six; five are real gaps, `terrain` is not.** One more real gap, `information_providers`, was missed, plus minor counters (§5) | M1-now |
| 5a | executor | profile picks executor implicitly | **Confirmed** | M3+ |
| 5b | commit path | none for Modes 1 to 3a | **Confirmed** | M3+ (no leak) |
| 5c | event sink | ordering feeds the digest | **Not confirmed.** No event digest found; the final hash is state-only | M2 (cost, not correctness) |

## 2. Clock

| site | what the code does | reaches | evidence |
|---|---|---|---|
| `kernel.py:412-461,478-480` | `perf_counter_ns` phase timers into `_phase_costs` | telemetry; also `tick_compute_ms` signal (below) | `src/engine/kernel.py:412` |
| `kernel.py:465-474` | frame pacing `time.sleep` to reach `max_tick_budget_ms`; off with `no_frame_pacing` | nothing (delays only) | `kernel.py:218,465` |
| `kernel.py:612-619`, `:487-488` | mid-tick and end-of-tick budget checks | report only, `_report_budget_overrun`; no result dropped, no mode forced | `kernel.py:612` (PERF-D1 comment) |
| `kernel.py:170,1248` | `datetime.now` for run `started_at`/`ended_at` | manifest | `kernel.py:170` |
| `worker_manager.py:44,234` | per-packet `perf_counter_ns`, stored as `WorkerResult.compute_time_ns` | telemetry; copied at `executor.py:351`, the field is declared at `core/worker_protocol.py:103`. No reader on an authoritative path found by grep | `src/engine/worker_manager.py:44` |
| `run_identity.py:21` | `int(time.time())`, pid and `uuid4` in the default run id | run directory name only; the seeded part is a stateless draw (`:25`) | `src/engine/run_identity.py:21` |
| **`kernel.py:482` into `signal_source.py:190-194` into `governor.py:79,82,97`** | measured `final_compute_ms` becomes `PressureSignals.tick_compute_ms`; `effective_tick_cost` returns it when `tick_cost` is unset; the governor compares it with the budget and returns `DEGRADED`/`SURVIVAL` | **the runtime mode, then `GovernorPolicy`, then scheduling (`kernel.py:555-566`), then state** | `governor.py:79,82,97`; `core/governance.py:59-61`; `config/profiles.py:57` (default `SignalContract.LIVE`) |

**Verdict.** The `perf_counter_ns` and `sleep` sites the proposal names are telemetry. The leak is the signal path in the
last row. `select_signal_source` (`signal_source.py:190`) zeroes the signals under `audit_mode` and uses model-derived
`tick_cost` under `CANONICAL`; the default `LIVE` contract uses the wall clock, so on `LIVE` the same seed on a slower host
can reach `DEGRADED` and schedule different work. PERF-D1 input 1 already says this (`governor.py:~100` comment). The
`current_mode` field is not hashed (see §5), so the final hash would not flag the cause, only the downstream state.

**Class:** M1-now for any run that is not on fixed budgets. Owner: `perf-planner`. Per PERF-D1 amendment A2
(`docs/architecture/performance_optimization_decisions.md`, about :357), a run judged on its outcomes uses **fixed budgets**:
`audit_mode`, or pinned NORMAL. That is Mode 1. `CANONICAL` is for runs that measure governance or cost (`tools/perf`
baselines, the tripwire, capacity runs). The two are **not interchangeable**: under today's cost model T08 (#591) measured
`strategic_100` and `mixed_200` in CONSTRAINED or SURVIVAL, `frontier_extended` in SURVIVAL on 902 of 1000 ticks and
`frontier_marches` in CONSTRAINED on 876 of 1000, so a `CANONICAL` run and an `audit_mode` run give different outcomes. Never
compare runs across contracts. The A2 default flip is rpg's `TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-*`, queued after v1.

## 3. Random source

| leak | evidence | what the code does | class | why |
|---|---|---|---|---|
| restore uses `base_seed=0` | `src/engine/scenario_checkpoint.py:85` | `DeterministicRNG(base_seed=0)`, then `set_state(state.rng_checkpoint)`. `set_state` (`platform/rng.py:57-63`) restores only the per-domain **stream** generators. The stateless draws `get_float`/`get_int` (`rng.py:84-110`) seed from `self._base_seed` through `_composite_seed`, so after a restore they draw from seed 0 instead of `state.seed`. The code comment at `scenario_checkpoint.py:83-84` ("base_seed is irrelevant post-restore") is wrong for these draws. **Which path a checkpointed scenario takes:** `ScenarioCheckpointer.restore` builds its own kernel here, so a restored scenario does *not* go through `ScenarioRuntimeService._build_kernel` (`scenario_runtime.py:419-424`). That method seeds from the initial state at `:420` (`base_seed=self._initial_state.seed`), and its other branch at `:423` is a fresh `AuthoritativeState(tick=0, seed=0)` with `base_seed=0`, which agrees with its own state seed, so `:423` is consistent, not a leak. Only `scenario_checkpoint.py:85` forces 0 against a state whose seed may differ | M1-now (restore path only) | a restored run diverges from the unbroken run for any seed other than 0, at the first stateless draw. Whether any shipped flow restores and compares a hash is UNVERIFIED (needs run: restore at tick N, run to N+K, compare the hash with an unbroken run) |
| salted `hash()` for a group id | `src/engine/military_conflict.py:339` | `abs(hash((contested_region_id, attacker_id, state.tick))) % 2**31` becomes `GroupRecord.id`. The tuple holds a `str`, so the value depends on `PYTHONHASHSEED` | M1-now (cross-process) | `groups` is hashed (`checkpoint.py:126`), so two processes with the same seed produce different final hashes whenever a faction attack fires. In one process it is stable |
| salted `hash()` for perceived ids | `src/domains/perception/filter.py:88,97` | `hash(signal.signal_id)` for a non-integer entity id, and always for resource `node_id` | M1-now provisional | `PerceivedEntity.entity_id`/`node_id` are string-salted. UNVERIFIED whether they reach authoritative state or only a per-tick view (needs a read of the consumers, or a two-`PYTHONHASHSEED` run) |
| `id(obj)` | `src/engine/executor.py:243`; `src/engine/biological_needs.py:94-96` | object identity as a key / cache validity token | M3+ | not traced past the line. `biological_needs.py` uses it as a cache-staleness token, which is per-process by design |
| `uuid`, `random.` module | `src/engine/run_identity.py:21` only, in `src/engine src/core src/domains src/systems src/ai src/worldassembly` | no `import random` or `random.` call found on an authoritative path in that sweep | none | sweep pattern: `\bhash\(`, `\bid\(`, `uuid\.`, `\brandom\.(random\|choice\|shuffle\|randint\|sample\|seed)`, `import random`. Set-iteration order was **not** swept (UNVERIFIED) |

## 4. Process-global singletons

Question asked of each: would two runs in one process (the Mode 3 pool case) interfere, and does it touch state or the hash?

| singleton | evidence | interferes in a pool? | reaches state/hash? | class |
|---|---|---|---|---|
| `behavior_consumers` catalog, gate, resolver | `src/engine/behavior_consumers.py:14-16`; `configure_behavior_consumers` at `:19` | yes if two runs configure different catalogs; the default auto-init loads `data/content` (`:76-80`) | read-only catalog; reaches decisions, but identical catalog gives identical results | M3+ |
| `ObservabilityConfig._override_mode` | `src/observability/config.py:27,187-205,287` | yes: a class attribute, set by `observability/sweeper.py:150`, restored at `:394` | observability mode only | M3+ |
| observability queue and drain worker | `src/observability/queue.py:165,168,173-189` | yes: one shared queue and worker for all runs | event delivery only | M3+ |
| stream adapter | `LiveEventPublisher.get_instance()` at `src/observability/stream/adapters.py:54,65`. **Correction:** no module-level mutable was found in `adapters.py`; the singleton is the publisher it calls | yes: one publisher | telemetry only | M3+ |
| `decision_trace_writer` | `src/observability/cognition/decision_trace_writer.py:50` (`_active_writer`, "set by Kernel at run start/end") | **yes, and a hazard:** a second kernel's start overwrites the first's writer, and the first's end clears it | trace output only | M3+ |
| `scenario_registry` | `src/engine/scenario_registry.py:8` (`_registry` dict) | yes if two runs register the same scenario id | no | M3+ |
| content tick-context flag | `src/content/repository.py:23,235`; set at `kernel.py:404,408` | **no**: it is `threading.local`, so it is thread-safe, though it ties "tick active" to the thread, which a process pool does not share | guards catalog loads only | none |
| **added:** terrain cache | `src/content/terrain_cost.py:22,40-54` (`_terrain_cache`) | yes if profiles differ | movement cost, so decisions; identical content gives identical values | M3+ |
| **added:** warm-catalog provider | `src/content/common_knowledge_seed.py:31-32,37,73` | yes: installed by `behavior_consumers` | seeding | M3+ |

**Verdict.** The §5 list is accurate except for the thread-local, which is not a leak. None of these reaches
`CanonicalStateHasher`, so none is an `M1-now` or `M2` item. They are all `M3+`: a process-pooled Mode 3 has one process per
run and does not hit them, and an in-process thread pool would. `decision_trace_writer` is the one a thread pool would break
first. Owner for a fix: `perf-planner` (engine runtime); the observability ones are `rpg-planner`'s `src/observability/`.

## 5. CanonicalStateHasher coverage (main item)

Hasher: `CanonicalStateHasher.to_canonical_data`, `src/engine/checkpoint.py:94-168`. `AuthoritativeState`:
`src/core/state.py:1339` onward. The final-hash call is `kernel.py:1196-1197` (`CanonicalHashScheduler(...).compute_digest`);
it hashes state only. Mutation path: every durable field is rebuilt in `ApplyPath.apply_generation`, the replace at
`src/engine/apply.py:495-575`.

### 5.1 Every field, covered or not

| field (`state.py`) | hashed at (`checkpoint.py`) | mutable after assembly? | verdict |
|---|---|---|---|
| `tick` 1335, `seed` 1336, `world_time` 1337 | 100-102 | yes (`apply.py:495-497`) | covered |
| `entities` 1340 | 114 | yes | covered |
| `resource_nodes` 1341, `ground_items` 1342, `corpses` 1343, `owed` 1344, `chests` 1345, `buildings` 1346, `camps` 1347, `regions` 1348, `places` 1349, `local_scars` 1350 | 120, 124, 122, 123, 125, 121, 128, 117, 118, 119 | yes, except `places` (passthrough, `apply.py:557`) | covered |
| `groups` 1381, `global_resources` 1383, `home_storage` 1384 | 126, 130, 127 | yes | covered |
| `town_center` 1385, `movement_count` 1386, `maturity` 1387, `last_calamity_tick` 1388 | 106, 103, 104, 105 | yes | covered |
| `grief_drained_tick` 1389 | 108 (`_grief_fields`, only once set) | yes | covered |
| `blocked_tiles` 1390, `town_tiles` 1391, `building_tiles` 1392 | 132, 133, 134 | passthrough (`apply.py:510,511,519`) | covered |
| `rng_checkpoint` 1394 | 137 | yes | covered (stream state only, not `_base_seed`: §3) |
| `region_loyalty_pressure`, `region_culture_states`, `entity_legend_facts`, `entity_belief_institutions`, `event_fidelity` (1415-1458, `compare=False`) | 146, 147, 150, 159, 166 | passthrough per episode | covered, though `compare=False` |
| `information_source_profiles` 1404 | 155 | single-fire | covered |
| **`item_instances` 1351** | **none** | **yes** (`apply.py:295-303,529`) | **GAP: durable, mutable** |
| **`recent_world_events` 1459** | **none** | **yes**, windowed (`apply.py:384,543`) | **GAP: durable, mutable** |
| **`quest_registry` 1460** | **none** | **yes** (`apply.py:386-395,544`) | **GAP: durable, mutable** |
| **`factions` 1464** | **none** | **yes** (`apply.py:398-457,545`) | **GAP: durable, mutable** |
| **`clans` 1466** | **none** | **yes** (`apply.py:469-480,546`) | **GAP: durable, mutable** |
| **`information_providers` 1462** | **none** | **yes** (`apply.py:491-492,547`) | **GAP: durable, mutable. Not in the §5 list** |
| `terrain` 1382 | none | **no**: passthrough `apply.py:512`; the only replace is a scenario fixture, `certification/scenarios.py:219` | no gap after assembly. Assembly-time terrain is not hash-verified, low risk |
| `next_node_id` 1536, `next_entity_id` 1537, `next_item_instance_id` 1538 | none | yes (`apply.py:530`) | minor gap: ids show up in hashed entities once allocated, so a divergence is caught late rather than never |
| `processed_transaction_ids` 1535, `transaction_trace` 1395, `rejection_registry` 1397, `pressure_signals` 1399 | none | yes (`apply.py:522-524`) | `transaction_trace`, `rejection_registry`, `processed_transaction_ids`: diagnostic counters, no gap. `pressure_signals` is **dormant**: `kernel.py:528` passes it to `record_tick` (observability only) and does not set state. `state.pressure_signals` changes only through `StateUpdate.pressure_signals_set` (`apply.py:345`; declared `core/updates.py:1044`), and nothing in `src/` produces that today (the wall-clock producer was removed by TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING, PERF-D1 A1, pinned by `tests/unit/resource/test_buy_price_independent_of_host_timing.py`). Its one reader is `pipeline.py:86-91`, where `ENABLE_*` keys switch feature flags; only `src/testing/scenario_runner.py:100` and tests populate it. Class M3+ (dormant) |
| `current_mode` 1533 | none | yes, from the governor | derived from signals (§2); the hash sees its effects, not the mode |
| `town_entity_ids` 1393 | none | cached, passthrough (`apply.py:520`) | derived, no gap |
| `pending_information_responses` 1402, `pending_self_model_information_events` 1403, `feature_flags` 1405 | none | transient or input | no gap by design (`compare=False`) |
| `MAX_PROCESSED_IDS`, `MAX_TRACE_SIZE`, all `_*_cache`, `occupancy_snapshot`, `movement_cache`, `route_plans`, `world_indexes`, `semantic_entity_indexes`, `transient_claims`, `_opt_profile`, `_force_full_scan` | none | caches | no gap |

**§5 claim, checked.** "Hash omits factions, clans, quest_registry, item_instances, terrain, recent_world_events":
**true for all six.** For five of them it is a real gap. `terrain` is constant after assembly, so it is not. One field the
claim missed, `information_providers`, is a sixth gap.

**Is the gap partly closed elsewhere?** No. Settled: the replay fingerprint (`StateFingerprinter.get_fingerprint`) does not cover
the six fields either; see `conformance_suite_design.md` §4.1a. `observability/event_extractor.py:1519,1544,1675` reads
`factions` to emit events, so a faction divergence may show up in the event stream, but no event digest exists (§6).

**Why it matters for the proposal.** Modes 2 and 3 are accepted as correct if they reproduce Mode 1's final hash. A fast
path that diverges only in `factions`, `quest_registry` or `recent_world_events` would pass that check. Closing the gap
changes the digest value for every world (the `PROOF_DIGEST_SCHEME` constant in `checkpoint.py` would need a version bump
and every pinned baseline would be re-recorded), which is a `perf-planner` scheme decision and a hard dependency of the
conformance suite. **Until the scheme is bumped, any hash-equality proof is blind to these fields.** The T3 `no_replay` proof is
unaffected: it touches only non-authoritative output.

## 6. Executor, commit path, event sink

- **executor (confirmed).** `kernel.py:193-198`: an explicit `executor` argument wins, else `max_worker_count > 0` picks
  `ConcurrentExecutionAdapter`, else `LocalSequentialExecutor` (`executor.py:112`). The profile drives the choice, as §5 says.
  The `Protocol` is `IWorkExecutor` (`executor.py:63`). M3+.
- **commit path (confirmed).** `kernel.py:735,782` call `ApplyPath.apply_generation` after `AuthoritativeApplyPipeline.refine`
  (`pipeline.py:41`), in `_phase_resolution` order (`final_results.sort(key=ConcurrencyLaw.commit_key)`, `kernel.py:606`).
  No leak found for Modes 1 to 3a.
- **event sink (not confirmed as stated).** §5 says "ordering feeds the digest". A grep for `event_digest|events_digest|digest_events`
  under `src/` found nothing, and the final hash (`kernel.py:1196-1197`) is state-only. The `EventRecorder` buffer is bounded
  and evicts (`event_recorder.py:72,223-233`, `buffer_evicted_count`), so the H3 eviction cost is real, but that is a cost,
  not a correctness leak. If a digest over events exists elsewhere (tests, certification) this audit did not find it:
  UNVERIFIED. Class: M2 for cost. The proposal's wording should change if the digest is confirmed absent; that edit is item B.

## 7. Findings to route (drafts; architecture-planner sends them)

**F1 to rpg-planner and perf-planner. Hash omits six mutable durable fields (M1-now).**
> `CanonicalStateHasher.to_canonical_data` (`src/engine/checkpoint.py:94-168`) does not hash `item_instances`
> (`state.py:1351`), `recent_world_events` (`:1459`), `quest_registry` (`:1460`), `factions` (`:1464`), `clans` (`:1466`) or
> `information_providers` (`:1462`). All six are rebuilt every tick in `ApplyPath.apply_generation` (`apply.py:529,543-547`),
> so a divergence in any of them is invisible to the final hash and to Mode 2/3 conformance. `terrain` is omitted too but is a
> passthrough (`apply.py:512`), no gap. Question for rpg-planner: is `recent_world_events` (a windowed list) meant to be
> part of canonical state, or is it a view? Question for perf-planner: adding fields changes every digest, so
> perf owns the scheme bump (PERF-D5, `flat-sha256-v1` to vN). It needs an owner-approved PERF-D5 amendment and comes after
> RECORD-BASELINE-V1, then the baselines are re-recorded. rpg's ruling on `recent_world_events` decides whether the field count is
> five or six. Until the bump, hash-equality proofs are blind to these fields (the T3 `no_replay` proof is not affected). Evidence: `docs/plans/architecture/port_leak_audit.md` §5.

**F2 to perf-planner. Default `LIVE` signal contract lets wall-clock choose the runtime mode (M1-now).**
> `config/profiles.py:57` defaults `signal_contract` to `LIVE`; `signal_source.py:190-194` returns `_ZEROED` for
> `audit_mode` (signals zeroed), `_CANONICAL` for `signal_contract` CANONICAL (the reference work model) and `_LIVE` otherwise;
> only `LIVE` uses measured `tick_compute_ms`; `governor.py:79-105` turns `cost_ms >= budget_ms` into `DEGRADED`, and
> the policy changes scheduling (`kernel.py:555-566`). The same seed on a slower host can schedule different work. This is
> PERF-D1 input 1, already known; the ask is that the proposal's Mode 1 state fixed budgets (`audit_mode`, or pinned NORMAL) as a precondition, per PERF-D1 A2,
> and that the conformance suite pin it. `CANONICAL` is for runs that measure cost or governance and must not stand in for it:
> T08 (#591) measured `frontier_extended` in SURVIVAL on 902 of 1000 ticks and `frontier_marches` in CONSTRAINED on 876 of 1000, so
> the two contracts give different outcomes. Never compare runs across contracts. The A2 default flip is rpg's
> `TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-*`, queued after v1.

**F3 to rpg-planner. Checkpoint restore draws stateless randoms from seed 0 (M1-now, restore path).**
> `scenario_checkpoint.py:85` builds `DeterministicRNG(base_seed=0)`. `rng.set_state` (`platform/rng.py:57`) restores only
> the per-domain streams; `get_int`/`get_float` (`:84-110`) seed from `_base_seed`, so every stateless draw after a restore
> differs from the unbroken run unless the seed is 0. The comment at `:83-84` is wrong for them. Fix: build the RNG with
> `state.seed`. Path note: `scenario_runtime.py:420` seeds from the initial state and `:423` is a fresh seed-0 state, both consistent;
> a checkpointed scenario takes `scenario_checkpoint.py:85`, not those. Needs a run to size: restore at tick N, run K more, compare the final hash with an unbroken run. (§5 says a
> finding on this was already sent; this adds the mechanism.)

**F4 to rpg-planner. Salted `hash()` at `military_conflict.py:339` and `perception/filter.py:88,97` (M1-now, cross-process).**
> `GroupRecord.id` comes from `hash((contested_region_id, ...))` over a `str`, so it depends on `PYTHONHASHSEED`; `groups`
> is hashed, so the final hash differs between processes whenever a faction attack fires. `perception/filter.py` does the
> same for string signal ids; whether that reaches state is unverified. Fix: a stable digest (e.g. `zlib.crc32` over the
> canonical string) or an allocator-issued id. (`:339` is already with rpg per §5.)

**F5 to rpg-planner (perf-planner copied). `pressure_signals` is dormant; id counters are low risk (M3+, dormant).**
> `state.pressure_signals` (`state.py:1399`) is unhashed but nothing in `src/` writes it: `kernel.py:528` is only the
> `record_tick` argument, and the only producer of `StateUpdate.pressure_signals_set` (`apply.py:345`) was removed by
> TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING. The one reader is `pipeline.py:86-91`, where `ENABLE_*` keys gate phases; only
> `src/testing/scenario_runner.py:100` and tests populate it. Not a live leak. Recommend rpg either delete the `ENABLE_*` back door
> (perf's preference) or hash the field. The id counters (`:1536-1538`) are not hashed directly but surface in the hashed entity
> and node ids at the next allocation: low risk, no fix.

## 8. Not settled by reading

- Whether any shipped flow restores a checkpoint and compares hashes (F3).
- Whether `perception/filter.py` ids reach authoritative state (F4).
- Set-iteration-order sweep (not done).
- Whether an events digest exists outside `src/` (§6).

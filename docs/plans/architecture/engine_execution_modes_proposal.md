---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, performance, determinism]
---

# Engine execution modes: fix the waste first, then five labelled modes

**Status:** proposal, advisory, not decided. Drafted by `architecture-planner-u24` on 2026-10-22, at the user's
request in its terminal (approval logged on issue #715, comment 6338162467). Nothing here changes a recorded
decision. Each step that would change one is marked **needs ADR** and goes to lead-planner. Code goes to rpg-planner
or perf-planner.

**Companion:** `faster_feature_testing_draft_tickets.md` (same folder) holds the draft tickets for step 1.

## 1. Why

The owner wants two things:
- **(a)** real-simulation feature testing (paired runs, the rpg gate, corpus runs) to take less wall time;
- **(b)** the engine to be able to run in more than one mode (parallel, performance, and distributed if a real need
  appears) without breaking what the certified mode proves.

The simulation has many agents that decide freely, with no turn order. That shapes the design, but it does not by
itself call for giving up determinism:
- **Deciding is already parallel by design.** Collection reads one immutable snapshot (`docs/engine/kernel.md`,
  "Concurrency & The Resolution Bottleneck").
- **Applying is where agents meet.** Two claims on one tile, one loaf, one enemy. Resolution settles them with a
  fixed sort (class priority, local priority, ID), so the result does not depend on worker order.
- **Determinism comes from that conflict rule, not from running agents one after another.** A mode can be parallel
  and still deterministic.

## 2. Measured starting point (PROVISIONAL, single loaded host; `docs/performance/tick_cost_growth.md`)

| fact | value | source |
|---|---|---|
| Collection (the only parallel phase) | 6 to 26 % of a tick, so the Amdahl ceiling is 1.06 to 1.35x | idea 08 table; tick_cost_growth §2 |
| 4-thread pool vs 0 workers | Collection 1.6 to 2.1x **slower** (GIL plus dispatch, `[inferred]`) | idea 08, finding 2 |
| serial waste, named | H1 hostility per pair (29 to 62 % synthetic), H2 cooperation candidates (43 to 61 % of `strategic_100`), H3 EventRecorder eviction (42.5 % late `frontier_extended`, measured before the 2026-10-19 partial fix in #645), H4 event validation (up to 14 %) | tick_cost_growth §3 |
| projection after H1 to H3 | `strategic_100` 615 to about 270 ms; late corpus tick 130 to about 75 ms (shares, not measured fixes) | tick_cost_growth §3 |
| replay digest when allowed | 9.2 % (`strategic_100`) to 27.1 % (`frontier_extended`) of a tick | tick_cost_growth §4 |
| engine working set | about 101 to 130 MB per run; the 1.7 GB figure is the harness's `gc.disable()` | tick_cost_growth §5 |
| Resolution (`refine`) | one chained fold over a single `StateUpdate`: 43 `run_phase` calls (12 flag-gated) plus 6 direct calls, each reading what earlier phases wrote | `src/engine/pipeline.py:135-438`; `docs/performance/phase_inventory.md` |

**Reading.** One world's tick is bound by serial work, most of it named waste. Parallelism on top of that waste only
parallelises the waste: pair work that grows with n² still grows that way on 8 threads. **Removing the waste also
raises the parallel ceiling later**, because Collection becomes a larger share of a smaller tick.

## 3. Order of work

1. **Fix the named waste (no mode change).** H2, H3 and H4 (draft tickets), next to H1 (rpg Lane B,
   `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`) and H5 (rpg, via #593). Every fix has to be
   behaviour-neutral: identical canonical hashes under `audit_mode` (`performance_contract.md` §4.1, parity
   invariant). **After v1:** nothing touching `src/**` lands before the v1 record PR merges.
2. **Make the test cycle measurable, and move it off this host** (draft tickets T1 to T3). No engine change.
3. **Name the ports, then add modes one at a time** (§5, §6). Each mode goes through the conformance suite (§5)
   before any result it produces is used.

Steps 1 and 2 serve goal (a). Step 3 serves goal (b), and is worth it only after step 1 has landed.

## 4. The five modes

Every mode runs the **same simulation rules**. Only the execution around them changes: executor, clock, commit
order, proof output. Every result carries its mode label (`performance_contract.md` §3.1 already requires
Execution Mode and RuntimeMode on a claim). **Results are compared only within one mode.**

| # | Mode | Same seed, same result? | Where the speed comes from | Status |
|---|---|---|---|---|
| 1 | Certified | yes, byte-identical, every tick | none (the reference) | exists |
| 2 | Fast test | yes, same outcomes and the same final hash | drops per-tick proof output | new, cheap |
| 3 | Parallel-deterministic | yes, but only for backends a parity matrix proves | more cores | new, medium to hard |
| 4 | Live | no | sheds work to keep wall-clock pace | exists (server only) |
| 5 | Relaxed / distributed | no | many machines, arrival-order apply | new, hardest; **needs ADR** |

### Mode 1: Certified (today's outcome-run contract)
- **Runs as:** `LocalSequentialExecutor`, `PinnedNormalGovernor`, `audit_mode` and `no_frame_pacing`, fixed budgets.
  Replay is on, so the per-tick SHA-256 `TICK_END.hash` is emitted (`docs/engine/kernel.md`, "State Hashing in
  Phase 7"; `tools/test_architecture/rpg_gate_run.py:60-66`).
- **Guarantees:** DET-PORT-0 (PERF-D2); PERF-D1 A2's "fixed budgets" contract for outcome runs.
- **Gives up:** nothing. Every other mode is checked against this one.
- **Used for:** the rpg gate, paired runs, certification, determinism and regression tests.

### Mode 2: Fast test
- **Runs as:** Mode 1 plus `no_replay` (the flag exists: `src/engine/kernel.py:206`), so no per-tick
  `TICK_END.hash`.
- **Keeps:** the same executor, the same fixed budgets and the same world evolution. `kernel.md` says "Shutdown
  always emits the final canonical hash regardless of runtime mode", so end-state proof stays.
- **Gives up:**
  - per-tick determinism proof: you cannot name the first tick at which two runs diverge;
  - replay of the run. Phase-7 digest output is the replay proof stream (`kernel.md`, Phase 7).
- **Does not give up:** the PERF-D1 A2 contract. `no_replay` changes no budget and reads no clock.
- **Expected saving:** the digest share, 9 to 27 % of a tick (PROVISIONAL).
- **Used for:** paired arms (behaviour and, once T3 passes, neutral steps), the rpg gate if testing-planner agrees,
  and exploratory runs.
- **Paired proofs do not read the digest (code read, 2026-10-22).** `tools/rpg_measure/arm_child.py:58,69` computes
  `start_hash` and `final_hash` directly with `CanonicalStateHasher.get_hash`. The neutral check
  (`paired.py:174-180`) and the self-check (`stats.py:125`) compare those hashes plus fates and counters. Mode 2
  could therefore serve neutral steps too.
- **Two facts to verify first (draft T3):**
  - that `no_replay` leaves the canonical hashes identical, i.e. no game logic reads `replay_allowed`;
  - that the behaviour counters, which `arm_child.py:35-36` tallies from `simulation_events.jsonl`, are still
    written.
- **Not used for:** certification.
- **Owner of the ruling:** perf-planner (PERF-D1 contracts).

### Mode 3: Parallel-deterministic
- **Runs as:** more cores, applied in stages:
  1. **3a, Collection only:** a process pool (exists, never enabled, never measured on today's engine),
     free-threaded CPython (an open owner question in `performance_stack_survey.md`) or a native kernel (Rust is
     accepted as a toolchain).
  2. **3b, later, partitioned Resolution:** regions applied in parallel, borders and global phases serial.
- **Guarantees:**
  - DET-PORT-1 under PERF-D2: "guaranteed only for backends and counts in a passing parity matrix; otherwise
    unclaimed";
  - `performance_contract.md` §4.1 still applies: a hash mismatch against Mode 1 is a failure.
- **Gives up:**
  - the DET-PORT-0 certification reference, so its proofs are comparable only within its tier;
  - the evidence base: most existing evidence is at 0 workers.
- **3b blockers (code read, 2026-10-22):**
  - order-dependent reads inside `refine`:
    - the cognition chain;
    - `action_routing`'s sliding state, in ascending ID order with a neighbour radius of 10 (`actions.py:194-345`);
    - `combat_engagement` reading this tick's routing (`pipeline.py:320`);
    - dirty-set rebuilds;
    - `lifecycle` re-running its own transfers;
    - `faction_sentiment` over all of the tick's bonds;
    - the world-wide occupancy claim map;
  - cross-region writes:
    - combat and kill rewards;
    - movement, swaps and `region_id` changes (`apply.py:721`);
    - `military_conflict` territory transfer;
    - the faction registry (`apply.py:399`);
    - the economy's global pool;
    - groups and clans;
    - inheritance;
    - spawns;
  - one shared entity-ID allocator;
  - ordered `world_events_add` and recorder order feeding the digest.
  - RNG is counter-keyed (`src/platform/rng.py:85-90`), so draw order is safe.
- **Status:** 3b is parked as C-10 / M3, reopened only for evaluation under **PERF-M6-T05**
  (`docs/architecture/performance_optimization_decisions.md`). This proposal feeds that evaluation. It does not
  open a second track. **Needs ADR** before any 3b code.
- **Smallest safe 3b experiment:** shadow instrumentation only. Tag each `StateUpdate` write with the region it
  touches, and count cross-region and global writes per tick on the corpus. No parallel code.

### Mode 4: Live (exists)
- **Runs as:** the Live contract (wall-clock); the governor sheds work to keep pace.
- **Gives up:** reproducibility, since the result depends on host speed. Under DEGRADED, `TICK_END.hash` is null;
  under SURVIVAL there is no `TICK_END` (`kernel.md` Phase 7). Results carry the `REDUCED` verification label.
- **Allowed for:** the live server, and tests that opt in to test adaptation. **No other run may depend on host
  speed** (PERF-D1 amendment A2).

### Mode 5: Relaxed / distributed (only on a stated need)
- **Runs as:** state partitioned across processes or machines; claims applied in arrival order.
- **Gives up:** everything Mode 1 proves, namely:
  - determinism;
  - replay;
  - the canonical hash as a proof;
  - comparison with any certified result;
  - the paired-run method, since noise in both arms means more seeds are needed for the same effect.
- **Conflicts with recorded decisions:**
  - `docs/architecture/system_overview.md`, "What is deliberately not distributed" ("The engine is one process and
    one writer ... Scaling is per run");
  - the devops amendment's single engine replica;
  - Kafka and Postgres are rejected.
- **Needs ADR:** an amendment, and only after a real world-size requirement exists. One machine must first fail to
  hold the per-tick work after step 1 and Mode 3.
- **Not a test-speed lever.** For testing, "distributed" means **many seeds on many machines, each run in Mode 1 or
  2**. That keeps determinism and needs no ADR (draft T2).

## 5. Ports and the conformance suite (precondition for Modes 2, 3 and 5)

A mode should swap an implementation behind a named port, not patch the core. Proposed ports, each with its
contract and its Mode 1 implementation:

| port | Mode 1 implementation | known leak to close first (lead-planner-u24's review, 2026-10-22) |
|---|---|---|
| clock | fixed budgets, pinned NORMAL | `kernel.py` `perf_counter_ns` and `time.sleep` pacing; `worker_manager.py:44/234`; `run_identity.py:21` |
| random source | `DeterministicRNG(seed)`, counter-keyed | `scenario_checkpoint.py` restores with `base_seed=0` (finding sent to rpg); salted `hash()` at `military_conflict.py:339` (sent to rpg, after v1) |
| executor | `LocalSequentialExecutor` | the profile drives the executor choice implicitly |
| commit path | `refine` then `ApplyPath.apply_generation` | none for Modes 1 to 3a; 3b and 5 change it |
| event sink | `EventRecorder`, ordered | ordering feeds the digest; H3 eviction cost |
| state store and hash | `AuthoritativeState`, `CanonicalStateHasher` | hash omits factions, clans, quest_registry, item_instances, terrain, recent_world_events (audit pending with rpg) |
| process scope | one process per run | process-global singletons (behavior_consumers, `ObservabilityConfig._override_mode`, the observability queue, stream adapter, decision_trace_writer, scenario_registry, content thread-local) |

**Conformance suite.** A fixed set of worlds and seeds runs in every mode:
- Modes 2 and 3 must reproduce Mode 1's final canonical hash.
- Mode 4 asserts invariants only, as `test_cert_long_run_stability.py` does today.
- Mode 5 asserts invariants and outcome distributions only.

**Ownership:** testing-planner (lane placement), with perf-planner for the parity matrix (PERF-D2).

## 6. What each step needs, and who owns it

| step | needs | owner |
|---|---|---|
| 1 H2, H3, H4 fixes | draft tickets, after v1; hash-identical | rpg-planner (src), perf-planner reviews the measurement |
| 2 T1 run and rerun accounting | draft ticket | testing-planner (with rpg for `tools/rpg_measure`) |
| 2 T2 paired runs off this host | draft ticket | testing-planner; lead for host policy |
| 2 T3 / Mode 2 `no_replay` for paired arms | perf ruling, then a draft ticket | perf-planner rules; rpg or testing implements |
| Mode 3a | stack-survey evaluation, parity matrix | perf-planner (PERF-D2, M6) |
| Mode 3b | PERF-M6-T05 proposal, then an ADR | perf-planner, then lead-planner |
| Mode 5 | a world-size requirement, then an ADR amendment | owner, then lead-planner |
| ports, conformance suite | a design pass after step 1 | architecture (this folder) proposes; rpg and testing build |

## 7. Explicitly not proposed

- Non-determinism as a speed lever. It buys little on its own, and it costs paired runs, replay and the gate.
- More threads in Collection under the GIL: measured slower.
- A relaxed mode inside the gate path. PERF-D1 A2 requires fixed budgets for outcome runs, and the rpg gate is
  advisory, never a required check (`docs/plans/test_architecture/roadmap.md` §4.1, §4.2).

## 8. Open questions for the owner

1. **Target scale for goal (b):** agent count, ticks per second, live or offline. It decides whether Mode 5 belongs
   in the plan at all.
2. **Mode 2:** may paired arms (and the gate) use it once perf rules on it and T3 passes?
3. **H2, H3, H4:** file them after v1 (this proposal's recommendation), or post on #593 that they wait?

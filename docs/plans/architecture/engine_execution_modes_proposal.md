---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, performance, determinism]
---

# Engine execution modes: fix the waste first, then four labelled modes

**Status:** proposal, advisory, not decided. Drafted by `architecture-planner-u24` on 2026-10-22, at the user's
request in its terminal (approval logged on issue #715, comment 6338162467). Nothing here changes a recorded
decision. Each step that would change one is marked **needs ADR** and goes to lead-planner. Code goes to rpg-planner
or perf-planner.

**Revised 2026-10-23** (`TCK-20261023-ARCHITECTURE-ENGINE-MODES-PROPOSAL-UPDATE`, scope approved on #715, comment 6347241081).
What changed, and why:
- Mode 2 now carries perf-planner's YES and its five conditions (#593, comment 6343379030), in place of the three facts to verify (§4, §8 Q2).
- H3 and H4 were re-measured after #645 and both closed (#593, comment 6343696936; PR #723) (§2, §3, §6, §8 Q3).
- §5's leak column is replaced by the audited verdicts of [port_leak_audit.md](port_leak_audit.md); the event-sink line is corrected;
  Mode 1 is stated as fixed budgets per PERF-D1 A2; the v1 baseline is noted as blind to six fields.
- The conformance paragraph points to [conformance_suite_design.md](conformance_suite_design.md).
- §6 marks the audit and the design done, and records the T2 runner facts and that PERF-M6-T05 has no ticket.

**Revised 2026-10-26** (owner answered Q1 on #715, comments 6408481790 and 6409936521; lead-planner-u24's review folded in):
- **Target scale = offline research scale on one machine** (about today's corpus, roughly 100 to 2000 entities). **Mode 5 is dropped** (§4, §6, §8 Q1).
  The 10,000 entity / 50 ms / 2 GB figure in `docs/performance/optimization_architecture.md:21` stays as perf's stated bigger-world target,
  measured by a capacity run (PERF-M2-T03/T04); that doc is perf's, not edited here.
- The hash is blind to **seven** fields, not six (§5).
- The "nothing touching `src/**` before the v1 record merges" rule is retired: v1 is recorded and re-anchored (#725, #747, #748) (§3).
- H2 is done on Lane C; the 615 to 270 ms projection is retired (§2, §3, §6).
- `fused_strategic_pass` is named as uncosted serial Resolution work (§2); H5 is a timer fix, not waste.
- PERF-M6-T05 is unticketed, so the "fold E into it" step needs perf to record it on the M6 epic or file T05 (§6).

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
| serial waste, named | H1 hostility per pair (29 to 62 % synthetic), H2 cooperation candidates (43 to 61 % of `strategic_100`), H3 EventRecorder eviction and H4 event validation (both **closed** by the re-measure in the next row) | tick_cost_growth §3 |
| projection after H1 to H3 | **RETIRED (2026-10-26).** The 615 to 270 ms and 130 to 75 ms figures were shares, not measured fixes, and the late-corpus one assumed H3 at 42.5 % (now 0.69 %). Re-measure after H1 and H2 land instead of quoting shares. H2 is done on Lane C: hashes equal on 3 worlds, paired neutral IDENTICAL, cooperation phase -64 % / -85 % (lead-planner-u24 relay, PR about to open) | tick_cost_growth §3 |
| replay digest when allowed | 9.2 % (`strategic_100`) to 27.1 % (`frontier_extended`) of a tick | tick_cost_growth §4 |
| H3 and H4 re-measured after #645 (2026-10-22) | both CLOSE. H3 `EventRecorder.record` 0.69 % of the tick (was 42.5 %). H4 `event_shapers.py` 1.18 % and event-path pydantic 0.65 % (`strategic_100`); the 7.15 % total pydantic share belongs to the H1/H2 callers. Shapers at 3.74 % on `frontier_extended` are rpg's call. PROVISIONAL: shares, one host | #593 comment 6343696936; PR #723 |
| engine working set | about 101 to 130 MB per run; the 1.7 GB figure is the harness's `gc.disable()` | tick_cost_growth §5 |
| `fused_strategic_pass` | 92 to 99 % of the 12 to 33 % "overhead" that tick_cost_growth's H5 attribution uncovered. It is serial Resolution work that nobody has costed or labelled as waste or legitimate. **H5 itself is only a timer fix and makes nothing cheaper.** It limits what Mode 3a can buy even after H1 and H2 | tick_cost_growth (H5 attribution); lead-planner-u24 review 2026-10-26 |
| Resolution (`refine`) | one chained fold over a single `StateUpdate`: 43 `run_phase` calls (12 flag-gated) plus 6 direct calls, each reading what earlier phases wrote | `src/engine/pipeline.py:135-438`; `docs/performance/phase_inventory.md` |

**Reading.** One world's tick is bound by serial work, most of it named waste. Parallelism on top of that waste only
parallelises the waste: pair work that grows with n² still grows that way on 8 threads. **Removing the waste also
raises the parallel ceiling later**, because Collection becomes a larger share of a smaller tick.

## 3. Order of work

1. **Fix the named waste (no mode change).** H2 (done on Lane C; H3 and H4 are closed, §2), then H1 (rpg Lane B,
   `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`). Cost `fused_strategic_pass` (§2) before calling it waste or legitimate. Every fix has to be
   behaviour-neutral: identical canonical hashes under `audit_mode` (`performance_contract.md` §4.1, parity
   invariant). v1 is recorded and re-anchored (#725, #747, #748), so the old "nothing touching `src/**` before the v1 record" rule no longer applies.
2. **Make the test cycle measurable, and move it off this host** (draft tickets T1 to T3). No engine change.
3. **Name the ports, then add modes one at a time** (§5, §6). Each mode goes through the conformance suite (§5)
   before any result it produces is used.

Steps 1 and 2 serve goal (a). Step 3 serves goal (b), and is worth it only after step 1 has landed.

## 4. The four modes

Every mode runs the **same simulation rules**. Only the execution around them changes: executor, clock, commit
order, proof output. Every result carries its mode label (`performance_contract.md` §3.1 already requires
Execution Mode and RuntimeMode on a claim). **Results are compared only within one mode.**

| # | Mode | Same seed, same result? | Where the speed comes from | Status |
|---|---|---|---|---|
| 1 | Certified | yes, byte-identical, every tick | none (the reference) | exists |
| 2 | Fast test | yes, same outcomes and the same final hash | drops per-tick proof output | new, cheap |
| 3 | Parallel-deterministic | yes, but only for backends a parity matrix proves | more cores | new, medium to hard |
| 4 | Live | no | sheds work to keep wall-clock pace | exists (server only) |

### Mode 1: Certified (today's outcome-run contract)
- **Runs as:** `LocalSequentialExecutor`, `PinnedNormalGovernor`, `audit_mode` and `no_frame_pacing`, fixed budgets.
  Replay is on, so the per-tick SHA-256 `TICK_END.hash` is emitted (`docs/engine/kernel.md`, "State Hashing in
  Phase 7"; `tools/test_architecture/rpg_gate_run.py:60-66`).
- **Guarantees:** DET-PORT-0 (PERF-D2); PERF-D1 A2's "fixed budgets" contract for outcome runs.
- **Contract:** fixed budgets (`audit_mode`, or pinned NORMAL), per PERF-D1 A2. `CANONICAL` is only for runs that measure cost or
  governance, and a run is never compared with a run on another contract; see [conformance_suite_design.md](conformance_suite_design.md) §2.
- **Gives up:** nothing. Every other mode is checked against this one.
- **Used for:** the rpg gate, paired runs, certification, determinism and regression tests.

### Mode 2: Fast test
- **Runs as:** Mode 1 plus `no_replay` (the flag exists: `src/engine/kernel.py:206`), so no per-tick
  `TICK_END.hash`.
- **Keeps:** the same executor, the same fixed budgets and the same world evolution. `kernel.md` says "Shutdown
  always emits the final canonical hash regardless of runtime mode", so end-state proof stays.
- **Gives up:** the whole replay stream, not only the digest. `no_replay` sets `replay_allowed=False`, and
  `ReplayManager.emit` returns early for every event (`src/engine/replay_manager.py:99`). So there is no
  `REFINED_UPDATE` with its fingerprint (`kernel.py:657`) and no `TICK_END` with its hash (`kernel.md`, Phase 7).
  That means:
  - no per-tick determinism proof: you cannot name the first tick at which two runs diverge;
  - no replay of the run.
- **Does not give up:** the PERF-D1 A2 contract. `no_replay` changes no budget and reads no clock.
- **Expected saving:** at least the digest share, 9 to 27 % of a tick (PROVISIONAL; a lower bound, since the
  other replay emits stop too).
- **Used for:** paired arms (behaviour and, once T3 passes, neutral steps), the rpg gate if testing-planner agrees,
  and exploratory runs.
- **Paired proofs do not read the digest (code read, 2026-10-22).** `tools/rpg_measure/arm_child.py:58,69` computes
  `start_hash` and `final_hash` directly with `CanonicalStateHasher.get_hash`. The neutral check
  (`paired.py:174-180`) and the self-check (`stats.py:125`) compare those hashes plus fates and counters. Mode 2
  could therefore serve neutral steps too.
- **Ruled YES by perf-planner (2026-10-22, #593 comment 6343379030):** "Paired arms may run with `no_replay`, under five
  conditions." It is consistent with PERF-D1 A2, because A2 decides the budget and signal contract and `no_replay` changes
  neither, nor any clock; it turns off one non-authoritative output. The five conditions, quoted:
  1. "**Arm path only.** `arm_child.py` and the gate both call `rpg_gate_run.build_kernel` [...] Adding the flag there would also
     change the gate, which is testing-planner's call and an open owner question. T3 must pass `no_replay` only from the arm,
     e.g. an explicit parameter that defaults off."
  2. "**T3's proof stands as drafted:** identical start and final hashes, fates and counters with and without the flag (3 worlds
     × s42 × 1000 ticks). `simulation_events.jsonl` counters are still written. The manifest's `audit_mode` and
     `signals_zeroed` are non-null in both arms. This is a code reading, so the run has to confirm it."
  3. "**Recorded and refused when mixed.** The arm document records `replay`. Paired refuses to compare a replay-on arm with a
     replay-off arm unless the hashes prove them equal."
  4. "**No perf claim.** The wall-time before and after is a same-host, PROVISIONAL tooling number. It is not a baseline and not
     a tripwire reference, and nobody quotes it as an engine speed-up."
  5. "**Proof scope.** Behaviour and neutral proofs keep comparing `CanonicalStateHasher` state hashes, which are unchanged.
     Anything that later needs a per-tick digest trail (replay verification, divergence bisection) runs with replay on."
- **Not used for:** certification.
- **Owner of the ruling:** perf-planner (PERF-D1 contracts). Whether the gate adopts Mode 2 stays an owner question (§8 Q2).

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
  - ordered `world_events_add` and recorder order (whether any digest depends on event order is unconfirmed: no event digest was found, §5).
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

### Mode 5: dropped (2026-10-26)
Relaxed or distributed execution is **not in this plan**. The owner set the target scale to offline research on one machine
(#715, comment 6408481790), and it conflicts with `docs/architecture/system_overview.md` ("What is deliberately not distributed")
and the devops amendment's single replica. It reopens only by an ADR amendment (lead-planner), and only if the owner names a world
that one machine cannot hold after step 1 and Mode 3a. For testing, "distributed" still means **many seeds on many runners, each in
Mode 1 or 2** (draft T2), which keeps determinism and needs no ADR.

## 5. Ports and the conformance suite (precondition for Modes 2 and 3)

A mode should swap an implementation behind a named port, not patch the core. Proposed ports, each with its
contract and its Mode 1 implementation:

| port | Mode 1 implementation | audited verdict ([port_leak_audit.md](port_leak_audit.md), at `b281d0c3d`) |
|---|---|---|
| clock | fixed budgets, pinned NORMAL | Pacing and timers reach telemetry only. The leak is the default `LIVE` signal contract choosing the runtime mode ([§2](port_leak_audit.md#2-clock)) |
| random source | `DeterministicRNG(seed)`, counter-keyed | Confirmed: a checkpoint restore draws stateless randoms from seed 0, and salted `hash()` at `military_conflict.py:339` reaches hashed `groups`; one more salted `hash()` site, reach unverified ([§3](port_leak_audit.md#3-random-source)) |
| executor | `LocalSequentialExecutor` | Confirmed: the profile picks the executor implicitly; M3+ ([§6](port_leak_audit.md#6-executor-commit-path-event-sink)) |
| commit path | `refine` then `ApplyPath.apply_generation` | Confirmed: no leak for Modes 1 to 3a; 3b and 5 change it |
| event sink | `EventRecorder`, ordered | "Ordering feeds the digest" is **not confirmed**: no event digest exists and the final hash is state-only. Eviction is a cost, and H3 is closed (§2) |
| state store and hash | `AuthoritativeState`, `CanonicalStateHasher` | Confirmed and wider: the hash omits seven durable fields (the six below plus `last_hit_tick`), `information_providers` among them; `terrain` is not a gap ([§5](port_leak_audit.md#5-canonicalstatehasher-coverage-main-item)) |
| process scope | one process per run | Confirmed, all M3+, none reaches the hash; the content thread-local is not a leak ([§4](port_leak_audit.md#4-process-global-singletons)) |

**The v1 baseline is blind to seven fields.** The final hash, and the paired proofs that rely on it, cannot see a divergence in `item_instances`, `recent_world_events`, `quest_registry`, `factions`, `clans` or `information_providers` (lead-planner-u24, #593 comment 6346664156; rpg-planner ruled `recent_world_events` is state, so all six count, #593 comment 6347182683), nor in HUNGER step B's `last_hit_tick`, which ships unhashed by perf ruling (ii) (#593 comment 6384425767; owner #715 comment 6384423281). F1's single flat-sha256 bump hashes all seven; it starts after step B lands and finishes before the M1 record ticket. v1 itself stays as it is. Until F1 lands, a "same final hash as Mode 1" check is blind to seven fields, so building the conformance suite waits for it.

**Conformance suite.** A fixed set of worlds and seeds runs in every mode:
- Modes 2 and 3 must reproduce Mode 1's final canonical hash.
- Mode 4 asserts invariants only, as `test_cert_long_run_stability.py` does today.

The worlds, seeds, cases, blind-to lists, the side digest, the Mode 3 matrix and the lanes are in
[conformance_suite_design.md](conformance_suite_design.md). Lane placement stays pending testing-planner.

**Ownership:** testing-planner (lane placement), with perf-planner for the parity matrix (PERF-D2).

## 6. What each step needs, and who owns it

| step | needs | owner |
|---|---|---|
| 1 H2 fix | done on Lane C (PR about to open); hash-identical. H1 next on Lane B. H3 and H4 are closed (§2) | rpg-planner (src), perf-planner reviews the measurement |
| 2 T1 run and rerun accounting | draft ticket | testing-planner (with rpg for `tools/rpg_measure`) |
| 2 T2 paired runs off this host | draft ticket | testing-planner; lead for host policy |
| 2 T3 / Mode 2 `no_replay` for paired arms | perf ruling **done: YES** (§4); the draft ticket remains | perf-planner ruled; rpg or testing implements |
| Mode 3a | stack-survey evaluation, parity matrix | perf-planner (PERF-D2, M6) |
| Mode 3b | PERF-M6-T05 proposal, then an ADR. PERF-M6-T05 has **no ticket**: it is a line in `docs/plans/design_enhancement/performance_milestones_epic.md` (M6), so perf should record the fold of the Resolution-parallelism evaluation on the M6 epic or file T05, or it can silently disappear | perf-planner, then lead-planner |
| ports, conformance suite | **audit done** ([port_leak_audit.md](port_leak_audit.md)); **design done** ([conformance_suite_design.md](conformance_suite_design.md)); building the suite waits on step 1 and the F1 seven-field hash bump; a docs-only port-contract pass can start now | architecture proposed; rpg and testing build |

**T2 runner facts** (platform-planner, relayed by lead-planner, 2026-10-22):
- there is no self-hosted runner, and the repo is public, so adding one means hardware, hardening and an owner decision;
- GitHub-hosted runners have 4 vCPU and 16 GB, a 6 h job limit and free minutes;
- a runner's identity is a description, not a fixed machine: fine for byte-identity checks, unfit for timing comparisons;
- run both arms of a pair in the same job, on one VM.

## 7. Explicitly not proposed

- Non-determinism as a speed lever. It buys little on its own, and it costs paired runs, replay and the gate.
- More threads in Collection under the GIL: measured slower.
- A relaxed mode inside the gate path. PERF-D1 A2 requires fixed budgets for outcome runs, and the rpg gate is
  advisory, never a required check (`docs/plans/test_architecture/roadmap.md` §4.1, §4.2).

## 8. Open questions for the owner

1. **Target scale for goal (b):** **Answered 2026-10-26** (#715, comments 6408481790 and 6409936521): option A, offline research scale on one
   machine (about 100 to 2000 entities). Speed comes from step 1 (H1, H2) plus T2; Mode 3 is evaluate-only; **Mode 5 is dropped**. The
   10k / 50 ms / 2 GB figure in `docs/performance/optimization_architecture.md:21` stays as perf's bigger-world target, measured by a capacity run (PERF-M2-T03/T04).
2. **Mode 2:** may paired arms (and the gate) use it once perf rules on it and T3 passes? **Answered in part:** perf ruled YES under five conditions (§4, #593 comment 6343379030). Whether the **gate** adopts it is still the owner's and testing-planner's call.
3. **H2, H3, H4:** **Answered.** H3 and H4 were re-measured and both CLOSE (§2). H2 is done on Lane C (§2).

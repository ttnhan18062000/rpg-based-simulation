---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, determinism]
---

# Conformance-suite design for the engine execution modes

**Status:** design, advisory, not decided. Design only: no tests, code or runs were written, and every number is
carried from the cited document, not measured here. Written by `architecture-implementer` for ticket
`TCK-20261022-ARCHITECTURE-CONFORMANCE-SUITE-DESIGN`, dispatched by `architecture-planner` (scope approval: issue #715,
comment 6345579717; start approval: comment 6346236596). Input: [port_leak_audit.md](port_leak_audit.md) (findings F1 to
F5, audited at `main` `b281d0c3d`). The suite is the one the proposal's §5 names as the precondition for Modes 2, 3 and 5;
this doc cites the proposal by section, not by quote, because item B may change its wording.

**Decisions this doc does not take.** Lane placement is testing-planner's. The hash scheme and the stopgap digest are
perf-planner's. Whether `recent_world_events` is canonical state is rpg-planner's. Each is an open question in §9.

## 1. What the suite must prove, and the one thing it cannot yet see

The proposal asks that Modes 2 and 3 reproduce Mode 1's final canonical hash, that Mode 4 assert invariants only and that
Mode 5 assert invariants and outcome distributions only. The audit shows that hash equality is a weaker proof than it
looks today:

- the hash omits `item_instances`, `recent_world_events`, `quest_registry`, `factions`, `clans` and `information_providers`
  (audit §5; F1), so a mode can diverge there and still pass;
- the hash depends on `PYTHONHASHSEED` whenever a faction attack fires (F4);
- a restored checkpoint draws stateless randoms from seed 0 (F3);
- on the default `LIVE` contract the runtime mode depends on host speed (F2).

So the suite has two jobs: assert what each mode promises, and **say, case by case, what the assertion cannot see**. Every
case below carries a "blind to" list. A green result is read with that list beside it.

## 2. Mode preconditions

Every case records its **signal contract** (`signal_contract_record`, `src/engine/signal_source.py:197`; the kernel writes it
into the run manifest at `kernel.py:184,388`). The suite **never compares two runs across contracts** and refuses a mixed
pair (case P1).

| mode | precondition the suite enforces | source |
|---|---|---|
| 1 Certified | fixed budgets: `audit_mode`, or pinned NORMAL (`PinnedNormalGovernor`), `LocalSequentialExecutor`, `no_frame_pacing`, replay on. Build it with the pinned recipe at `tools/test_architecture/rpg_gate_run.py:build_kernel` | PERF-D1 A2 (`docs/architecture/performance_optimization_decisions.md`, about :357); proposal §4 |
| 2 Fast test | Mode 1 plus `no_replay`. The flag is **recorded in the arm's manifest** and a pair with mixed `no_replay` is **refused** unless the hashes prove them equal. `no_replay` is passed **from the arm path only**, because `rpg_gate_run.build_kernel` is shared with the gate and must not change for it. Replay stays **on** wherever a per-tick digest trail is needed (any case that must name a first divergent tick) | perf-planner conditions, #593 comment 6343379030; draft T3 |
| 3 Parallel-deterministic | Mode 1 contract plus a named backend and worker count. Claimed only for a backend and count in a passing parity matrix (PERF-D2 DET-PORT-1); otherwise the case reports "unclaimed", not red | proposal §4; PERF-D2 |
| 4 Live | `LIVE` contract, by design. The suite asserts invariants only and records the contract | proposal §4 |
| 5 Relaxed | none beyond a stated seed set. Invariants and distributions only | proposal §4 |

**`CANONICAL` is not a stand-in for fixed budgets.** It is for runs that measure cost or governance (`tools/perf` baselines,
the tripwire, capacity runs). Under today's cost model T08 (#591) measured `strategic_100` and `mixed_200` in CONSTRAINED
or SURVIVAL, `frontier_extended` in SURVIVAL on 902 of 1000 ticks and `frontier_marches` in CONSTRAINED on 876 of 1000, so a
`CANONICAL` run and an `audit_mode` run give different outcomes. The default flip for outcome runs is rpg's
`TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-*`, queued after v1; until it lands the suite must **set** fixed budgets
explicitly and not rely on a default.

## 3. Worlds and seeds

A small fixed matrix. Worlds are loaded as `WorldRepository("data/worlds").load_world_with_context(name)` then
`WorldCompiler.compile(spec, seed, context=...)` (`rpg_gate_run.py:build_kernel`). Corpus roles are from
`tools/generate_corpus_registry.py:30-52`. Cost figures are the per-tick means from `docs/performance/tick_cost_growth.md`
§2 (pinned contract, one loaded 6-vCPU host, **PROVISIONAL**); the gate worlds have no figure there, so their cost is
`UNVERIFIED (needs run)` and assumed to be of the same order.

| id | world (`data/worlds/<name>/`) | why it is in | ticks per case | rough cost per run |
|---|---|---|---|---|
| W1 | `frontier_living_world` | rpg gate world and paired-run world (`tools/rpg_measure/paired.py:27`); broad coverage: needs, economy, social, cooperation. Corpus role `end_to_end` | short 300, full 1000 | UNVERIFIED; same order as W4 assumed, so about 30 to 40 s short and 2 min full |
| W2 | `urban_political` | gate and paired world; the political, faction and information content. Corpus role `regression_baseline`. A candidate for exercising `factions`, `clans` and `quest_registry` | short 300, full 1000 | UNVERIFIED, same assumption |
| W3 | `crowded_frontier` | gate and paired world; density, so the pair-cost paths (H1, H2). Corpus role `stress` | short 300 | UNVERIFIED, likely the dearest of the three |
| W4 | `frontier_extended` | the corpus world with the longest profile: events fill the recorder buffer (`max_events` 5000) so the eviction path (H3) runs; the late ticks are where `advancement` grows from 16 % to 40 % of a tick | full 1000 only | 105 ms per tick early, 130 ms late (`tick_cost_growth.md` §2), so about 2 min |
| W5 | `unit_faction_tension` | the smallest faction world, the **F4 candidate**: it must produce at least one `GroupRecord` with `FACTION_SQUAD` roles from `MilitaryConflictPhase` (`military_conflict.py:~335-345`). Corpus role `unit` | 300 | UNVERIFIED, small |
| W6 | in-test 3-faction state `_make_initial_state` | `tests/integration/scenarios/test_faction_campaign.py` builds ALPHA/BETA at WAR with `border_region`. It has **no entities**, so no GUARD squad forms; it exercises the siege and territory logic, not the F4 group id. Listed so nobody assumes it covers F4 | 25 | negligible |

**Seeds.** Seed **42** on every world (the seed the paired neutral check and draft T3 already use). Seeds **43 and 44** on W1
and W2 in the full lane only, to catch a seed-dependent divergence without multiplying cost. Seed **0 must never be the
only seed**: F3 is invisible at seed 0 (the restore uses seed 0 and so agrees with it). This is a rule of the matrix.

**The attack precondition (F4).** Whether W5 or W2 actually fires a faction attack is `UNVERIFIED (needs run)`. The suite
therefore starts with a **probe case (A0)**: run the world to its tick count in Mode 1 and assert that at least one group
with role `FACTION_SQUAD` exists in `state.groups` (or was added) at some tick. A cross-process case on a world that fails
A0 proves nothing about F4 and must be reported as **vacuous**, not green. If neither W5 nor W2 passes A0, the matrix needs a
purpose-built world; that is an open question for rpg-planner (§9).

**Restore case (F3).** A checkpoint-restore case runs W1 at seed 42: run to tick 200, save and restore with
`ScenarioCheckpointer` (`src/engine/scenario_checkpoint.py`), run 200 more, and compare the final hash with an unbroken
400-tick run. Seed must be non-zero. Existing coverage is `tests/unit/engine/test_scenario_checkpointer.py` (round trip of
the tick, the header and the RNG checkpoint); it does not compare a hash with an unbroken run (audit §8, UNVERIFIED).

## 4. Assertions per mode, and what each is blind to

"Final hash" is `CanonicalHashScheduler(...).compute_digest(...).require_value()` at `kernel.py:1196-1197`; `kernel.md`
says shutdown emits it in every mode. "Trail" is the per-tick `TICK_END.hash`, which exists only where replay is on.

| mode | asserted | blind to |
|---|---|---|
| **1** | (a) Reproducibility: the same world and seed run twice, in two processes, gives the same final hash and the same trail. (b) Invariants: HardLawMonitor clean, conservation holds (`src/core/conservation.py`). (c) Contract recorded and equal to fixed budgets. (d) `state.pressure_signals == {}` at the end (guard G1, audit F5) | the six unhashed fields (until PERF-D5); `current_mode` (unhashed, effects only); a divergence that exists in **both** runs (a deterministic bug is not a conformance failure); anything the world never exercises |
| **2** | final hash equals Mode 1's, on the same world, seed, ticks and contract; fates and behaviour counters equal; the manifest records `no_replay`; the pair is refused if the flag is mixed | everything Mode 1 is blind to; **no trail, so the first divergent tick cannot be named** (a red result needs a Mode 1 re-run with replay to localise it); the replay stream itself (absent by design); whether a consumer reads `replay_allowed` outside the hash (draft T3 verification 1 to 3) |
| **3** | final hash and the trail equal Mode 1's, **for each (backend, worker count) in the parity matrix**, run with replay on so the trail exists; a backend outside the matrix reports "unclaimed" | everything Mode 1 is blind to; order-dependent effects that cancel out by the end of the run; the 3b order-dependent reads (proposal §4: they are not exercised until 3b exists); the six fields, which is the worst case here because parallel apply could reorder exactly the registries (`factions`, `clans`, `quest_registry`) that nothing hashes |
| **4** | invariants only, as `tests/certification/test_cert_long_run_stability.py` does (5000, 2000 and 1000 tick runs with warmup): HardLawMonitor, conservation, no crash, bounded memory growth; the contract is recorded as `LIVE` | all outcomes: two Mode 4 runs are expected to differ. Cannot detect a subtle rule bug that preserves invariants |
| **5** | invariants plus outcome **distributions** over a stated seed set (population, fates, economy totals), compared with Mode 1's distribution on the same seeds | per-run identity; any single-seed regression; the power of the test is bounded by the seed count (the paired method needs more seeds under noise, proposal §4) |

### 4.1 Canary: the six unhashed fields (audit F1)

Because Modes 2 and 3 rest on hash equality, the suite carries an **inverted canary (case C1)**: take a Mode 1 end state,
change one of the six fields on a copy (add an `item_instances` entry, append a `recent_world_events` entry, flip a faction
field, and so on), hash both, and assert that the hashes **differ**. Today C1 is **expected-red for all six fields** (the
hash is blind), which documents the gap in executable form. It turns green only when the PERF-D5 bump covers each field. A
field that rpg rules out of canonical state (for example `recent_world_events`, if it is a view) is removed from C1 with
the ruling cited.

### 4.2 Stopgap per-field digest (a design option only; perf's call)

Until the bump, the suite could compute a **side digest** over exactly the six omitted fields, test-side, with the same
canonical-JSON rule as the hasher (sorted keys, compact separators, SHA-256), and assert it equal alongside the final hash
in Modes 2 and 3. Properties:

- it is **suite-only**: it is not `PROOF_DIGEST_SCHEME`, never appears in a manifest as a proof digest and does not touch
  `src/**`;
- a mismatch is a conformance failure, a match is *not* a determinism proof (it is one more field set compared, no more);
- it needs a canonical dict for each of the six value types, and some may not have `to_canonical_dict` (an audit read did
  not check); `UNVERIFIED (needs read)`;
- it is discarded when the PERF-D5 bump lands.

Whether to build it is perf-planner's call (§9, Q2). Without it, the "blind to" list in §4 stands in full.

## 5. Cross-process and in-process cases

| id | case | catches | expected today |
|---|---|---|---|
| X1 | same world, seed and ticks in **two processes with different `PYTHONHASHSEED`** (for example `0` and `1`), Mode 1; compare the final hash | F4: `hash((contested_region_id, ...))` at `military_conflict.py:339`, and possibly `perception/filter.py:88,97` | **vacuous** unless the world passes A0. **Expected-red** on a world that passes A0 (`GroupRecord.id` is salted, and `groups` is hashed). Green on a world with no attack proves nothing |
| X2 | two runs of two different worlds **in one process, sequentially**, each compared with its own solo run | process-global state that leaks between runs: `behavior_consumers`, `scenario_registry`, the terrain cache (audit §4) | expected green (a sequential run resets nothing it depends on); a red here is a new finding |
| X3 | two runs **in one process, interleaved on threads** (the Mode 3 in-process pool case) | `decision_trace_writer._active_writer` (a second start overwrites the first), `ObservabilityConfig._override_mode`, the shared observability queue and publisher | final hashes expected green (none of these reaches the hash); **trace and event output expected red** (cross-contaminated). X3 asserts per-run output files are disjoint and complete. Marked "Mode 3 thread-pool only"; not needed for a process pool |
| X4 | a run **resumed from a checkpoint** vs an unbroken run (the F3 case of §3) | F3: `scenario_checkpoint.py:85` | **expected-red** until rpg builds the RNG with `state.seed` |

## 6. Contract and guard cases

| id | case | covers |
|---|---|---|
| P1 | a pair whose arms recorded different `signal_contract` (or different `no_replay`) is refused before any hash is compared | F2; the Mode 2 condition of §2 |
| P2 | a Mode 1 case on a profile whose `signal_contract` is `LIVE` and which is not on fixed budgets is refused as "not Mode 1" | F2 |
| P3 | informational only: one world run under `CANONICAL` and under fixed budgets, with the two mode traces recorded side by side and **never compared for equality** | documents the T08 finding for readers; no pass or fail |
| G1 | at the end of every Mode 1 and 2 run, `state.pressure_signals` is empty | F5: a tripwire if anyone adds a producer of `StateUpdate.pressure_signals_set` (`apply.py:345`) or populates it outside `src/testing/scenario_runner.py:100` |
| A0 | the attack-precondition probe of §3 | F4 (makes X1 non-vacuous) |

## 7. Findings to cases

| audit finding | case | note |
|---|---|---|
| F1 hash omits six fields | C1 (inverted canary), the "blind to" lists of §4, the optional side digest of §4.2 | green only after PERF-D5 |
| F2 `LIVE` default lets wall-clock choose the mode | P1, P2, P3, and the precondition rows of §2 | the A2 default flip is a separate rpg ticket |
| F3 restore draws from seed 0 | X4 (§3 restore case); the non-zero-seed rule | expected-red |
| F4 salted `hash()` | A0, X1 | X1 is vacuous without A0; `perception/filter.py:88,97` reach is `UNVERIFIED` and X1 on a world that exercises perception would show it |
| F5 `pressure_signals` dormant | G1 | the id counters are **not covered, because** they surface in hashed entity and node ids at the next allocation (audit F5: low risk, no fix) |
| audit §4 singletons (no finding number) | X2, X3 | M3+ |
| audit §6 event sink (no event digest found) | **not covered, because** there is no event digest to compare; if one is found, add it to the Mode 1 row and to the blind-to lists | audit §6, `UNVERIFIED` |

## 8. Lanes (DRAFT, pending testing-planner) and dependencies

**Runner facts (draft T2).** GitHub-hosted runners: 4 vCPU, 16 GB, 6 h job limit, free minutes, no self-hosted runner. Both
arms of a pair run in one job on one VM. A runner's timing is unfit for timing comparisons, so **no case asserts on
time**; every case asserts on hashes, counts or invariants only. An engine run holds about 101 to 130 MB (`tick_cost_growth`
§5), so several runs fit in one job. Existing lanes: `tests/` fast (`-m "not slow and not extra_slow"`, `test.yml`), a
nightly cron (`test.yml:7-12`), `slow-regression.yml`, and the sharded gate (`rpg-gate-report.yml`).

| lane (proposed) | cases | why |
|---|---|---|
| C-short: a PR-time job | A0, C1, G1, P1, P2, W5 seed 42 at 300 ticks for X1 and Mode 1 vs Mode 2, W1 seed 42 at 300 ticks for Mode 1 vs Mode 2 | minutes; the cheapest cases that can catch an F4 or Mode 2 regression |
| C-nightly: the `test.yml` cron | W1 to W3 at 1000 ticks, seeds 42 to 44 (W1, W2), Mode 1 vs Mode 2, X1, X2, X4 | a few tens of runs of about 2 min each, one job per world (shard as the gate does) |
| C-slow: `slow-regression` | W4 at 1000 ticks (the eviction path), X3, Mode 4 invariants (the certification long-run tests exist) | longest runs |
| not CI | P3 and any Mode 3 matrix with real workers | Mode 3 needs a runner with the same interpreter and OS identity to stay DET-PORT-0 (draft T2 note); until then it is a local or second-host case |

**Dependencies.** `pending step 1` marks a case that needs step-1 code that does not exist yet.

| case | waits on |
|---|---|
| A0, C1, G1, P2 | nothing for the design; the code is test-side. A0 is the first thing to run once anyone runs anything |
| P1 | `no_replay` in the arm path and its manifest record (draft T3): **pending step 1** |
| Mode 1 reproducibility (two processes) | v1 record PR merged (the freeze: nothing touching `src/**` lands before it); no code needed, but the lane needs T2 (paired arms off this host) for a CI job: **pending step 1** |
| Mode 2 vs Mode 1 | draft T3 and a perf ruling that `no_replay` is consistent with PERF-D1 A2: **pending step 1** |
| C-nightly worlds timed | draft T1 (run and rerun counts) for lane budgeting: **pending step 1** |
| X1 | A0 passing on a world; rpg fix F4 to turn it green |
| X4 | rpg fix F3 to turn it green |
| C1 | PERF-D5 scheme bump, which comes after `RECORD-BASELINE-V1` (perf-planner); rpg ruling on `recent_world_events` |
| X3 | nothing; only meaningful for a Mode 3 thread pool |
| Mode 3 | a named port set (proposal §5), a parity matrix (PERF-D2), 3a code: **pending step 1** and later |
| Mode 4, 5 | existing certification tests for Mode 4; Mode 5 needs its ADR first |
| H2, H3, H4 fixes | they are what the suite is for: each must pass Mode 1 against its own base with identical hashes (`performance_contract.md` §4.1); the neutral check in `paired.py:174-180` already does this for 3 worlds at seed 42 |
| A2 default flip | rpg `TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-*`, after v1; until then the suite sets fixed budgets explicitly |

## 9. Open questions

| # | question | owner |
|---|---|---|
| Q1 | Where does each lane run, and is C-short a required check? (The test_architecture roadmap principle 8 says paired jobs are not required checks.) | testing-planner |
| Q2 | Is the §4.2 side digest worth building before PERF-D5, or does the "blind to" list suffice? | perf-planner |
| Q3 | Is `recent_world_events` canonical state or a view? Decides whether C1 has five or six fields. | rpg-planner |
| Q4 | Does any shipped world (W5, W2) pass A0? If none does, is a purpose-built attack world acceptable in `data/worlds`? | rpg-planner |
| Q5 | Does `StateFingerprinter.get_fingerprint` (`src/replay/fingerprint.py:33`) cover `factions`, `clans` or `quest_registry`? If so the trail already sees them under replay and the Mode 3 blind-to list shrinks (audit §5, `UNVERIFIED`) | perf-planner |
| Q6 | Is there any events digest outside `src/`? If yes, add it to the Mode 1 row (audit §6) | perf-planner |
| Q7 | The Mode 3 matrix: which backends and worker counts, and on which host kind? | perf-planner with testing-planner |

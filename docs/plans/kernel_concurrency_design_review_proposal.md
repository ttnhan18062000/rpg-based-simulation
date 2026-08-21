---
status: active
layer: engine
authority: P2
audience: agent
tags: [engine, documentation, determinism, performance]
---

# Proposal: Kernel Concurrency Design Review — Findings & Follow-Ups

**Origin**: a system-design discussion session (2026-08-17, no code/test changes made) that
investigated the kernel's concurrency model — why the tick loop is a synchronous fork-join
orchestrator over a bounded worker pool rather than asyncio/anyio, how race conditions are
structurally prevented, how the engine behaves under resource pressure, and what governs
performance claims. The discussion surfaced one piece of missing documentation and several
concrete gaps between what the docs claim and what the code/CI actually does. This proposal
captures each as a discrete, independently-addressable concern for investigation and ticketing.
None of these have been fixed yet — this document is the handoff.

---

## C1 — Land the kernel concurrency & design-philosophy doc

We produced a complete high-level design write-up during the discussion, covering: why the
kernel's Collection phase is a synchronous fork-join over a bounded thread/process pool instead
of asyncio/anyio; how immutable state snapshots, a stateless per-call RNG, and the "Option A"
one-result-per-entity protocol structurally prevent race conditions without relying on locks or
the GIL; how the RuntimeMode ladder (NORMAL/CONSTRAINED/DEGRADED/SURVIVAL) and PhaseBudgetGovernor
degrade load gracefully under pressure; and the implicit design-priority order the engine follows
(see C5). This currently exists only as this conversation and an external artifact link — it is
not discoverable via `search_docs`, `graphify query`, or `docs/REGISTRY.yaml` the way the rest of
the project's institutional knowledge is. The full drafted content is in Appendix A below. We want
it placed into the docs tree (most likely `docs/architecture/`, alongside the other ADR-shaped
design docs), cross-linked from `docs/engine/kernel.md` and the three concurrency contracts it
summarizes, and folded into the knowledge index (`make knowledge-index-update`).

**Update (TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC, closed 2026-08-21):** resolved. Landed at
`docs/architecture/kernel_concurrency_design_philosophy.md` (status: active, authority: P1,
audience: developer), with all 4 mermaid diagrams (not the 2 this section's own intro implied),
cross-linked from `kernel.md` and all three concurrency contracts, and the two stale internal
"Known documentation drift" items updated in place.

## C2 — Fix the "is Collection concurrent or not" contradiction

`docs/engine/kernel.md` §"Concurrency & The Resolution Bottleneck" states: *"Concurrent
Collection: the Deliberation phase is the only window for parallel execution."* But
`docs/engine/contracts/simulation_kernel_contract.md` §9 "Kernel Boundaries" states: *"No
concurrency or parallel execution."* Both docs carry `status: active, authority: P1` and both
claim to be authoritative about the same kernel. The actual code (`src/engine/worker_manager.py`,
`ThreadPoolExecutor`/`ProcessPoolExecutor`) matches `kernel.md`'s description, not the contract's.
One of these two docs is stale and needs correcting to match the other and the code.

**Update (TCK-20260817-FIX-CONCURRENCY-DOC-CONTRADICTION, closed 2026-08-21):** resolved.
§9 "Kernel Boundaries" was corrected to a narrower, accurate statement: concurrency is bounded to
the COLLECTION phase only (`WorkerManager`'s `ThreadPoolExecutor`/`ProcessPoolExecutor`), with
RESOLUTION applying all proposals through a single deterministic serial commit order
(`ConcurrencyLaw`, `src/core/concurrency_law.py`) — kernel.md, simulation_kernel_contract.md, and
bounded_concurrency_contract.md now agree.

## C3 — Fix the 6-phase vs. 7-phase contradiction

`docs/engine/architecture.md` §2 describes a 6-phase kernel loop: INIT, GOVERNANCE, SCHEDULING,
PACKETIZATION, RESOLUTION, PERSISTENCE. `docs/engine/kernel.md` and
`docs/engine/contracts/simulation_kernel_contract.md` §4 both describe a 7-phase loop: INIT,
SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE — with no named GOVERNANCE
or PACKETIZATION phases at all. These three P1-authority docs disagree with each other about how
many phases the kernel actually has and what they're named. Needs reconciliation against the
actual phase implementation in `src/engine/kernel.py` (`_phase_scheduling`, `_phase_collection`,
`_phase_resolution`, `_phase_cleanup`, etc.), and the losing description(s) corrected.

**Update (TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION, closed 2026-08-21):** resolved. Corrected
`architecture.md` §2's fabricated GOVERNANCE/PACKETIZATION table to the real 7-phase list, also
fixed the identical defect in `docs/guides/simulation.md` (found during this ticket, not in its
original scope), added a reconciling note to `substrate_baseline_contract.md` §4, and removed the
`xfail(strict=True)` marker from `tests/docs/test_kernel_phase_names_consistent.py` — the living
test now genuinely passes for the first time.

## C4 — Close the benchmarking-integrity gap (RuntimeMode not scoped or enforced)

`docs/engine/performance_contract.md` §3.1 "Scoped Claims" requires a performance claim to bind
to exactly four dimensions: Runtime Profile, Hardware Class, Scenario, Execution Mode (LOCAL vs
CONCURRENT). `RuntimeMode` (NORMAL/CONSTRAINED/DEGRADED/SURVIVAL) is not one of the required
dimensions. We checked the actual CI gate directly:
`grep -rn "RuntimeMode\.|current_mode|assert.*mode" src/perf/*.py tests/perf/test_perf_regression_baseline.py`
returns only `src/perf/long_run_harness.py:225`, which *records* `active_mode` into its output
but is never asserted on. `tests/perf/test_perf_regression_baseline.py` — the live CI gate per
`docs/performance/perf_baseline_policy.md`'s own 2026-08-08 correction note — computes a single
blended `avg_tick_compute_ms` over the whole sampled run and compares it to `baseline_avg * 1.25`,
with no check that `RuntimeMode` stayed `NORMAL` for every sampled tick. This is a real masking
mechanism, not just a documentation gap: if a benchmark scenario's load pushed the engine into
CONSTRAINED/DEGRADED partway through its 1,000-tick sampling window, those ticks get cheaper
(smaller budgets, `EXACT_DIRTY` scan policy instead of `FULL`) and blend into the reported
average — a real regression that makes NORMAL-mode ticks slower could be partially offset by the
engine degrading sooner and doing measurably less work per tick, without anyone acting in bad
faith. This directly conflicts with `docs/engine/contracts/certification_contract.md` §6's stated
principle: *"No modification of kernel laws for benchmark vanity."* That discipline already
exists for full certification runs (`FAILED_DEGRADATION_ORDER`, `FAILED_RECOVERY` conformance
checks) and is absent from the everyday CI perf-baseline gate that actually blocks commits. We
want `RuntimeMode` added as a required Scoped-Claims dimension in `performance_contract.md`, and
an enforcement mechanism (assertion or gate) added to `tests/perf/test_perf_regression_baseline.py`
(or wherever the investigation determines is correct) that fails or clearly flags a benchmark run
if the Governor ever left NORMAL mode during the sampled window.

**Update (TCK-20260817-RUNTIMEMODE-BENCH-SCOPING, closed 2026-08-21):** resolved. `RuntimeMode`
added as a 5th Scoped-Claims dimension; `BenchHarness.run_benchmark()` now samples
`kernel.status.current_mode` every tick and exposes `result["mode_sequence"]`;
`test_regression_vs_baseline` asserts no excursion occurred, independent of the compute-time
check. An empirical measurement pass (not assumed) against all 6 live-parametrized scenarios
found a real, unrelated pre-existing defect: `WorkerManager.get_stats()` defaults
`worker_utilization` to `1.0` (not `0.0`) whenever `max_worker_count == 0`, which every
`PERF_*_LOCAL` profile sets — this unconditionally trips the Governor's DEGRADED threshold
regardless of real load, so all 6 scenarios currently show `DEGRADED` for every sampled tick.
The new gate is correctly soft (warning-only) for all 6 pending a follow-up ticket to fix the
`WorkerManager`/Governor signal defect itself — not silently loosened or force-fit to pass hard.

## C5 — State the engine's design-priority order explicitly

`docs/engine/project_lawbook_m10.md` § Architectural Pillars lists five pillars — Determinism,
Authoritative Apply, Bounded Resources, Hardware-Class Honesty, Observability Separation — with
no stated precedence between them when they trade off against each other. Notably,
performance/throughput is not one of the five pillars at all; it appears only as a constraint
("Hardware-Class Honesty") riding on top of "Bounded Resources." During the discussion we found
that every concrete mechanism in the kernel — the fork-join barrier that blocks Resolution until
all workers return, the RuntimeMode ladder's immediate-escalate/gated-recover asymmetry, work
debt being recorded as a durable ledger instead of being silently dropped, and
`certification_contract.md`'s "no modification of kernel laws for benchmark vanity" — is
consistent with one implicit ordering: Determinism, then Resource-Safety, then Performance
(pursued only within what the first two allow), then Auditability (proving the first three
actually held). This ordering is never written down as a rule anywhere we could find — it has to
be re-derived from code and cross-referencing multiple docs each time. We want this order (or
whatever the maintainers confirm is actually intended, if our reconstruction is wrong) stated
explicitly in the lawbook or a doc it links to.

**Update (TCK-20260817-STATE-DESIGN-PRIORITY-ORDER, closed 2026-08-21):** resolved.
`project_lawbook_m10.md`'s Architectural Pillars section now states the reconstructed order
(Determinism, then Resource-Safety, then Performance — only within what the first two allow, then
Auditability — proving the first three held) as a terse rule, cross-linking
`kernel_concurrency_design_philosophy.md` Part 1 as the single source of truth for the full
reasoning; the 5-item pillar list itself is unchanged and not mapped term-by-term onto the 4-item
order. Part 1's own stale "it is not stated as a rule anywhere" sentence was corrected in place to
confirm the lawbook now carries the terse rule while Part 1 remains the SSOT for the reasoning.
Four new doc-consistency tests were added to `tests/docs/test_doc_integrity.py` guarding order-term
verbatim match, cross-link presence, and non-recurrence of the stale sentence.

## C6 — Document why `concurrency_limit` decreases as `RuntimeMode` escalates

`src/engine/policy.py`'s `GovernorPolicy.from_mode()` sets `concurrency_limit` to 1.0 for NORMAL,
1.0 for CONSTRAINED, 0.5 for DEGRADED, and 0.25 for SURVIVAL — the active worker pool shrinks as
pressure rises. This is not self-evidently correct: naively, one might expect more pressure to
call for more parallel workers to clear a backlog faster. The actual reasoning (reconstructed
during discussion, not found written down anywhere) is that every other lever already shrinks the
scheduled batch by the time concurrency is throttled (LOD, cadence gating, phase budgets), so a
smaller worker pool on an already-smaller batch reduces thread/IPC contention rather than adding
scheduling noise to an already-stressed system. No doc states this rationale. We want it written
down next to `GovernorPolicy.from_mode()` or in `docs/engine/governance_logic.md`, so a future
contributor doesn't "fix" this into scaling the wrong direction.

**Update (TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE, closed 2026-08-21):** resolved. The
reconstructed rationale above was verified against real code (`PhaseBudgetGovernor.evaluate()`,
`SystemCadence.should_run()`, `DeterministicScheduler.select_work()`'s LOD/cadence gating) and
written down in both places: a docstring on `GovernorPolicy.from_mode()`
(`src/engine/policy.py`) and `docs/engine/contracts/bounded_concurrency_contract.md` §5.1 (not
`governance_logic.md`, which turned out to cover an unrelated Town Governance concept).

## C7 — Confirm where (if anywhere) the Collection-phase worker path consumes RNG

A grep across `src/engine/domain_logic.py`, `src/engine/combat.py`, `src/engine/movement.py`, and
`src/engine/worker_logic.py` for `rng.get_*` / `next_float` / `next_int` / `.choice(` /
`.weighted_choice` / `.sample(` calls returned no matches. This suggests combat-roll-style
randomness is resolved later, in the serial Resolution/apply phase, rather than inside the
parallel Collection-phase workers — which would be notable, since it means the concurrent worker
path may currently be fully deterministic-from-state with zero RNG consumption. This was only
confirmed by absence of a grep match, not a full call-graph trace, so it needs a definitive
investigation of where (if anywhere) `DeterministicRNG` is actually consumed in the tick, and the
finding recorded in `docs/engine/kernel.md` or the worker contract either way.

**Update (TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION, closed 2026-08-21):** resolved with a full
trace, not just an absence-of-grep-match inference, recorded at
`docs/engine/contracts/simulation_kernel_contract.md` §7.1 "RNG Consumption in Practice." Finding:
the Collection-phase worker path (`worker_logic.py`/`domain_logic.py`/`combat.py`/`movement.py`)
consumes zero RNG, consistent with combat's deterministic-by-design mechanics (`docs/mechanics/
02_combat_laws.md:11`); the only RNG draw in Collection-phase packet construction is
`executor.py:301`'s `packet_seed`, confirmed genuinely dead (computed, never read) and explicitly
deferred rather than silently left undocumented; and the three real downstream RNG consumers
(`EntityGenerator`, `QuestGenerator`, `GuildAction`) all run in serial `Kernel._phase_resolution()`,
never `_phase_collection()`.

## C8 — Audit `docs/engine/`, `docs/architecture/`, and `docs/performance/` for stale/duplicate/
contradictory content, and propose a structure that prevents this class of drift

This one discussion surfaced three live contradictions between individually-authoritative
(`status: active, authority: P1`) docs in these three directories: C2 (concurrent vs. not), C3
(6-phase vs. 7-phase), and a third — already self-flagged in-repo — where
`docs/performance/perf_baseline_policy.md` §2.2's core-count-only hardware-class table conflicts
with `docs/engine/contracts/certification_contract.md` §3's binary AND-rule (a 4-core/<8GB
machine is `CLASS_B` under one doc, `CLASS_C` under the other), flagged by
`TCK-20260702-OBSISO-ISOLATION-PROOF` as "known conflict, not resolved here." Three
contradictions found incidentally, in docs specifically about the topic we were investigating,
raises the question of how many more exist elsewhere in these directories on topics nobody has
recently cross-examined. We want a broader audit: identify any other stale, duplicate, or
mutually-contradictory docs across `docs/engine/`, `docs/architecture/`, and `docs/performance/`
(not limited to concurrency/performance topics), and propose a structural convention that makes
this class of drift less likely going forward — for example, a single canonical doc per topic
with all others required to cross-link rather than restate, or a periodic doc-parity check
similar to how `docs/parity_ledger/` already tracks mechanics-vs-code parity. Findings should be
recorded even in places where no immediate fix is applied, following the precedent already set by
`perf_baseline_policy.md`'s callout box for the hardware-class conflict.

---

## Appendix A — Drafted content for C1

The following is the full text produced during the discussion, intended as the starting point for
whichever doc location C1's investigation determines is correct. It includes two mermaid diagrams
(tick-loop flowchart, race-safety sequence diagram, and a RuntimeMode state diagram) that should
be preserved in the landed version.

> Also published as a live artifact during the discussion:
> https://claude.ai/code/artifact/5b90c23d-5251-411d-983e-4160973475f6

```markdown
---
status: draft
layer: engine
authority: P2
audience: developer
---

# Kernel Concurrency Model & Design Philosophy

## Purpose

The engine contracts define the *laws* concurrency and performance must obey. None of them
narrate the *model*: why the tick loop is synchronous while still running work in parallel, what
the engine is actually optimizing for when those laws trade off against each other, and how
"use the hardware" and "never break determinism" coexist under real load. This doc is that
missing narrative layer.

## Part 1 — Design Philosophy: what we're actually optimizing for

`docs/engine/project_lawbook_m10.md` lists five Architectural Pillars — Determinism,
Authoritative Apply, Bounded Resources, Hardware-Class Honesty, Observability Separation —
unordered, with performance appearing only as a constraint on Bounded Resources, never as a
goal in its own right. Reading `harness_architecture.md`'s Core Principles (Absolute Determinism
-> Resource Boundaries -> Auditability), `architecture.md`'s three Resource-Safe laws (Bounded
State, Non-Blocking Persistence, Progressive Degradation), and `certification_contract.md`'s
reporting law ("No modification of kernel laws for benchmark vanity") together implies one
consistent order: Determinism, then Resource-Safety, then Performance (only within what the
first two allow), then Auditability (proving the first three held). This ordering is implicit,
reconstructed from three documents plus code — it is not stated as a rule anywhere.

Every mechanism traced below is a specific engineering answer to one governing question: "How
do we use the hardware's available parallelism without ever letting *when* something ran change
*what* the outcome is?"

## Part 2 — The tick loop, with Collection expanded

The kernel (`src/engine/kernel.py`) executes 7 phases per tick: INIT, SCHEDULING, COLLECTION,
RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE. Only COLLECTION runs work in parallel; every other
phase is single-threaded. `_phase_collection()` dispatches work to a bounded thread/process pool
(`WorkerManager`, `ThreadPoolExecutor`/`ProcessPoolExecutor`) and blocks on `future.result()` for
every chunk before `_phase_resolution()` begins. That barrier is required by determinism, not a
missed optimization: `_phase_resolution()`'s first act is
`self._final_results.sort(key=lambda r: (r.class_priority, -r.local_priority, r.entity_id))` —
"same seed + same profile + same inputs => bit-identical state" requires applying every proposal
in one global, stable order, which requires having all of them before sorting any of them.

This is fork-join, not asyncio/anyio, because the Collection-phase workload (brain/action/
movement decision logic in `src/engine/domain_logic.py`, `worker_logic.py`) is CPU-bound, not
I/O-bound. asyncio's value is interleaving many idle-but-not-blocked tasks on one thread; CPU work
still needs `run_in_executor`/`to_thread.run_sync` underneath, i.e. the same thread/process pool
already in use. An event loop would add a scheduling layer for zero new capability, and
cooperative concurrency's safety model ("nothing mutates shared state across an `await` point")
is weaker than what's actually enforced (Part 3). `asyncio` does exist in this codebase, entirely
inside `src/api/ws/stream.py` — the FastAPI WebSocket layer streaming non-authoritative
observability events, on the explicitly non-authoritative side of the kernel contract's own state
classification.

## Part 3 — How Collection avoids race conditions

Three independent mechanisms:

1. State is structurally read-only, not read-only by convention. `EntityState.to_readonly()`
   converts entity properties to `ReadOnlyDict`, wounds/scars/inventory to tuples, equipment to
   `ReadOnlyDict`. Everything else workers can see (regions, resource nodes, buildings, terrain,
   groups, corpses, ground items) is `deep_freeze()`'d once in the kernel thread before dispatch
   and cached by object identity (`src/engine/executor.py`). Workers never hold a mutable
   reference to shared state.

2. The RNG is stateless per call. `DeterministicRNG.get_float/get_int/choice/...`
   (`src/platform/rng.py`) build a fresh `random.Random(composite_seed)` per call, seeded by a
   pure hash of `(base_seed, domain, tick, entity_id, sub_id)` — no shared generator to race, and
   results are order-independent regardless of which worker finishes first. The deprecated
   stateful twin (`next_float`/`next_int`) is unused anywhere in `src/`.

3. Output collisions are prevented structurally and validated twice ("Option A"). A worker's
   result set is filtered to `eid == packet.subject.id or eid == 0`
   (`src/engine/worker_logic.py:default_simulation_worker`). `ProtocolValidator`
   (`src/core/protocol_validator.py`) enforces "one work item per entity per tick" before
   dispatch and "no duplicate result per entity" after collection, raising
   `ProtocolViolationError` on conflict rather than silently merging it. Each pool chunk
   accumulates its own local result list; merging into the shared list happens only in the
   kernel thread, after every future has resolved. The one genuinely shared mutable object —
   `WorkerManager`'s inflight/active/peak counters — is protected by an explicit `threading.Lock`.

Open question, now resolved (TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION, closed 2026-08-21, see
C7 above): no `rng.get_*` calls were found in `domain_logic.py`, `combat.py`, or `movement.py` —
the Collection-phase worker path consumes no randomness. This is no longer only an
absence-of-grep-match inference; a full trace confirmed it and is recorded at
`docs/engine/contracts/simulation_kernel_contract.md` §7.1.

## Part 4 — Performance under pressure

Performance is implemented as graceful, provable scope reduction — the direct expression of
"Progressive Degradation." Two control loops plus a hard backstop:

**Slow loop — RuntimeMode** (`src/engine/governor.py`): `ResourceGovernor.evaluate()` reads
`PressureSignals` every tick and walks NORMAL -> CONSTRAINED -> DEGRADED -> SURVIVAL. Escalation
is immediate on any threshold breach. Recovery requires a minimum dwell time *and* a full
confidence window of samples all below a watermark-scaled threshold, stepping down one level at
a time — deliberately slow and hysteresis-protected, so the engine doesn't flap between modes.

Each mode is a pre-composed policy bundle (`src/engine/policy.py`):

| | NORMAL | CONSTRAINED | DEGRADED | SURVIVAL |
|---|---|---|---|---|
| `concurrency_limit` | 1.0 | 1.0 | 0.5 | 0.25 |
| brain/strategic cadence | every 10 ticks | every 20 | every 50 | every 100 |
| `scan_policy` | FULL | THROTTLED | EXACT_DIRTY | EXACT_DIRTY |
| candidate/movement budget | 1000 | 500 | 200 | 50 |
| opportunistic work | allowed | allowed | off | off |
| replay richness | FULL | FULL | MINIMAL | off |

`concurrency_limit` goes *down* as pressure rises because everything else already shrank the
batch by then — fewer, less-contended workers on a smaller batch beats fighting for cores on an
already-stressed system (see C6 in the parent proposal — this rationale isn't written down
anywhere else).

**Fast loop — PhaseBudgetGovernor** (`src/engine/phase_governor.py`): independent of mode, reacts
to *this tick's* measured phase costs (locomotion, final_integrity) and tightens budgets further
in real time, regardless of the mode's baseline.

**Scheduling shrinks demand before it's dispatched**: `DeterministicScheduler.select_work()`
(`src/engine/scheduler.py`) filters candidates via readiness gating, LOD
(`LODService.should_execute` — entities far from focus points skip), and cadence gating (brain/
strategy re-evaluation staggered per entity). A population spike means more entities competing
for the same bounded budget slots, not a proportionally larger per-tick workload.

**Hard backstop**: if Resolution runs long, `kernel.py` checks elapsed time every 10 results and,
past the hard cap, drops remaining results outright, records the drop, force-escalates to
DEGRADED, and fires a watchdog alert. Dropped work becomes an entry in
`state.work_debt[subsystem_id]` (`src/engine/apply.py:280` — a typed, durable, per-subsystem
ledger), drained later via low-priority `DRAIN_DEBT` items that always sort last in the
deterministic commit order, so backlog repayment never starves fresh critical work.
`work_debt_total >= max_work_debt` is itself one of the two hardest SURVIVAL triggers: "can't
keep up" means "shrink scope further," never "blow the budget."

## Part 5 — Benchmarking integrity

DEGRADED and SURVIVAL exist for unexpected runtime events. They must never be the mode a
performance claim was actually measured in. See C4 in the parent proposal for the full gap
analysis: `performance_contract.md`'s Scoped Claims dimensions omit `RuntimeMode`, and the live
CI gate (`tests/perf/test_perf_regression_baseline.py`) has no assertion that it stayed NORMAL
for every sampled tick — a real mechanism by which a benchmark could silently blend cheaper
degraded-mode ticks into a reported baseline and mask a genuine regression.

## Known documentation drift (see C2, C3, C8 in the parent proposal for follow-up)

1. Concurrency framing contradiction: `kernel.md` ("Concurrent" Collection) vs.
   `simulation_kernel_contract.md` §9 ("No concurrency or parallel execution").
2. Phase-count contradiction: `architecture.md`'s 6-phase framing vs. `kernel.md`/
   `simulation_kernel_contract.md`'s 7-phase framing.
3. Hardware-class definition conflict (already self-flagged): `perf_baseline_policy.md` §2.2 vs.
   `certification_contract.md` §3, per `TCK-20260702-OBSISO-ISOLATION-PROOF`.

**Update (TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT, closed 2026-08-21):** full audit recorded at
`docs/audits/D25_engine_docs_drift.md`, including a 4th newly-found item (architecture.md's
inverted hardware-class table) and 2 direct fixes (README.md, CLAUDE.md) folded in beyond this
list's original 3.

## References

- `src/engine/kernel.py`, `src/engine/executor.py`, `src/engine/worker_manager.py`,
  `src/engine/worker_logic.py`, `src/engine/scheduler.py`, `src/engine/governor.py`,
  `src/engine/phase_governor.py`, `src/engine/policy.py`
- `src/core/protocol_validator.py`, `src/platform/rng.py`, `src/core/state.py`
- `src/engine/apply.py:280`, `src/perf/long_run_harness.py:225`,
  `tests/perf/test_perf_regression_baseline.py`
- `docs/engine/project_lawbook_m10.md`, `docs/engine/architecture.md`, `docs/engine/kernel.md`,
  `docs/engine/governance_logic.md`, `docs/engine/runtime_profiles.md`
- `docs/engine/contracts/bounded_concurrency_contract.md`, `worker_contract.md`,
  `concurrent_integrity_contract.md`, `harness_architecture.md`, `certification_contract.md`,
  `simulation_kernel_contract.md`
- `docs/engine/performance_contract.md`, `docs/performance/perf_baseline_policy.md`
- `src/api/ws/stream.py`
```

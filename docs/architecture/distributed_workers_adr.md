---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, engine, determinism, platform]
amends: [docs/architecture/system_overview.md#what-is-deliberately-not-distributed, docs/architecture/devops_plan_amendment_proposal.md#what-stays-from-the-adr]
---

# ADR: an opt-in mode may run the Collection pool outside the engine process

**Accepted by the owner on 2026-11-11 (#715 6777076537), after lead-planner's review (2/2, re-check clean).** It amends
`system_overview.md` ("What is deliberately not distributed") and `devops_plan_amendment_proposal.md` ("What stays from the ADR");
the text applied there is in §5.
- Drafted by architecture-planner-u24 for `TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`, child 0 of
  `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT` (owner, #715 6735920310). Adopted by lead-planner.
- The design it rests on is `docs/plans/architecture/distributed_workers_experiment_design.md` (accepted with it, at f517f1fdf).
- Nothing is implemented yet.

**Companion:** the next-generation engine ADR (`docs/architecture/next_generation_engine_adr.md`, accepted #715 6742854335). It is a
direction for the whole kernel; this ADR is one opt-in mode for Collection. A future default mode at scale must fit that ADR's phase
contract, not fork it (design §13).

## Status

Accepted (owner, #715 6777076537). The design's §10 choices are the owner's answers (#715 6776551375), and the scale direction is
#715 6776564953.

## Context

- **The decision it amends.** `system_overview.md`, "What is deliberately not distributed": "The engine is one process and one
  writer. That is a choice, not a gap: determinism and replay depend on it ... Scaling is per run (many seeds in parallel), not per
  tick."
- **The same decision elsewhere.** The devops amendment (`devops_plan_amendment_proposal.md`, "What stays from the ADR"): "The engine
  stays one process with one writer. ... Kubernetes runs it as a single replica; only the API and workers could scale."
- **Mode 5** was dropped on 2026-10-26 (`engine_execution_modes_proposal.md`). It reopens only by an ADR amendment, and "only if the
  owner names a world that one machine cannot hold".
- **The owner's choice.** An opt-in experiment mode: several containers, one holding N engine workers, with the default path
  unchanged ("Epic + ADR first", #715 6731714291). It is an experiment, not a speed-up.
- **Measured starting point (PROVISIONAL).** Collection is 14 to 26 % of a tick in py-spy shares (`tick_cost_growth.md` §2), and
  5.2 to 16 % in the benchmark records. The mode may well be slower than sequential.
- **The design** is `docs/plans/architecture/distributed_workers_experiment_design.md`. A `RemoteWorkerManager` behind the
  existing `ConcurrentExecutionAdapter`, passed as an explicit executor; gRPC between engine and worker, pickle as the first codec
  behind a codec seam, two-way authentication, a MAC on every response (design §4).
- **The owner's scale direction** (#715 6776564953): the mode may become the default when the engine scales up. It ships opt-in;
  promotion is gated (design §13).

## Decision

1. **Kept: one writer.**
   - Workers only compute `WorkerResult`s from a `WorkerPacket`.
   - The kernel validates every result (`ProtocolValidator.validate_result_batch`, `kernel.py:556`), sorts by
     `ConcurrencyLaw.commit_key` (`kernel.py:580`), and applies through `ApplyPath` alone.
   - Scaling stays per run. The engine stays a single replica.
2. **Relaxed, and only here: "one process", for the Collection pool, under the opt-in experiment profile only.** Every other phase,
   and every run without the profile, stays one process.
3. **The default is unchanged.** No change to:
   - the executor selection at `kernel.py:193-198` (the mode enters through the existing explicit-executor branch, from the CLI and
     the test harness only);
   - `LocalSequentialExecutor`, `ConcurrentExecutionAdapter` or `WorkerManager`;
   - `docker compose up` without a profile.
4. **Determinism rule.**
   - A run in the mode must give an identical final hash under the current proof scheme (`PROOF_DIGEST_SCHEME`) and `TICK_END` trail to `LocalSequentialExecutor` on the
     same world and seed, or the mode is unclaimed for it. This is PERF-D2: anything but DET-PORT-0 needs a passing parity matrix,
     and the content compare is primary.
   - Outcomes never depend on worker speed:
     - a slow or dead worker's chunk is recomputed locally from the same packets, and recorded, never answered with a FAILURE no-op;
     - a worker exception is handled as it would be locally;
     - a late result is dropped (design §6).
5. **Why it reopens.** The owner's experiment choice (#715 6731714291) **replaces** Mode 5's reopen condition for this mode only.
   It makes no claim of speed.

6. **Owner's choices for the first build** (#715 6776551375): a dead or slow worker's chunk is recomputed locally and recorded; the
   mode is reached from the CLI and the test harness only; the transport is gRPC, point to point (no broker); the first codec is
   pickle, guarded (compose-internal network only, a test that the worker port is never published, two-way authentication, a
   security review of child 3, a typed codec before the mode leaves its opt-in profile).

**Not decided here:**
- more than one writer, engine replicas, an API/engine split;
- parallel Resolution (C-10 and the Gate B evaluation, PERF-M6-T05, are unchanged);
- multi-host or k8s deploys;
- promotion to a default mode (below, Consequences).

## 5. Text applied to other documents

### 5.1 `docs/architecture/system_overview.md`, "What is deliberately not distributed", first bullet (applied)

> - **The engine has one writer.** That is a choice, not a gap: determinism and replay depend on it
>   (`docs/architecture/kernel_concurrency_design_philosophy.md`). Every result is validated, sorted and applied by the kernel alone.
>   **By default the engine is also one process.** One recorded exception exists: the opt-in distributed-workers mode may run the
>   Collection pool in a separate container (`distributed_workers_adr.md`, #715 6777076537), and it must give results identical to
>   the sequential run. Scaling is per run (many seeds in parallel), not per tick.

The next-generation engine ADR's direction paragraph in the same section is unchanged.

### 5.2 `docs/architecture/devops_plan_amendment_proposal.md`, "What stays from the ADR" (applied)

> - **The engine stays one writer and a single replica.** Determinism and replay depend on it. Kubernetes runs it as a single
>   replica; only the API and workers could scale. Under the opt-in distributed-workers profile only, the Collection pool
>   may run in a separate `engine-worker` container on the compose-internal network (`distributed_workers_adr.md`, #715 6777076537).

### 5.3 `docs/engine/contracts/worker_contract.md` §5, Non-Goals (not applied: epic child 5)

> - No distributed workers (network boundaries), **except the opt-in distributed-workers experiment mode**: the Collection pool in
>   one separate container, results validated and applied by the kernel as in §3, with an outcome independent of worker speed.

### 5.4 `docs/plans/architecture/engine_execution_modes_proposal.md`, Mode 5 (not applied: architecture-planner-u24, now accepted)

> Reopened for one opt-in mode only, by ADR (`docs/architecture/distributed_workers_adr.md`, #715 6777076537). The owner's experiment choice replaces the condition
> "a world one machine cannot hold" for this mode. Relaxed or distributed execution otherwise stays out of this plan.

## Consequences

- **What the epic's children may do once this is accepted:** measure packet cost (child 2), build the remote manager (child 3) and
  the compose profile (child 4), each behind the gates in the epic.
- **The default deployment and every existing evidence path are unchanged.** The gate, paired arms and `rpg_measure` refuse a
  non-sequential executor (child 6).
- **A result slower than sequential is a valid outcome**, and is reported.
- **Not decided here: promotion.** The owner expects the mode may become the default at scale (#715 6776564953). This amendment
  does not make it so. Promotion, and any multi-host deploy, needs its own ADR, decided against the gates in the design's §13.
- **Risks:**
  - an unsafe-deserialization surface, since the first build uses pickle (owner, #715 6776551375). Guards: compose-internal
    network only, a test that the worker port is never published, two-way authentication with a MAC on every response, and a
    security review of child 3. A typed codec is required before the mode leaves its opt-in profile;
  - two accepted first-build risks: the plaintext per-run secret on the internal network, and a compromised worker container,
    whose signed results the engine still decodes (closed by the typed codec and mTLS, design §13 gates 3 and 4). Child 3's
    review also binds the tick or a per-call nonce into the response MAC (replay);
  - hidden reads outside the packet, such as process-global content: covered by the content fingerprint and the long equivalence test.

## Related

- `TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT` (the ticket that adopted it)
- `docs/architecture/next_generation_engine_adr.md` (companion)
- `docs/plans/architecture/distributed_workers_experiment_design.md`
- `docs/architecture/system_overview.md`, `docs/architecture/devops_plan_amendment_proposal.md`
- `docs/plans/architecture/engine_execution_modes_proposal.md` (Mode 5)
- `docs/engine/deterministic_execution.md` (PERF-D2)

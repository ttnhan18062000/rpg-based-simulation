---
status: active
layer: performance
authority: P2
audience: developer
tags: [performance, determinism, testing, engine]
---

# Epic Plan — Performance M1: Correctness Prerequisites

## Outcome

Correct or resolve known measurement and semantic-foundation weaknesses before creating trusted
performance baselines. M1 changes behavior only where an M0 decision and corrected specification
authorize it.

## Entry conditions

- M0 has reconciled affected P1 sources.
- PERF-D1 governs pressure signals and determinism/control inputs.
- PERF-D3 governs debt meaning.
- PA-03A evidence and PERF-D5 govern hash work.
- The `WorkerResult` ordering question has an owner under PERF-D1.

## Candidate child tickets

| Candidate ID | Ticket scope | Depends on | Deliverable |
|---|---|---|---|
| PERF-M1-T01 | Zero-capacity signal semantics and correction | PERF-D1 | Contract/tests for unavailable, disabled, local, configured-zero, idle, busy, saturated; affected-baseline invalidation |
| PERF-M1-T02 | Debt-harness correctness | PERF-D3 | Exact integer accounting, non-empty fixtures, checkpoint/work-admission noninterference proof |
| PERF-M1-T03 | Hash-policy reconciliation | PA-03A + PERF-D5 | Schedule/scheme/tick/freshness rules, same-scheme conformance, baseline migration or no-change record |
| PERF-M1-T04 | Tied `WorkerResult` determinism verification | PERF-D1 owner disposition | Adversarial ID-zero/system-result experiment and contract conclusion |
| PERF-M1-T05 | Correctness-baseline invalidation ledger | T01–T04 as applicable | Consolidated list of artifacts that remain valid, require rerun, or are incomparable |

T03 may close as a documented no-change result. T04 is verification-first: it must not modify the
commit key unless its investigation proves a defect and a separately approved correction scope
selects a remedy.

## Tied-result verification contract

T04 covers randomized insertion and worker completion order, supported local/thread/process
routes, and tied combinations of class priority, local priority, and ID zero. It compares:

- ordered validated `WorkerResult` batches;
- raw `StateUpdate`;
- refined update;
- authoritative state;
- same-scheme canonical hash.

The result must prove one of: a complete unique key, bounded commutative merge rules, a confirmed
defect with a corrected specification, or an explicitly narrower supported protocol. It may not
label the concern a defect from sort-key inspection alone.

## Out of scope

- General performance tuning or M5 accelerators.
- Hierarchical hashing unless Gate A later proves material flat-hash cost and PERF-D5 permits it.
- Semantic deferred-work queues.
- Concurrent RESOLUTION.
- Baseline promotion before M2 defines the claim contract.

## Exit criteria

- Corrected behavior has specification-based tests rather than parity with known-broken output.
- Debt fixtures exercise nonzero values and exact counts.
- Hash policy has a versioned identity and explicit freshness behavior.
- `WorkerResult` ordering has a contract disposition supported by adversarial evidence.
- Every affected old baseline has an explicit retain/invalidate/migrate disposition.
- Canonical state, invariants, and unaffected scenarios remain covered.

## Primary surfaces

- `src/engine/worker_manager.py`
- `src/engine/governor.py`
- `src/perf/long_run_harness.py`
- `src/engine/checkpoint.py`
- `src/engine/kernel.py`
- `src/core/protocol_validator.py`
- `tests/unit/core/test_signal_hardening.py`
- `tests/perf/test_concurrency_parity.py`

## References

- `performance_optimization_prerequisite_execution_plan.md` PA-01..03B
- `system_design_terms_and_concepts.md` §14, WorkerResult disposition
- `../../../engine/deterministic_execution.md`


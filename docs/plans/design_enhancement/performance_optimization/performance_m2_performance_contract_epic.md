---
status: active
layer: performance
authority: P2
audience: developer
tags: [performance, certification, testing, governance]
---

# Epic Plan — Performance M2: Authoritative Performance Contract

## Outcome

Create one versioned performance-claim model and explicit executable projections for fast CI and
controlled scheduled runs. A passing smoke gate must not be mistaken for a capacity claim.

## Entry conditions

- PERF-D2 defines the portability/hardware/runtime claim tiers.
- PERF-D4 selects the P1 authority and reconciliation process.
- M1 identifies every correction that changes benchmark or baseline identity.
- Performance and Release/Certification owners are named.

## Candidate child tickets

| Candidate ID | Ticket scope | Depends on | Deliverable |
|---|---|---|---|
| PERF-M2-T01 | Clause-level source inventory | PERF-D4 | Matrix across engine contract, certification contract, baseline policy, gate code, tests, and CI selectors |
| PERF-M2-T02 | Benchmark identity and result schema | T01 + PERF-D2 | Versioned schema for scenario/config/content/checkpoint/runtime/hardware/executor/mode/cardinality/observer identity |
| PERF-M2-T03 | CI-fast tripwire projection | T02 | Cheap deterministic change detector, relative/absolute thresholds, failure states, and explicit non-capacity claim |
| PERF-M2-T04 | Controlled capacity/confirmation projection | T02 | Warmup/sample/repetition, paired base/head option, and p50/p95/p99/max/variance/memory contract on approved runners |
| PERF-M2-T05 | Baseline and known-debt lifecycle | T02, M1-T05 | Create/promote/invalidate/migrate/reject rules plus owner/expiry quarantine; missing or incompatible evidence cannot silently pass |
| PERF-M2-T06 | P1 publication and gate-conformance map | T03–T05 | Owner-approved P1 contract plus machine-checkable mapping from change classes and live gates to enforced clauses |

T03 and T04 are different products of the same identity schema. They may proceed in parallel and
must use names that make their evidence strength impossible to confuse.

## Required contract dimensions

- scenario builder/checkpoint and workload cardinality;
- engine, content/rules, config, RNG, schema, and baseline versions;
- hardware/runtime and DET-PORT tier;
- executor/backend and worker count;
- warmup, measured ticks, independent repetitions, and variance handling;
- latency distribution, throughput, CPU/wall time, memory high-water, and scaling slope;
- `RuntimeMode` sequence, verification level, processed/dropped/coalesced work;
- replay/hash/control-trace validity;
- observer level and measured observer overhead;
- gate tier, trigger, blocking/informational status, and maximum feedback latency;
- relative and absolute regression thresholds, noise budget, retry limit, and confirmation rule;
- missing, stale, or incompatible artifact behavior.

## Regression-signal policy

Every executable projection returns one of `PASS`, `REGRESSION`, `INCONCLUSIVE`, or
`NOT_APPLICABLE` with a reason. Only `PASS` satisfies a required gate. Missing baselines, stale
identity, excessive variance, unsupported runners, empty scenario selection, and exhausted retries
are explicit non-pass outcomes rather than skips disguised as success.

The fast PR projection optimizes feedback latency and detects material change; it does not certify
capacity. A controlled projection confirms noisy signals with predeclared repetitions and, where
appropriate, paired base/candidate execution on the same runner. Both projections record raw
samples and use relative thresholds plus absolute floors so tiny benchmarks and shared-runner noise
do not dominate decisions.

Threshold and baseline changes are reviewed changes of evidence, not fixes for a failing build.
They require a cause tied to a ticket/change, compatible before/after identities, owner approval,
and an audit record. A retry may diagnose an inconclusive run; repeated execution until one sample
passes is forbidden.

Known historical failures are separately enumerated with owner, scope, expiration/review date, and
expected signature. The quarantine may prevent an already-red lane from blocking temporarily, but
new or worsened deltas still produce a regression signal. Promotion from informational to blocking
requires stable calibration and an explicit P1/CI-owner decision.

## Out of scope

- Producing the M4 baseline matrix.
- Selecting optimizations.
- Lowering thresholds to accommodate known-invalid runs.
- Allowing a local developer-machine sample to become a portable capacity promise.

## Exit criteria

- One P1 authority is selected and published by its owner.
- Every live gate states which contract clauses it enforces and which it does not.
- CI-fast and scheduled evidence use the same identity vocabulary but distinct thresholds/claims.
- Missing mandatory evidence fails or produces an explicit non-claim outcome.
- Baseline comparison rejects incompatible identities.
- Tests cover absent baseline, stale schema, mode/cardinality mismatch, and percentile behavior.
- Tests cover changed-file under-selection, new drift inside a known-debt lane, excessive variance,
  bounded retries, and baseline-update authorization.

## Primary surfaces

- `docs/engine/performance_contract.md`
- `docs/engine/contracts/certification_contract.md`
- `docs/performance/perf_baseline_policy.md`
- `src/perf/regression_gate.py`
- `src/perf/bench_harness.py`
- `tests/perf/test_perf_regression_baseline.py`
- CI workflows selecting performance tests

## References

- `performance_optimization_prerequisite_execution_plan.md` PA-04
- `performance_optimization_conflict_approval_review.md` PERF-D4
- `system_design_terms_and_concepts.md` §§11–13

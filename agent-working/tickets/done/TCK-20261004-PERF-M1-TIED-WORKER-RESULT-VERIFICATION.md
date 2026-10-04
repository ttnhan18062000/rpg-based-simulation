---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION
phase: done
date: 2026-10-04
tags: [performance, determinism, testing, engine]
---

# TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION

## Title
PERF-M1-T04: verify whether tied `WorkerResult` sort keys make the committed state depend on worker completion order

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Released by the owner's partial lift on 2026-10-04 (`performance_optimization_roadmap.md`, "Gate
definition and partial lift"). This ticket is **verification-first**: it adds tests and evidence,
and edits no gated file.

`Kernel._phase_resolution` (`src/engine/kernel.py`, around line 608) sorts results with
`key=(class_priority, -local_priority, entity_id)` before merging them. `WorkerResult`
(`src/core/worker_protocol.py`) defaults both priorities to 0. Python's sort is stable, so two
results with equal keys keep the order in which they arrived in `_final_results`, and that order can
depend on worker completion. Typical ties are several results for the same entity, or system results
that all use `entity_id` 0. Whether a tie can change the committed state depends on whether the
tied results commute when merged. The M1 epic forbids calling this a defect from reading the sort
key alone ("Tied-result verification contract").

## Scope
- Inventory who produces `WorkerResult`s and which can tie on the full key: same entity, ID zero /
  system results, equal priorities. Read `src/core/worker_protocol.py`,
  `src/engine/worker_manager.py`, `src/core/protocol_validator.py` and the resolution loop in
  `kernel.py` (read only)
- Adversarial experiment as tests: permute the order of `_final_results` before resolution, using
  every supported route (local, thread, process, where available). Do it with a test seam or by
  driving the executors, not by editing `kernel.py`. Cover tied class priority, tied local priority
  and ID zero. Compare, per the epic's contract, at each level:
  - the ordered validated `WorkerResult` batch;
  - the raw `StateUpdate`;
  - the refined update;
  - the authoritative state;
  - the proof digest (`CanonicalStateHasher.get_hash`; PERF-D5: never the fingerprint).
- Use non-combat scenarios (movement, resource, strategic, idle). Combat is excluded while
  `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` is open. Its divergence would
  confound this experiment, and this experiment may help diagnose it later
- Write the conclusion as exactly one of the four outcomes the epic allows:
  - a complete unique key;
  - bounded commutative merge rules;
  - a confirmed defect, with a corrected specification;
  - an explicitly narrower supported protocol.

  Record it in `docs/engine/deterministic_execution.md` or the PERF-D1 record, whichever the
  evidence belongs to, and in the parity ledger (`infrastructure.yaml`)

## Out of Scope
- Changing the sort key or the merge in `kernel.py`. It is a gated core file. A confirmed defect
  becomes a separately approved correction ticket that waits for the gate
- `src/engine/governor.py` (held back by the partial lift)
- Concurrent RESOLUTION (C-10)

## Acceptance Criteria
1. The tests permute tied results across every supported route and compare all five levels above
2. At least one test constructs a real tie of each kind (same entity, ID zero, equal priorities).
   Each test proves the tie occurs: it asserts that the permuted input differs while the keys are equal
3. The conclusion names one of the four outcomes, with the evidence. "Defect" is claimed only if a
   test shows different committed state or proof digests
4. No edit to `kernel.py`, `apply.py`, `pipeline.py`, `state.py` or `governor.py`
   (`git diff --stat` in the ticket)
5. Mutation proof: a deliberately non-commutative tied pair injected in a test makes the comparison
   fail. This shows the instrument can see a divergence

## Related Tickets
- `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`
- `TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE` (proof digest naming)

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md` (PERF-M1-T04, tied-result verification contract)
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, PERF-D5)
- `docs/engine/deterministic_execution.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `src/engine/worker_manager.py`, `src/core/protocol_validator.py` (edits allowed, if a test seam is needed)
- `src/core/worker_protocol.py`, `src/engine/kernel.py` (read only)
- `tests/perf/test_concurrency_parity.py`, `tests/unit/core/`

## Assumptions / Open Questions
- If a permutation seam needs an edit to `kernel.py`, stop and report. Do not edit it. A
  test-only monkeypatch of `_final_results` before `_phase_resolution` is the expected route
- Concrete tie to include (perf-planner, 2026-10-04): the resolution loop does `work_debt_updates[res.subsystem_id] = res.work_debt_update` (`kernel.py`, around line 647). That is last-writer-wins, not a sum, so two `DRAIN_DEBT` results for the same subsystem in one tick (both `entity_id` 0, same class) keep whichever sorts last. Today every drain value is equal (`-max_worker_count`), so it may be harmless in practice; the test should say so either way. See `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`
- The process route may be unavailable in CI. Mark those cases and say which routes ran

## Implementation Notes
- **Outcome: bounded commutative merge rules.** Entity results have a unique key (validator and resolution guard reject a duplicate). System results (`entity_id` 0, `DRAIN_DEBT`) tie on the whole key; their merge is last-writer-wins per `subsystem_id`, so it commutes exactly when no subsystem has two system results with different values in one tick. The shipped scheduler/executors emit one per subsystem per tick. It is not a unique key (ID-zero ties are real) and not a defect (no shipped path diverges, no test shows different state or digests for shipped inputs).
- **The gap, stated once:** `ProtocolValidator.validate_result_batch` accepts two system results for one subsystem. With different values the committed state and proof digest depend on arrival order (mutation test). Enforcing "at most one per subsystem per tick" is a separate approved change (`protocol_validator.py` is within the lift; not done here because this ticket is verification only). Today every drain value is equal (`-max_worker_count`), so the divergent case is also value-equal in practice; see `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`.
- Seam: a `Kernel` subclass overriding `_phase_resolution` (test-only), and a wrapper on the static `AuthoritativeApplyPipeline.refine` to capture raw and refined updates. No edit to `kernel.py`.
- Level 1 is compared as the same results in key order: the ordered batch differs inside a tied group by construction (stable sort keeps arrival order), which is asserted separately. Wall-clock fields are excluded: `WorkerResult.compute_time_ns`, `sub_phase_costs`, metric counters named `*_ms`. Runs use `audit_mode=True`.
- Routes that ran: local, thread (`WorkerManager(use_processes=False)`) and process (`use_processes=True`, ProcessPoolExecutor, 2 workers): 0 skipped on this machine. The process route is skipped automatically if the pool cannot be created.
- Scenarios (non-combat): idle, movement, resource, strategic, and `ready_movers` (twelve entities ready every tick, so many CRITICAL results share class and local priority). The four stock scenarios schedule one entity result per tick, so ties among entity results needed `ready_movers`. Debt is seeded for four subsystems so four ID-zero results tie every tick.
- Seeded debt: the system-result ties in the tests come from seeded debt; in ordinary play `work_debt` stays empty and no `DRAIN_DEBT` result is produced today (`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`). Said in the Rule 2 bullet and in `INFRA-420`.
- Docs: `docs/engine/deterministic_execution.md` Rule 2 corrected (it said the key is "always stable and total") and parity ledger `INFRA-420` added (`make parity-ledger-schema-check`: 0 rose, 0 new).
- Limits: five ticks, small worlds, four permutations per route, no combat, `audit_mode` on. With `audit_mode` off the mid-tick throttle drops the tail of the sorted list, so which tied result is dropped would follow arrival order; that path is already wall-clock-dependent and is not covered.

## Test Summary
- `tests/integration/kernel/test_tied_worker_result_order.py`: 26 passed in about 38 s (5 scenarios x 3 routes permutation test, 5 cross-route digest tests, ID-zero, equal-priority, same-entity, validator gap, shipped-constructor and mutation cases).
- AC2: the ID-zero test asserts the tied key and that the reversed input order differs while the key is equal; the permutation test asserts at least one tied group was reordered; the same-entity test shows both orders raise.
- AC5 (mutation proof): two same-subsystem drains (-1, -4) make the comparison fail at the first differing level and the proof digests differ; equal-valued duplicates (-2, -2) commute.
- Time cost: about 38 s for the module; it is not marked `slow`.

## Files Changed
- `tests/integration/kernel/test_tied_worker_result_order.py` (new)
- `docs/engine/deterministic_execution.md`, `docs/parity_ledger/infrastructure.yaml`, `docs/REGISTRY.yaml`
- No `src/` file. `git diff --stat` shows no gated file.

## Completion Summary
The outcome of the tied-result verification is bounded commutative merge rules: entity results have a unique key; system results tie but commute unless one subsystem has two results with different values in a tick, which the shipped producers never emit and the validator does not forbid. 26 new tests pass, with a mutation proof, and no `src/` file changed.

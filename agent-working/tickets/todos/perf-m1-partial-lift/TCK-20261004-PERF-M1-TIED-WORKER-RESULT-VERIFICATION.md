---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION
phase: open
date: 2026-10-04
tags: [performance, determinism, testing, engine]
---

# TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION

## Title
PERF-M1-T04: verify whether tied `WorkerResult` sort keys make the committed state depend on worker completion order

## Status
OPEN

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
- The process route may be unavailable in CI. Mark those cases and say which routes ran

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

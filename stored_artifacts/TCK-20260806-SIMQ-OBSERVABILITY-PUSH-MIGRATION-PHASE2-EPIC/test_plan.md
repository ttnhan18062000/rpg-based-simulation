---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC
artifact_type: test_plan
tags: [observability, engine, simulation-quality, performance, progression]
---

# test_plan.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC

## Scope of testing at the epic level

The epic itself makes no code changes and requires no `pytest` run directly. Testing rigor was
enforced per-child-ticket, each with its own Test/Architecture-Verify/Parity/Verify gates:

- **Child 1** (perf gate): 2 new `@pytest.mark.slow` tests in
  `tests/perf/test_simq_isolation_overhead.py`, 25% overhead band locked from real convergence
  measurements.
- **Children 2-5** (shaper builds): dedicated unit test files per domain (26/18/25/20 tests
  respectively), all SHADOW-mode, all passing.
- **Child 6** (deferred-instrumentation closure): 14 new unit tests, real-kernel verification of
  `resource_node_depleted`/`regenerated`/`node_recharged`/`faction_extinct`.
- **Child 7** (shadow validation + perf re-run, P0): 6-world x 500-tick real event-stream
  comparison across the combined registry, 5/6 exact parity, 1/6 root-caused to `INFRA-273`, not a
  shaper defect. Extended perf gate: -0.35% overhead for the complete registry.
- **Child 8** (cutover): full scoped unit+perf suite (908 passed, 7 skipped), full `tests/perf/`
  suite (1046 passed, 2 pre-existing unrelated failures disclosed), real 5-world kernel runs in
  both flag directions, and the full calibration corpus (79 scenarios, 37/69 grade-regression
  failures root-caused as pre-existing `INFRA-273`, not a regression).

## Non-negotiable ordering — honored throughout

Child 8 (cutover) did not begin until child 7 (shadow validation) reached its GO verdict,
confirmed by directly reading child 7's own Completion Summary at child 8's own Scope phase —
enforced by `SEQUENCE.md`'s explicit dependency note and child 8's own ticket file listing child 7
as a hard blocker, not left as an informal convention.

## Final regression status

`grade_anchors.json` was left unrecalibrated across the entire epic — every drift found (Phase 1's
32/69, Phase 2's 37/69) was root-caused to the same pre-existing, already-documented `INFRA-273`
tick-budget-watchdog mechanism via decisive differential-repro, never assumed or waived, and never
used as a reason to reflexively recalibrate against an unrelated infrastructure issue.

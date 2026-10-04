---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS
date: 2026-10-04
tags: [performance, testing]
---

# Test plan: TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS

| AC | Test | Proof |
|---|---|---|
| 1 | spec tests: one / several / returned-to-zero / empty debt | exact hand-computed `work_debt` and `systems_with_debt` |
| 2 | kernel-driven debt run | each sample equals the recorded state debt at the same tick |
| 3 | sampling vs bare kernel | equal proof digest at every compared tick |
| 4 | revert the line | new tests fail with `TypeError`; output pasted in the ticket |
| 5 | `tests/certification/test_cert_long_run_stability.py` | still passes (it is `slow`/`extra_slow`; run with `-m` override once, under a memory cap) |

Normal flow, empty edge, zero-return edge, failure mode (old defect), regression path (revert proof).

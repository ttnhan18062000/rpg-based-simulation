---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan

N = 3 repeated runs of `tests/visual_assets/drawing/integration/test_ops.py` under the same bounded load that failed before (6 busy loops, MemoryMax=3G scope, own `--basetemp`, one run at a time, foreground), each with the external gap sampler running outside the scope.

Pass criteria (option A, evidence ties the failure to a stall):
- Every failing run's slow call coincides (within 2 s) with an external-sampler gap of at least the call's duration minus 2 s.
- Every non-stalled `bwrap` call is under 5 s.

If option B is chosen: a unit test with a faked slow monotonic/wall gap asserts the stall-specific `AdapterError`; the unchanged-message paths (`test_negative` timeout tests) stay green; then the strict local proof run refreshes `docs/assets/aseprite_local_proof.json`.

Runs: 6 loaded runs, all failed on a stalled call; runs 4-6 had the external sampler and every slow call maps to a gap (see the ticket Test Summary and `evidence/`).

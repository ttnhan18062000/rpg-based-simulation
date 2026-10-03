---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-TEST-SCENARIO-HELPER-AND-REPLAY-DIFF
artifact_type: test_plan
tags: [testing]
---

# Test plan

`pytest tests/mechanic_scenarios -m "not slow and not extra_slow"` (the `perf-cert-arena` step's scenario path): green; replay-diff: 1 in-envelope case + 1 violation per dimension (not hand-built, unseeded, different seed, 11 ticks, different profile); determinism suite still green.

---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-RENDERING-EVIDENCE-PINNED-TO-A-FROZEN-WORLD-SNAPSHOT
artifact_type: test_plan
tags: [rendering, testing, world, investigation]
---

# Test plan

- The six existing tests stay green under their (possibly renamed) names.
- (B/C) New live tests on the chosen world assert only what the live world produces today, each number measured, not relayed.
- `tests/unit/rendering` in full; `tests/unit/tools` serially under MemoryMax=3G; `make code-health`; `make lint-imports`.

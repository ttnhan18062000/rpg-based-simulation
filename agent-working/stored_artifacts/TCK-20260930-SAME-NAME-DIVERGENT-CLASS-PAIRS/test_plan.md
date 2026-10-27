---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
artifact_type: test_plan
tags: [core, bug]
---

# Test plan

- Guard test: enumerates same-name top-level classes across `src/`; fails on a mechanism-shaped name that is not allowlisted with a reason, and on an allowlist entry that no longer matches a real duplicate; proved to fire on a deliberate instance in a temp tree.
- Per deleted twin: confirm zero readers again (src, tests, tools) before deleting; the live twin's own tests stay green.
- Each of the 19 other names is listed with its classification in the guard's data.
- Scoped: tests/unit/core, tests/unit/strategic, tests/unit/progression, tests/unit/world, tests/integration/economy, `tests/unit/tools` serial under MemoryMax=3G, code-health, lint-imports.

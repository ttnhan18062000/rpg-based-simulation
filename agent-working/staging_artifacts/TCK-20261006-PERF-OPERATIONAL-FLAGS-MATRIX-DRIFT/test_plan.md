---
status: active
layer: observability
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT
date: 2026-10-08
tags: [performance, observability, documentation]
---

# Test plan: TCK-20261006-PERF-OPERATIONAL-FLAGS-MATRIX-DRIFT

- `flags={"no_replay": True}`: the kernel's policy has `replay_allowed=False` from construction and after several ticks (the governor re-evaluates each tick), and the replay sink receives no `emit`.
  Strongest observable that needs no `src/` change: a recording replay manager passed to `Kernel(replay=...)`.
- Mutation proof: remove the `no_replay` branch locally; the new test fails for that reason; restore.
- Forbidden flags: each of the three raises `ConfigValidationError` through `ProfileValidator.validate_flags`.
- Unread-but-validated: `SURVIVAL_ONLY` + `REPLAY_ENABLED` is rejected by the validator and a kernel given only `SURVIVAL_ONLY` runs unchanged.
- Full runs: tests/unit/tools, tests/docs, tests/parity, plus the file itself.

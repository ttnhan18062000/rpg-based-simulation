---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED
date: 2026-10-18
tags: [performance, benchmarking]
---

# Plan: TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED

1. `tools/perf/_profiling_common.py`: `contract_kernel_args(..., replay=False)` sets `no_replay` to `not replay`; `make_replay_manager` builds a `ReplayManager` rooted at a given directory with the profile's buffer size and signal contract (as the kernel's default one is); `run_scenario_ticks(..., replay, replay_dir)` injects it through `Kernel(replay=...)`, records `replay_allowed` and `replay_richness` per measured tick from `kernel._current_policy`, and reads `get_stats()` at the end; `replay_summary` counts allowed and disallowed ticks.
2. `tools/perf/profile_tick.py`: `--replay` (default off) and a hidden `--replay-dir`; `child_command` puts the replay directory beside the child output, so under `--out-dir`. `phases.md` prints the replay line; `phases.json` carries `summary.replay`.
3. Tests in `tests/unit/perf/test_profile_tick_contract.py`.
4. Measure (after the planner and lead give the slot), write the numbers into `docs/performance/tick_cost_growth.md` section 4, close or route per the ticket's close rule. PROVISIONAL throughout.

Out of scope: any `src/` edit; any fix to fingerprinting.

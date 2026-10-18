---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED
date: 2026-10-18
tags: [performance, benchmarking]
---

# Test plan: TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED

Unit tests (`tests/unit/perf/test_profile_tick_contract.py`): the flag maps to `no_replay` False for every contract and the default is unchanged; the child command carries `--replay` and a replay directory under `--out-dir` only with the option; a replay run without a directory is refused; the summary counts disallowed ticks; a tiny real run (idle, 10 entities, 2 ticks) writes replay chunks only under the given directory and records the policy and stats.

## Proof Plan
- level: unit (tool change); the measurement itself is a report-only diagnostic, not a gate.
- proof kind: option-mapping and recording tests; mutation check by flipping the default.
- oracle source: `Kernel` flag semantics at `kernel.py:200` and `:562`; `ReplayManager.get_stats()`.
- expected effect: `--replay` off by default leaves every existing caller's output unchanged; on, replay chunks appear under the out-dir.
- selected commands: `.venv/bin/python3 -m pytest tests/unit/perf tests/tools/test_profiling_toolkit.py -q` under `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`.

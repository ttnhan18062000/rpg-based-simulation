---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION
date: 2026-10-14
tags: [performance, benchmarking, regression]
---

# Test plan: TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION

- `tests/unit/perf/test_profile_tick_contract.py`: `--contract live` leaves the child command and flags exactly as today; `pinned` builds the kernel with `PinnedNormalGovernor` and the three flags; `canonical` uses `canonical_variant(profile)`; `audit` sets `audit_mode`; an unknown contract is a usage error; the corpus option calls `rerun_baselines`' loader (stubbed), and no second loader exists (a grep-style test).
- No test of measured numbers (they are host evidence, in the doc, not assertions).
- Doc checks: `tick_cost_growth.md` has frontmatter and passes the docs tests; every table row has host, CPU, loadavg, sha and contract.
- Guards: paths guard, `codebase.health check`.

## Proof Plan
- **Level:** unit for the tool options; measured runs for the findings. **Proof kind:** deterministic unit tests of option mapping; folded-stack and phase-table evidence from capped runs. **Oracle:** `phases.json` processed-work counters equal across the contract variants of one scenario (proves the work is fixed); mode sequence all NORMAL under pinned; each finding cites the run directory and its folded excerpt.

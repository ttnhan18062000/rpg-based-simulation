---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION
date: 2026-10-16
tags: [performance, benchmarking]
---

# Test plan: TCK-20261015-PERF-RESOLUTION-OVERHEAD-ATTRIBUTION

A measurement ticket: no `src/` change and no new maintained tool, so no pytest suite is added. Verification is by evidence:

| Check | Proves | AC |
|---|---|---|
| classifier dry run on the #597 folded files, and a hand-made folded fixture (3 stacks: one inside a timed block, one residual in `_phase_resolution`, one outside `_phase_resolution`) checked in the script's own `--selftest` | the timed/residual/outside split is right | AC1 |
| cross-check: timed-sample share vs `sum(sub_phase_costs) / res_total` per scenario, difference reported | the line ranges match the profiled commit | AC1 |
| each scenario's residual attribution reaches at least 80 % in named call sites, or the shortfall is stated with the ambiguous-sample share | | AC1 |
| `movement_2000` pinned vs canonical: per-tick mode sequence beside the per-tick residual | the canonical jump is explained or stated as unexplained with what was ruled out | AC2 |
| `tick_cost_growth.md` H5 row and ranked list present; `make knowledge-index-update`; docs frontmatter checks; the rpg items are in a message to lead-planner | | AC3 |
| resource rule: one process at a time, MemoryMax=3G, lead told before `movement_2000`, `free -m` >= 2.5 GB first | | AC4 |

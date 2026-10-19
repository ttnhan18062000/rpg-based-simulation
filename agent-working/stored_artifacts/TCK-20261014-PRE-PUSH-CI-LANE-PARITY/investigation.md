---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261014-PRE-PUSH-CI-LANE-PARITY
artifact_type: investigation
tags: [delivery, testing, workflows]
---

# investigation — TCK-20261014-PRE-PUSH-CI-LANE-PARITY

## Findings
- The hook is `tools/delivery/pre_push_advisory_hook.py` (no `pre_push.py`); it ran no tests. `test.yml` has 20 jobs: 5 are path-filtered
  through the `changed-files` outputs (perf-cert-arena, migration-lanes, frontend, docker-build, scenario-lane), the rest run on every PR.
- The filters live as shell regex variables (PERF_RE grep -P with a lookahead, MIG/FRONTEND/DOCKER grep -E) in one step, plus
  `tools.test_architecture.scenario_lane_paths` for the scenario lane. Python `re` matches all four.
- #536 (453 files): changed `tests/perf/test_simq_isolation_overhead.py`, `tests/api/test_metadata_api.py`, `tests/visual_assets/...`: the three
  lanes' paths are perf-cert-arena (filtered), api-cli-engine (two checks). The thread-leak check was not traced to a changed test.
- Mapping agreed with testing-planner by message (always-on never "not affected", three-dot committed diff, fail-open, derived always-on,
  slow lanes listed as not on PR, a guard test on the real file).

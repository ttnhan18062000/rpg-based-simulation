---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260519-SIM-OBS-BASE-LOKI
phase: done
date: 2026-05-19
tags: [sim, obs, base, loki]
---

# TCK-20260519-SIM-OBS-BASE-LOKI

## Title
Phase 1 Observability Foundation: Performance Baselines and Loki Label Hardening

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Establish safe observability foundations. Before adding any Prometheus /metrics endpoints or HardLawMonitor infrastructure, capture pre-observability performance benchmarks, Git commit anchors, and confirm 404 behavior. Then, resolve the Promtail high-cardinality label risk by removing `tick` label promotion from `promtail-config.yml` while ensuring all contextual attributes remain queryable inside JSON log payloads.

## Scope
- Record pre-observability Git commit hash.
- Verify and document that the Prometheus `/metrics` endpoint currently returns HTTP 404.
- Execute standard benchmark smoke tests (`python3 scripts/run_benchmarks.py --smoke`).
- Execute standard baseline profiling suite (`python3 scripts/run_perf_baseline.py`).
- Modify [promtail-config.yml](file:///home/vboxuser/Work/rpg-based-simulation/promtail-config.yml) relabel and parsing stages to prevent promotion of `tick` or other high-cardinality keys to Loki labels.
- Verify `JsonFormatter` in [formatter.py](file:///home/vboxuser/Work/rpg-based-simulation/src/logging/formatter.py) keeps context attributes (like `tick` and `entity_id`) inside the JSON log payload.
- Implement static validation tests in a new file [test_loki_cardinality.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/logging/test_loki_cardinality.py) to prevent label cardinality regressions.

## Out of Scope
- Mounting Prometheus `/metrics` routing endpoint (Milestone 1).
- Setting up the `HardLawMonitor` module or kernel check integrations (Milestone 3).
- Setting up WebSocket observatory streams or entity timeline buffers.

## Acceptance Criteria
- [x] Baseline performance reports exist under `reports/perf/` matching pre-observability state.
- [x] Promtail configuration does not promote `tick`, `entity_id`, `worker_id`, `causal_id`, or `transaction_id` as Loki labels.
- [x] JSON logging format continues to emit `tick` and `entity_id` inside the log message body payload.
- [x] Static label-safety validation test suite passes cleanly.
- [x] Total system performance/TPS does not regress from pre-observability baseline.

## Related Tickets
- None

## Related Docs
- [obs_sim_phase1.md](file:///home/vboxuser/Work/rpg-based-simulation/obs_sim_phase1.md)

## Related Stored Artifacts
- [observability_feasibility_and_milestones_v3.md](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260519-SIM-OBSERVATORY-REVIEW/observability_feasibility_and_milestones_v3.md)

## Related Code Areas
- [promtail-config.yml](file:///home/vboxuser/Work/rpg-based-simulation/promtail-config.yml)
- [formatter.py](file:///home/vboxuser/Work/rpg-based-simulation/src/logging/formatter.py)
- [test_loki_cardinality.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/logging/test_loki_cardinality.py)

## Assumptions / Open Questions
- None.

## Implementation Notes
- Captured Git Commit Anchor: `0da5d3daaa2fcef3df80acebfe14650e5c45fe5f`.
- Confirmed that FastAPI `/metrics` returns HTTP 404 since no endpoint is registered yet.

## Test Summary
- Ran benchmark smoke tests successfully.
- Ran standard performance baseline successfully (`reports/perf/latest.json` established).
- Implemented and executed static verification tests under [test_loki_cardinality.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/logging/test_loki_cardinality.py) verifying promtail label safety and json logging. All tests passed cleanly in `0.06s`.

## Files Changed
- [promtail-config.yml](file:///home/vboxuser/Work/rpg-based-simulation/promtail-config.yml)
- [test_loki_cardinality.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/logging/test_loki_cardinality.py)
- [loki_label_policy.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/loki_label_policy.md)
- [phase_1.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/phase_1.md)

## Completion Summary
- Completed Milestone 0 safety checkpoint and baseline profiling.
- Completed Milestone 2 Loki label relabel modification and validation. The high-cardinality dynamic label leak has been safely plugged, and the engine remains fully deterministic, stable, and ready for Prometheus endpoint mounting.

# TCK-20260419-V2-CONSOLIDATION-FINAL-HARDENING

## Title
Final V2 Engine Signal Hardening & consolidation

## Status
INPROGRESS

## Request Summary
Close the remaining "Signal Semantic Compression" and "Environmental Capture" drift items identified in the final V2 review to reach 100% production readiness.

## Scope
- Refactor `PressureSignals` for explicit Worker vs Queue utilization.
- Implement moving averages (Trending) in `RuntimeStatus` for Memory and CPU.
- Standardize `EnvironmentCapture` to distinguish between Detected and Effective classes.
- Update `CertificationHarness` to report these truthful signals.
- Finalize all repository documentation (Tickets, Logs, Artifacts).

## Out of Scope
- Major architectural changes to the worker model itself.
- New simulation features.

## Acceptance Criteria
- [ ] `PressureSignals` contains `worker_utilization` and `queue_utilization` separately.
- [ ] Certification proof JSONs contain `tick_compute_ms_avg` and `memory_trend_mb_per_tick`.
- [ ] `test_final_gate.py` passes with scenario matrix validation.
- [ ] All tickets and artifacts are migrated to `done/` or `stored/`.

## Related Docs
- `docs/engine/observability_contract_m7.md`
- `resource_implementation_v2_review.md`

## Related Code Areas
- `src/core/governance.py`
- `src/engine/runtime_status.py`
- `src/engine/kernel.py`
- `src/certification/harness.py`

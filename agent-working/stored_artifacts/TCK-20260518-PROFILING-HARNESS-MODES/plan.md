---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260518-PROFILING-HARNESS-MODES
artifact_type: plan
tags: [profiling, harness, modes]
---

# Profiling Harness Modes Plan

## Proposed Changes

### 1. `scripts/profile_engine.py`
- Add `--mode` CLI argument with choices `["pure", "runtime", "audit"]`, defaulting to `"pure"`.
- Define mode flag mappings:
  - `pure`: `no_replay=True`, `no_frame_pacing=True`, `audit_mode=False`
  - `runtime`: `no_replay=False`, `no_frame_pacing=False`, `audit_mode=False`
  - `audit`: `no_replay=False`, `no_frame_pacing=True`, `audit_mode=True`
- Pass `mode: str` into `ProfilingHarness.run_scenario`.
- Pass appropriate flag dictionary to `Kernel` initialization.
- Incorporate `mode` into output filenames:
  - `profile_path = self.out_dir / f"{scenario_name}_{entity_count}_{mode}.prof"`
  - `text_path = self.out_dir / f"{scenario_name}_{entity_count}_{mode}.txt"`
  - `report_path = self.out_dir / "report.md"`
- Write a summary `report.md` that explicitly lists the mode and flags used, and includes a notice that GC/memory stability cannot be guaranteed or claimed without accompanying GC/RSS telemetry.

### 2. `tests/unit/perf/test_profiling_harness_modes.py`
- Implement unit tests covering all acceptance criteria as outlined in `perf_test_plan.md`:
  - `test_profiling_pure_mode_sets_clean_compute_flags`
  - `test_profiling_runtime_mode_allows_replay_and_frame_pacing`
  - `test_profiling_audit_mode_enables_audit_without_frame_pacing`
  - `test_profile_output_includes_mode_and_flags`
  - `test_profile_report_does_not_claim_gc_resilience_without_gc_metrics`

## Verification
- Run `pytest tests/unit/perf/test_profiling_harness_modes.py`
- Execute `python scripts/profile_engine.py --scenario idle --entities 100 --ticks 10 --mode pure` to verify end-to-end execution and report generation.

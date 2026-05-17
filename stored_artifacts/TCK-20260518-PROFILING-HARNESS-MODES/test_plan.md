# Test Plan - Profiling Harness Modes

## Automated Unit Tests
File: `tests/unit/perf/test_profiling_harness_modes.py`

### Test Cases
1. `test_profiling_pure_mode_sets_clean_compute_flags`:
   - Initialize `ProfilingHarness` and run a mock scenario in `"pure"` mode.
   - Verify `Kernel` receives `no_replay=True`, `no_frame_pacing=True`, `audit_mode=False`.
   - Verify output filenames contain `_pure.prof` and `_pure.txt`.
2. `test_profiling_runtime_mode_allows_replay_and_frame_pacing`:
   - Verify `"runtime"` mode passes `no_replay=False`, `no_frame_pacing=False`, `audit_mode=False`.
   - Verify output filenames contain `_runtime.prof` and `_runtime.txt`.
3. `test_profiling_audit_mode_enables_audit_without_frame_pacing`:
   - Verify `"audit"` mode passes `no_replay=False`, `no_frame_pacing=True`, `audit_mode=True`.
   - Verify output filenames contain `_audit.prof` and `_audit.txt`.
4. `test_profile_output_includes_mode_and_flags`:
   - Inspect generated `report.md` and `.txt` header to ensure exact flags dictionary and mode string are recorded.
5. `test_profile_report_does_not_claim_gc_resilience_without_gc_metrics`:
   - Verify that generated `report.md` content does not contain ungrounded text like "GC resilience" or "no memory fragmentation" unless explicit GC/RSS telemetry metrics are present and populated.

## Manual Verification
- Run `python scripts/profile_engine.py --scenario idle --entities 50 --ticks 5 --mode pure`
- Verify `reports/profile/idle_50_pure.prof`, `idle_50_pure.txt`, and `report.md` are correctly generated.
- Inspect `report.md` content.

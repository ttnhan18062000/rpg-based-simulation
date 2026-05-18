# Profiling Harness Modes Investigation

## Context & Problem
`scripts/profile_engine.py` currently runs simulation scenarios with `flags={"audit_mode": False}`. It does not explicitly configure `no_replay` or `no_frame_pacing`. Consequently, standard profiling runs capture non-computational overhead like replay persistence serialization (`dataclasses.asdict`) and frame pacing sleeps (`time.sleep`), skewing compute cost analysis.

Furthermore, generated reports lack explicit tracking of the flags used, and prior reporting templates/claims incorrectly asserted GC/memory resilience without providing explicit GC or RSS measurements.

## Technical Details
`src.engine.kernel.Kernel` supports the following flags:
- `no_replay`: bypasses replay persistence recording.
- `no_frame_pacing`: bypasses target frame rate sleep loops.
- `audit_mode`: enables rigorous validation and dirty set tracking.

By introducing a `--mode` parameter (`pure`, `runtime`, `audit`), we can map directly to clean flag configurations:
```python
MODES = {
    "pure": {"no_replay": True, "no_frame_pacing": True, "audit_mode": False},
    "runtime": {"no_replay": False, "no_frame_pacing": False, "audit_mode": False},
    "audit": {"no_replay": False, "no_frame_pacing": True, "audit_mode": True},
}
```

## Solution Requirements
1. `scripts/profile_engine.py` must accept `--mode` (default: `pure`).
2. `ProfilingHarness` must configure `Kernel` flags exactly according to the chosen mode.
3. Output files must be labeled by mode: `reports/profile/{scenario}_{entities}_{mode}.prof` and `.txt`.
4. Report generation (`report.md` or header in `.txt`) must explicitly output the mode and flags dictionary.
5. Report generation must never make unverified claims of GC resilience or memory non-fragmentation without concrete GC/RSS metrics.

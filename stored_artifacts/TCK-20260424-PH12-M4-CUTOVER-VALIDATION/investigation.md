# Phase 12 Milestone 4: Cutover Validation Investigation

## 1. V2 Stress Test (Real Condition)
- **Command**: `python3 -m src cli --ticks 1000 --seed 42 --entities 50`
- **Result**: SUCCESS
- **Execution Time**: 7.73s (~129 ticks/sec)
- **Stability**: Stable memory and CPU usage. No unhandled exceptions.
- **Verification**: Final Auth Hash `33d2e86abca97b7285a099a342311a9225d43bf0d82d302e4189b73735a2926f` generated.

## 2. Rollback Functional Integrity
- **Command**: `USE_LEGACY_SRC=1 python3 -m src cli --ticks 100 --seed 42 --entities 50`
- **Result**: SUCCESS
- **Verification**: Correctly triggered the legacy engine (logged `registry_loader` and `world_loop` events).
- **Execution Time**: ~54s (~1.8 ticks/sec). Significantly slower than V2.

## 3. Operational Drift: Replay Artifacts
> [!CAUTION]
> Significant drift detected in operational output formats between engines.

| Feature | Legacy Engine | V2 Engine |
| :--- | :--- | :--- |
| **Output Type** | Single File (`replay.json`) | Directory (`run_dir/`) |
| **Structure** | Flat JSON array | Manifest + JSON Chunks |
| **Resource Safety** | Unbounded (Dangerous) | Chunked Rotation (Safe) |

### Impact
- Downstream replay tools designed for the legacy flat file will fail when targeting V2 directories.
- Milestone 6 exit package must explicitly document this migration path.

## 4. Final Verdict
The `src` engine is operationally stable and provides a ~70x performance increase in headless mode compared to the legacy engine. The rollback mechanism is verified and functional. The cutover is **RATIFIED** for Milestone 5.

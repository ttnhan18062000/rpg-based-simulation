# Investigation — TCK-20260701-SIMQ-LOOP-WINDOW-TUNE

## Current Behavior

### PillarAccumulator (pillar_accumulator.py:14–31)
- `__init__` reads `_window_size` and `_loop_threshold` from `weights.detection` when a `ScoringWeights` instance is passed; falls back to constructor defaults (200/0.70) when weights=None.
- `_check_loop_detection()` (line 58): iterates `window_buffer`, counts tag frequencies, fires `loop_flags.add(tag)` when `count / window_len > _loop_threshold`.
- `window_buffer` is a `deque(maxlen=self._window_size)`. Oldest records are silently dropped when full — the window is a sliding over scored events, not over ticks.

### Detection Params source
- `config/simulation_quality/detection_params.yaml`: `window_size: 200`, `loop_threshold: 0.70`
- Loaded by `ScoringWeights.load()` (weights.py:62–67) into a frozen `DetectionParams` Pydantic model.
- `ScoringWeights` itself is also frozen (ConfigDict frozen=True) — patching requires `model_copy(update=...)`.

### calibrate_simq.py CLI (main(), lines 234–289)
- Current args: `--ticks`, `--seed`, `--name`, `--entities`, `--profile`, `--output`.
- **No `--window-size` or `--loop-threshold` override exists.** Running a sweep currently requires hand-editing detection_params.yaml between runs — this is the gap.
- Weights are loaded via `_load_weights(profile)` at line 272, then passed into `_build_hub()` at line 273. The override would be inserted between these two lines.

## Mechanics/Engine Constraints
- `quality_scoring_contract.md §4.7`: "200-tick sliding window" and "LOOP_THRESHOLD (default 0.70)" are documented as the global default. No per-pillar or per-world-type profile exists for detection params — any introduction of one would be a documented divergence.
- Loop flags are **diagnostic only** — they do not add an extra score penalty. Changing window size affects which tags get flagged as looping (and by extension, what the human sees in drill-down reports) but does NOT change the raw delta scoring path.

## Parity Ledger Overlap
- `infrastructure.yaml` last entry: INFRA-250. `SIMQ-CALIBRATED-001` also exists (ad-hoc entry).
- No existing entry covers "loop detection window externalization" or "calibrate_simq CLI override".
- A new entry `INFRA-251` should be added after implementation.

## Prior Work
- `TCK-20260628-SIMQ-E7-CALIBRATE`: built calibrate_simq.py; initially broken (tick_count=0 bug).
- `TCK-20260630-SIMQ-CALFIX`: fixed world loading in calibrate_simq.py (resolved tick_count=0).
- `TCK-20260630-SIMQ-ANCHORS`: grade regression anchors (test_grade_regression.py).
- `TCK-20260630-SIMQ-RECALIBRATE`: re-ran calibration after CALFIX; established current data/calibration/ artifacts.
- D20 audit (`docs/audits/D20_simq_integration.md`): flags that NARRATIVE dropped from 16 events at 57 ticks to 3–4 at 200 ticks in sandbox_world, attributed to loop suppression.

## Risks and Open Questions
1. **Is 200-event window correct for 200-tick runs?** At 200 ticks, sandbox_world produces ~600–800 scored events (10 entities × ~60–80 events each). The window holds only the last 200 scored events, not 200 ticks. For 200-tick runs the window may actually cover fewer ticks than expected if event density is high.
2. **Sweep scope:** The ticket calls for window sizes 100/150/200/300 against sandbox_world and dungeon_crawl. We do NOT need to sweep all 13 corpus worlds.
3. **No per-world-type profile exists:** Introducing one would require a divergence entry in `v2_intentional_divergences.md`. The sweep result will determine if this is needed.
4. **grade_anchors.json:** If sweep reveals that 200/0.70 is suppressing real signal (and we change defaults), test_grade_regression.py anchors may need updating. This is a follow-up if it occurs.

## Anti-Drift Hazards
- Do NOT mutate `detection_params.yaml` during the sweep.
- Do NOT change scoring deltas/weights — this ticket is purely about loop detection tuning.
- The `--window-size` flag must be run-scoped (passed through weights patching), not persisted.
- `ScoringWeights` is frozen; use `model_copy(update=...)`, not `object.__setattr__`.

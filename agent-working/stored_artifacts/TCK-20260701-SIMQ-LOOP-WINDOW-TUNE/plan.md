# Plan — TCK-20260701-SIMQ-LOOP-WINDOW-TUNE

## Ordered Steps

### Step 1 — Add CLI override flags to calibrate_simq.py (main())
File: `tools/calibrate_simq.py`

Add two optional argparse args immediately after the existing `--output` arg (lines ~250–255):
```python
parser.add_argument(
    "--window-size", type=int, default=None,
    help="Override detection_params.yaml window_size for this run only (does not mutate YAML)."
)
parser.add_argument(
    "--loop-threshold", type=float, default=None,
    help="Override detection_params.yaml loop_threshold for this run only (does not mutate YAML)."
)
```

### Step 2 — Patch ScoringWeights after load (run-scoped, no YAML mutation)
File: `tools/calibrate_simq.py`

After `weights = _load_weights(profile)` (line 272), insert:
```python
if args.window_size is not None or args.loop_threshold is not None:
    patched_detection = weights.detection.model_copy(update={
        k: v for k, v in {
            "window_size": args.window_size,
            "loop_threshold": args.loop_threshold,
        }.items() if v is not None
    })
    weights = weights.model_copy(update={"detection": patched_detection})
```

Also update the print line to show effective window/threshold:
```python
print(f"[calibrate_simq] Running engine: {run_tag} entities={args.entities} profile={profile} "
      f"window_size={weights.detection.window_size} loop_threshold={weights.detection.loop_threshold}")
```

Scope guards: only `main()` and `_load_weights` are touched. `PillarAccumulator`, `DetectionParams`, `ScoringWeights` source files are NOT changed.

### Step 3 — Add two unit tests to test_accumulator.py
File: `tests/simulation_quality/test_accumulator.py`

Add after the existing `test_loop_detection_does_not_fire_below_threshold` test:

`test_accumulator_respects_injected_window_size` — verifies window_size override flows through via patched ScoringWeights (not default 200).

`test_accumulator_respects_injected_loop_threshold` — verifies a lower threshold causes loop to fire earlier than the default 0.70.

Both tests create patched ScoringWeights via `weights.model_copy(update={"detection": weights.detection.model_copy(update={...})})` using the `scoring_weights` fixture from conftest.

### Step 4 — Run empirical sweep
After the code is in place, run:
```bash
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name sandbox_world --window-size 100
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name sandbox_world --window-size 150
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name sandbox_world --window-size 200
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name sandbox_world --window-size 300
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name dungeon_crawl --window-size 100
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name dungeon_crawl --window-size 200
```
Capture per-pillar `event_count` and `grade` for each run. Determine whether any pillar materially improves grade with a different window.

### Step 5 — Document decision in quality_scoring_contract.md §4.7/4.8
File: `docs/simulation_quality/quality_scoring_contract.md`

Update §4.7 to note: "The `tools/calibrate_simq.py` `--window-size` and `--loop-threshold` CLI flags allow per-run override without mutating `detection_params.yaml` — intended for sweep analysis only."

Add §4.8 subsection (or update existing): record the sweep decision and final confirmed values.

### Step 6 — Add parity ledger entry
File: `docs/parity_ledger/infrastructure.yaml`

Append INFRA-251:
```yaml
- id: INFRA-251
  text: "calibrate_simq.py --window-size and --loop-threshold CLI flags override detection_params.yaml
    for the current run only, without mutating the YAML source. ScoringWeights is patched via
    model_copy() — no global state mutation."
  status: verified
  priority: P1
  v2_evidence: "tools/calibrate_simq.py::main() — model_copy patch after _load_weights()"
  test_path: "tests/simulation_quality/test_accumulator.py::test_accumulator_respects_injected_window_size"
  divergence_note: null
```

## Scope Guards (what NOT to touch)
- `src/simulation_quality/pillar_accumulator.py` — no changes
- `src/simulation_quality/weights.py` — no changes
- `config/simulation_quality/detection_params.yaml` — no changes (unless sweep proves 200/0.70 is wrong)
- Scoring deltas/weights for any pillar
- Any file outside `tools/calibrate_simq.py`, `tests/simulation_quality/test_accumulator.py`, `docs/simulation_quality/quality_scoring_contract.md`, `docs/parity_ledger/infrastructure.yaml`

## Dependency Map
- Step 3 depends on Step 1+2 being implemented (needs model_copy pattern to exist for test reference)
- Step 4 depends on Step 1+2 (CLI must exist)
- Step 5 depends on Step 4 (decision comes from sweep data)
- Step 6 depends on Step 1+2 (parity entry references the implementation)

## Acceptance Criteria → Steps
| AC | Steps |
|---|---|
| `calibrate_simq.py` accepts window-size override without editing YAML | 1, 2 |
| Sweep data recorded | 4 |
| Documented decision | 5 |
| `quality_scoring_contract.md` §4.7/4.8 updated | 5 |
| No regression in test_accumulator.py or test_grade_regression.py | 3, tests |

## Deviations
(none yet — fill if implementation diverges)

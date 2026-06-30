---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-CALFIX
artifact_type: plan
tags: [simq, calibration, implementation-plan]
---

# Plan: TCK-20260630-SIMQ-CALFIX

## Ordered Implementation Steps

### Step 1 — Add `--profile` and `--output` CLI arguments
Add `--profile` (default: `name` if file exists else `"default"`) and `--output`
(override for cal_dir) to the argparse block in `main()`.
Pass profile to `_load_weights()`.

### Step 2 — Refactor `_load_weights()` to accept profile
Change signature from `_load_weights()` to `_load_weights(profile: str = "default")`.
Pass profile through to `ScoringWeights.load()`.

### Step 3 — Add world loading to `_run_engine()`
Change `_run_engine(seed, ticks, entity_count)` to accept `name: str = "generic"`.
Logic:
1. Compute resolved_path = `data/worlds/{name}/resolved/world.resolved.yaml`
2. If path exists:
   a. Load YAML → `WorldSpec(**data)`
   b. Call `WorldCompiler.compile(spec, seed)` → `(state, compile_report)`
   c. Use returned `state` directly, skip generic entity construction
3. If path does not exist, use generic entity construction (fallback)

### Step 4 — Fix goblin spawn positions in generic fallback
Change `(60.0 + i, 60.0 + i)` to `(20.0 + (i % 5) * 8, 20.0 + (i // 5) * 8)`.
This places goblins in a 5-wide grid starting at (20,20), minimum 12 tiles from
hero at (64,64).

### Step 5 — Wire name and profile through `main()`
Pass `args.name` to `_run_engine()`.
Resolve profile: check `config/simulation_quality/profiles/{args.name}.yaml` exists;
if so use `args.name` as default profile, else `"default"`.
Apply `--output` override to `cal_dir` if provided.

### Step 6 — Update ticket Implementation Notes
Fill in what was done.

### Step 7 — Re-run calibration for 2 worlds to verify differentiation
```bash
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 200
python3 tools/calibrate_simq.py --name urban_political --seed 42 --ticks 200
```
Confirm: different pillar scores, no LAW-OCCUPANCY-COLLISION.

## Key Design Decisions

- World loading is optional (graceful fallback) to preserve quick generic benchmarks
- `WorldCompiler.compile()` is called with no context (no DI) — verified safe
- The `--output` arg is convenience; the default naming convention `{name}_seed{seed}_{ticks}t` is preserved
- Kernel + QualityHub wiring unchanged — only the world state fed into Kernel changes

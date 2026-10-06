# Probes for hazard growth (rpg-implementer-2, 2026-10-05)
`hazard.py <world> <ticks> <out.jsonl>`: every 500 ticks, each region's hazard and trauma, death causes so far, and the tick hazard first exceeded its authored value. Run from a worktree root with `PYTHONPATH=.` and the project venv.
- `capped_*` run on the unified-lookup tip (capped growth); `uncapped_*` on the same tree with the cap removed.
- `generated_frontier_3_42` pair: deterministic, identical until growth starts at tick 6911.
- `frontier_living_world` pair: NOT a valid pair (`uncapped_fl_10000_UNPAIRED`); see `determinism_check_fl_2000_run1/2` (8 vs 10 deaths at tick 500 on identical code).
- The `alive` field in checkpoints reads 0 throughout and was not verified: do not cite it.

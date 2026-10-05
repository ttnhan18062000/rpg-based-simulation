# Probes for the region-overlap audit (rpg-implementer-2, 2026-10-05)

Throwaway measurement scripts and their outputs, kept so a later session does not re-run them. Every run: real `Kernel.tick_once()`,
`PROD_SMALL`, seed 42, world compiled with `tests.helpers.scenario.compile_world`. Run from a worktree root with `PYTHONPATH=.` and the project venv.
Outputs are `.jsonl` because `.gitignore` drops `stored_artifacts/*.json`.

## Scripts

| script | what it records |
|---|---|
| `trauma2.py <world> <ticks> <out.jsonl>` | per tick, the trauma series of the regions in its `watch=[...]` list (edit it per world: a name that is not a region of the world raises KeyError at the end of the run, after the ticks are spent); per death: tick, entity id, regions containing the point by CLOSED bounds, the region `SpatialQueryService.get_region_at` credits, end-of-tick position, kind, death_reason, passive cause, age, hp. Writes checkpoints to `<out.jsonl>` and a `<out.jsonl>.full.json` (the files here were converted to `.jsonl`). |
| `trace.py <world> <ticks> <out.json>` | wraps `WorldDynamicsSystem._get_region_for_pos`, records each call with its call-site line, the position, the region returned and every region containing the point, plus per-tick trauma deltas. |
| `nocred.py <full.json> <label>` | counts deaths credited to no region, how many are within 10 of the origin, and the cause mixes. |
| `infl.py <world> <ticks>` | wraps `FactionInfluenceService.process_influence_shift` to count calls and effects. |

## Outputs and what each proves

| output | proves |
|---|---|
| `main_fl_10000_*` | on `main`, trauma crosses 50 at ticks 5211 (goblin_camp) and 5217 (bandit_road), no plateau by 10,000; the two series are never identical tick by tick (distinct deaths, one tick apart) |
| `main_fl_5000_deaths_with_causes` | near_forest / wolf_den / trading_hometown deaths are mostly HAZARD deaths credited to bandit_road or goblin_camp: overlap shadowing |
| `main_gf_5000_deaths`, `main_gf_1000_moon_cave_starvation` | moon_cave deaths are passive STARVATION, correctly credited to moon_cave, and its trauma stays 0.0 (the trauma block ignores passive deaths) |
| `main_fl_1500_trauma_block_lookups` | one real trauma-block call traced: a point inside bandit_road, near_forest and wolf_den is credited to bandit_road, the first declared |
| `laneA_tip_*` (three-arm A/B) | the cluster of deaths credited to no region is the four tactical `(0.0, 0.0)` retreat targets: 20 on `main`, 1 on Lane A's tip, 21 with only `tactical.py` reverted |
| `after_smallest_area_*` | the SAME world after the smallest-area rule: near_forest and wolf_den are STILL 0.0, and bandit_road is still credited about the same deaths, because bandit_road (area 1,200) is smaller than wolf_den (1,400) and near_forest (2,025); the regions overlap partially and are not nested |

## Row formats

`trauma_series` lines: `{"kind":"trauma_series","region":<id>,"values":[<one number per tick>]}`.
`death` lines: `{"kind":"death","row":[tick, entity_id, regions_by_closed_bounds, credited_region_or_null, [x, y], kind, death_reason, passive_cause, age_ticks, max_age_ticks, hp]}`;
the earliest runs carry only the first five or six fields.
`*_checkpoints.jsonl`: one line per 500 ticks with the watched regions' trauma, first tick over 50, per-region maxima and the running death count.

## Added after the rule landed
`trauma2.py` now watches every region of the world (`watch=list(st.regions)`), so a world with different region names no longer crashes at the end of the run. `after_smallest_area_gf342_10000_checkpoints.jsonl` and `after_smallest_area_gf342_10000_deaths_and_series.jsonl` are the `generated_frontier_3_42` run (10,000 ticks, seed 42): trauma crosses 50 only in `goblin_camp` (tick 6911); 3 of 138 deaths lie in two regions; there is no before-run.

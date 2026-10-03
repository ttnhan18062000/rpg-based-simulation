# D03 Investigation — Behavioral Emergence Quality

## Pre-condition Bug

`data/worlds/sandbox_world/world.yaml` had `quest_definitions: []` (line 53).
`WorldTemplateSpec` (recipe.py:87) defines the field as `quests:`, not `quest_definitions:`.
`extra="forbid"` caused immediate ValidationError on sim start.

Fixed: renamed to `quests: []`. WorldTemplateExpander maps `quests → quest_definitions` internally (L140).

## Run Configuration

Two runs executed:

| Run | Seed | Ticks | Entities | World |
|---|---|---|---|---|
| run_1781801466_7032 | 42  | 200 | 20 | sandbox_world |
| run_1781802xxx | 137 | 200 | 20 | sandbox_world |

Both: `observability_mode=LIGHT`, `scenario_type=mixed_sandbox`.

## Metric Windows

### Seed 42

| Window | Ticks | Alive avg | Active avg | Rejections | Events | Quests active |
|---|---|---|---|---|---|---|
| W1 | 1–100 | 15.3 | 20.0 | 94 | 8 | 0.0 |
| W2 | 101–200 | 15.0 | 20.0 | 100 | 0 | 0.0 |

### Seed 137

| Window | Ticks | Alive avg | Active avg | Rejections | Events | Quests active |
|---|---|---|---|---|---|---|
| W1 | 1–100 | 15.43 | 20.0 | 426 | 9 | 0.0 |
| W2 | 101–200 | 15.0 | 20.0 | 500 | 0 | 0.0 |

## Event Distribution (both seeds)

Seed 42: 8 events total (5 combat_damage, 3 quest_event) — all in ticks 3-7.
Seed 137: 9 events total (mix combat/quest) — all in ticks 3-20.

After tick 20 (seed 137) / tick 7 (seed 42): zero events for remaining 180-193 ticks.

## Behavioral Observations

**Movement:** Only 3-4 of 20 entities moved at all (2-3 moves each, ticks 1-20).
**Resource use:** Zero resource node charge changes in 200 ticks.
**Economy:** `gold_total_avg = 0.0` throughout both runs.
**Quests:** `quest_active_count = 0.0`, `quest_completed_count = 0.0` throughout.
**Goal variety:** `kind_set` field is null on all REFINED_UPDATE payloads (LIGHT mode does not capture goal kind).
**Entity deaths:** 5 of 20 entities die by tick ~15 and are not replaced. Count stabilises at 15.

## Positive Observations

- Both 200-tick runs complete successfully (LifecycleOutcome.SUCCESS)
- Final state hash is deterministic (same hash on multiple runs with same seed)
- Zero hard law violations in either run
- Governor mode stays NORMAL throughout
- Average tick compute: 12-13ms (well within 50ms budget most ticks)
- 5 combat_damage events confirm combat system does fire (briefly)

## Tick Budget Overruns (Seed 42)

Five ticks exceeded budget (35, 100, 105, 130, 191). Tick 35 breakdown:
- `final_integrity`: 46.83ms of 59.57ms total — dominates the overrun
- Consistent with D10 F2 (ItemStack.position AttributeError in world_index.py)
  which likely causes expensive fallback paths in final_integrity validation.

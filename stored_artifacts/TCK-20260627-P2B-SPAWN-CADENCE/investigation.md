# Investigation — TCK-20260627-P2B-SPAWN-CADENCE

## Current Behavior (file:line refs)

### SpawnService (`src/world/spawn.py`)
- `SpawnService.SPAWN_INTERVAL = 50` (L17) — fires every 50 ticks
- `process_spawns()` (L20): if `state.tick % 50 != 0` → return empty update
- Per region below density target: spawns exactly **1 monster** using a single RNG draw per region (L58–78)
- Density formula (L52): `target_count = max(2, int((area/10000) * 2.0 * (1+hazard_level)))`

### SpawnConfig (`src/world/spawn_config.py`)
- `BASE_MONSTER_DENSITY = 2.0` (L38)
- `SPAWN_POOLS` (L31): three region kinds supported (FOREST, PLAINS, MOUNTAIN)
- `DIFFICULTY_ZONES` (L24): 4 tiers by distance from (0,0)
- No config struct exists — all values are module-level constants

### D06 Observation (docs/audits/D06_longrun_health.md §F5)
| Phase | Seed 42 alive_avg | Seed 137 alive_avg |
|---|---|---|
| Ticks 1–500 | 15.0 | 15.0 |
| Ticks 501–700 | 18.0 (spawn fired) | 18.0 (spawn fired) |
| Ticks 801–900 | 15.7 | 15.1 |
| Ticks 901–1000 | **13.1** | **14.6** |

### Root Cause
The spawn fires every 50 ticks but only adds **1 entity per region** that is below density. Late-run
combat attrition (combat_damage events reappear at ticks 800–1000) can kill multiple entities per
combat tick, while the spawn replenishment trickles in at 1/region/50-ticks. Once attrition exceeds
the trickle rate, the population trends downward. At 5,000 ticks this risks near-zero entities.

There is also a density-cap interaction: when entity count is at or above `target_count` the spawn
skips all regions, creating a dead zone until attrition pulls count below the threshold.

## Mechanics/Engine Constraints
- No Mechanics Bible chapter governs `SpawnService` cadence directly — this is simulation tuning
- Spawn must use the `Domain.SPAWN` RNG domain to preserve determinism (src/world/spawn.py L58)
- All spawned entities must go through `StateUpdate.entities_add` (authoritative pipeline path)
- `generator._last_id` must be updated correctly when adding multiple entities per call (L42, L82)

## Parity Ledger Overlap
- **No existing WORLD-xxx entry** covers `SpawnService` cadence or batch-size behavior
- WORLD-102 is the last numeric entry — new entry WORLD-103 to be added
- Calamity/faction-raid spawn entries (WORLD-048, WORLD-049) use interval-based pattern but are separate systems

## Prior Work
- `TCK-20260619-AUDIT-D06-LONGRUN` — D06 audit that identified this finding (stored_artifacts/TCK-20260619-AUDIT-D06/)
- `TCK-20260627-P2A-SPAWN-LOCK-COND` — companion ticket (must be done first; reduces early dead-time)
- No prior spawn-cadence tuning tickets found

## Risks and Open Questions
1. **Determinism**: Adding batch spawning with multiple RNG draws per region per tick may break
   determinism for existing seeds if the RNG key scheme changes for single-spawn calls.
   **Resolution**: Use original keys for `batch_idx=0`, suffixed keys (`{r_id}_b{i}`) for `i>0` only.
   This preserves existing determinism for single-spawn (base) case.
2. **Density cap interaction**: Batch spawning only fires when `current_count < target_count`.
   With `batch_size=2`, we still only spawn as many as needed to reach target (min(batch_size, deficit)).
3. **1,000-tick AC already met**: Both seeds achieve alive_avg=13.1/14.6 at ticks 901-1000 (both ≥ 12).
   The fix targets the downward trend to prevent failure in extended runs (5,000 ticks).
4. **Other tickets**: TCK-20260627-P0A-ADVENTURE-FLAG must be clear before long-run behavioral metrics
   are fully meaningful, but SpawnService runs regardless of adventure routing state.

## Anti-Drift Hazards
- `generator._last_id` must be incremented once per spawned entity — batch spawning must update it
  correctly after each entity, not just once at the end
- The `next_entity_id_set` field in `StateUpdate` must reflect the total after all batch spawns
- Do not touch `SPAWN_INTERVAL` constant itself — only batch size changes

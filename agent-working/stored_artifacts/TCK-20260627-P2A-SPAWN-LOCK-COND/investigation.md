# Investigation — TCK-20260627-P2A-SPAWN-LOCK-COND

## Current Behavior (file:line refs)

### Lock check (where lock prevents routing)
- `src/domains/adventure/phase.py:67` — `if tick < active_proj.lock_until_tick: continue`
  Entities with an active, locked project are entirely skipped by the adventure routing phase.
- `src/engine/tactical.py:59` — `if current_project and state.tick < current_project.lock_until_tick:`
  Same guard in the tactical evaluation path (maintains current task while locked).

### Lock assignment (where lock_until_tick is written)
| File | Line | Value |
|---|---|---|
| `src/domains/adventure/mapper.py` | 101 | `tick + 10` |
| `src/systems/strategic_systems/intelligence.py` | 1340 | `current_tick + 10` (goal-scored projects incl. COMBAT_RETREAT, RECOVER) |
| `src/systems/strategic_systems/intelligence.py` | 1266 | `current_tick + 20` (detour projects) |
| `src/systems/social_systems/contracts.py` | 180 | `tick + 50` (recruitment/loan contract projects) |

### The cascade mechanism (root cause of D06 F2 dead window)
No single 200-tick lock exists in the code. The D06 observation ("ticks 101–200 produce zero behavioral events") is caused by cascading 10-tick relocks:

1. Entities engage in combat during ticks 1–100 (combat events appear).
2. At ~tick 100, `COMBAT_RETREAT` or `RECOVER` goal scores high (HP < 50%).
3. `intelligence.py:1340` creates project with `lock_until_tick = current_tick + 10 = 110`.
4. At tick 110, lock expires, entity re-evaluates. HP still low → new project, `lock_until_tick = 120`.
5. Cascade repeats until HP naturally recovers to ≥ 90% (stamina also required for RECOVER).
6. Under current combat parameters this takes ~100 ticks of cascade → events absent 101–200.

The "200 ticks" in the D06 audit is the CUMULATIVE observation, not a single lock value.

### Existing behavior models
- `src/ai/goals/scorers.py` CombatRetreatScorer: returns 0 utility when `hp_ratio >= 0.5 AND not fleeing`.
- `src/ai/goals/scorers.py` RecoverScorer: returns 0 utility when `hp_ratio >= 0.9 AND stamina_ratio >= 0.9`.
- `src/core/strategic.py:243` `ProjectState.lock_until_tick: int = 0` (default — no lock).
- Hostility check available via `SpatialQueryService.nearby_entities` + faction comparison.
  `src/core/enums.py:24` `Faction` — `HERO_GUILD=0`, `MONSTER_HORDE=1`; faction mismatch ≈ hostile.

## Mechanics/Engine Constraints
- Engine contract: decision logic reads state; durable state only via typed records through authoritative path.
- `adventure/phase.py` is already on the authoritative path (produces `StateUpdate` with `EntityUpdate`).
- No mutations to `ProjectState` may be done directly — must use `replace()` to produce updated record.
- The early-release check must be pure read-only logic.

## Parity Ledger Overlap (IDs + status)
- `strategic_cognition.yaml` entry for "project lock prevents switching" — currently verified.
  This ticket adds a CONDITIONAL path alongside the lock, not replacing it. Parity update required.
- No existing entry for "spawn-lock conditional on threat resolution" — new entry needed.

## Prior Work
- D06 audit (`docs/audits/D06_longrun_health.md` F2) first identified the dead window.
- D03 pre-fix had the same symptom; RC1 resolved cascade source but not the lock cascade.
- P1-A (TCK-20260627-P1A-REJECTION-BACKOFF) is complementary — reduces dead time from a different angle.
- `stored_artifacts/TCK-20260619-AUDIT-D06/` contains the audit investigation material.
- `tickets/working_log.csv` — no prior TCK targeting lock_until_tick conditional release.

## Risks and Open Questions
- **None unresolved.** Faction-mismatch as proxy for "hostile" is sufficient for this ticket (confirmed by CombatRetreatScorer pattern).
- HP threshold 80% vs 90%: ticket says 80%, RecoverScorer uses 90% to stop scoring. 80% is intentionally less strict — the early-release lets the entity re-route BEFORE fully recovered.
- `has_hostile` check uses `SpatialQueryService.nearby_entities(radius=10.0)` — consistent with `AdventureRouteGenerator` neighborhood radius.

## Anti-Drift Hazards
- Do NOT modify `lock_until_tick` check in `engine/tactical.py:59` — that path is for immediate task continuity during combat, not adventure routing. The ticket targets `adventure/phase.py` only.
- Do NOT change `RecoverScorer` or `CombatRetreatScorer` thresholds — those are goal scoring laws.
- Do NOT remove the lock check entirely; the lock still applies when threat is NOT resolved.

---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP
artifact_type: investigation
tags: [bug, lifecycle, engine, determinism]
---

# Investigation — TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP

## Phase ordering (verified in code)
- Passive path (`src/engine/apply.py` `_compute_entity_changes`): `total_passive_dmg` drives `new_hp` to 0 and
  sets `combat.alive=False` and `lifecycle.active=False` in the same apply, with no `EntityUpdate`.
  `resolve_lifecycle` then skips the inactive entity (`if not active: continue`) forever. So a passive
  death is only visible as an already-inactive, combat-dead entity with no `death_reason`.
- Hazard path (`src/engine/world_dynamics.py:39`): stages `alive_set=False` with `outcome_kind="HAZARD"` in
  the same tick before `resolve_lifecycle` runs, so it is detectable the same tick. It overwrites a
  same-tick combat `KILL` (separate ticket TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND).
- `outcome_kind` is not persisted in `EntityState`; the only state signal for a passive death is the bio
  thresholds (hunger >= 95.0, sleep_debt >= 98.0), already named in `src/engine/semantic_entity_index.py`.

## DEFEAT / REBIRTH (decided with rpg-feature-planning, 2026-10-01)
Non-lethal under world rule LIFE-02 (`docs/world_rules/life-body/lifecycle.md`) and Bible ch. 02 rebirth. Not
classified here. The real defect (a defeated hero silently becomes permanently dead a tick later via
`apply.py:109`) is a separate ticket.

## Decisions (final)
- No classification ships here. Passive bio deaths: record the cause at the writer when `comb.hp > 0 and
  new_hp == 0` (follow-up ticket). Hazard deaths: `world_dynamics.py:39` overwrites `KILL`/`DEFEAT`/`REBIRTH`
  with `HAZARD`, so a `HAZARD` branch cannot tell them apart; sequenced behind the overwrite ticket.
- Rejected inference: cause from bio thresholds (LIMIT-04, CAUSE-01, HP-02, CAUSE-05, LIFE-02).

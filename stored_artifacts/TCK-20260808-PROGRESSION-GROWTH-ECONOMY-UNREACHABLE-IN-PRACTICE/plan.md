---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [progression, combat, feature-flags]
---

# Plan — TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE

## Fix

**File:** `src/engine/movement.py`, `MovementSystem.resolve_move`, opportunity-attack branch
(current lines ~193-204).

Current (buggy):
```python
if attackers:
    combat_update = CombatResolutionSystem.resolve_multi_attack(
        attackers, entity, state_or_context, is_opportunity_attack=True, is_lethal=False
    )
    updates[entity.id] = EntityUpdate(entity_id=entity.id, combat=combat_update)
```

New:
```python
if attackers:
    combat_update = CombatResolutionSystem.resolve_multi_attack(
        attackers, entity, state_or_context, is_opportunity_attack=True, is_lethal=False
    )
    updates[entity.id] = EntityUpdate(entity_id=entity.id, combat=combat_update)

    # Reward attribution: combat_update.resource_transfers is meant for whoever defeated
    # `entity`, not for `entity` itself. resolve_multi_attack already collapses the reward to
    # a single ResourceTransferIntent list attributed via combat_update.attacker_id (the same
    # "first attacker" convention entity_killed's own shaper already uses for multi-attacker
    # kills, src/observability/event_shapers.py:158) — mirror that here rather than inventing a
    # per-attacker split resolve_multi_attack doesn't itself produce.
    if combat_update.resource_transfers and combat_update.attacker_id is not None:
        reward_upd = EntityUpdate(
            entity_id=combat_update.attacker_id,
            resource_transfers=combat_update.resource_transfers,
        )
        existing_attacker_upd = updates.get(combat_update.attacker_id)
        updates[combat_update.attacker_id] = (
            existing_attacker_upd.merge(reward_upd) if existing_attacker_upd else reward_upd
        )
```

`updates` can already hold an entry for another entity id at this point in the function (line 128,
`updates[occupant_id] = ...` from an earlier occupancy-swap branch) — use `.merge()` defensively
rather than a raw assignment, so an unrelated pre-existing update for the same id (if
`combat_update.attacker_id == occupant_id` in some edge case) isn't clobbered.
`EntityUpdate.merge()` already concatenates `resource_transfers` correctly (`src/core/
updates.py:677`, confirmed in investigation.md).

The caller (`src/engine/pipeline_phases/movement.py:240-255`,
`MovementPhase.route_movement_intent`) already iterates every key `resolve_move` returns and
`.merge()`s each into `refined_entity_updates` — confirmed safe for a multi-key return dict,
no caller-side change needed.

## `is_lethal=False` hardcoding — leave as-is, out of scope for this fix

Investigate flagged this as a secondary, related-but-distinct gap (opportunity-attack deaths can
never produce `outcome_kind == "KILL"`, only `"DEFEAT"`, so `entity_killed` never fires for this
death class either). Whether `is_lethal=False` here is intentional design (opportunistic strikes
during retreat shouldn't be treated as full kills) is a game-design judgment call, not a
mechanically-forced consequence of the resource_transfers bug — the XP/gold reward already flows
correctly through the `DEFEAT` outcome branch (`combat.py:389`'s `if not alive and
defender.combat.alive:` guard checks `alive`, not `outcome_kind`), so fixing resource_transfers
attribution alone is sufficient to unblock progression without touching this. Flagging as a
follow-up observability gap rather than folding it into this fix, to keep this change narrowly
scoped to the confirmed, load-bearing bug. Will note in Completion Summary as a disclosed,
deliberately-deferred item, not a silently-dropped one.

## `EVOLUTION_THRESHOLD` dead constant

Per ticket's own Acceptance Criteria ("either removed or wired for real use — not left as
unreachable dead code either way"): remove the dead module-level constant in
`src/engine/evolution.py` (confirmed in the ticket's own Request Summary via `grep -n
"EVOLUTION_THRESHOLD"` — referenced exactly once, at its own definition). A one-line deletion,
no behavior change (nothing reads it).

## Docs / parity ledger

No formula changes — the XP/threshold math itself (`combat.py`'s per-kill XP,
`LevelingService.get_xp_required()`) is untouched and already correctly documented/parity-verified
per investigation.md. This fix corrects a reward-delivery wiring defect, not a mechanics formula,
so no `docs/mechanics/` or `docs/parity_ledger/progression.yaml` edit is required by the fix
itself. `doc_staleness_check.py`'s gate is expected to pass on `behavior_changed=true` +
`src/engine/movement.py` changed + no `docs/` path touched only if it treats this as a bugfix not
requiring a doc update — if the gate disagrees, that is authoritative over this plan's expectation
and will be honored, not routed around (per CLAUDE.md's Gate Integrity rule).

## Acceptance-criteria map

| Acceptance criterion | How this plan satisfies it |
|---|---|
| Resolve `RewardPatch`/`EvolutionSystem` double-application question | Already resolved in investigation.md — not a bug, no code change needed |
| Real measured kill rate reported | Already reported in investigation.md (9 deaths / 2000 ticks, `sandbox_world`) |
| Quest-completion rate re-confirmed with fresh data | Already reported in investigation.md (0 quest events, 2 worlds, fresh 1000-tick runs) |
| Real fix with measurable `xp_granted`/`level_up` increase on 2+ worlds at 1000+ ticks | The `movement.py` fix above + Test step 4 (before/after real-run verification on `sandbox_world` + `urban_political`) |
| `EVOLUTION_THRESHOLD` removed or wired | Removed (dead code, one-line deletion) |
| Docs/parity updated if formulas change | N/A — no formula change; documented above |
| Scoped pytest passes | `test_plan.md`'s scoped command |

## Out of scope (reaffirmed from ticket)

- `ENABLE_PROGRESSION_EVOLUTION` corpus-wide rollout
- HERO-specific underperformance (sibling ticket)
- Quest dormancy root cause (sibling/follow-up ticket)
- `is_lethal=False` semantics on the opportunity-attack path (flagged above as a deliberate,
  disclosed deferral, not silently dropped)

---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION
phase: open
date: 2026-09-11
tags: [world, architecture]
---

# TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION

## Title
Reconstructed survivors return with default `combat.hp`/`.max_hp`/`.atk`/`.def_stat`, not stats recomputed from their carried `evolution_level` — the stats-dirty recompute path never fires at reconstruction time

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION`'s own
investigation, while determining whether it was safe to leave `combat.hp`/`.atk`/`.def_stat`
uncarried on the assumption they're recomputed from carried `level`. They are not, for a
reconstructed survivor specifically.

`src/engine/apply.py`'s `stats_dirty` recompute path (`SkillScalingService.get_effective_stats()`,
called around line 564) only fires when comparing an incoming `EntityUpdate` against the entity's
own **current tick state within an already-running episode** — specifically gated by conditions
like `update.identity.evolution_level_set is not None and update.identity.evolution_level_set >
entity.identity.evolution_level` (a level *increase relative to itself*). A freshly-reconstructed
survivor at episode start has no prior-tick state to compare against; its own
`identity.evolution_level` already reflects the carried value from the moment it's constructed, so
no update-vs-self comparison ever detects a "level increase" to recompute against. The entity's
`combat` component instead sits at `EntityState`'s own bare defaults (typically 100 HP / 10 ATK /
5 DEF) regardless of the survivor's real carried level, until/unless they level up again within the
new episode.

## Scope
- Confirm this determination with a real, direct check (not just the code-read reasoning above) —
  construct a reconstructed survivor with a real carried `evolution_level` > 1 and inspect its
  `combat.hp`/`.max_hp`/`.atk`/`.def_stat` immediately after `_build_initial_state()` returns.
- Fix: call the real recompute path (`SkillScalingService.get_effective_stats()` or equivalent)
  once at reconstruction time for each survivor, using their carried level/class/attributes/
  equipment, so `combat` reflects their real accumulated power the same way a normal in-episode
  level-up would set it.
- This is a narrow, well-understood fix (reuse the existing recompute function, don't reimplement
  stat derivation) — hotfix tier.

## Out of Scope
- `TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION`'s own identity fields
  (`kind`/`role`/`faction`/`properties`/`traits`/`personality`) — different fix shape (carry vs.
  recompute), filed and fixed separately per that ticket's own peer-review direction.
- Whether `AttributeComponent` (STR/INT/etc.) itself should carry forward — not currently carried
  by `EntityCarryForward` either; if `get_effective_stats()`'s own recompute needs real carried
  attributes (not just level) to be meaningful, that's a further, not-yet-scoped question this
  ticket's own Investigate phase should surface, not assume.

## Acceptance Criteria
- [ ] Direct confirmation (not just code-read reasoning) that reconstructed survivors currently
      return with default combat stats regardless of carried level.
- [ ] Real fix: survivor combat stats recomputed from carried level (and whatever else
      `get_effective_stats()` needs) at reconstruction time, verified by a real test showing a
      high-level survivor's `combat.max_hp`/`.atk`/`.def_stat` differ from the bare default after
      reconstruction.
- [ ] No regression in `tests/unit/domains/campaigns/`, `tests/integration/campaigns/`.

## Related Tickets
- `TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION` (origin of this finding)
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` (the first ticket in this same
  reconstruction-branch arc)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()`'s survivor-reconstruction
  branch)
- `src/engine/apply.py` (`stats_dirty` recompute path, for comparison — this ticket does not touch
  the tick-time recompute logic itself, only reconstruction-time)
- `src/engine/rpg_depth.py` (`SkillScalingService.get_effective_stats()`,
  `LevelingService.recalculate_combat_stats()`)

## Assumptions / Open Questions
- Whether `AttributeComponent` also needs carrying for the recompute to be meaningful is the real
  open question here — not assumed, real Investigate work.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_

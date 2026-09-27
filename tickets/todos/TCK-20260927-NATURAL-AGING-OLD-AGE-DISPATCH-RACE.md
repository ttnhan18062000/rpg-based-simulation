---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE
phase: open
date: 2026-09-27
tags: [engine, lifecycle, bug]
---

# TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE

## Title
Natural aging deactivates an entity with no death reason and no succession: `ApplyPath` and
`LifecycleSystem.resolve_lifecycle` both write old-age deactivation

## Status
OPEN — drafted, not started. First-wave milestone M1 in
`docs/plans/systemic_world/first_wave_plan.md`; starts only after the owner reviews that plan's
scope.

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
An entity that reaches `max_age_ticks` through ordinary per-tick aging never gets an OLD_AGE death
record or succession. `ApplyPath._compute_entity_changes` (`src/engine/apply.py:106-109`) increments
`age_ticks` and, in the same commit, sets `lifecycle.active = (new_hp > 0 and new_age <
max_age_ticks)`. On the tick the incremented age reaches `max_age_ticks`, the entity is committed
inactive with `death_reason=None`. `LifecycleSystem.resolve_lifecycle` reads the prior tick's
persisted age (`src/systems/lifecycle_systems/lifecycle.py:193-194`), so it has not yet seen the
threshold, and on every later tick it skips the entity because it is already inactive
(`lifecycle.py:147`). Heir inventory transfer, feud-blocker transfer, and dying-wish seeding never
run.

The existing aging/succession tests (`tests/mechanic_scenarios/test_aging_death_value_differential.py`,
`tests/simulation_quality/test_heir_inventory_transfer_corpus.py`,
`tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`) do not catch this:
they stage `age_ticks` already past `max_age_ticks` in the tick-0 snapshot, so `resolve_lifecycle`
fires on the first tick before the `ApplyPath` branch can pre-empt it.

Reproduction (verified 2026-09-27 on branch `systemic-world-roadmap-proposal`, seed 42,
`PROD_SMALL`, two entities built with `V2EntityBuilder`: subject `age_ticks=0, max_age_ticks=3,
heir_entity_id=2` carrying `iron_sword`; heir alive, empty inventory; 6 real `Kernel.tick_once()`
calls, no mid-run staging):

```
tick=1 age=1 active=True  death_reason=None heir=[]
tick=2 age=2 active=True  death_reason=None heir=[]
tick=3 age=3 active=False death_reason=None heir=[]
tick=4 age=4 active=False death_reason=None heir=[]   (never recovers)
```

Real-play frequency is low today: the default `max_age_ticks` is 70 fantasy years (20,160,000 ticks,
`src/core/state.py:165`), far beyond current corpus runs. The defect matters for any long run, and
it blocks the roadmap's composed lineage sequence (roadmap §7.1).

## Scope
- Give old-age deactivation a single canonical authority with a declared resolution rule, most
  likely `LifecycleSystem.resolve_lifecycle`, which already records `death_reason`/`death_tick` and
  dispatches succession. `ApplyPath` keeps advancing `age_ticks`.
- Add a regression scenario that ages an entity through ordinary per-tick increments and asserts an
  OLD_AGE death record and heir dispatch.
- Update the `aging_death`/`succession` mechanism-registry notes and the relevant parity-ledger entry
  with the new evidence.

## Out of Scope
- Starvation / sleep-debt passive death (see Assumptions): same shape of gap, but a separate ticket.
- Any general `ApplyPath` rewrite or a universal `revalidate()` API.
- The composed two-hop lineage run (first-wave milestone M4a), which is gated on this ticket.
- Observer/evidence work (M2) and the three authority-boundary checks (M3a/b/c).

## Acceptance Criteria
1. The regression scenario ages an entity from `age_ticks=0` to `max_age_ticks` with no manual
   staging. The entity ends with `active=False`, `death_reason="OLD_AGE"` and a `death_tick`, and the
   heir receives the transferred inventory.
2. On no tick of that scenario is the entity inactive with `death_reason=None`.
3. The death tick is pinned by the test. With `resolve_lifecycle` as the authority, death is
   recorded on the tick after the increment that reached `max_age_ticks`: one tick later than the
   current (reason-less) deactivation. The ticket records whether that one-tick shift is acceptable,
   or it passes cadence into `resolve_lifecycle` to keep the old timing.
4. `test_aging_death_value_differential.py`, `test_heir_inventory_transfer_corpus.py`,
   `test_lineage_dispatch_deterministic_kernel_tick.py`, `tests/unit/progression/test_lifecycle.py`
   and `tests/unit/engine/test_dirty_set_passive_decay_consumers.py` pass unmodified.
5. Combat death (`resolve_lifecycle`'s KILL/PERMADEATH branch) and HP-based passive deactivation
   behave exactly as before, shown by the existing tests in criterion 4.
6. The `initial_active=False` question below is resolved and recorded before merge.

## Related Tickets
- TCK-20260904-LINEAGE-DEATH-DISPATCH (the succession dispatch this unblocks)
- TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION (`aging_death` registry note)

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §3.1, §7.1
- `docs/plans/systemic_world/first_wave_plan.md` M1
- `docs/mechanics/05_world_evolution.md` (OLD_AGE/COMBAT death and default heir selection)

## Related Stored Artifacts
None.

## Related Code Areas
- `src/engine/apply.py` (`ApplyPath._compute_entity_changes`, passive lifecycle branch)
- `src/systems/lifecycle_systems/lifecycle.py` (`LifecycleSystem.resolve_lifecycle`)
- `src/entities/archetype_factory.py:130-131` (`initial_active=False` spawns)

## Assumptions / Open Questions
- **`initial_active=False` spawns.** The current expression recomputes `active` from HP and age on
  every lifecycle-due tick, including for an entity that was inactive in the prior state. A spawn
  created with `initial_active=False` (`archetype_factory.py:130-131`) is therefore switched on by
  the first lifecycle tick. If the fix keeps a prior-inactive entity inactive, that behavior
  changes. The production spawner uses `initial_active=True` (`src/worldassembly/entity_spawner.py:71`),
  and the only `initial_active=False` caller found is `tests/unit/entities/test_archetype_entity_factory.py:163`.
  Decide whether that implicit activation was intended before merging. (Code inspection only; not
  run.)
- **Starvation / sleep-debt death, sibling gap.** The same branch sets `active=False` when passive
  hunger/sleep damage takes HP to 0, with no `death_reason`, and `resolve_lifecycle` detects only
  OLD_AGE and COMBAT. A starvation death would therefore also skip succession. This is an inference
  from code inspection and has not been run. File it separately.
- **Unreviewed prototype.** An unreviewed prototype of this fix (one-line `apply.py` change plus the
  regression scenario, 3/3 failing before the change) exists on the local, unpushed branch
  `natural-aging-old-age-dispatch-fix-unreviewed`. It was started under a superseded instruction.
  It has not been run against the suite and does not settle the `initial_active` question. Use it
  or discard it.

## Implementation Notes
_Not started._

## Test Summary
_Not started._

## Files Changed
_Not started._

## Completion Summary
_Not started._

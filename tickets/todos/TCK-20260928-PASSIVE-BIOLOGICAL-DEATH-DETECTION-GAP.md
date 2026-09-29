---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP
phase: open
date: 2026-09-28
tags: [bug, lifecycle, engine, determinism]
---

# TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP

## Title
Passive starvation/sleep-debt HP-loss deaths are silent: `resolve_lifecycle` has no HP/alive-based
death-detection branch

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`LifecycleSystem.resolve_lifecycle` (`src/systems/lifecycle_systems/lifecycle.py`) currently
detects death via exactly two branches: `age_ticks >= max_age_ticks` (`"OLD_AGE"`, `:193-195`) and
`ent_upd.combat.outcome_kind in ("KILL", "PERMADEATH")` (`"COMBAT"`, `:202-204`) — confirmed by a
repo-wide grep finding these are the only two `death_reason =` string literals anywhere in `src/`.

An entity whose HP is driven to 0 purely by passive hunger/sleep-debt decay
(`ApplyPath._compute_entity_changes`'s `total_passive_dmg` branch, `src/engine/apply.py:98-106`)
writes `combat.hp=0, combat.alive=False, lifecycle.active=False` directly, with no corresponding
`EntityUpdate` for `resolve_lifecycle` to ever observe. It never receives a `death_reason` and
never dispatches lineage consequences (heir/heirloom transfer, nemesis-feud transfer, dying-wish
seeding) — the identical silent-death *symptom* that `TCK-20260928-NATURAL-AGING-DEATH-DUAL-
WRITER-RACE` fixed for old age, but from a genuinely different *cause*: a missing detection
branch, not a timing race between two writers.

Empirically confirmed by that ticket's own investigation and regression test
(`tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py::
test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix`): an entity built with
`hunger=95.0, sleep_debt=98.0, hp=1`, run through one `Kernel.tick_once()`, ends with
`combat.hp=0, combat.alive=False, lifecycle.active=False, lifecycle.death_reason=None` — still
silent after that ticket's writer-precedence fix landed, exactly as expected, since that fix only
changed the age term.

## Scope
- Add a new `resolve_lifecycle` branch that detects an already-`combat.alive=False` entity with no
  existing `death_reason` reaching this tick's refine pass (i.e. a passive-decay-caused death the
  passive branch already recorded but no writer has yet classified).
- Assign a new `death_reason` for this path (e.g. `"STARVATION"` or `"BIOLOGICAL"` — this ticket's
  own investigation should decide the exact string, and whether hunger- and sleep-debt-caused
  deaths need distinct reasons or can share one).
- Wire the new branch through the same lineage-dispatch path `OLD_AGE` and `COMBAT` already use
  (heir/heirloom transfer, nemesis-feud transfer, dying-wish seeding, `EconomicVacancyService`
  vacancy detection via `recent_deaths`).
- Add regression coverage proving the previously-silent starvation/sleep-debt death path now
  produces a real `death_reason` and dispatches its full lineage consequences, matching the shape
  of `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s own AC1-AC3.

## Out of Scope
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s own writer-precedence fix (already
  shipped, unaffected by this ticket).
- Any change to the `total_passive_dmg` computation itself, the hunger/sleep-debt accrual rates, or
  the `new_hp > 0` immediate-HP-death gate in `ApplyPath._compute_entity_changes` — this ticket
  only adds a *detection* branch in `resolve_lifecycle`, it does not change how or when HP is lost.
- Deciding whether starvation- and sleep-debt-caused deaths need distinct `death_reason` strings
  vs. one shared reason — real design choice for this ticket's own investigation/plan phase, not
  pre-decided here.

## Acceptance Criteria
1. An entity whose HP is driven to 0 purely by passive hunger/sleep-debt decay is recorded dead
   with a real, non-`None` `death_reason`.
2. That death dispatches its full lineage consequences (heir inventory/heirloom transfer,
   nemesis-feud transfer, dying-wish seeding), matching `OLD_AGE`/`COMBAT`'s existing behavior.
3. `EconomicVacancyService`'s vacancy detection correctly observes this death via `recent_deaths`,
   the same as it now does for `OLD_AGE` (per `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s
   own Step 4 finding).
4. No tick exists where the entity is `active=False`/`combat.alive=False` with `death_reason=None`
   as a terminal state, for this specific passive-decay-driven path.
5. Existing death, inheritance, passive-decay, group/clan-lifecycle and economy-vacancy tests pass
   unmodified, in particular
   `tests/unit/engine/test_dirty_set_passive_decay_consumers.py` (all 4 tests — directly exercises
   an already-combat-dead entity on the passive path) and
   `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py::
   test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix` (this test's own final
   assertion, `death_reason is None`, must be updated as part of *this* ticket once the fix lands
   — it is deliberately pinning the pre-this-ticket gap, not a permanent invariant).
6. `docs/simulation/lifecycle_systems_contract.md`'s forward-reference note (added by
   `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s Step 8) is updated to reflect the gap is
   now closed, and the death-trigger table gains the new row.

## Related Tickets
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — parent investigation. Fixed the age
  dual-writer race (AC1-AC6); its own AC7 answered this starvation/sleep-debt path as
  empirically-affected-but-not-fixed-here and split it into this ticket.

## Related Docs
- `docs/simulation/lifecycle_systems_contract.md` — the death-trigger table and Biological section
  this ticket must update once the new branch lands.
- `docs/mechanics/01_entity_anatomy.md` §4 "Biological Laws" — hunger/sleep-debt accrual rates and
  HP-damage thresholds (unaffected by this ticket, which only adds detection, not the underlying
  formula).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE/investigation.md` — the
  empirical probe and root-cause trace this ticket's Request Summary is drawn from.

## Related Code Areas
- `src/systems/lifecycle_systems/lifecycle.py:189-205` — `resolve_lifecycle`'s two existing
  death-detection branches; the new branch belongs alongside these.
- `src/engine/apply.py:98-106` — `ApplyPath._compute_entity_changes`'s `total_passive_dmg` branch,
  the write site this ticket's new detection branch must observe (indirectly, via `combat.alive`
  and the absence of an existing `death_reason`), not modify.
- `tests/mechanic_scenarios/test_natural_aging_old_age_dispatch.py::
  test_starvation_sleep_debt_driven_hp_loss_is_still_silent_post_fix` — the pinned pre-fix
  signature this ticket's own fix must update.

## Assumptions / Open Questions
- **Death-reason string(s).** Whether to use a single `"STARVATION"`/`"BIOLOGICAL"` reason for both
  hunger- and sleep-debt-driven deaths, or distinguish them, is not pre-decided — real design
  choice for this ticket's own investigation/plan phase.
- **Detection mechanism shape.** Whether the new `resolve_lifecycle` branch should read
  `entity.combat.alive` (pre-tick, already `False` from a *prior* tick's passive write) or inspect
  something staged this same tick is an implementation detail for the investigation phase to
  resolve against the real phase-ordering trace, not assumed here.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._

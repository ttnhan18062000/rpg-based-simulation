---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION
phase: open
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION

## Title
Determine whether `BiologicalSystem.update()` is a dormant, never-wired "explicit passive decay" design that should be wired in — or genuinely dead code to remove

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Found during `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION`'s trace of the real
passive-decay mechanism: `src/systems/biological_system.py`'s `BiologicalSystem.update()` is a
**different**, explicit-`EntityUpdate`-producing biological decay implementation
(`ent_upd.biological.hunger_delta`, `ent_upd.combat.hp_delta` — see its own test,
`tests/unit/core/test_biological.py`) from the mechanism the live pipeline actually uses
(`src/engine/apply.py`'s `_compute_entity_changes`, an apply()-time-only "candidates" fallback that
never produces an `EntityUpdate` at all). A repo-wide grep
(`grep -rln "BiologicalSystem" src/ tests/`) finds `BiologicalSystem.update()` called from **nowhere**
in `src/engine/` or anywhere else in the live pipeline — only its own module and its own test
reference it.

**This is more consequential than a typical "harmless dead code" finding** (per the base-rate
argument this session already applied to `TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION`, and
per peer review `rpg-feature-planning`'s explicit escalation of this one specifically): if
`BiologicalSystem.update()` is the original intended "promote passive decay to a real,
dirty-set-visible `EntityUpdate`" design that simply never got wired into the pipeline, then
wiring it in (or reproducing its design inline) would make the entire class of read-model
staleness found in `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` disappear at the
source — passive decay would flow through the normal `update.entity_updates` →
`DirtySetBuilder.mark_from_update()` path like every other domain, with no special-casing needed
anywhere (including in `ReadModelCache`, the confirmed-affected consumer).

## Scope
- Determine whether `BiologicalSystem.update()` was ever wired into `src/engine/pipeline.py` (check
  git history / `git log -p` / `git blame` for the module and for the apply.py passive-decay
  branch, to establish which came first and whether one was meant to supersede the other) or was
  always a parallel, never-integrated design.
- Compare the two mechanisms' actual decay formulas (`BiologicalSystem.update()`'s
  `hunger_delta`/`sleep_debt_delta`/`hp_delta` math vs. `apply.py`'s `_compute_entity_changes`
  passive branch) for behavioral parity — if they diverge, wiring the dormant one in would be a
  real behavior change, not just an architecture change.
- Record a disposition: **remove** `BiologicalSystem.update()` (confirmed truly orphaned, no
  design intent to wire it, diverges materially from the real live formula so reviving it would be
  wrong anyway) or **flag for the follow-up `ReadModelCache` staleness fix ticket** as a real,
  considered fix-approach option (wiring it in eliminates the staleness at the source, at the cost
  of a materially bigger architectural change than a cache-local patch).
- This is a hotfix-tier disposition-only ticket, same as its `SPAWN-CALAMITY` precedent. Do not
  implement either the removal or the wiring here — record the disposition and, if "wire it in" is
  viable, hand it to the follow-up fix ticket as an explicitly considered option rather than
  implementing a competing fix in two places.

## Out of Scope
- Actually wiring `BiologicalSystem.update()` into the pipeline, or actually implementing the
  `ReadModelCache` staleness fix — both belong to the follow-up fix ticket once it has this
  disposition's finding to weigh.
- `apply.py`'s own passive-decay "candidates" fallback mechanism's own correctness — already
  confirmed working as designed by the investigation ticket; not reopened here.

## Acceptance Criteria
- [ ] Git history evidence for whether `BiologicalSystem.update()` was ever wired, or was always
      parallel/dormant.
- [ ] A real comparison of the two decay formulas, confirming or ruling out behavioral parity.
- [ ] A disposition (remove / flag-as-fix-option) recorded with rationale.
- [ ] If "remove": the dead method and its own test are deleted, verified via the existing
      `tests/unit/core/` and `tests/unit/systems/` suites passing unchanged.
- [ ] If "flag-as-fix-option": this ticket closes with that recorded, and the follow-up
      `ReadModelCache` staleness fix ticket's own investigation/plan phase must reference this
      ticket and explicitly accept or reject the wiring option before choosing its own approach.

## Related Tickets
- `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` (origin of this finding)
- `TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION` (precedent: same disposition-ticket pattern
  for a different "harmless dead code" finding)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/systems/biological_system.py` (`BiologicalSystem.update()`)
- `src/systems/lifecycle_systems/biological.py` (referenced alongside it in the original grep;
  check whether this is a third related module or the same dormant design)
- `src/engine/apply.py` (`_compute_entity_changes`'s passive branch — the real, live mechanism to
  compare against)
- `src/api/read_model_cache.py` (the confirmed-affected consumer this disposition informs)

## Assumptions / Open Questions
- Whether the two decay mechanisms were ever meant to coexist (e.g. one is a legacy V1 holdover,
  the other its V2 replacement) or represent an incomplete migration is the central question —
  not assumed either way here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_

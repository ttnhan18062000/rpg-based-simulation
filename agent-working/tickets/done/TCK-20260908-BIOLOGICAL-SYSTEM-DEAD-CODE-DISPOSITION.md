---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION
phase: done
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION

## Title
`BiologicalSystem.update()` confirmed superseded by `apply.py`'s live passive decay — deleted

## Status
DONE

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
- [x] Git history evidence for whether `BiologicalSystem.update()` was ever wired, or was always
      parallel/dormant. Confirmed always dormant, and independently flagged before this audit:
      `TCK-20260831-CREATURE-TERRITORY-LIFECYCLE`'s own commit message (2026-08-31,
      `a2954cfaa`) states "Investigation found the ticket's own premise about BiologicalSystem's
      HERO/VILLAGER gate was wrong -- that gate is dead code; the design is purely additive
      instead, no divergence entry needed." — a prior, unrelated ticket already discovered the gate
      was inert and routed around it rather than wiring `BiologicalSystem.update()` in.
- [x] A real comparison of the two decay formulas, confirming divergence, not parity. Live
      (`apply.py:89-100`): hunger `+0.1 * cadence.biological`, sleep_debt `+0.05 *
      cadence.biological`, HP penalties at `hunger >= 95.0` / `sleep_debt >= 98.0`, applied to
      **every** entity kind with an active/due lifecycle (no kind gate — `biological` is a
      default-populated component on every `EntityState`). Dead (`BiologicalSystem.update()`):
      flat `0.5%`/`0.3%` per-tick decay, HP penalties at `90`/`95`, gated to HERO/VILLAGER kinds
      only. Confirms the Mechanics Bible's own documented rates
      (`docs/mechanics/01_entity_anatomy.md` §4: `+0.1`/`+0.05`, `95.0`/`98.0`) already match the
      live formula exactly, not the dead one — the Bible was always written against the real path.
- [x] Disposition: **remove**. Confirmed superseded (not missing/unwired), confirmed materially
      divergent (different numbers, different applicability scope), confirmed pre-flagged as dead
      by an unrelated prior ticket. Explicit peer sign-off given (2026-09-11) after this audit's
      own drift finding: wiring the dead formula in would have silently changed decay rates and
      death thresholds across the simulation.
- [x] Removed: `src/systems/lifecycle_systems/biological.py` (the class), `src/systems/
      biological_system.py` (its re-export shim), `tests/unit/core/test_biological.py` (entirely
      orphaned by the deletion — both its tests exercised only `BiologicalSystem.update()`).
      Verified via a direct repo-wide grep for `BiologicalSystem`/`biological_system` before and
      after deletion (zero remaining references), and via `tests/unit/cognition/`, `tests/unit/
      core/`, `tests/unit/world/` passing unchanged post-deletion.
- [x] `docs/simulation/lifecycle_systems_contract.md`'s "Biological" section — previously described
      the now-deleted `BiologicalSystem.update()` as the live mechanism, with its stale numbers —
      corrected to describe the real live `apply.py` mechanism, its real formula, and its real
      (broader-than-documented) applicability scope. Not originally in this ticket's own Scope, but
      required: deleting code a doc describes as authoritative-and-live without correcting the doc
      would leave the doc pointing at nothing.

## Related Tickets
- `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` (origin of this finding)
- `TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION` (precedent: same disposition-ticket pattern
  for a different "harmless dead code" finding)

## Related Docs
- `docs/simulation/lifecycle_systems_contract.md` (Biological section corrected to describe the
  real live `apply.py` mechanism)
- `docs/mechanics/01_entity_anatomy.md` §4 (Certified Level 1 authoritative — already matched the
  live formula, confirming it not the dead one)
- `docs/audits/unreachable_code_inventory.md` (origin of the drift finding that prompted deletion)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/systems/biological_system.py` — deleted (`BiologicalSystem.update()`'s re-export shim)
- `src/systems/lifecycle_systems/biological.py` — deleted (the class itself)
- `src/engine/apply.py` (`_compute_entity_changes`'s passive branch — the real, live mechanism)
- `src/api/read_model_cache.py` (the consumer `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-
  INVESTIGATION` found affected — unaffected by this deletion, since the dead code was never in
  its path)

## Assumptions / Open Questions
- Whether the two decay mechanisms were ever meant to coexist (e.g. one is a legacy V1 holdover,
  the other its V2 replacement) or represent an incomplete migration is the central question —
  not assumed either way here.
- **Sharpened (2026-09-11), per peer review during `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`**:
  confirmed directly that `src/engine/apply.py:89-100` genuinely does its own live, apply-time
  passive hunger/sleep-debt decay (`hunger += 0.1 * cadence.biological`,
  `sleep_debt += 0.05 * cadence.biological`, HP penalties at 95/98 thresholds) — a real, wired
  mechanism doing the same job as `BiologicalSystem.update()`'s own hunger/sleep-debt decay (0.5%/
  0.3% per tick, HP penalties at 90/95). Different specific numbers, same job. This is now a
  second confirmed instance (alongside `spawn_calamity()` vs. `CalamityService.
  process_world_dynamics()`, and the broader `src/domains/optimization/` package vs.
  `ResourceGovernor`/`GovernorPolicy`) of the SAME shape across this codebase: **a superseded
  earlier implementation left alongside its live replacement, not a missing/unwired feature.**
  Does not settle this ticket's own Acceptance Criteria on its own (still need the exact formula-
  parity comparison and git-history check this ticket's own Scope already calls for), but
  materially raises confidence toward the "remove" disposition over "flag as fix option."

## Implementation Notes
Confirmed the deletion target's full footprint before touching anything: `grep -rn
"BiologicalSystem" --include="*.py" .` found exactly 3 references — the class definition, its
one-line re-export shim, and its own dedicated test file — nothing else, in `src/` or `tests/`.
Deleted all three. Found and read the `TCK-20260831-CREATURE-TERRITORY-LIFECYCLE` commit
(2026-08-31, predates this whole audit arc) independently confirming the HERO/VILLAGER gate was
already known dead at that time, closing this ticket's own git-history AC with real evidence
rather than inference.

Discovered while comparing formulas: `apply.py`'s live decay has no entity-kind gate at all
(`biological` is default-populated on every `EntityState`, and `_compute_entity_changes` applies
no kind filter) — broader in scope than either the dead code or the doc claimed, not just
different in rate. Corrected `docs/simulation/lifecycle_systems_contract.md`'s Biological section
to state this explicitly, since the previous text ("Only HERO and VILLAGER... Monsters and NPCs do
not have biological needs") was itself wrong about the live system, not just about which module
implements it.

## Test Summary
- `pytest tests/unit/cognition/test_information_seeking.py tests/unit/core -q` — 307 passed
  (confirms the sibling `effective_certainty()` deletion in the same PR didn't break anything
  cognition-adjacent, and that `tests/unit/core/` has no other reference to the deleted module).
- `pytest tests/unit/world/test_calamity_raid.py tests/unit/world/test_stronghold.py
  tests/unit/world/test_world_dynamics.py -q` — 17 passed.
- `pytest tests/refactor/test_import_compatibility.py -q` — 3 passed.
- Final sweep: `grep -rn "BiologicalSystem\|biological_system" --include="*.py" .` — zero hits.

## Files Changed
- `src/systems/lifecycle_systems/biological.py` — deleted
- `src/systems/biological_system.py` — deleted
- `tests/unit/core/test_biological.py` — deleted (entirely orphaned by the class deletion)
- `docs/simulation/lifecycle_systems_contract.md` — Biological section rewritten to describe the
  real live `apply.py` mechanism (formula, thresholds, and true kind-agnostic applicability);
  `last_verified` bumped

## Completion Summary
Confirmed via direct code comparison (not the audit tool's own output, which cannot see this pair
at all due to the generic-method-name collision limitation) that `BiologicalSystem.update()` and
`apply.py`'s live passive decay do the same job with materially different numbers and different
applicability scope — a superseded implementation, not a missing/unwired one. Independently
corroborated by an unrelated 2026-08-31 ticket's own commit message, which had already found the
same gate dead and routed around it. Deleted the class, its shim, and its now-fully-orphaned test
file; corrected the one doc (`lifecycle_systems_contract.md`) that described the dead code as the
live mechanism, using numbers that had already drifted from what actually runs. The Mechanics
Bible itself needed no correction — it was already written against the real live formula.

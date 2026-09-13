# Investigation — TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS

## Pre-pickup Scope correction (already committed separately in PR A / #174)
Before starting this ticket, updated its own Scope: `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-
DISPOSITION` closed via PR #163 — `BiologicalSystem.update()` was confirmed a superseded
implementation (not missing/unwired) and deleted outright. The "weigh wiring the dormant system
in" alternative this ticket's Scope required reading first no longer exists. The cache-local fix
below is the only real option, not a fallback contingent on that disposition.

## Confirming the real data flow (read-only trace before any edit)
Traced exactly what `ApplyPlanBuilder.build_plan()` (`src/engine/apply_plan.py:293-365`) and
`ApplyPath.apply_generation()` (`src/engine/apply.py:189-509`) already compute:

- `plan.dirty_tags_by_entity` is populated for every entity with a real component change,
  including passive-decay-only entities — the `candidates` set (`apply_plan.py:298-315`) includes
  `prior_state.entities.keys()` whenever biological/lifecycle cadence is due (or a hazard/stamina
  condition), not just `update.entity_updates.keys()`.
- `apply_generation()` (`apply.py:264-265`) already feeds every one of those tags into a local
  `dirty_builder: DirtySetBuilder` via `mark_entity()`. But `dirty_builder.build()` — the real,
  apply-time-computed `DirtySet` — was only ever assembled and surfaced (`apply.py:274-279`, prior
  to this fix) if the caller passed a truthy `audit_dirty_set` collector. No real caller does:
  grepped every `apply_generation(` call site (`scenario_runner.py:114`, `kernel.py:757`,
  `kernel.py:811`, `apply.py:514`, `apply.py:520`) — none passes `audit_dirty_set`. The correct,
  already-computed dirty set was silently discarded on every real tick.
- `apply_generation()` returns a bare `AuthoritativeState`, nothing else. `engine_manager.py`'s
  `_update_latest_state()` never calls `apply_generation()` itself — it reads
  `kernel.status.dirty_set` (the pre-apply, `update.entity_updates`-only set) and feeds that
  directly into `ReadModelCache.update()`. The real, correct apply-time dirty set never reached the
  cache by any path.

## Plumbing decision (brought to peer review before implementing, per standing instruction)
Proposed and got explicit approval for: a **separate channel** for `ReadModelCache`, not a
widening of `update.dirty_set`'s own meaning (which `PhaseDependencyGraph`'s skip logic and the
movement cache both rely on staying pre-apply-scoped — confirmed benign by the originating
`TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION`'s Consumer #1 finding, not to be
reopened here).

Peer review corrected one detail in the initial proposal: `_readonly_entities_cache` (the
precedent pattern cited) is not an undeclared attribute stashed post-construction — it is a real
declared dataclass field (`src/core/state.py:1316`,
`field(default=None, repr=False, compare=False)`), reset in `__post_init__`
(`state.py:1433`/now alongside the new field), and then explicitly repopulated after construction
via `object.__setattr__` where the real value is known. An undeclared attribute set only
post-construction is discoverable only by grep, has no default, and disappears silently if
anything reconstructs the state via `replace()` without explicitly carrying it forward — exactly
how `places` was lost for every tick in every mode until `TCK-20260908-HOTFIX-STATE-PLACES-APPLY-
CARRYFORWARD-GAP`. Followed the precedent completely: declared `_apply_time_dirty_set` as a real
field with the same shape, reset by default in `__post_init__`, and carried forward explicitly by
`to_readonly()`'s own `replace(self, ...)` call (`state.py:1527`) alongside the other cache fields
that pattern already carries — a carry-forward this ticket's fix would otherwise have silently
missed, the same failure class as `places`.

Also per peer review: `ReadModelCache` reads `state._apply_time_dirty_set` directly rather than
`getattr(state, "_apply_time_dirty_set", None)` — since it is now a declared field with a default,
direct access is always safe and fails loudly (an `AttributeError`) if the field is ever removed,
instead of silently reverting to stale-cache behavior.

## Why not a return-type change
Considered surfacing the dirty set as part of `apply_generation()`'s own return value instead of a
state field. Peer review counted five real call sites (`scenario_runner.py:114`, `kernel.py:757`,
`kernel.py:811`, `apply.py:514`, `apply.py:520`), not the three assumed initially — a return-type
change would touch all five plus every test constructing a mock/stub around the current
`AuthoritativeState`-only return contract. The declared-field approach gives the same
discoverability (a real field, not a hidden stash) with zero call-site changes.

## Fix implemented
1. `src/core/state.py`: declared `_apply_time_dirty_set: Any = field(default=None, repr=False,
   compare=False)` alongside the other derived-cache fields; added its reset to `__post_init__`
   (so any construction path other than `apply_generation()` never carries forward a stale,
   differently-scoped value); added it to `to_readonly()`'s own explicit carry-forward list.
2. `src/engine/apply.py`: `dirty_builder.build()` is now always computed (previously conditional
   on `audit_dirty_set`), and the result is stashed onto `new_state` via `object.__setattr__`
   immediately after construction — same post-construction pattern already used for
   `_readonly_entities_cache` two lines above.
3. `src/api/read_model_cache.py`: `ReadModelCache.update()` and `compute_tick_delta()` both union
   `state._apply_time_dirty_set.all_dirty_entities` into their computed dirty-id set (when present
   and not already doing a full scan) as a second, independent source. `dirty_set`'s own type and
   `ReadModelInvalidationPolicy.get_dirty_entity_ids()` are untouched — the union happens locally
   in each `ReadModelCache` method, reading a second parameter already in scope (`state`), not by
   widening what `dirty_set` itself means to any other consumer.

## Scope discipline
Did not touch `update.dirty_set`'s own publication semantics, `DirtySetBuilder.mark_from_update()`,
or `PhaseDependencyGraph`'s skip logic — exactly as this ticket's own Scope required. Did not
implement `apply_plan.py`'s own `invalidate_read_model` hint field (confirmed dead by the
originating investigation, grep-only reference in a stale comment) — out of scope, a separate
finding if anyone wants it filed.

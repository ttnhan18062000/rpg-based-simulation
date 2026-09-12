# Plan — TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS

## Disposition (peer-reviewed plumbing shape, approved before implementing)
Give `ReadModelCache` a supplementary, apply-time-computed invalidation-id source, independent of
`update.dirty_set`'s own publication semantics. Implemented as a declared, non-authoritative field
on `AuthoritativeState` (`_apply_time_dirty_set`), following the exact precedent of
`_readonly_entities_cache` — not a return-type change to `apply_generation()` (peer review found
five real call sites, making that materially more invasive) and not an undeclared post-construction
attribute stash (the precise failure class that lost `places` for every tick until a prior hotfix).

## Steps
1. `src/core/state.py`: declare `_apply_time_dirty_set: Any = field(default=None, repr=False,
   compare=False)`; reset it in `__post_init__`; carry it forward explicitly in `to_readonly()`'s
   own `replace(self, ...)` alongside the other cache fields that pattern already carries.
2. `src/engine/apply.py`: compute `dirty_builder.build()` unconditionally (previously gated behind
   an `audit_dirty_set` collector no real caller passes); stash it onto `new_state` via
   `object.__setattr__` right after construction, mirroring `_readonly_entities_cache`'s own
   post-construction assignment two lines above.
3. `src/api/read_model_cache.py`: `update()` and `compute_tick_delta()` both union
   `state._apply_time_dirty_set.all_dirty_entities` into their locally-computed dirty-id set
   (direct attribute access — the field always exists once declared) when present and not already
   doing a full scan. `ReadModelInvalidationPolicy.get_dirty_entity_ids()` and `dirty_set`'s own
   type are untouched.
4. Update `tests/unit/engine/test_dirty_set_passive_decay_consumers.py`'s
   `test_consumer_2_read_model_cache_serves_a_stale_dto_confirmed_bug` to assert the fix (renamed
   `test_consumer_2_read_model_cache_invalidates_passive_decay_only_change`, per this repo's "no
   process labels in identifiers" convention — name for what the code does, not the ticket).
5. Run the ticket's own named regression scope (`tests/unit/api/test_read_model_cache.py`,
   `tests/unit/domains/optimization/test_phase_dependency_graph.py`, `tests/unit/engine/`) plus a
   broader sanity sweep (`tests/unit/core/`, `tests/unit/api/`, determinism/replay suites) since
   this touches `AuthoritativeState`'s own dataclass shape and `apply_generation()`'s own hot path.

## Guardrails
- Do not touch `update.dirty_set`'s own publication semantics, `DirtySetBuilder.mark_from_update()`,
  or `PhaseDependencyGraph`'s skip logic — Consumer #1 from the originating investigation is
  confirmed benign; this fix must not reintroduce risk there.
- Do not implement `apply_plan.py`'s own `invalidate_read_model` hint field — confirmed dead by the
  originating investigation; a separate finding if anyone wants it revisited, not this ticket's job.
- `_apply_time_dirty_set` must default to `None` and reset on every construction other than
  `apply_generation()`'s own explicit population — never carry forward a stale value from a
  differently-scoped state, which would be worse than the original staleness bug (wrong-entity
  invalidation instead of missing-entity invalidation).

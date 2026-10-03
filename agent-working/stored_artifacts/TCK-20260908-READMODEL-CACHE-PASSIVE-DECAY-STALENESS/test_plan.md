# Test Plan — TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS

## Real evidence
- `tests/unit/engine/test_dirty_set_passive_decay_consumers.py`'s own repro test updated to assert
  the fix: `test_consumer_2_read_model_cache_invalidates_passive_decay_only_change` — real pipeline
  + real `apply_generation()`, an entity whose only per-tick change is passive biological decay
  (already dead in combat, `lifecycle.active` cleanup pending), confirms `next_state.
  _apply_time_dirty_set` genuinely contains the entity while the published pre-apply `dirty_set`
  stays empty (unchanged from before the fix — other consumers see exactly what they saw), and that
  `ReadModelCache.get_entity_dto()` now correctly returns a fresh DTO reflecting the real accrued
  hunger instead of serving the stale pre-tick snapshot.
- Sibling control test `test_consumer_2_full_scan_or_explicit_dirty_tag_avoids_the_staleness` left
  unchanged and still passing — confirms the fix doesn't alter `force_full_scan` behavior.
- `test_consumer_1_phase_shortcircuit_is_confirmed_benign_not_a_bug` left unchanged and still
  passing — confirms this fix doesn't touch or reopen the originating investigation's other,
  already-confirmed-benign finding.

## Regression suites run
- `tests/unit/engine/test_dirty_set_passive_decay_consumers.py` — 4 passed (all 4, including the
  updated one).
- `tests/unit/api/test_read_model_cache.py`, `tests/unit/domains/optimization/
  test_phase_dependency_graph.py`, `tests/unit/engine/` (the ticket's own named AC scope) — 231
  passed, 1 skipped.
- `tests/unit/core/test_authoritative_state_contract.py`, `tests/unit/engine/
  test_hash_scheduler.py` — 24 passed (the new declared field's shape/determinism-neutrality).
- `tests/unit/core/`, `tests/unit/api/` (broader sanity sweep, since this touches
  `AuthoritativeState`'s own dataclass shape and `apply_generation()`'s hot path) — 305 passed.
- `tests/integration/kernel/test_determinism_suite.py`, `tests/unit/kernel/
  test_replay_determinism.py` (`-m "not slow and not extra_slow"`) — 5 passed. Confirms the new
  field (declared `compare=False`, excluded from `CanonicalStateHasher.to_canonical_data()`'s
  explicit field enumeration per peer review) does not affect the determinism hash.

## Acceptance criteria mapping
- `BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`'s finding read and weighed before choosing a fix
  approach → satisfied by the 2026-09-12 pre-pickup Scope update (PR A / #174): that ticket closed
  via PR #163, so there was nothing left to weigh — the cache-local fix is the only real option.
- A real fix implemented that makes `ReadModelCache` correctly invalidate passive-decay-only
  changes, without widening `update.dirty_set`'s own semantics → done; `update.dirty_set`'s type
  and every other consumer's read of it are byte-for-byte unchanged.
- Real test evidence: the existing repro test updated and passes → done.
- No regression in the three named suites → confirmed, all pass.

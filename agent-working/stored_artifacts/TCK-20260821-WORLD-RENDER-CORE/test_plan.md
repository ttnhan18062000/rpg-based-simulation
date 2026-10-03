---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-WORLD-RENDER-CORE
artifact_type: test_plan
tags: [rendering, world, determinism]
---

# Test Plan — TCK-20260821-WORLD-RENDER-CORE

## Regression Surface

No existing test suite currently imports anything under `experiments/spatial_rendering/prototype/`
or a `src/rendering/` package (neither exists yet as a tested import target — confirmed no test
file references `png_writer`, `render_world`, or `render_incremental`). This ticket is additive, so
the regression surface is about **not breaking the things this ticket touches by reuse**, not about
re-running unrelated suites.

- **unit** — `tests/unit/observability/test_retention_manager.py` (all 3 tests: must keep passing
  unmodified — this ticket must not touch `retention.py`, and these tests are the existing proof
  that `RetentionPolicy.classify_run`/`RetentionManager.generate_cleanup_plan`/`execute_cleanup`
  behave as documented, which this ticket's own new retention-integration test builds on).
- **unit** — `tests/unit/observability/reporting/test_phase27_behavior_artifact_paths.py` (same
  `RunArtifactRepository`/`RetentionManager` area — keep passing unmodified).
- **unit** — `tests/unit/core/` (any test touching `AuthoritativeState`/`EntityState`/`DirtySet`
  construction, e.g. anything using `V2EntityBuilder` — this ticket reads but must never mutate
  these types).
- **perf** — `tests/perf/test_dirty_parity.py`, `tests/perf/test_dirty_set_integrity.py` — this
  ticket is a new *consumer* of `DirtySet`, not a modifier of it; these existing tests are the
  proof that `DirtySet`'s own semantics (`movement_entities`, `lifecycle_entities`, etc.) remain
  correct and this ticket can safely trust them.
- **unit** — `tests/unit/worldbuilding/test_world_repository.py`,
  `tests/unit/worldbuilding/test_*compiler*` (if present) — this ticket must not touch
  `src/worldbuilding/compiler.py` at all (terrain-casing fix is explicitly out of scope); these
  tests prove the compiler's terrain-painting behavior this ticket only *reads* is unaffected.

## New Tests Required

1. **`test_render_produces_valid_png`**
   - Category: unit
   - Verifies: `render(state, out_path)` (for a small synthetic `AuthoritativeState` built via
     `V2EntityBuilder`, following `tests/unit/worldbuilding` / `tests/unit/core` conventions —
     no real `WorldRepository`/`WorldCompiler` load needed for this test) writes a file at
     `out_path` whose first 8 bytes match the PNG signature (`b"\x89PNG\r\n\x1a\n"`), and whose
     IHDR chunk declares dimensions matching the entity/terrain bounding box × scale. Also asserts
     the file is non-empty and parses as a well-formed PNG (walk the chunk structure: IHDR, at
     least one IDAT, IEND with correct length prefixes / CRC32s — this is cheap to hand-verify
     without a new dependency, mirroring `png_writer.write_png`'s own chunk-building logic).
   - Location: `tests/unit/rendering/test_render_core.py`

2. **`test_render_golden_hash_bit_identical_across_three_independent_runs`**
   - Category: unit (architecture-guard-flavored — pins a determinism guarantee, same spirit as
     `tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py`)
   - Verifies: build (or load) the **same** `AuthoritativeState` three independent times (three
     separate `render()` calls, ideally against three independently-constructed state objects that
     are content-equal, not the same Python object reused, to actually exercise
     iteration-order-independence — not just "call the same function three times on one object").
     For each, call `render(state, out_path_i)`, then `hashlib.sha256(Path(out_path_i).read_bytes())
     .hexdigest()`. Assert all three hashes are exactly equal. This is the ticket's headline AC —
     do **not** substitute `state_hash`/`state.tick`-based equality for this (per investigation.md's
     Prior Work section: `state.terrain` is excluded from both `StateFingerprinter` and
     `CanonicalStateHasher`, so a state-hash-based test would not actually prove render
     correctness). Hash PNG bytes directly.
   - Location: `tests/unit/rendering/test_render_core.py` (or a dedicated
     `tests/architecture/test_world_render_determinism_guard.py` if the implementer prefers to
     mirror the existing architecture-guard style/location — either is acceptable, pick one and be
     consistent).

3. **`test_dirty_set_incremental_render_pixel_identical_to_full_rerender`**
   - Category: unit / architecture guard
   - Verifies: tick a real (or synthetic multi-tick) kernel forward N ticks, capturing
     `kernel._status.dirty_set` per tick (falls back to a full-scan candidate set when absent, per
     `src/core/dirty.py`'s own `get_relevant_entity_ids` convention — the renderer must mirror this
     fallback, not assume `dirty_set` is always present). Render the final state two ways: (a) via
     `IncrementalRenderer`-equivalent DirtySet-filtered updates applied incrementally tick-by-tick,
     (b) via a full non-incremental `render()` call against the same final state. Assert the two
     resulting pixel buffers (or PNG byte content, if draw order is fully pinned — see
     investigation.md's Anti-Drift Hazards on cross-collection draw order) are pixel-identical, not
     merely close/similar. This is the ticket's second headline AC and the direct regression guard
     against an under-scoped DirtySet domain union (investigation.md Risk #3) — if the implementation
     picks too narrow a `dirty_set` field union (e.g., missing a field whose change affects a pixel),
     this test is what catches it.
   - Location: `tests/unit/rendering/test_render_incremental.py`

4. **`test_terrain_casing_normalized_with_loud_fallback`**
   - Category: unit
   - Verifies three sub-cases against the render-boundary color lookup directly (not the whole
     `render()` pipeline, to keep this test fast and precise):
     (a) `"PLAIN"` and `"plain"` (and ideally `"Plain"`) all resolve to the *same* color —
     proving case-insensitive normalization, not two colliding colors;
     (b) a real known-vocabulary value like `"forest"`/`"FOREST"` resolves correctly regardless of
     input case;
     (c) a genuinely unrecognized string (e.g. `"NOT_A_REAL_TERRAIN"`) resolves to the loud
     fallback color, and that fallback color is visibly distinct from every entry in the known
     terrain-color table (assert it, don't just eyeball it — e.g. assert it's not equal to any
     value in the color-table dict) — this directly enforces AC #6's "not silently mismapped"
     requirement.
   - Location: `tests/unit/rendering/test_terrain_color_normalization.py`

5. **`test_render_writes_under_data_runs_run_id_renders_directory`**
   - Category: integration
   - Verifies: calling the renderer's storage-integration entrypoint (however
     `render(state, out_path)` is wired to `data/runs/{run_id}/renders/`) actually creates the file
     at `data/runs/{run_id}/renders/<expected-name>.png`, using a `tmp_path`-scoped fake
     `RunArtifactRepository.base_dir` (same mocking pattern as
     `tests/unit/observability/test_retention_manager.py`'s `test_retention_manager_generate_plan`)
     — never write into the real `data/runs/` during tests.
   - Location: `tests/unit/rendering/test_render_storage_integration.py`

6. **`test_renders_directory_not_pruned_by_normal_expiry_but_removed_with_full_run_purge`**
   - Category: integration (this is the test that resolves investigation.md's flagged Risk #1 —
     it tests actual `retention.py` behavior rather than the AC's optimistic phrasing)
   - Verifies, against the **real, unmodified** `RetentionManager.execute_cleanup()`:
     (a) create a `tmp_path`-scoped fake run directory containing a `renders/` subfolder with a PNG,
     an old `started_at` (forces `is_expired=True`, mirroring
     `test_retention_manager_execute_cleanup`'s existing pattern), and `status="COMPLETED"`;
     (b) call `execute_cleanup()`; (c) assert the named telemetry files get removed (existing
     behavior, unchanged) **and** assert `renders/` **still exists** afterward (documents the real,
     current gap rather than silently asserting the AC's literal wording, which the code cannot
     satisfy without modifying `retention.py` — see investigation.md Risk #1);
     (d) separately, construct a *corrupted* run (missing `run_manifest.json`) containing a
     `renders/` subfolder, call `execute_cleanup()`, and assert the entire run directory —
     `renders/` included — is gone (`shutil.rmtree` path, `retention.py:186-190`). Together these
     two sub-assertions give an honest, code-verified regression guard for exactly what
     `RetentionPolicy`/`RetentionManager` actually do with a `renders/` subfolder today, instead of
     asserting an unverified claim. **If the planner/implementer instead decides AC #4 requires
     `retention.py`'s hardcoded file list to be extended, this test must be rewritten accordingly —
     do not silently downgrade this AC's coverage without documenting the decision.**
   - Location: `tests/unit/observability/test_retention_manager.py` (co-locate with the existing
     retention tests, since it exercises the same `RetentionManager`, not a new module) or
     `tests/unit/rendering/test_render_retention_integration.py` if the implementer prefers to keep
     all render-related tests under one directory — either is acceptable.

7. **`test_render_does_not_mutate_authoritative_state`**
   - Category: architecture guard
   - Verifies: capture `state.terrain`/`state.entities`/`state.blocked_tiles`/`state.building_tiles`
     object identity (or a deep-equality snapshot) before calling `render(state, out_path)`, assert
     unchanged after. Directly enforces CLAUDE.md's Architecture Rule ("Decision logic reads state.
     It does not authoritatively mutate durable state") and the ticket's own "must not become a
     second source of truth... never mutates it" constraint from
     `docs/plans/world_rendering/idea_world_rendering_core.md:78`.
   - Location: `tests/unit/rendering/test_render_core.py`

8. **`test_render_no_new_third_party_dependency`**
   - Category: architecture guard (import-boundary style, mirrors
     `tests/architecture/test_phase18_import_boundaries.py`'s general shape)
   - Verifies: statically inspect the new `src/rendering/` module's imports (e.g. via `ast.parse` +
     walking `Import`/`ImportFrom` nodes, or a simple `inspect.getsource` substring check) and
     assert none of them are `numpy` or any other non-stdlib package. This is a cheap, permanent
     guard against a future "just use numpy, it's already installed" regression flagged in
     investigation.md Risk #4.
   - Location: `tests/architecture/test_rendering_zero_new_dependency_guard.py`

## Scoped Pytest Commands

```bash
# This ticket's own new tests
PYTHONPATH=. pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v

# Regression surface: retention (must stay green, unmodified retention.py)
PYTHONPATH=. pytest tests/unit/observability/test_retention_manager.py tests/unit/observability/reporting/test_phase27_behavior_artifact_paths.py -v

# Regression surface: DirtySet semantics this ticket depends on but must not modify
PYTHONPATH=. pytest tests/perf/test_dirty_parity.py tests/perf/test_dirty_set_integrity.py -v -m "not slow"

# Regression surface: worldbuilding compiler must be untouched by this ticket
PYTHONPATH=. pytest tests/unit/worldbuilding/ -v
```

Never `pytest tests/` — all commands above are scoped to the rendering domain plus the specific
reused subsystems (retention, dirty-set, worldbuilding-compiler) this ticket must not regress.

## Anti-Drift Test Guards

- **Test 8** (`test_render_no_new_third_party_dependency`) is the direct guard against the
  numpy-temptation drift flagged in investigation.md — it fails loudly the moment anyone imports a
  non-stdlib module into `src/rendering/`.
- **Test 6** guards against a silent, undocumented change to `retention.py` — if a future session
  is tempted to "just add `renders/*.png` to the hardcoded file list to make the AC literally true,"
  this test's two sub-assertions must both be re-derived and re-justified, not quietly patched to
  match new behavior without updating the ticket's own documented resolution of Risk #1.
- **Test 7** guards against the renderer becoming a second mutator of `AuthoritativeState` — the
  single most likely architecture violation for a new module that reads deeply nested entity/world
  fields (e.g. accidentally calling `state.entities[...]= ...` on a plain dict view instead of the
  read-only wrapper, or caching a mutable derived structure back onto the state object).
- **Test 4**'s sub-case (c) (unrecognized terrain → distinct loud color, not blended into an
  existing one) guards specifically against the tempting shortcut of mapping unknown values to
  `PLAIN`/`GRASS` "since that's probably what it meant" — which the ticket explicitly forbids
  ("not silently mismapped").
- **Regression-surface commands above, run before closing this ticket**, guard against any
  accidental edit creeping into `retention.py`, `dirty.py`, or `compiler.py` despite the ticket's
  explicit "unmodified"/out-of-scope constraints on all three.

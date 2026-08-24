---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT
artifact_type: test_plan
tags: [api-design, content]
---

# Test Plan — TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT

## Regression Surface

**Unit — presenter / content layer:**
- `tests/unit/api/test_state_presenter.py` (9 existing tests) — `present_map`/`present_static`/
  `_terrain_code_map` must stay byte-for-byte unchanged; this ticket must not modify
  `_terrain_code_map`'s signature or behavior, only reuse it (or replicate its exact logic) from a
  new call site. If the manifest implementation needs `_terrain_code_map` callable from outside
  `StatePresenter`, that's a widening of its visibility, not a behavior change — must not alter its
  existing return values for any existing test's fixtures.
- `tests/unit/content/test_catalog.py`, `tests/unit/content/test_layered_catalog.py` —
  `CatalogRepository.load_all()`/`_compute_fingerprint()`/`.fingerprint`/`.version` must keep their
  current contracts; this ticket only reads these, never modifies `CatalogRepository` itself.
- `tests/unit/content/test_content_usage_matrix.py` — unaffected (this ticket doesn't touch the
  content-resolution pipeline `world/terrain`'s row documents).

**Unit — API layer:**
- `tests/unit/api/test_read_model_service.py`, `tests/unit/api/test_read_model_cache.py`,
  `tests/unit/api/test_engine_manager.py`, `tests/unit/api/test_economy_route.py` — must stay green;
  none of these are touched by this ticket, but they share `src/api/` import surface with the new
  route/DI wiring, so a scoped run should include them as a regression net for `dependencies.py`
  changes (a new `set_catalog_repository`/`get_catalog_repository` pair is additive, but any typo in
  shared imports would break these first).

**Architecture guard:**
- `tests/architecture/test_api_read_model_guard.py` — the new manifest route file/handler must not
  import `AuthoritativeState`/`EntityState` outside `TYPE_CHECKING`; this guard will fail loudly if
  it does. Must stay green unmodified.

**Integration / REST parity:**
- `tests/api/test_rest_parity.py` — existing subprocess-server-based smoke test (`/health`,
  `/api/v1/state`, `/api/v1/control/pause`/`resume`). Must keep passing; this ticket's new route
  should not affect server startup (`create_v2_app()`/`lifespan()`), but the new `lifespan()`
  catalog-load step is exactly the kind of change that could break server boot if the catalog path
  resolution fails — this test's server-starts-successfully assertion is the cheapest real
  regression check for that failure mode.
- Other `tests/api/test_*.py` files using the direct-handler-invocation pattern (e.g.
  `test_decision_api.py`, `test_scenario_runtime_api.py`) are unaffected but confirm the established
  test-writing convention for the new tests below.

## New Tests Required

Per Acceptance Criteria (see `investigation.md`'s Risks section for the unresolved `terrain_types`
id-space design decision the implementation must make and document — these tests assume whichever
concrete design is chosen and must be adjusted to match it, not written blind ahead of that
decision):

1. **`test_manifest_returns_separate_protocol_and_dictionary_version`**
   - Category: unit (route/handler-level, direct invocation — no live server)
   - Verifies: response has both `protocol_version` and `dictionary_version` as distinct top-level
     keys, not a single combined `schema_version` field (AC #1).
   - Location: `tests/api/test_manifest_api.py` (new file, matching the existing
     `tests/api/test_<feature>_api.py` naming convention).

2. **`test_manifest_terrain_types_live_from_catalog_repository`**
   - Category: unit
   - Verifies: `terrain_types` values (display names) come from a live `CatalogRepository.terrain`
     lookup, not a hardcoded literal dict — assert changing a test-fixture catalog's `display_name`
     for a terrain id changes the manifest's output for that entry (mock/inject a `CatalogRepository`
     with controlled fixture data, don't rely on the real `data/content/` files for this assertion).
   - Location: `tests/api/test_manifest_api.py`.

3. **`test_manifest_terrain_types_id_space_matches_present_map_grid`**
   - Category: unit — the single most important new test for this ticket, directly exercising the
     open design question flagged in `investigation.md`.
   - Verifies: for a given `AuthoritativeState.terrain` fixture, every int code that
     `StatePresenter.present_map(state)`'s RLE grid actually emits has a corresponding key in the
     manifest's `terrain_types` dict for that same state (round-trip: decode the RLE grid's distinct
     values, assert each is a key in `terrain_types`). Must include a fixture containing `"PLAIN"`
     and/or `"GRASS"` (the real, confirmed-uncataloged default terrain values — see
     investigation.md's Risks section) to directly test the catalog-lookup-miss fallback path, not
     just the catalog-covered happy path.
   - Location: `tests/api/test_manifest_api.py` (or `tests/unit/api/test_state_presenter.py` if the
     terrain-code-to-manifest-entry logic ends up living alongside `_terrain_code_map` — location
     depends on where the implementation places this logic; the plan should pin this down).

4. **`test_manifest_entity_kinds_and_building_types_from_catalog`**
   - Category: unit
   - Verifies: `entity_kinds`/`building_types` are `{catalog_id: display_name}` projections of
     `CatalogRepository.entity_archetypes`/`.buildings` — assert against a small fixture catalog, not
     the full real content set, so the test doesn't silently pass/fail as real content data changes.
   - Location: `tests/api/test_manifest_api.py`.

5. **`test_manifest_dictionary_version_changes_with_catalog_fingerprint`**
   - Category: unit
   - Verifies: `dictionary_version` equals `catalog_repository.fingerprint` (or is deterministically
     derived from it) and changes when the fixture catalog's content changes across two calls; assert
     `protocol_version` stays constant across the same two calls (AC #3's two-part claim, tested as
     one test with two assertions since they're the same before/after comparison).
   - Location: `tests/api/test_manifest_api.py`.

6. **`test_manifest_location_types_decision_documented_behavior`**
   - Category: unit
   - Verifies: whichever `location_types` decision the plan documents (new minimal registry vs.
     explicit field drop) — if dropped, assert the field is either absent or an explicit empty/`None`
     marker (not silently omitted without a documented reason in the response or docs); if a minimal
     registry is added, assert it's populated live from that new source, matching the pattern used
     for the other three dictionaries.
   - Location: `tests/api/test_manifest_api.py`.

7. **`test_catalog_repository_di_wiring_loaded_once_at_startup`**
   - Category: architecture guard (asserts a load-performance/correctness property, not just a
     response shape)
   - Verifies: `get_catalog_repository()` returns the *same* object instance across two calls (proof
     it's a startup-time singleton per `dependencies.py`'s existing `set_x`/`get_x` pattern, not a
     fresh `CatalogRepository().load_all()` re-parse on every request — see investigation.md's
     Anti-Drift Hazards). Mirrors the existing pattern implicitly relied on by
     `get_engine_manager`/`get_quality_hub`, made explicit here since this is new plumbing.
   - Location: `tests/unit/api/test_dependencies.py` (new file — no existing test file covers
     `src/api/dependencies.py` directly; confirmed via `grep -rl dependencies tests/unit/api/` →
     no hits before this ticket) or `tests/api/test_manifest_api.py` if kept colocated.

8. **`test_manifest_route_does_not_import_authoritative_state`**
   - Category: architecture guard — a scoped, explicit companion to the existing repo-wide
     `test_api_read_model_guard.py` (that guard already runs against every file under
     `src/api/routes/`/`src/api/ws/`/`src/api/server.py`, so the new manifest route file is
     automatically covered once it exists — this entry documents that expectation rather than
     requiring a genuinely new guard).
   - Location: covered by the existing `tests/architecture/test_api_read_model_guard.py`; no new
     file needed, just confirm (during implementation) the new route lands under one of its
     `_API_ROOTS` paths so it's actually scanned.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/api/ tests/unit/api/ tests/unit/content/ tests/architecture/test_api_read_model_guard.py -v
```

Rationale for scope: `tests/api/` (new manifest route tests + REST parity regression),
`tests/unit/api/` (presenter/read-model/engine-manager/dependencies regression),
`tests/unit/content/` (CatalogRepository regression — this ticket reads it but must not change its
behavior), `tests/architecture/test_api_read_model_guard.py` (the one directly-relevant architecture
guard). Do not run the full `tests/` suite (per CLAUDE.md's Testing Rule) — this scope covers every
domain this ticket's `## Related Code Areas` touches (`src/api/server.py`, `src/content/repository.py`,
`src/content/schema.py`, `src/api/presenters/state_presenter.py`) plus its test-file counterpart
(`tests/api/test_rest_parity.py`, already inside `tests/api/`).

Frontend (no existing test runner convention confirmed in this investigation — if
`frontend/src/hooks/useSimulation.ts`'s new manifest fetch has a test harness, it should follow
whatever pattern (if any) already covers `loadInitial()`'s existing `/map`/`/static` fetches; none
was found to exist yet as of this investigation, so this is a gap to flag at Test phase, not
something this test plan can scope to a concrete existing command).

## Anti-Drift Test Guards

- **`test_manifest_terrain_types_id_space_matches_present_map_grid`** (New Test #3 above) is itself
  the primary anti-drift guard for this ticket's single riskiest area: it would immediately catch a
  regression where `terrain_types` silently reverts to a naive `CatalogRepository.terrain` string-id
  passthrough that no longer matches `present_map`'s int-coded grid — the exact failure mode
  `investigation.md`'s Risks section identifies as the central open design question.
- **New Test #7** (`test_catalog_repository_di_wiring_loaded_once_at_startup`) guards against a
  performance/correctness regression where a future edit accidentally reverts the manifest route to
  re-instantiating and re-`load_all()`-ing `CatalogRepository` per request (re-reading every YAML
  file under `data/content/` on every `/api/v1/manifest` call) — a silent perf regression that no
  shape-only response test would catch.
- **Existing `tests/unit/api/test_state_presenter.py`'s 9 tests**, run unmodified in this ticket's
  scoped command, guard against this ticket accidentally changing `_terrain_code_map`'s existing
  behavior while widening its call surface for manifest reuse.
- **`tests/architecture/test_api_read_model_guard.py`**, run unmodified, guards against the new route
  handler reaching for `AuthoritativeState` directly instead of going through
  `V2EngineManager`/`StatePresenter` — the concrete architecture-boundary risk this ticket's
  state-dependent `terrain_types` design surfaces (see investigation.md's Mechanics / Engine
  Constraints section).
- A **negative test on `colors.ts`/`GameCanvas.tsx`** is not applicable here (no test framework
  assertion can enforce "a file was not touched") — the anti-drift guard for that boundary is
  procedural (git diff review at Verify phase), not a pytest test.

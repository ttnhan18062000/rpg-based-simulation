PHASE_TS: 2026-06-27T13:40:48Z

# Investigation — TCK-20260627-P2N-DEGRADED-FALLBACK

## Current Behavior (file:line refs)

### Primary location — `src/core/registries.py`

The D02 §6.6 audit finding points to `src/domains/optimization/degradation.py` as the file, but
investigation reveals the actual location is **`src/core/registries.py`**:

- **Line 541**: `runtime_content_source: str = "legacy_hardcoded"` — module-level global default.
  This initialises the telemetry string before `seed_phase1_content()` runs.
- **Line 568**: `global runtime_content_source, catalog_fingerprint, fallback_usage_reported`
- **Line 619**: `runtime_content_source = "catalog"` — set when catalog is successfully used.
- **Line 732**: `runtime_content_source = "legacy_hardcoded"` — set when hardcoded fallback is
  used (LEGACY_FALLBACK path, catalog is None).
- **Line 740**: `seed_phase1_content(mode=RuntimeContentMode.LEGACY_FALLBACK)` — self-seeds on
  import; if `data/content/` absent, the hardcoded fallback activates and `runtime_content_source`
  stays `"legacy_hardcoded"`.

The D02 finding says the DEFAULT is `"legacy_hardcoded"`. This is confirmed at line 541. The
current code already sets it correctly after seeding, but the pre-seeding default is incorrect.

### `src/domains/optimization/degradation.py` — `GracefulDegradationManager`

This class manages **tick-time pressure** (NORMAL/CONSTRAINED/DEGRADED/CRITICAL) via
`update_pressure(tick_time_ms, limit_ms)` and controls phase skipping via
`should_skip_phase(phase_name)`. It has **no content-source selection logic**.

The ticket scope says to update this class to support catalog-driven content selection in
degraded mode. This is new behavior that does not exist today.

### `src/content/repository.py` — `CatalogRepository`

`CatalogRepository` exposes indexed dicts by content family: `self.items: Dict[str, ItemDefinition]`,
`self.resources: Dict[str, ResourceDefinition]`, etc.
`ItemDefinition` has `base_value: float` (line 297 of schema.py — cost field).
`ResourceDefinition` has `required_tool: Optional[str]` (line 243 — complexity/cost proxy).
No `get_lowest_cost_for_type()` method exists today.

### Existing strict mode

`src/core/modes.py:7`: `_FORBIDDEN_FALLBACK_MODES = frozenset({"catalog_strict", "catalog_with_compatibility"})`.
`seed_phase1_content()` raises `FallbackRestrictedError` for these modes when catalog is absent.
This covers AC3 (strict mode raises) in the existing code **for `seed_phase1_content`**.
`GracefulDegradationManager.resolve_content_source` does not exist yet, so strict mode there is new.

## Mechanics/Engine Constraints

- **WORLD-CAT-004** (`src/content/repository.py:L13`): `load_all()` must not be called inside a
  kernel tick. Content-source resolution must happen at bootstrap, not during ticks.
- `get_lowest_cost_for_type()` must therefore be a read-only, post-load accessor — no side effects.
- `GracefulDegradationManager.resolve_content_source()` must be callable before first tick (at
  bootstrap time), not inside `tick_once()`.

## Parity Ledger Overlap (IDs + status)

- **`infrastructure.yaml`** — no entry directly covering `runtime_content_source` global state or
  catalog-driven degraded fallback. A new entry will be required after implementation.
- **Nearest existing entry**: INFRA-019 (worker fallback) / INFRA-020 (deterministic ordering in
  local mode) — these are worker fallbacks, not content-source fallbacks. Separate concern.

## Prior Work

- `stored_artifacts/TCK-20260609-REGISTRY-BOOTSTRAP-MODES/` — investigated how bootstrap modes
  (CATALOG_STRICT, CATALOG_WITH_COMPATIBILITY, LEGACY_FALLBACK) are enforced in `bootstrap_registries`.
  Key finding from that work: strict mode guard already in `bootstrap_registries` via
  `HardcodedFallbackError`; the `seed_phase1_content` path received the same guard later.
- `tickets/done/TCK-20260619-PARITY-P0-BUGS.md` — unrelated (combat parity).
- `docs/guidelines/fallback_retirement_criteria.md` — all 9 criteria are now MET. Document says
  "retirement may proceed to TCK-20260610-FALLBACK-RESTRICT-MODES". Full retirement is out of scope
  for this ticket.

## Risks and Open Questions

1. **Typing import**: `GracefulDegradationManager` in `src/domains/optimization/degradation.py`
   would need to reference `CatalogRepository` from `src/content/repository.py`. Use
   `TYPE_CHECKING` guard to avoid circular imports.
2. **Return type of `get_lowest_cost_for_type`**: Returns `Dict[str, CatalogBaseDefinition]`
   subclasses. The caller (`GracefulDegradationManager.resolve_content_source`) is generic — it
   does not convert to registry types (adapters are not called here). This is intentional: the
   method is a catalog-level accessor, not a registry bootstrapper.
3. **Existing test `test_optional_fallback_mode`** checks `runtime_content_source == "legacy_hardcoded"`
   after a LEGACY_FALLBACK call with no catalog. The LEGACY_FALLBACK VALUE is unchanged; only the
   module-level DEFAULT at line 541 changes. This test will still pass.
4. **`test_seed_phase1_content_legacy_fallback_no_catalog_succeeds`** checks that LEGACY_FALLBACK
   with no catalog returns None (does not raise). This is unchanged.

## Anti-Drift Hazards

- Do NOT change the `LEGACY_FALLBACK` runtime value from `"legacy_hardcoded"` — only the
  module-level DEFAULT at line 541.
- Do NOT call `CatalogRepository.load_all()` inside any tick path.
- Do NOT break `_FORBIDDEN_FALLBACK_MODES` guard in `seed_phase1_content`.
- Do NOT remove the hardcoded fallback map from `seed_phase1_content` — out of scope.

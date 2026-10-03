# Test Plan — TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION

## Unit — `src/worldassembly/resolver.py`

- `_hash_point_in_bounds`: deterministic (same key + bounds → same point, across repeated calls);
  point always within `[min_x, max_x] x [min_y, max_y]`; different keys in the same bounds usually
  produce different points (not asserting uniqueness — the de-confliction layer's job).
- `_resolve_spawn_position`:
  - Unknown `spawn_region` (not in `region_bounds`) → returns `None` (falls through to
    `default_position` at the spawner).
  - Two calls with different keys, same region, no prior collision → both succeed, distinct points,
    both within bounds.
  - Two calls with different keys, same region, **forced collision** (monkeypatch
    `_hash_point_in_bounds` to return the same point for both, or use a 1x1-bounds region to force
    it deterministically) → second call returns a different point via the probe sequence, still
    within bounds.
  - Degenerate case: bounds too small for the probe sequence to find a free point (e.g. a true 1x1
    region with 3+ populations) → returns a point (documented fallback collision), does not raise.

## Integration — `CompileProfileResolver.resolve()`

- Real world composition using one of the 3 real-corpus modules identified in investigation.md
  (`bandit_road_trade_pressure`, `forest_warden_grove`, or `sunken_swamp_border` — two populations,
  one shared region) — assert both resulting `ResolvedEntityProfile.spawn_position` values are
  non-`None`, within that region's real bounds, and distinct from each other. This is the direct
  regression test for the "collisions are the expected case" finding — must use one of the real
  modules, not a synthetic one, so the test tracks real content behavior.
- A population whose profile is built via `ResolvedEntityProfile(...)` directly in a unit test
  (no `spawn_region` context) still has `spawn_position=None` — confirms the field is genuinely
  optional/backward compatible, not silently defaulted to `(0,0)`.

## `tests/integration/worldassembly/test_world_entity_spawner.py`

- Update/extend for the `spawn_position`-present case: a `ResolvedEntityProfile` with a real
  `spawn_position` set produces an `EntityState` at that position (not `default_position`).
- Confirm the existing `default_position` fallback path (profile with `spawn_position=None`) is
  unchanged — direct regression test for Step 3's one-line change.

## Real Campaign episode re-verification (the ticket's own AC)

- Delete `CampaignOrchestrator._scatter_catalog_entities()` and its call site.
- Re-run the same real, uninstrumented Campaign episode shape used in
  `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own verification (same world composition,
  same tick count). Assert:
  - Zero `LAW-OCCUPANCY-COLLISION` violations (`src/observability/hard_law_monitor.py`) — the
    ticket's own headline AC.
  - A plausible event-type mix (not dominated by proximity-gated `cooperation_event`/
    `contract_offer_created` the way the co-located-spawn baseline was).
- This must be a real run, not a unit test of the position values alone — matches this ticket's own
  AC wording and this repo's Testing Rule (prefer real, uninstrumented runs for this class of claim).

## Regression surface

- `tests/integration/worldassembly/` (full directory — position resolution touches the core
  compile-context construction path used by every consumer).
- `tests/unit/certification/`, `tests/integration/certification/` — per this ticket's own AC4.
- `tests/unit/domains/campaigns/`, `tests/integration/campaigns/` — the scatter-workaround deletion
  and the Campaign-mode re-verification.
- `tests/unit/domains/demographics/` if it exists — sanity check only; this ticket does not touch
  `population_cohorts`/count logic (that's the sibling ticket), but `region_bounds` construction
  touches the same `spec.regions` loop demographics indirectly depends on via `RegionState`.

Scoped pytest command (per CLAUDE.md's Testing Rule — not the full suite):
```
pytest tests/integration/worldassembly/ tests/unit/certification/ tests/integration/certification/ \
       tests/unit/domains/campaigns/ tests/integration/campaigns/ \
       -m "not slow and not extra_slow"
```

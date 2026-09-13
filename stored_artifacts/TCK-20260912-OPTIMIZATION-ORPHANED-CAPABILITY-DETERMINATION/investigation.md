# Investigation — TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION

## Real evidence per capability, checked before any disposition

1. **`should_skip_phase()`**: `pipeline.py` gates cooperation as `"ENABLE_SOCIAL_COOPERATION"`, not
   the `"ENABLE_COOPERATION"` this capability's own hardcoded list checks — a genuine name
   mismatch. `"ENABLE_LIFE_ARC_CAMPAIGNS"` matches no real phase or flag anywhere in `src/engine/`
   — zero grep hits. Only `ENABLE_WORLD_EMERGENCE` is still accurate. Even if wanted, 2 of 3 target
   names need real fixing before this could be revived as-is.
2. **`resolve_content_source()`**: the underlying `CatalogRepository.get_lowest_cost_for_type()`
   has zero real callers beyond this dead wrapper. No live content-resolution path branches on
   pressure level today.
3. **`get_provider_cap()`**: `PhaseBudgets` (the real, live budget dataclass this would extend)
   genuinely has no `provider_budget` field — a real structural gap. But "provider" as a
   rate-limited concept exists nowhere in live code; real providers do exist and run live
   (`src/world/providers/*`), just uncapped. Same underlying question as
   `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION` — answered once there,
   inherited here (see that ticket's own investigation.md).
4. **`cache_strategy.py`'s shop_stock/services/pressure caching**: `WorldIndexes` (the real spatial
   index dataclass) has no field for any of these. `shop_stock` and `regional_pressure` as literal
   concepts exist nowhere else in the codebase — no live Shop/Store class at all (only Guild
   concepts, a different thing).
5. **`dirty_scheduler.py`'s bounded cross-tick drain**: `DirtySet`'s own docstring confirms a
   fresh-every-tick snapshot, no persistent backlog anywhere in the live engine.
6. **`trace_governor.py`'s summarize-with-count**: confirmed genuinely distinct from both live
   neighbors — `EventRecorder` caps total volume (drops/truncates); `AlertDeduplicator.
   should_suppress()` fully suppresses repeats within a window (binary, alerts-only). Neither
   preserves a repeat-count signal for a general trace event.

## Disposition (user decision, routed via peer): delete all four modules, record the ideas

Two argument tracks, one conclusion:
- **1, 2, 4**: demonstrably aged out — stale/wrong target names, concepts (`shop_stock`,
  `regional_pressure`) that exist nowhere else in the live codebase. A revival would need to be
  written fresh against current names/systems anyway; the existing code offers a misleading sketch,
  not a shortcut.
- **3, 5, 6**: real, structurally non-redundant performance/resource-management capabilities, but
  no evidence any addresses an *observed* problem, and the user's standing direction defers
  performance work to a dedicated future effort. The drift found in 1/2/4 is itself the argument
  against assuming 3/5/6 haven't also drifted in ways nobody has checked.

This is a deletion on priority and staleness grounds, not a finding that the capabilities are
worthless — stated explicitly per peer's own instruction, and preserved as a named section in
`docs/plans/design_enhancement/performance_milestones_epic.md` (the real, current performance
initiative planning doc) for whoever picks up that epic.

## Non-import-reference guard applied

Checked `.github/workflows/*.yml` and `Makefile` for hardcoded references to all 4 module
filenames, their class names, and their dedicated test file paths — zero matches (unlike the
diagnostics-deletion miss earlier this batch, which hit a hardcoded CI path argument). Also found
and surgically preserved (not deleted wholesale) real, independent test coverage riding along in
`tests/unit/core/test_degraded_fallback.py` — 4 of its 10 tests covered `CatalogRepository.
get_lowest_cost_for_type()` and a `registries.py` module-default directly, unrelated to the deleted
`GracefulDegradationManager` wrapper; kept those, removed only the 6 tests calling the deleted
class.

Two real, non-fatal comment corrections made in `src/api/admission_control.py`, which had already
been flagged (by this ticket's own Scope) as citing `cache_strategy.py` by name/line as if it were
a live dependency — it never was, only an illustrative pattern reference. Corrected once the
deletion made the citation doubly stale.

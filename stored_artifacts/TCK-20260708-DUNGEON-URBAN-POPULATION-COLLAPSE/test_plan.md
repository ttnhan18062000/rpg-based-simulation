---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE
artifact_type: test_plan
tags: [simulation-quality, world, corpus, calibration]
---

# Test Plan — TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE

## Regression Surface

Existing tests that must keep passing after the content fix + recompiles. Grouped by domain.

### unit — world module / hazard mechanism (must be untouched by this fix)
- `tests/unit/world/test_regional_consequences.py` — all 8 tests, especially
  `test_hazard_drain_default_hazard_kind_no_regression` (asserts the `"PHYSICAL"` default and that
  nothing is immune to it by default — must still pass; this ticket does not change the mechanism)
  and `test_hazard_drain_different_faction_same_hazard_kind_full_drain` /
  `test_hazard_drain_shared_hazard_kind_hurts_mutually_hostile_factions_equally` (confirm the
  drain-without-match semantics this fix relies on are unchanged).

### unit — world compiler / resolved-spec content (`dungeon_crawl`/`urban_political`-specific)
- `tests/unit/worldbuilding/test_world_compiler.py`:
  - `test_urban_political_resolved_world_seeds_one_pending_self_model_information_event`
  - `test_urban_political_resolved_world_seeds_one_pending_information_response`
  - `test_urban_political_resolved_world_seeds_two_information_sources`
  - `test_urban_political_resolved_world_seeds_bandit_town_council_tension`
  (all read `data/worlds/urban_political/resolved/world.resolved.yaml` directly — recompiling
  `urban_political` must not change `information_source_profiles`, `pending_information_responses`,
  `pending_self_model_information_events`, or `faction_tension_overrides`-derived `tension_level`;
  these are hand-authored in `world.yaml` and independent of `hazard_kind`, but must be
  re-verified post-recompile since the whole resolved file regenerates.)

### integration — world composition / assembly
- `tests/integration/worldassembly/test_real_content_world_compositions.py::test_dungeon_crawl_composition`
- `tests/integration/worldassembly/test_real_content_world_compositions.py::test_urban_political_composition`
- `tests/integration/worldassembly/test_e2e_smoke.py::test_smoke_dungeon_crawl_compiles_to_authoritative_state`
- `tests/integration/worldassembly/test_e2e_smoke.py::test_smoke_urban_political_compiles_to_authoritative_state`
- `tests/integration/worldassembly/test_e2e_smoke.py::test_urban_political_all_entities_have_region_id`

### unit — corpus diversity (this ticket's direct target file)
- `tests/unit/worldassembly/test_corpus_diversity.py`:
  - `test_entity_count_band` — `dungeon_crawl`/`urban_political` are not in `ANCHORED_WORLD_BANDS`,
    unaffected, but full parametrize must stay green (no accidental entity-count drift from the
    content edit — adding `hazard_kind` must not change `entity_count`).
  - `test_distinct_populated_factions[dungeon_crawl]` (expected 4) and
    `test_distinct_populated_factions` has no `urban_political` entry today — confirm this stays
    true; a content fix that changes who survives does not change *compile-time* distinct-faction
    count, only tick-time alive count, so this must not regress.
  - `test_hazard_kind_completeness[dungeon_crawl]` / `[urban_political]` — must keep passing (already
    does; the fix adds *matching* hazard_kind values, which only strengthens this test's premise).
  - `test_module_family_anchored` — unaffected (module-family anchoring, not hazard content).

### unit — 3rd affected world sharing `ruins_mystery_quest` (anti-drift check, not in original scope list)
- `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[hero_guild_routing]`
  — currently passing; must re-verify it still passes after `ruins_mystery_quest.yaml` gains
  `hazard_kind` (low risk — fix only adds an exemption, never removes one — but must be run, not
  assumed, per Anti-Drift Hazards in investigation.md).

## New Tests Required

Per Acceptance Criteria: "Root cause identified... documented separately," "Fix applied,"
"`test_population_stability[dungeon_crawl]` and `[urban_political]` pass without `xfail`."

1. **Remove the `xfail` markers** for `dungeon_crawl` and `urban_political` from
   `KNOWN_POPULATION_COLLAPSE_WORLDS` in `tests/unit/worldassembly/test_corpus_diversity.py`
   (lines 120–129) once both are confirmed passing — this *is* the acceptance-criterion-mandated
   test change; `test_population_stability` itself needs no new logic, only the removal of the
   `xfail(strict=False, ...)` wrapper for these two `pytest.param` entries (lines 227–239).
   - Category: regression guard (existing test, scope change only)
   - Verifies: both worlds now genuinely satisfy the 60%-alive-at-every-50-tick-checkpoint floor
     for 300 ticks at seed 42 — no config change to the test itself.
   - Location: `tests/unit/worldassembly/test_corpus_diversity.py`

2. **Content-level hazard_kind/hazard_immunities match assertions** (new, targeted — closes the
   test-coverage gap noted in investigation.md Risk 5, scoped narrowly to the two fixed worlds so
   as not to re-litigate `test_hazard_kind_completeness`'s broader out-of-scope redesign):
   - Test name: `test_hazard_kind_matches_populating_faction_immunity` (or added as assertions
     inside a new parametrized test, distinct from `test_hazard_kind_completeness` which only
     checks presence)
   - Category: unit / regression guard
   - What it verifies: for `dungeon_crawl` and `urban_political`'s resolved specs, every region
     with `hazard_level > 0` that has an entity population resolves to a `hazard_kind` that is
     present in **at least one** of its populating factions' `hazard_immunities` (i.e., not every
     entity in the region needs immunity, but the region's own "native" faction — the one the
     module's `factions`/`populations` list names as primary — does). This is what
     `test_hazard_kind_completeness` does *not* check today (presence only, not match) and is the
     exact gap this ticket's root cause exploited.
   - Where it should live: `tests/unit/worldassembly/test_corpus_diversity.py`, alongside
     `test_hazard_kind_completeness` (same fixture-loading helpers, same
     `HAZARD_KIND_COMPLETENESS_WORLDS` list is a reasonable starting scope, though the assertion
     logic needs a per-world "native populating faction per region" mapping that
     `test_hazard_kind_completeness` doesn't currently need — implementer should decide the
     minimal-diff way to express this, e.g. reusing `_load_resolved_spec`'s region/faction data
     directly rather than adding a new fixture file).

3. **Recompile-freshness guard for `urban_political`** (closes the specific "stale compile" gap
   that caused half of this bug — prevents recurrence):
   - Test name: `test_urban_political_resolved_bandit_road_hazard_kind_matches_source` (or fold into
     #2 above if the implementer judges that sufficiently covers it — a duplicate test is not
     required if #2's match-check already catches a future re-staling)
   - Category: unit / regression guard
   - What it verifies: `data/worlds/urban_political/resolved/world.resolved.yaml`'s `bandit_road`
     region has `hazard_kind: NATURAL_TERRAIN` (matching `bandit_road_trade_pressure.yaml`'s
     current source declaration) — a literal regression guard against this exact staleness
     recurring silently.
   - Where it should live: `tests/unit/worldbuilding/test_world_compiler.py` (alongside the other
     `test_urban_political_resolved_world_seeds_*` tests that already assert against this same
     resolved file) or `tests/unit/worldassembly/test_corpus_diversity.py` if grouped with #2.

## Scoped Pytest Commands

```bash
# Primary target — the two fixed worlds' population-stability + hazard-kind coverage
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v

# Hazard-drain mechanism unit tests — confirm the mechanism itself is untouched
.venv/bin/python3 -m pytest tests/unit/world/test_regional_consequences.py -v

# World compiler content-shape tests for both affected worlds
.venv/bin/python3 -m pytest tests/unit/worldbuilding/test_world_compiler.py -k "dungeon_crawl or urban_political" -v

# World assembly integration + e2e smoke for both affected worlds
.venv/bin/python3 -m pytest tests/integration/worldassembly/test_real_content_world_compositions.py -k "dungeon_crawl or urban_political" -v
.venv/bin/python3 -m pytest tests/integration/worldassembly/test_e2e_smoke.py -k "dungeon_crawl or urban_political" -v
```

Never `pytest tests/`. `test_population_stability` is `@pytest.mark.slow` (300-tick full drive per
world) — run it explicitly rather than filtering it out with `-m "not slow"` during this ticket's
own verification, since it is the acceptance-criterion test; `-m "not slow"` is fine for unrelated
CI runs afterward.

## Anti-Drift Test Guards

- **`hero_guild_routing` population-stability re-run** (see Regression Surface) guards against the
  `ruins_mystery_quest.yaml` content edit having an unexpected side effect on the one other world
  that reuses it — must be run explicitly, not assumed safe from "the fix only adds exemptions."
- **Full `test_corpus_diversity.py` suite (not just the 2 target parametrize cases)** guards against
  scope creep into `ANCHORED_WORLD_BANDS`/`test_entity_count_band` or
  `test_distinct_populated_factions` — this ticket's fix must not change any world's `entity_count`
  or `distinct_populated_factions` (a `hazard_kind` edit is drain-only, not population-count-only;
  if either shifts, that is a sign the fix touched more than intended).
- **`test_hazard_drain_default_hazard_kind_no_regression`** (existing,
  `tests/unit/world/test_regional_consequences.py`) is the guard against the "wrong" fix (a
  blanket/universal immunity) — if this test starts failing after implementation, the fix took the
  wrong shape (mechanism-level instead of content-level) and must be reverted to a per-module
  `hazard_kind` edit instead.
- **The 4 `test_urban_political_resolved_world_seeds_*` tests** in
  `test_world_compiler.py` guard against the `urban_political` recompile silently dropping or
  mutating the hand-authored `information_source_profiles` / `pending_information_responses` /
  `pending_self_model_information_events` / `faction_tension_overrides` blocks in `world.yaml` —
  these are easy to lose if the recompile is done via a different code path than the original
  compile (e.g. a script that doesn't forward composition-level overrides correctly).
- **xfail-marker removal must be atomic with the fix, not preemptive.** If either world's fix is
  landed but the other is still pending, only remove that one world's entry from
  `KNOWN_POPULATION_COLLAPSE_WORLDS` / its `xfail` — do not remove both markers speculatively
  before both are independently re-verified at the full 300-tick checkpoint sequence.

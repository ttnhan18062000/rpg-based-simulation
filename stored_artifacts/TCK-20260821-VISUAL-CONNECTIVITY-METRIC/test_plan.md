---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-CONNECTIVITY-METRIC
artifact_type: test_plan
tags: [visualization, simulation-quality, world]
---

# Test Plan — TCK-20260821-VISUAL-CONNECTIVITY-METRIC

## Regression Surface

This is a new, additive, pure-function module with no existing call sites — nothing currently depends
on it, so there is no behavior-change regression surface in the traditional sense. The regression
surface that matters is: the code this ticket *reuses the rule from* must not have silently drifted,
and the renderer package this ticket sits beside (per module-placement recommendation) must not be
broken by adding a sibling file.

- unit:
  - `tests/unit/rendering/` (whole directory) — `test_render_core.py`, `test_render_incremental.py`,
    `test_render_retention_integration.py`, `test_render_storage_integration.py`,
    `test_terrain_color_normalization.py` — must keep passing; confirms adding a new module to
    `src/rendering/` did not disturb the existing renderer package (import ordering, `__init__.py`
    surface, etc.), if that module-placement recommendation is followed.
  - `tests/unit/` legality tests covering `LegalityServiceV2.verify_occupancy` (locate via
    `grep -rl "verify_occupancy" tests/unit/` at implementation time) — confirms the walkability rule
    this ticket reuses has not changed shape since this investigation was written.
- integration: none identified — this metric has no integration-level consumer yet (grade-scorer
  integration is a separate, later ticket).

## New Tests Required

1. **`test_connected_map_is_one_component_fully_reachable`**
   - Category: unit
   - Verifies: a small, fully-connected synthetic grid (all tiles walkable, no WALL/blocked_tiles)
     returns `walkable_count == total tile count`, `component_count == 1`, `percent_reachable == 100.0`.
     Construct via a plain `terrain` dict (all non-`"WALL"` values) and empty `blocked_tiles`, passed
     directly as the two fields the function reads — no need to build a full `AuthoritativeState` or
     use `V2EntityBuilder` for this case, matching the ticket's own Scope line that this is "pure
     geometry computation" over just `terrain`/`blocked_tiles`, not a full-state function. (If the
     final function signature does take an `AuthoritativeState`, build one minimally via
     `AuthoritativeState(tick=0, seed=42, terrain=..., blocked_tiles=...)`, mirroring
     `tests/unit/rendering/test_render_core.py`'s `_build_state()` helper pattern.)
   - Where: `tests/unit/rendering/test_connectivity.py` (or the equivalent path matching wherever the
     implementer places the module — see investigation.md's module-placement discussion; keep the test
     path a direct sibling of the source path).

2. **`test_two_disconnected_islands_reports_correct_component_count`**
   - Category: unit
   - Verifies: a constructed grid with exactly 2 separate walkable regions, physically separated by a
     `WALL` (or `blocked_tiles`) barrier with no shared cardinal-adjacent walkable tile — returns
     `component_count == 2`, `walkable_count` equal to the sum of both islands' tile counts, and
     `percent_reachable` computed per whichever definition `plan.md` settles on (see investigation.md's
     flagged open question — assert the *specific* chosen definition explicitly in the test, with a
     comment citing which definition was chosen and why, so this isn't silently ambiguous in the test
     suite itself).
   - Additional variant strongly recommended (AC only requires ">=2", so covering 3 is a natural
     extra to catch an off-by-one in the BFS/visited-set loop, e.g. a hidden edge case only appears at
     component index 2 or higher): a 3-island fixture, `component_count == 3`.
   - Where: same file as above, `tests/unit/rendering/test_connectivity.py`.

3. **`test_blocked_tiles_alone_can_fragment_connectivity`** (edge case beyond the literal AC wording,
   worth adding since the ticket explicitly says the rule is "terrain != WALL **minus blocked_tiles**")
   - Category: unit
   - Verifies: a grid with no `WALL` terrain at all, but a `blocked_tiles` set forming a complete
     barrier, still fragments into >=2 components — proves `blocked_tiles` is actually consulted, not
     just `terrain`, closing a real gap the two tests above (which likely use `WALL` as the barrier)
     would not otherwise catch.
   - Where: same file.

4. **`test_does_not_mutate_authoritative_state`** (architecture guard, per CLAUDE.md's "Architecture
   tests: verify read-only logic did not mutate live state")
   - Category: architecture guard
   - Verifies: calling the connectivity function twice on the same `AuthoritativeState` (or the same
     `terrain`/`blocked_tiles` objects, whichever the final signature takes) produces identical results
     both times, and the input `terrain`/`blocked_tiles` dict/set identity and contents are unchanged
     after the call (`assert terrain == terrain_before`, `assert blocked_tiles == blocked_tiles_before`,
     or equivalent pre/post snapshot comparison) — since `AuthoritativeState` is a frozen dataclass but
     `terrain`/`blocked_tiles` are themselves mutable containers, this is the concrete way to catch an
     in-place-mutation bug the frozen-dataclass guarantee alone would not catch.
   - Where: same file.

5. **`test_dungeon_crawl_matches_documented_evidence`** (AC #1, real-corpus reproduction)
   - Category: integration (real compiled world, real content data — not a pure synthetic unit test,
     though it lives in `tests/unit/` per AC #5's explicit placement requirement)
   - Verifies: loading the real `dungeon_crawl` world via
     `WorldRepository("data/worlds").load_world("dungeon_crawl")` →
     `WorldCompiler.compile(spec, seed=<any fixed seed, e.g. 42>)` (exact precedent pattern from
     `tests/unit/rendering/test_render_incremental.py:29-32`) and running the new connectivity function
     against the resulting `AuthoritativeState.terrain`/`blocked_tiles` reproduces
     `walkable_count == 15245`, `component_count == 1`, `percent_reachable == 100.0` — the exact figures
     from `experiments/spatial_rendering/PROPOSAL.md:429` and
     `docs/plans/world_rendering/idea_world_render_validation.md:42`.
   - **Contingency, stated explicitly per investigation.md's Risk section**: since these numbers were
     originally produced by uncommitted, one-off code rather than a fixed script, if this test does not
     reproduce exactly 15,245/1/100% on first run, that is a real finding to report (world content or
     the walkability rule's real behavior may have drifted since 2026-07-16/08-14), not something to
     force-fit by adjusting the walkability rule or the test's expected numbers without flagging it.
     Terrain layout is confirmed seed-independent (`PROPOSAL.md`'s Variant-diversity section, 3-seed
     byte-identical-histogram comparison), so seed choice is not a plausible source of mismatch if one
     occurs.
   - Where: `tests/unit/rendering/test_connectivity.py`, in the same file as the synthetic-fixture
     tests, or a clearly-separated real-corpus test module if the implementer prefers isolating
     real-world-loading tests (matches `test_render_incremental.py`'s own precedent of a dedicated file
     for a real-corpus test rather than mixing into `test_render_core.py`'s synthetic-fixture tests).

## Scoped Pytest Commands

```
pytest tests/unit/rendering/ -v
```

If the module is placed outside `src/rendering/` per the planner's final module-placement decision,
scope to that directory's test path instead (e.g. `tests/unit/worldquality/` or wherever
`test_connectivity.py` actually lands) — do not fall back to `pytest tests/` (CLAUDE.md hard rule).

Additionally, to confirm the walkability-rule source of truth is unchanged:

```
pytest tests/unit/ -k "verify_occupancy or legality" -v
```

(Refine the `-k` filter at implementation time once the exact legality test file(s) are located via
`grep -rl "verify_occupancy" tests/unit/`.)

Never: `pytest tests/` (CLAUDE.md hard rule — always scope to affected domain).

## Anti-Drift Test Guards

- **No `tests/parity/` marker anywhere in this ticket's new tests** — AC #5 is explicit, and
  `docs/testing/test_taxonomy.md` (per `idea_world_render_validation.md:63`) already classifies
  metric-correctness tests, connectivity included, as ordinary `tests/unit/` tests requiring no special
  marker. A test accidentally carrying `@pytest.mark.parity` (or being placed under `tests/parity/`)
  should be treated as a scope violation of the ticket's own explicit AC, not a minor detail.
- **No grading/threshold assertions.** Because grade-band integration is out of scope
  (TCK-20260821-VISUAL-GRADE-SCORER's job), no new test here should assert an S/A/B/C/D/F grade or a
  pass/fail boolean derived from a threshold — only the raw structural facts (walkable count, component
  count, percent reachable) per AC #2. A test asserting a grade would be evidence the implementation
  scope-crept into the scorer's territory.
- **No CI-gating.** None of these new tests should be wired into any regression-baseline or
  gate-enforcement script (e.g. nothing added to `tests/tools/test_parity_index_baseline.py`-style
  baseline files, no addition to a CI-required check list) — Out of Scope explicitly forbids this;
  these tests exist to prove correctness on demand, not to block merges.
- **No corpus-sweep test.** A test iterating all/most of `data/worlds/*` to run connectivity broadly
  would silently expand scope into TCK-20260821-VISUAL-QUALITY-CALIBRATION's territory (Out of Scope:
  "Expanding evidence beyond dungeon_crawl to other worlds"). Only `dungeon_crawl` should appear as a
  real-corpus test target in this ticket's test suite.
- **Mutation guard (test 4 above) is not optional filler** — it is the concrete mechanism catching the
  specific hazard flagged in investigation.md (mutable `dict`/`set` fields on an otherwise-frozen
  `AuthoritativeState`); omitting it would leave that hazard structurally uncaught by any other test in
  this plan.

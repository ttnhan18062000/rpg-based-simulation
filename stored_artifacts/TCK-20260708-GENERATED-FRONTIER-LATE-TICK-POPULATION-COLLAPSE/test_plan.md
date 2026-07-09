---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE
artifact_type: test_plan
tags: [simulation-quality, world, corpus, calibration]
---

# Test Plan — TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE

## Regression Surface

Existing tests that must keep passing after any content fix lands.

**unit / worldassembly:**
- `tests/unit/worldassembly/test_corpus_diversity.py::test_entity_count_band` — not affected
  (`generated_frontier_3_42` is not in `ANCHORED_WORLD_BANDS`), run anyway as a corpus-file
  sanity check since the world file is being touched.
- `tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions
  [generated_frontier_3_42]` — must stay at `7`. The `moon_cave` fix (hazard_kind only) must not
  change which factions are populated, only whether their population survives.
- `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability
  [generated_frontier_3_42]` — the existing 300-tick, 50-tick-checkpoint guard. Must keep
  passing (it already does; the fix should not regress the well-understood 0-300 window).
- `tests/unit/worldassembly/test_corpus_diversity.py::test_hazard_kind_completeness
  [generated_frontier_3_42]` — already passes today (checks presence only); must keep passing.
  Fixing `moon_cave` makes it pass more meaningfully but does not change its pass/fail status.
- `tests/unit/worldassembly/test_corpus_diversity.py::test_module_family_anchored` — asserts
  `moon_cult_ruins` is present in an anchored world's module list; unaffected by a hazard_kind
  content edit within that module.
- `tests/unit/world/test_regional_consequences.py` (in particular
  `test_hazard_drain_default_hazard_kind_no_regression` and siblings) — the mechanism-level
  tests; must be untouched and passing, confirming the drain mechanism itself is not being
  changed, only the content declaring it.

**simulation_quality (only if the fix changes `generated_frontier_3_42`'s calibration output):**
- `tests/simulation_quality/test_grade_regression.py` — `generated_frontier_3_42`'s 200t/3-seed
  and 1000t/seed42 anchors in `tests/simulation_quality/fixtures/grade_anchors.json` were
  established (`TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS`) **with the collapse
  included**. If the content fix changes `entity_count`, `COMBAT` event volume, or any other
  pillar signal at 200t or 1000t, these anchors will drift and must be re-verified/re-anchored in
  the same session per the Authoritative Mechanics Rule (parity + doc in the same session as the
  behavior change). Re-run via `tools/calibrate_simq.py` for `generated_frontier_3_42` at
  seed{42,123,456}_200t and seed42_1000t.

## New Tests Required

1. **`test_hazard_kind_matches_populating_faction_immunity[generated_frontier_3_42]`**
   — Category: unit / architecture guard.
   — Extend `HAZARD_KIND_MATCH_WORLDS` in `tests/unit/worldassembly/test_corpus_diversity.py`
   from `["dungeon_crawl", "urban_political"]` to include `"generated_frontier_3_42"`. Verifies
   every hazardous, populated region's `hazard_kind` matches at least one populating faction's
   `hazard_immunities` — directly guards Root cause 1 (`moon_cave`/`arcane_circle`). **Only add
   this world to the list after the `moon_cult_ruins.yaml` fix lands and is recompiled** (per
   investigation.md Anti-Drift Hazards — adding it pre-fix would fail immediately, which is
   correct-but-premature and would conflict with this ticket's own commit sequencing).
   — Location: `tests/unit/worldassembly/test_corpus_diversity.py` (existing test,
   parametrization list extended).

2. **`test_population_stability_extended[generated_frontier_3_42]`** (or an equivalent
   world-specific extension — do **not** widen the existing 300-tick
   `test_population_stability` parametrization to 1000 ticks for all worlds; see Anti-Drift Test
   Guards below).
   — Category: unit / integration (drives the real `Kernel` for up to 1000 ticks — `@pytest.mark.slow`).
   — What it verifies: `generated_frontier_3_42` stays at or above the 60%-alive floor at
   checkpoints through at least tick 1000, per the ticket's AC.
   — **Requires an explicit planner decision (investigation.md Risk 1) on methodology before this
     test can be written correctly**: either (a) accept a documented, wider-than-usual tolerance
     reflecting genuine run-to-run variance from the tick-budget governor (Root cause 3), sampled
     across multiple seeds/runs rather than asserted on a single deterministic trajectory, or (b)
     drive the Kernel with `audit_mode=True` to structurally disable the throttle paths, in which
     case the test's docstring must clearly state it verifies unthrottled/best-case population
     health, not the load-dependent behavior a real run would show. **Do not write this test by
     silently picking one option** — flag it for the planner's plan.md to decide, then implement
     per that decision.
   — Location: `tests/unit/worldassembly/test_corpus_diversity.py` (new function, or a new file
     `tests/unit/worldassembly/test_generated_frontier_extended_stability.py` if the planner
     decides the methodology differs enough from the existing 300-tick guard's shape to warrant
     separating them — either is acceptable, decide in plan.md).

3. **`test_generated_frontier_moon_cave_hazard_kind_declared`** (narrow, fast, content-only
   regression — optional if Test #1 above is judged sufficient, but recommended since it pins the
   specific fixed value rather than only the general pattern).
   — Category: unit.
   — What it verifies: `data/content/world_modules/moon_cult_ruins.yaml`'s `moon_cave` region
     declares a `hazard_kind` matching `arcane_circle`'s `hazard_immunities` (whatever kind value
     the fix settles on) — a static content-file assertion, no `Kernel` drive required, fast.
   — Location: `tests/unit/worldassembly/test_corpus_diversity.py` or a dedicated
     `tests/unit/content/test_moon_cult_ruins_content.py` if a per-module content test file
     convention exists elsewhere in the repo (check for precedent before creating a new file).

## Scoped Pytest Commands

```bash
# Corpus-diversity guards (fast — entity counts, module family, hazard-kind completeness/match,
# and the existing 300-tick population-stability guard, generated_frontier_3_42 only):
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -k generated_frontier_3_42 -v

# Full corpus-diversity file (regression check for the other worlds — must stay green,
# confirms this ticket's edits don't leak into unrelated worlds):
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v

# Hazard-drain mechanism unit tests (must be untouched):
.venv/bin/python3 -m pytest tests/unit/world/test_regional_consequences.py -v

# New extended-window test (once written, per whichever methodology the planner selects):
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -k "generated_frontier_3_42 and extended" -v -m slow

# SimQ anchor re-verification (only if calibration output for this world changed):
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -k generated_frontier_3_42 -v
```

Never run the full `pytest tests/` — scope to `tests/unit/worldassembly/`,
`tests/unit/world/`, and `tests/simulation_quality/` (only the `generated_frontier_3_42`-keyed
subset of the latter) per the Testing Rule.

## Anti-Drift Test Guards

- **Do not widen `test_population_stability`'s existing 300-tick window to 1000 ticks for all
  `POPULATION_STABILITY_WORLDS`.** The ticket's Out of Scope explicitly limits this to
  `generated_frontier_3_42`; every other world's tick-budget-throttle behavior past tick 300-400
  is unverified territory (investigation.md Risk 4) and should not be silently swept into a wider
  assertion window as a side effect of this ticket.
- **Do not add `generated_frontier_3_42` to `HAZARD_KIND_MATCH_WORLDS` before the content fix
  lands** — sequence the commit so the parametrization extension and the content fix land
  together (or the test extension strictly after), never before.
- **Do not silently choose `audit_mode=True` vs. a tolerance-based assertion for the new extended
  test without documenting the choice in plan.md** — per investigation.md Risk 1, these represent
  functionally different things being verified (best-case unthrottled population health vs.
  real/load-dependent population health), and picking one without recording the reasoning would
  make a future re-read of this test's intent impossible to recover.
- **A test asserting an exact alive-count trajectory (e.g. "must be exactly 28/44 at tick 800")
  would be actively wrong and must not be written** — this investigation directly demonstrated
  (two back-to-back runs, identical seed/code) that the exact trajectory is not reproducible.
  Only floor-style (`>=` threshold) or distributional (e.g. "floor holds in N of M repeated runs")
  assertions are valid here.
- **If the `bandit_road`/`town_council` gap (Root cause 2) is fixed as part of this ticket's
  scope, do not silently also resolve it for `urban_political`'s identical open case** —
  `urban_political`'s fix (if any) belongs to a decision that also touches
  `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`'s already-closed scope; keep this ticket's
  diff limited to `generated_frontier_3_42`'s own world/module files.
- **Re-run `test_hazard_kind_completeness` and `test_hazard_kind_matches_populating_faction_immunity`
  for `dungeon_crawl` and `urban_political` too** (not just `generated_frontier_3_42`) after any
  shared catalog file edit (e.g. if the fix adds a new `hazard_immunities` entry to
  `arcane_circle` or a new `hazard_kind` value to the shared vocabulary) — a catalog-level change
  has corpus-wide blast radius even when the *region* fix is world-specific.

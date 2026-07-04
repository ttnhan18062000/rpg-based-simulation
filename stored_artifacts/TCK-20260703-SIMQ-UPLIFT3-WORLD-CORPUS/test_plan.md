---
ticket_id: TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS
phase: test_plan
date: 2026-07-04
---

# Test Plan: Diversify the SimQ calibration world corpus

## Regression Surface

- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` / `SLOW_ANCHOR_KEYS` /
  `MINIMUM_FAST_ANCHORS`) — adding new anchor keys must not perturb the existing 25 entries for
  `dungeon_crawl`, `sandbox_world`, `simq_routing_test`, `urban_political`.
- `tests/simulation_quality/fixtures/grade_anchors.json` — additive only; no existing key's grade
  value should change as a side effect of this ticket's work.
- `tests/integration/worldassembly/test_real_content_world_modules.py::MODULE_MATRIX` — any new
  world composition must reference modules already present in `MODULE_MATRIX`, or the matrix must
  be extended (per the pattern `TCK-20260630-WORLD-TEST-MATRIX` established).
- `data/worlds/world_index.json` — must be updated if new world directories are added (mirrors the
  pattern for the existing 10 entries).
- `docs/plans/audit_fix_plan.md`'s P2-B row and the 13-run corpus table — must be updated to
  reflect this investigation's re-verification (P2-B's own scope resolved; the
  frontier_extended/frontier_living_world/wilderness_survival symptom re-attributed, not silently
  left as-is).
- `Makefile`'s `evaluate` / `evaluate-full` targets — must still exit 0 against the expanded
  `grade_anchors.json` (ticket AC6).
- Any world recompile (if the stale-compile sub-blocker fix is done in a follow-up ticket) touches
  `resolved/world.resolved.yaml`, `resolved/provenance_manifest.json`,
  `resolved/validation_report.json` for the affected world(s) — those are generated artifacts, not
  hand-edited; regenerate via the assembly resolver, don't patch by hand.

## New Tests Required

1. **World-shape unit test** (new, e.g. `tests/unit/worldassembly/test_corpus_diversity.py` or
   extend an existing worldassembly test file): assert the new/extended world(s)' compiled
   `entity_count`/`region_count`/`resource_node_count` fall in the specific band each was authored
   to fill (e.g. entity_count in [38, 44] for the "fills the 32→44 gap" world). Prevents silent
   drift back to duplicating an already-covered shape.
2. **Population-stability smoke test** for each new/extended world (mirrors the checkpoint-sampling
   method used in this investigation): drive `Kernel.tick_once()` for ≥300 ticks at seed 42, assert
   `alive_count` at every 50-tick checkpoint stays ≥ some world-specific floor (e.g. ≥60% of
   starting entity count) — this is the regression guard against reproducing Finding 3's early-tick
   collapse in a *new* world.
3. **Hazard-kind completeness guard** (new, architecture-style test): for every region in every
   world's `resolved/world.resolved.yaml` with `hazard_level > 0`, assert `hazard_kind` is set
   OR the region's populated archetypes declare `hazard_immunities` covering it. Prevents any new
   world (or content-family reuse) from silently reproducing the "flat-stat entity + no
   hazard exemption" bug class found in Finding 3/4.
4. **Grade anchor additions**: following `TCK-20260702-SIMQ-EVAL-MATRIX`'s established pattern —
   for each new/extended world added to the corpus, run ≥1 seed at a fast tick count (200/500t) and
   add anchors to `grade_anchors.json` + `FAST_ANCHOR_KEYS`. Do not add a single-seed anchor as the
   sole regression guard for a new world if it can be avoided — prefer at minimum 2 seeds, matching
   the multi-seed pattern already established for the 4 existing anchored worlds.
5. **Module-family coverage test** (extend `MODULE_MATRIX` in
   `tests/integration/worldassembly/test_real_content_world_modules.py`): confirm each newly-anchored
   module (drawn from the 11 "never anchored" list) is present in at least one anchored world's
   `module_refs`.

## Scoped Pytest Commands

```bash
# Existing SimQ regression suite (must stay green throughout, fast subset)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow"

# Slow (1000t/2000t) anchors — run before finalizing if any new anchor touches SLOW_ANCHOR_KEYS
pytest tests/simulation_quality/test_grade_regression.py -m slow

# World assembly / module matrix regression
pytest tests/integration/worldassembly/test_real_content_world_modules.py

# Spawn cadence unit tests (P2-B regression guard — must stay green; confirms two-tier cadence
# logic is untouched by this ticket, since this ticket's UQ-1 resolution recommends NOT touching
# spawn.py/spawn_config.py)
pytest tests/unit/world/test_spawn_cadence.py

# New world-shape / population-stability / hazard-kind-completeness tests (once authored)
pytest tests/unit/worldassembly/test_corpus_diversity.py  # or wherever authored

# Full calibration diff (dry run, no engine re-run) — ticket AC6
make evaluate
```

Do not run `pytest tests/` in full — scope to `tests/simulation_quality/`,
`tests/integration/worldassembly/`, and `tests/unit/world/` per the domain touched.

## Anti-Drift Test Guards

- **Do not weaken `±1`-band tolerance** in `test_grade_regression.py` to force a new world's grades
  to pass — if a new world's grade doesn't land where expected, that's a finding to document
  (per the DA-decision pattern established for AGENCY/dungeon_crawl ECONOMY-COGNITION), not a
  reason to loosen the regression guard.
- **Do not silently mark P2-B "RESOLVED" in `audit_fix_plan.md` without also recording the
  re-attribution finding** (Finding 3/4 in `investigation.md`) — a future reader must be able to
  see that "P2-B resolved" does not mean "frontier_extended/frontier_living_world population
  collapse is fixed."
- **Do not anchor any new world using a stale (pre-2026-07-01) compile.** Verify
  `resolved/provenance_manifest.json::created_at` postdates 2026-07-01 before running calibration
  against it, per the Anti-Drift Hazards section of `investigation.md`.
- **Do not reuse a `hazard_level > 0` module without `hazard_kind`** unless the new world's
  populated archetype for that region has matching `hazard_immunities` — this is exactly how
  Finding 3's collapse happened; a new world built carelessly from `orc_clan_territory` /
  `bandit_road_trade_pressure` / `old_mine_resource_loop` (the 3 modules confirmed missing
  `hazard_kind` in source) will reproduce it.
- **Do not seed FACTION/INFORMATION/SOCIAL/AGENCY-activating content** (tension overrides,
  information source profiles, cooperation/routing flags) into the new worlds as part of this
  ticket — that is explicitly Out of Scope; a test that starts asserting non-C grades for those
  4 pillars on a new world would indicate scope drift, not progress.

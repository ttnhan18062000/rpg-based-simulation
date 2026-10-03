---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION
artifact_type: test_plan
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# Test Plan — TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION

## Regression Surface

Existing tests that must keep passing after content lands in all 8 worlds. Grouped by domain; none
of these should require an edit for a pure-content change (if one does, that is a signal the change
went beyond content authoring and the planner should be told).

### Unit — schema / compiler / assembly (mechanism-level, unaffected by new content values)

- `tests/unit/worldbuilding/test_worldspec_schema.py` — `FactionSpec.initial_tension_level`
  bounds/defaults (mechanism, not content).
- `tests/unit/worldbuilding/test_world_compiler.py` — `test_compiler_seeds_faction_tension_from_spec`,
  `test_compiler_seeds_full_faction_roster_at_zero_tension_by_default`,
  `test_compiler_no_factions_declared_yields_empty_factions_dict`.
- `tests/unit/worldassembly/test_assembly.py` — `test_faction_tension_overrides_applied_after_merge`,
  `test_no_faction_tension_overrides_matches_current_behavior`,
  `test_faction_tension_overrides_unknown_faction_raises`,
  `test_faction_tension_overrides_out_of_range_raises`.
- `tests/unit/faction/test_faction_state.py`, `tests/unit/faction/test_diplomacy.py` (includes
  `test_urban_political_seeded_tension_fires_tense_transition`) — must keep passing unmodified;
  `urban_political`'s own content is untouched by this ticket.

### Unit — corpus-diversity regression guards (directly load-bearing for this ticket)

- `tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions` — **must
  show identical counts after this ticket's changes** for all 8 touched worlds (dungeon_crawl=4,
  sandbox_world=3, wilderness_survival=2, highland_traverse=3, swamp_border_world=4,
  frontier_living_world=6, frontier_extended=9, generated_frontier_3_42=7). A tension override never
  adds/removes a populated faction; if this count changes, the change went beyond what was
  authorized.
- `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability` — covers
  `frontier_extended`, `frontier_living_world`, `wilderness_survival`, `highland_traverse`,
  `swamp_border_world` (5 of the 8; `dungeon_crawl`/`sandbox_world`/`generated_frontier_3_42` are
  **not** parametrized here — a pre-existing gap, not something this ticket must close, but worth
  flagging: those 3 worlds' population stability after recompile is not covered by this specific
  guard).
- `tests/unit/worldassembly/test_corpus_diversity.py::test_hazard_kind_completeness` — same 5-world
  coverage as above; confirmed clean pre-change (all hazard_level>0 regions already carry
  `hazard_kind`).
- `tests/unit/worldassembly/test_corpus_diversity.py::test_entity_count_band` — the 5
  `ANCHORED_WORLD_BANDS` worlds must stay in their chosen entity-count band; adding
  `faction_tension_overrides`/`information_source_profiles` does not change entity counts, so this
  should be a pure pass-through, but is a cheap, valuable confirmation that content authoring did not
  accidentally also touch `module_refs`/populations.

### Integration — real-content composition/module loading

- `tests/integration/worldassembly/test_real_content_world_compositions.py` — the 4
  `frontier_living_world`-hardcoded tests plus `test_wilderness_survival_composition`,
  `test_urban_political_composition`, `test_dungeon_crawl_composition` all read from
  `data/content/world_compositions/`, **not** `data/worlds/` — per this ticket's own investigation,
  do not edit that directory, so these tests are exercising an intentionally-frozen mirror and should
  be unaffected either way. Still run them to catch any accidental edit to the wrong path.
- `tests/integration/worldassembly/test_real_content_world_modules.py` — module-level catalog
  loading; unaffected by composition-level content, run as a cheap sanity check.

### Simulation quality — scorer unit tests and grade regression

- `tests/simulation_quality/test_faction_scorer.py` — `FactionScorer` event-scoring logic (mechanism
  unit tests, no world content involved).
- `tests/simulation_quality/test_information_scorer.py` — `InformationScorer` event-scoring logic
  (same).
- `tests/simulation_quality/test_grade_regression.py -m "not slow"` — **the primary drift-check
  gate**. Every existing anchor for the 8 touched worlds currently in `FAST_ANCHOR_KEYS`
  (`sandbox_world_seed{42,137,999}_200t`, `dungeon_crawl_seed42_200t`,
  `frontier_extended_seed{42,123,456}_200t`, `frontier_living_world_seed{42,123,456}_200t`,
  `wilderness_survival_seed{42,123,456}_200t`, `highland_traverse_seed{42,123,456}_200t`,
  `swamp_border_world_seed{42,123,456}_200t`) and `SLOW_ANCHOR_KEYS`
  (`dungeon_crawl_seed{42,123,456}_{1000,2000}t`, `sandbox_world_seed42_{1000,2000}t`) must be
  re-verified against a **freshly re-run** calibration (not the stale pre-change
  `data/calibration/*` reports) — this is Scope item 6's own requirement, executed test-by-test here.

## New Tests Required

Per acceptance criteria — this ticket is primarily content authoring, so most "new tests" are
extensions of existing parametrized guards rather than new test files.

1. **Anchor entries for `generated_frontier_3_42`** (only if the planner decides to bring it into the
   calibration corpus — see investigation.md Risks; this world currently has zero anchors and is not
   in `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` at all)
   - Category: fixture data + regression-list update, not a new test function.
   - Verifies: if FACTION/INFORMATION content is added to this world, its resulting grades are
     captured as a committed anchor rather than silently left uncaptured (which would make future
     drift on this world invisible).
   - Location: `tests/simulation_quality/fixtures/grade_anchors.json` (new keys) +
     `tests/simulation_quality/test_grade_regression.py::FAST_ANCHOR_KEYS` (new entries), only if the
     planner decides to anchor it. If the decision is "do not anchor," add one line to
     `docs/simulation_quality/eval_matrix_results.md`'s existing `generated_frontier_3_42` note
     stating this ticket's content was added but the world deliberately remains outside the anchored
     corpus (explicit, not silent).

2. **Per-world drift-verification record** (documentation-as-test-evidence, not a pytest function)
   - Category: integration (calibration-run-based), recorded in Implementation Notes.
   - Verifies: for each of the 8 worlds, every pre-existing anchor key's pillar grades are re-measured
     post-content-change and shown to be within the `_within_band` ±1-grade tolerance
     `evaluate_simq.py`/`test_grade_regression.py` both use, OR the anchor is explicitly updated with
     a documented reason (content-driven, not code-driven) if it drifted beyond that band.
   - Where: `tests/simulation_quality/fixtures/grade_anchors.json` (updated in place per drifted key)
     + a new subsection per world in `docs/simulation_quality/eval_matrix_results.md` (per AC bullet
     6), mirroring the existing `### frontier_living_world (...)` per-world table format.

3. **FACTION/INFORMATION non-inert-signal confirmation per world** (verification procedure, not a
   new automated test)
   - Category: integration (manual calibration-report inspection, same procedure the sibling
     unit-tier ticket's plan.md Step 7 used).
   - Verifies: each world's post-change `quality_report.json` shows non-zero `tension_active`/
     `diplomacy_active` (or an honest `diplomacy_dormant` finding) hit counts for FACTION, and
     non-zero `belief_active` (or an honest `belief_system_silent` finding) for any world where
     INFORMATION content was seeded — distinguishing genuine signal from a letter grade that happens
     to read non-`C` for an unrelated reason.
   - Where: read directly from `data/calibration/{world}_seed{seed}_200t/quality_report.json`, record
     findings in ticket Implementation Notes + `eval_matrix_results.md`.

4. **`EXPECTED_DISTINCT_POPULATED_FACTIONS` non-regression** (existing test, re-run as a new
   verification gate for this ticket specifically)
   - Category: unit / architecture guard.
   - Verifies: this ticket's `faction_tension_overrides` authoring never accidentally changes which
     factions are populated (it must only ever set `initial_tension_level` on already-populated
     IDs).
   - Where: `tests/unit/worldassembly/test_corpus_diversity.py::test_distinct_populated_factions`
     (already exists — no new test function needed, just a mandatory re-run post-change).

5. **Per-world compile warnings check** (verification procedure, per AC bullet 4)
   - Category: integration (compile-report inspection).
   - Verifies: `data/worlds/{world}/world_compile_report.json::warnings == []` for all 8 worlds after
     recompile.
   - Where: manual/scripted check during implementation; not itself a pytest function, but could be
     promoted to a `pytest.mark.parametrize`-based guard over all 8 world IDs in
     `test_corpus_diversity.py` if the planner wants a permanent regression test for "0 warnings
     stays 0 warnings" (currently no such guard exists for any world — worth flagging as a candidate
     addition, not a hard requirement for this ticket).

## Scoped Pytest Commands

Never run the full suite. Scope to the domains this ticket touches:

```bash
# Schema/compiler/assembly mechanism tests (should be untouched by content-only changes)
pytest tests/unit/worldbuilding/test_worldspec_schema.py tests/unit/worldbuilding/test_world_compiler.py
pytest tests/unit/worldassembly/test_assembly.py

# Faction mechanism tests
pytest tests/unit/faction/test_faction_state.py tests/unit/faction/test_diplomacy.py

# Corpus-diversity regression guards (the load-bearing ones for this ticket)
pytest tests/unit/worldassembly/test_corpus_diversity.py

# Real-content composition/module integration (frozen-mirror sanity check)
pytest tests/integration/worldassembly/test_real_content_world_compositions.py
pytest tests/integration/worldassembly/test_real_content_world_modules.py

# SimQ scorer unit tests
pytest tests/simulation_quality/test_faction_scorer.py tests/simulation_quality/test_information_scorer.py

# Grade regression / drift-check gate (fast tier only — do not add --dry-run to `make evaluate`)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow"
```

Drift-check verification itself is not a pytest invocation — per investigation.md Risks, it is:

```bash
# Per touched world, per anchor seed/tick combination already in grade_anchors.json:
python3 tools/calibrate_simq.py --ticks <existing_tick_count> --seed <existing_seed> --name <world_id>
# then:
make evaluate   # NOT "make evaluate --dry-run" — that second flag is interpreted by GNU Make itself
                # and silently no-ops the recipe (confirmed defect, same as sibling ticket's finding)
```

## Anti-Drift Test Guards

- **`test_distinct_populated_factions` is the single most important guard for this ticket** — it
  directly encodes the "no non-populated-faction entries" AC as an executable check. Any PR/diff
  that changes one of its 8 relevant expected counts should be treated as a signal the change
  exceeded content-authoring scope (e.g. accidentally added/removed a `module_refs` entry) and
  investigated before proceeding, not silently updated to match.
- **`test_faction_tension_overrides_unknown_faction_raises`** (existing, `test_assembly.py`) is the
  regression guard against authoring a tension override for a faction ID that isn't even in the
  post-merge catalog set — keep this passing to catch a typo'd faction ID at test time rather than
  discovering it only at `resolve` time.
- **Do not let a drift-check silently pass a stale comparison.** Any diff to
  `tests/simulation_quality/fixtures/grade_anchors.json` for these 8 worlds' existing keys must be
  accompanied by a fresh `data/calibration/{run_key}/quality_report.json` (post-content-change
  timestamp) — a reviewer should treat an anchor edit with no corresponding fresh calibration
  timestamp as suspect.
- **`generated_frontier_3_42` anchor-status guard** — if this ticket decides not to anchor this
  world, add an explicit assertion or doc note (not silence) confirming it deliberately has zero
  `grade_anchors.json` entries even after this ticket's content lands, so a future reader does not
  mistake the absence for an oversight. If it IS anchored, it must appear in both
  `grade_anchors.json` and `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` together — an anchor entry with no
  corresponding key-list entry is silently never checked by `test_grade_regression.py`.
- **`data/content/world_compositions/` untouched-guard** — a diff to any file under this directory
  as part of this ticket's changes should be treated as scope creep and reverted; the investigation
  confirms this path is not read by the compile pipeline for these worlds and at least one file
  (`dungeon_crawl.yaml`) is already intentionally frozen at a stale shape guarded by
  `test_dungeon_crawl_composition`'s exact `len(spec.module_refs) == 2` assertion.
- **Profile YAML additive-only guard** — any new/edited `config/simulation_quality/profiles/*.yaml`
  should contain only `feature_flags: {ENABLE_BELIEF_ASSIMILATION: "ON"}` for worlds gaining
  INFORMATION content, and must not introduce a `pillar_weights:` block unless a specific AC
  requires it (none does) — an unexpected `pillar_weights` addition is a sign of unrequested scope
  and would also silently change composite scoring for that world in ways this ticket never asked
  for.
- **`dungeon_crawl.yaml` profile-merge guard** — since this is the one profile file that already
  exists among the 8 targets, a diff that replaces rather than extends its existing
  `pillar_weights:` block (COMBAT/FACTION/SOCIAL/INFORMATION) should be treated as a defect, not an
  acceptable edit.

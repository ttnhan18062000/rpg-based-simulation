---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS
artifact_type: test_plan
tags: [simulation-quality, corpus, calibration, world]
---

# Test Plan — TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS

## Regression Surface
This is a data-only ticket (new calibration artifact(s) + `grade_anchors.json` entries +
`FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` additions); no scorer, hub, engine, or world-content source
changes. The regression surface is "does everything that already passes keep passing," grouped by
category:

**Unit — SimQ scorer/accumulator/report (must all still pass unmodified):**
- `tests/simulation_quality/test_agency_scorer.py`
- `tests/simulation_quality/test_cognition_scorer.py`
- `tests/simulation_quality/test_faction_scorer.py`
- `tests/simulation_quality/test_information_scorer.py`
- `tests/simulation_quality/test_combat_scorer.py`
- `tests/simulation_quality/test_progression_scorer.py`
- `tests/simulation_quality/test_narrative_scorer.py`
- `tests/simulation_quality/test_world_dynamics_scorer.py`
- `tests/simulation_quality/test_economy_scorer.py`
- `tests/simulation_quality/test_social_scorer.py`
- `tests/simulation_quality/test_accumulator.py`
- `tests/simulation_quality/test_report.py`
- `tests/simulation_quality/test_weights.py`

**Integration — hub, persistence, harness:**
- `tests/simulation_quality/test_quality_hub_integration.py`
- `tests/simulation_quality/test_quality_hub_event_translation.py`
- `tests/simulation_quality/test_persistence.py`
- `tests/simulation_quality/test_evaluate_harness.py`
- `tests/simulation_quality/test_scenario_coverage.py`
- `tests/integration/test_world_profile_feature_flag_guardrail.py` (`INFRA-262`) — must stay green
  unmodified; this ticket adds no flags/content to `generated_frontier_3_42`'s profile, so
  `expected_world_flag_state.json` needs no edit and this test should require none either. A failure
  here would mean something unintentionally touched the profile YAML.

**Corpus/world-content (indirectly relevant — confirms this world's health under longer runs than
previously exercised):**
- `tests/unit/worldassembly/test_corpus_diversity.py` — specifically
  `test_population_stability[generated_frontier_3_42]` and
  `test_hazard_kind_completeness[generated_frontier_3_42]` must both keep passing (neither is `xfail`;
  `generated_frontier_3_42` is confirmed absent from `KNOWN_POPULATION_COLLAPSE_WORLDS`). An
  unexpected failure here (not just the 200t/1000t calibration grades) would be a stronger signal of a
  genuine world-health regression than a grade shift alone.
- `tests/integration/worldassembly/test_e2e_smoke.py::test_smoke_generated_frontier_3_42_compiles_to_authoritative_state`
  — compile-layer gate; must keep passing.
- `tests/unit/strategic/test_opportunities.py::test_resource_opportunities_orc_stronghold_tag_gap` —
  confirms the `orc_stronghold` resource-tag fix (shared module with this world) still holds; not
  expected to be touched by this ticket but worth confirming green since it shares content with
  `generated_frontier_3_42`'s `orc_clan_territory` module.

**Full fast/slow anchor regression (existing anchors must still pass with unmodified reports):**
- `.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -v` (fast, ~67
  existing non-metadata keys minus this ticket's additions) and
  `-m slow` (existing `SLOW_ANCHOR_KEYS` — currently 17 entries including the 6 landed by
  `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` — must stay within ±1 band). This ticket must not
  delete, overwrite, or regenerate any *other* world's committed `data/calibration/{run_key}/
  quality_report.json` — only add new `generated_frontier_3_42_*` directories.

## New Tests Required
Per this ticket's data-only mechanism, "new tests" are new fixture entries + key-list string
additions — `test_grade_within_anchor_band` and `test_grade_within_anchor_band_long_run` are already
generically parametrized over `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`, so no new test *function* is
needed. The concrete additions the Plan/Implement phase must make:

1. **New 200t anchor key(s) in `FAST_ANCHOR_KEYS`**
   (`tests/simulation_quality/test_grade_regression.py`, after line 99), matching the "matching corpus
   convention" wording in AC item 2 (the rest of the short-run corpus anchors at 3 seeds per world
   where 3-seed data already exists — which it does here):
   - `generated_frontier_3_42_seed42_200t` (minimum required)
   - `generated_frontier_3_42_seed123_200t`, `generated_frontier_3_42_seed456_200t` (recommended —
     data already exists for both; Plan phase to confirm whether to anchor all 3 or just seed42, per
     investigation.md Risk 3)
   - Category: regression anchor (parametrized, not a bespoke test function).
   - Verifies: this world's committed 200t grade snapshot stays within ±1 band on future runs.
   - Lives at: `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` list) +
     `tests/simulation_quality/fixtures/grade_anchors.json` (10-pillar grade dict, one entry per seed)
     + `data/calibration/generated_frontier_3_42_seed{N}_200t/quality_report.json` (source-of-truth
     artifact — already present for seeds 42/123/456; git-commit alongside the fixture per existing
     convention).

2. **New 1000t (long-run) anchor key(s) in `SLOW_ANCHOR_KEYS`**
   (`tests/simulation_quality/test_grade_regression.py`, after line 124):
   - `generated_frontier_3_42_seed42_1000t` (minimum required per AC item 3 — "at least one long-run
     anchor")
   - Category: regression anchor (parametrized, `@pytest.mark.slow`).
   - Verifies: this world's first-ever long-run grade snapshot stays within ±1 band on future runs, and
     exercises the `effective_denom` dilution mechanism (investigation.md's Mechanics/Engine
     Constraints) for the first time on this world's FACTION/INFORMATION/COGNITION pillars.
   - Lives at: `tests/simulation_quality/test_grade_regression.py` (`SLOW_ANCHOR_KEYS` list) +
     `tests/simulation_quality/fixtures/grade_anchors.json` + `data/calibration/
     generated_frontier_3_42_seed42_1000t/quality_report.json` (does not yet exist — must be generated
     fresh by `python3 tools/calibrate_simq.py --name generated_frontier_3_42 --seed 42 --ticks 1000`).
   - Must not exceed 2000t (epic-wide cap) — 1000t satisfies the AC as written; do not scope-creep to
     2000t without a documented reason.

3. **Structural sanity — implicit, already covered.**
   `test_grade_anchor_file_exists_and_valid` (line 249) already asserts every `FAST_ANCHOR_KEYS` entry
   in `grade_anchors.json` has exactly 10 pillar grades, all in `GRADE_ORDER`. This automatically
   validates the new fast-tier entries' structural correctness with no new assertion. (It does **not**
   currently check `SLOW_ANCHOR_KEYS` entries structurally — this is a pre-existing gap in the test,
   not something this ticket needs to fix, but the 1000t entry should still be authored with all 10
   pillars for consistency and to avoid surprising a future tightening of that assertion.)

4. **Live compile/run confirmation (new, ad hoc — not a committed pytest test, an
   Implement-phase verification step, per Scope item 1's "confirm live, do not assume").** Before
   trusting any anchor, run `python3 tools/calibrate_simq.py --name generated_frontier_3_42 --seed 42
   --ticks 200` (or reuse the existing artifact with an explicit documented decision — see
   investigation.md Anti-Drift Hazards) and the fresh `--ticks 1000` run, and confirm both complete
   without exception and produce a non-trivial `quality_report.json` (event_count > 0 for at least the
   already-active pillars: FACTION, INFORMATION, COGNITION, COMBAT, PROGRESSION, WORLD, NARRATIVE).

## Scoped Pytest Commands
```bash
# Fast scorer/hub/persistence/harness regression (must be 0 new failures):
.venv/bin/python3 -m pytest tests/simulation_quality/ -m "not slow" -v

# Slow anchor regression — existing 17 keys + this ticket's new 1000t key, once committed:
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -m slow -v

# Corpus population-stability / hazard-kind guard, scoped to this world:
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v -k generated_frontier_3_42

# Full corpus-diversity suite (confirm no cross-world regression from touching shared fixtures):
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v

# E2E compile smoke gate for this world:
.venv/bin/python3 -m pytest tests/integration/worldassembly/test_e2e_smoke.py -v -k generated_frontier_3_42

# Feature-flag guardrail (confirm this ticket didn't silently touch the profile fixture):
.venv/bin/python3 -m pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v

# AC-mandated full harness check (per Scope item 6 — run late, after all anchors committed):
make evaluate   # --dry-run: diffs committed data/calibration/ reports against grade_anchors.json, no engine re-run
```
Do **not** run bare `pytest tests/` — scope stays within `tests/simulation_quality/`,
`tests/unit/worldassembly/test_corpus_diversity.py`,
`tests/integration/worldassembly/test_e2e_smoke.py`, and
`tests/integration/test_world_profile_feature_flag_guardrail.py`, per repo testing rule.

## Anti-Drift Test Guards
- **`test_grade_within_anchor_band` (fast suite, 50 existing keys) must show zero drift on every
  *other* world's 200t/500t anchors.** This ticket only adds `generated_frontier_3_42` keys — no existing key's grade
  should move; any drift elsewhere would indicate an unintended cross-run interaction (e.g., a shared
  mutable config or scoring-weights file edited incorrectly) and must block the ticket.
- **`test_population_stability[generated_frontier_3_42]` and
  `test_hazard_kind_completeness[generated_frontier_3_42]` must remain passing, not newly `xfail` or
  failing.** Since this ticket runs the engine for 1000t on this world for the first time (previously
  only exercised to 300t via the population-stability test and 200t via calibration), a new erosion
  pattern surfacing past 300t is a real possibility this ticket's Implementation Notes must state
  honestly if observed — do not silently anchor a 1000t grade without checking whether entity count
  has collapsed by then (mirrors the sibling ticket's `urban_political` population-erosion cross-check,
  even though this world currently has no known collapse defect).
- **`INFRA-262`'s guardrail fixture (`expected_world_flag_state.json`) must show zero diff.** This
  ticket is calibration-data-only; if the guardrail test fails after this ticket's changes, that is a
  signal something unintentionally touched `config/simulation_quality/profiles/
  generated_frontier_3_42.yaml` or `data/worlds/generated_frontier_3_42/world.yaml` — both explicitly
  out of scope.
- **`FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` must gain exactly the keys the Plan phase commits to — no
  more, no less.** Cross-check the final list additions against `plan.md`'s stated seed/tick grid
  before considering the ticket done; a silent extra or missing key is the most likely copy-paste
  drift failure mode for this mechanism (precedent: `pytest.skip`, not a failure, is what happens when
  a `grade_anchors.json` entry exists without a matching key-list membership or calibration report, so
  a missed key would pass silently rather than fail loudly).
- **`make evaluate --dry-run` must report 0 REGRESS across the *entire* corpus, not just the new
  entries.** Per investigation.md's parity-ledger finding on `INFRA-252`, `evaluate_simq.py --dry-run`
  iterates every non-metadata `grade_anchors.json` key regardless of `FAST_ANCHOR_KEYS`/
  `SLOW_ANCHOR_KEYS` membership — AC item 6 is a genuine full-corpus check, not scoped only to this
  ticket's additions.

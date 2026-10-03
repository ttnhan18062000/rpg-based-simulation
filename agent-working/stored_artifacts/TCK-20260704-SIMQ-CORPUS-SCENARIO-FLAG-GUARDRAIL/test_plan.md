---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL
artifact_type: test_plan
tags: [simulation-quality, feature-flags]
---

# Test Plan — TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL

## Regression Surface

Existing tests that must keep passing (none of these overlap this ticket's new coverage — confirmed
by reading each file; listed because they touch the same profiles/worlds/flags surface and could be
affected by an accidental edit):

**Unit**
- `tests/unit/config/test_phase10_feature_flags.py` — `FeatureFlagManager` API-level unit tests
  (default-OFF, `set_flag_mode`, `is_enabled`, `is_shadow`, `serialize`). No profile-YAML or
  per-world coverage; must stay green untouched.
- `tests/unit/config/test_phase10_rollout_profiles.py` — `RolloutProfileManager` CLASS_B/CLASS_C
  matrix tests (confirmed unwired into any live default per the epic investigation §1 — do not wire
  it as part of this ticket).
- `tests/unit/worldassembly/test_corpus_diversity.py` — `ANCHORED_WORLD_BANDS`,
  `POPULATION_STABILITY_WORLDS`, `EXPECTED_DISTINCT_POPULATED_FACTIONS` per-world tables (marker
  `worldassembly`). Structural precedent for this ticket's own expected-state table; must not be
  edited by this ticket (out of scope — it tracks entity counts/faction counts, not flags).
- `tests/unit/worldassembly/test_hero_guild_routing_population_stability.py` — the
  `ENABLE_ADVENTURE_ROUTING`-ON population-floor test for `hero_guild_routing`. Confirms the flag is
  ON and functionally exercised; this ticket's test only asserts the *static config value*, not
  runtime population behavior — complementary, not overlapping.

**Integration**
- `tests/integration/test_scenario_feature_flag_defaults.py` — the *other* mechanism
  (`data/content/simulation_scenarios/*.yaml`, `TCK-20260627-P2E-FEATURE-FLAG-TEST`, parity
  `INFRA-221`). Must stay green; this ticket's new test must NOT be added to this file (different
  subsystem, different parity entry — see investigation.md "Anti-Drift Hazards").
- `tests/integration/domains/test_fused_loop.py` —
  `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` and
  sibling Branch-B tests. Confirms the runtime mechanism this ticket's static config check is a
  guardrail *for*; do not touch.

**Simulation quality / calibration**
- `tests/simulation_quality/test_grade_regression.py` — the `FAST_ANCHOR_KEYS`-driven grade-anchor
  regression suite, now covering all worlds with committed anchors across this epic's 9 sibling
  tickets. Must not regress; this ticket adds no new calibration runs and touches no anchors.

## Scoped Pytest Commands

```
pytest tests/integration/ -k "profile_feature_flag or corpus_flag_guardrail" -m "not slow" -v
pytest tests/unit/config/test_phase10_feature_flags.py tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"
pytest tests/integration/test_scenario_feature_flag_defaults.py -m "not slow"
```

(Exact `-k` substring depends on the final test/function names chosen during implementation — see
New Tests Required below for the recommended naming. Never run bare `pytest tests/`.)

## New Tests Required

Recommended file: `tests/integration/test_world_profile_feature_flag_guardrail.py` (new — distinct
from `test_scenario_feature_flag_defaults.py`, which covers the unrelated
`data/content/simulation_scenarios/` mechanism; see investigation.md's Anti-Drift Hazards for why
these must not be merged). `tests/integration/` chosen over `tests/certification/` because this is
a static/config-level assertion over already-committed repo files (no engine run, no certification
harness needed) — matching P2-E's own fix guidance ("`tests/integration/` or `tests/certification/`")
and the precedent set by the sibling `TCK-20260627-P2E-FEATURE-FLAG-TEST`, which also chose
`tests/integration/` for the same reason.

Register a new pytest mark, e.g. `corpus_flag_guardrail` (mirroring the existing
`scenario_flags`/`feature_flag_default` marks already registered in `pyproject.toml:91-92` for the
sibling ticket) — add it to `pyproject.toml`'s `markers` list.

Fixture file (per UQ-2, since the corpus is 17 worlds, past the ticket's own 15-world threshold):
`tests/simulation_quality/fixtures/expected_world_flag_state.json` (mirrors the existing
`tests/simulation_quality/fixtures/grade_anchors.json` location/naming convention), keyed by world
name, holding: `profile_file` (or `null` for default-fallback), the 3 named flags' expected
ON/OFF state, and which Pattern-6 content fields are expected to be non-empty. One documented
exception entry (or a separate small `known_exceptions` block) for
`urban_political`/`pending_self_model_information_events`, citing `INFRA-259`/`INFRA-260`.

Per UQ-1 (single parametrized test, table-as-data): recommended test functions —

1. **`test_all_worlds_have_a_resolvable_profile_or_default_fallback`**
   - Category: integration
   - Verifies: every world directory under `data/worlds/` (excluding `world_index.json`) either has
     a `config/simulation_quality/profiles/<world>.yaml` file or correctly falls back to
     `default.yaml` (mirrors `tools/calibrate_simq.py::_resolve_profile()`'s own logic, not a
     reimplementation with drift risk — import and call the real function rather than duplicating
     its path logic).
   - Lives in: `tests/integration/test_world_profile_feature_flag_guardrail.py`

2. **`test_flag_state_matches_expected_per_world`** (parametrized over all 17 worlds via the
   fixture file)
   - Category: integration
   - Verifies: for each world, `_load_profile_feature_flags(resolved_profile)`'s returned dict
     matches the fixture's expected ON/OFF state for `ENABLE_ADVENTURE_ROUTING`,
     `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_SELF_MODEL_COGNITION` exactly (absence in the profile ==
     expected-OFF in the fixture; do not require an explicit `"OFF"` key).
   - Lives in: `tests/integration/test_world_profile_feature_flag_guardrail.py`

3. **`test_agency_da_anti_drift_guard`**
   - Category: integration / architecture guard
   - Verifies explicitly and by name (not just incidentally via test 2's parametrization) that all
     9 originally-non-routing worlds (`urban_political`, `dungeon_crawl`, `sandbox_world`,
     `wilderness_survival`, `highland_traverse`, `swamp_border_world`, `frontier_living_world`,
     `frontier_extended`, `generated_frontier_3_42`) have `ENABLE_ADVENTURE_ROUTING` OFF/absent —
     this is AC 4, made a standalone, clearly-named test so a future CI failure message reads as
     "AGENCY-DA anti-drift guard broken," not just "one row of a big parametrized table failed."
     Cites `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s anti-drift note directly in the docstring.
   - Lives in: `tests/integration/test_world_profile_feature_flag_guardrail.py`

4. **`test_information_flag_content_pairing_both_directions`** (parametrized over all 17 worlds)
   - Category: integration
   - Verifies AC 3's both-directions rule for the one pair that's actually gated:
     `information_source_profiles`/`pending_information_responses` seeded ⇒
     `ENABLE_BELIEF_ASSIMILATION` ON, and vice versa — for every world except none (this pair has no
     documented exception; all 9 ON-flag worlds have matching content and all 8 OFF-flag worlds
     correctly lack content, per investigation.md's expected-state table).
   - Lives in: `tests/integration/test_world_profile_feature_flag_guardrail.py`

5. **`test_self_model_flag_content_pairing_both_directions_with_documented_exception`**
   (parametrized over all 17 worlds)
   - Category: integration
   - Verifies the same both-directions rule for `pending_self_model_information_events` ↔
     `ENABLE_SELF_MODEL_COGNITION`, with exactly one explicit, cited exception:
     `urban_political` (content seeded, flag OFF, cited to `INFRA-259`/`INFRA-260` in both the
     fixture's `known_exceptions` entry and the test's assertion-failure message). Any other world
     violating the pairing must fail the test — the exception list must not grow silently.
   - Lives in: `tests/integration/test_world_profile_feature_flag_guardrail.py`

6. **`test_faction_content_has_no_flag_requirement`**
   - Category: architecture guard (documents/enforces the asymmetry, prevents a future edit from
     wrongly "fixing" a FACTION-only world by adding an unnecessary flag)
   - Verifies: worlds with `faction_tension_overrides` seeded and no INFO/self-model content
     correctly have zero relevant flags set (e.g. `unit_faction_tension`, and the FACTION-only
     subset of `dungeon_crawl`/`wilderness_survival`) — a guard against someone "fixing" what looks
     like a missing-flag gap that is not actually a gap.
   - Lives in: `tests/integration/test_world_profile_feature_flag_guardrail.py`

7. **`test_new_batch_worlds_are_covered`** (or equivalent assertion embedded in the fixture-loading
   helper)
   - Category: integration / architecture guard
   - Verifies the fixture's world list is a superset of (or exactly equal to) the live
     `data/worlds/` directory listing at test-collection time — so a future world added without a
     fixture entry fails loudly (`KeyError`/explicit assertion) instead of silently not being
     covered. This is AC 2 and AC 3's "explicitly enumerates... not just the pre-epic baseline"
     requirement made self-enforcing rather than a one-time manual check.
   - Lives in: `tests/integration/test_world_profile_feature_flag_guardrail.py`

## Anti-Drift Test Guards

- Test 3 (`test_agency_da_anti_drift_guard`) and test 7 (`test_new_batch_worlds_are_covered`) are
  themselves the anti-drift guards named in the ticket's own Scope/AC — call this out in each
  test's docstring so a future maintainer understands their purpose is regression detection, not
  just corpus documentation.
- Test 6 exists specifically to prevent a future contributor from "fixing" a FACTION-only world by
  adding a flag it doesn't need (a plausible but wrong fix if someone sees an incomplete mental
  model of the flag/content pairing rules — see investigation.md's Mechanics/Engine Constraints
  section for why FACTION has no flag gate).
- Test 5's exception list (currently exactly one entry: `urban_political` self-model) must fail loudly
  if a new, uncited exception appears — i.e. the exception list should be a small, explicit,
  cited allow-list, not a broad "skip if mismatch" fallback, so a genuinely new misconfiguration in
  a future world doesn't get silently absorbed into a growing exception list.
- None of these new tests should ever import or duplicate logic from
  `tests/integration/test_scenario_feature_flag_defaults.py` — if a future change makes it tempting
  to merge the two files, that is a sign the two subsystems (scenario templates vs. calibration
  profiles) are being conflated and should be resisted (see investigation.md's Anti-Drift Hazards).

## Parity Ledger Update (companion to test authorship, not itself a test)

Once the new test file exists and passes:
- Add a new parity ledger entry (recommend `infrastructure.yaml`, next available `INFRA-###` ID)
  documenting the new per-world profile-flag guardrail, its `test_path`, and its relationship to
  (not duplication of) `INFRA-221`.
- Update `docs/plans/audit_fix_plan.md` P2-E section (currently: "OPEN (not re-checked 2026-07-03)
  — S — per-scenario feature flag test", `docs/plans/audit_fix_plan.md:623`) from OPEN to
  **RESOLVED**, citing the new test's path, and note explicitly that `INFRA-221`/
  `TCK-20260627-P2E-FEATURE-FLAG-TEST` had already closed the scenario-definition half of this
  finding, while this ticket closes the calibration-profile half — P2-E's finding actually spanned
  two distinct mechanisms, only one of which had prior coverage. Update the Summary Table row (line
  623) to match.

---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL
artifact_type: plan
tags: [simulation-quality, feature-flags]
---

# Implementation Plan — TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL

## Summary

Add a new, static, config-level guardrail test that closes the calibration-profile half of
`docs/plans/audit_fix_plan.md` P2-E ("Feature-gated phases have no per-scenario default test") — the
half `TCK-20260627-P2E-FEATURE-FLAG-TEST` (`INFRA-221`) never covered, because that ticket tests
`data/content/simulation_scenarios/*.yaml` scenario templates, a different subsystem from
`config/simulation_quality/profiles/<world>.yaml` calibration profiles. The new test loads every one
of the corpus's 17 worlds' resolved profile YAML (`tools/calibrate_simq.py::_resolve_profile()` /
`_load_profile_feature_flags()`, real functions, not reimplementations) against a checked-in fixture
recording the actual, already-correct current state (confirmed directly against every profile YAML
and every `world.yaml`'s Pattern-6 fields in this planning session), and asserts: (1) the
per-world ON/OFF flag state, (2) the AGENCY-DA anti-drift guard as its own named test, (3) that
`faction_tension_overrides` correctly has no flag gate, and (4) both-direction pairing for the two
Pattern-6 fields that are actually flag-gated (INFORMATION content ↔ `ENABLE_BELIEF_ASSIMILATION`,
self-model content ↔ `ENABLE_SELF_MODEL_COGNITION`), with exactly one cited, allow-listed exception
(`urban_political`'s self-model content, `INFRA-259`/`INFRA-260`). Because the corpus (17 worlds)
exceeds the ticket's own 15-world hardcode threshold, the expected-state table lives in a fixture
file (`tests/simulation_quality/fixtures/expected_world_flag_state.json`), mirroring the existing
`grade_anchors.json` precedent. This is a test-only, config-assertion-only change: no engine code,
`FeatureMode`, `feature_flags.py`, or any world/profile YAML is modified.

## Steps

### Step 1 — Author the fixture file
**Files:** `tests/simulation_quality/fixtures/expected_world_flag_state.json` (new)
**Change:** Create the fixture with the exact content below. It records, per world: the resolved
profile filename (or `null` for `default.yaml` fallback), the expected `ENABLE_ADVENTURE_ROUTING` /
`ENABLE_BELIEF_ASSIMILATION` / `ENABLE_SELF_MODEL_COGNITION` state (string `"ON"`/`"OFF"`, matching
`FeatureMode.value` casing used by `_load_profile_feature_flags()`), and which of the three
Pattern-6 content buckets are seeded (`faction_tension_overrides`; the INFORMATION pair
`information_source_profiles`+`pending_information_responses` collapsed into one
`information_content` boolean since they are always seeded together per Pattern 6; and
`pending_self_model_information_events` as `self_model_content`). A `known_exceptions` block records
the one cited asymmetry. A `_meta` block records the AGENCY-DA world groupings and world count for
the self-enforcing coverage check in Step 3's test 7.

Exact fixture content (verified directly against every file in `config/simulation_quality/profiles/`
and every `data/worlds/<world>/world.yaml` in this planning session — see Verify below):

```json
{
  "_meta": {
    "description": "Expected per-world FeatureMode flag state and Pattern-6 content-field seeding for config/simulation_quality/profiles/. Distinct from data/content/simulation_scenarios/ scenario-template defaults (see tests/integration/test_scenario_feature_flag_defaults.py, parity INFRA-221) -- do not merge or extend that file with this fixture's coverage.",
    "world_count": 17,
    "agency_da_non_routing_worlds": [
      "urban_political", "dungeon_crawl", "sandbox_world", "wilderness_survival",
      "highland_traverse", "swamp_border_world", "frontier_living_world",
      "frontier_extended", "generated_frontier_3_42"
    ],
    "agency_da_routing_worlds": ["simq_routing_test", "hero_guild_routing"],
    "source_ticket": "TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL"
  },
  "worlds": {
    "urban_political": {
      "profile_file": "urban_political.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": true, "self_model_content": true}
    },
    "dungeon_crawl": {
      "profile_file": "dungeon_crawl.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "OFF", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": false, "self_model_content": false}
    },
    "sandbox_world": {
      "profile_file": "sandbox_world.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": true, "self_model_content": false}
    },
    "wilderness_survival": {
      "profile_file": null,
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "OFF", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": false, "self_model_content": false}
    },
    "highland_traverse": {
      "profile_file": "highland_traverse.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": true, "self_model_content": false}
    },
    "swamp_border_world": {
      "profile_file": "swamp_border_world.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": true, "self_model_content": false}
    },
    "frontier_living_world": {
      "profile_file": "frontier_living_world.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": true, "self_model_content": false}
    },
    "frontier_extended": {
      "profile_file": "frontier_extended.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": true, "self_model_content": false}
    },
    "generated_frontier_3_42": {
      "profile_file": "generated_frontier_3_42.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": true, "self_model_content": false}
    },
    "simq_routing_test": {
      "profile_file": "simq_routing_test.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "ON", "ENABLE_BELIEF_ASSIMILATION": "OFF", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": false, "information_content": false, "self_model_content": false}
    },
    "unit_faction_tension": {
      "profile_file": null,
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "OFF", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": false, "self_model_content": false}
    },
    "unit_information_source": {
      "profile_file": "unit_information_source.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": false, "information_content": true, "self_model_content": false}
    },
    "unit_selfmodel_pilot": {
      "profile_file": "unit_selfmodel_pilot.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "OFF", "ENABLE_SELF_MODEL_COGNITION": "ON"},
      "content": {"faction_tension_overrides": false, "information_content": false, "self_model_content": true}
    },
    "hero_guild_routing": {
      "profile_file": "hero_guild_routing.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "ON", "ENABLE_BELIEF_ASSIMILATION": "OFF", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": false, "information_content": false, "self_model_content": false}
    },
    "crowded_frontier": {
      "profile_file": null,
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "OFF", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": false, "information_content": false, "self_model_content": false}
    },
    "resource_dense_basin": {
      "profile_file": null,
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "OFF", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": false, "information_content": false, "self_model_content": false}
    },
    "frontier_marches": {
      "profile_file": "frontier_marches.yaml",
      "flags": {"ENABLE_ADVENTURE_ROUTING": "OFF", "ENABLE_BELIEF_ASSIMILATION": "ON", "ENABLE_SELF_MODEL_COGNITION": "OFF"},
      "content": {"faction_tension_overrides": true, "information_content": true, "self_model_content": false}
    }
  },
  "known_exceptions": {
    "self_model_content_without_flag": [
      {
        "world": "urban_political",
        "field": "pending_self_model_information_events",
        "flag": "ENABLE_SELF_MODEL_COGNITION",
        "citation": ["INFRA-259", "INFRA-260"],
        "reason": "pending_self_model_information_events is seeded in data/worlds/urban_political/world.yaml (pop_1, material.moon_resin.source, answer_kind=unknown), predating this epic, but ENABLE_SELF_MODEL_COGNITION has intentionally never shipped ON in any config/simulation_quality/profiles/*.yaml for this world. INFRA-259 and INFRA-260 (docs/parity_ledger/infrastructure.yaml) both confirm this was verified via a test-scoped FeatureFlagManager override only -- 'never a shipped profile default; confirmed absent from every config/simulation_quality/profiles/*.yaml and data/worlds/*.yaml'. STRAT-245 (docs/parity_ledger/strategic_cognition.yaml) confirms unit_selfmodel_pilot is the only world that ships this flag ON. Do not resolve this exception by turning the flag on in urban_political.yaml -- that is a real behavior change, out of scope for TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL."
      }
    ]
  }
}
```

**Do NOT touch:** `tests/simulation_quality/fixtures/grade_anchors.json` or any other existing
fixture file — this is a new, separate file.
**Verify:** `python3 -c "import json; json.load(open('tests/simulation_quality/fixtures/expected_world_flag_state.json'))"` parses without error; manual diff of every `worlds.<name>.flags`/`content` entry against the profile YAML reads and `world.yaml` greps already performed in this planning session (recorded in this plan — no re-derivation needed by the implementer).

### Step 2 — Register the new pytest marker
**Files:** `pyproject.toml`
**Change:** Add one new line to the `[tool.pytest.ini_options]` `markers` list (after the existing
`"feature_flag_default: ..."` line, `pyproject.toml:92`):
```
    "corpus_flag_guardrail: per-world calibration-profile feature-flag/content-field guardrail assertions",
```
**Do NOT touch:** any other marker definition, `scenario_flags`, or `feature_flag_default` — those
belong to the sibling scenario-defaults test file and must remain unchanged.
**Verify:** `pytest --markers | grep corpus_flag_guardrail` shows the new marker registered.

### Step 3 — Author the guardrail test file
**Files:** `tests/integration/test_world_profile_feature_flag_guardrail.py` (new)
**Change:** Create the file with the structure below. Import the real resolution helpers from
`tools/calibrate_simq.py` (`_resolve_profile`, `_load_profile_feature_flags`) rather than
reimplementing path/fallback logic — this keeps the test bound to the actual runtime mechanism and
prevents drift if `_resolve_profile`'s logic ever changes. `tools/` is not a package with `__init__.py`
under `src/`; import via `sys.path` manipulation matching the pattern already used inside
`calibrate_simq.py` itself (`sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))`), or
via `importlib` if a direct `from tools.calibrate_simq import ...` fails due to path setup — confirm
which import style resolves cleanly in this repo's pytest config before finalizing (check
`tests/integration/test_scenario_feature_flag_defaults.py`'s import style as one data point, though
it doesn't import from `tools/`; check whether any other test already imports from `tools/` as
precedent, e.g. grep `from tools\.` under `tests/`).

Module docstring: state purpose, cite `TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL`, cite
`docs/plans/audit_fix_plan.md` P2-E, and explicitly state this is the calibration-profile half of
P2-E (distinct from `INFRA-221`/`test_scenario_feature_flag_defaults.py`, which covers the
scenario-template half).

Module-level constants/helpers:
- `_FIXTURE_PATH = Path("tests/simulation_quality/fixtures/expected_world_flag_state.json")`
- `_WORLDS_DIR = Path("data/worlds")`
- `_GATED_FLAGS = ("ENABLE_ADVENTURE_ROUTING", "ENABLE_BELIEF_ASSIMILATION", "ENABLE_SELF_MODEL_COGNITION")`
- `_load_fixture() -> dict` — loads and returns the parsed fixture JSON (module-scoped, loaded once).
- `_live_world_names() -> set[str]` — lists `data/worlds/*` directories, excluding `world_index.json` and any non-directory entry.
- `_world_params() -> list[pytest.param]` — `[pytest.param(name, entry, id=name) for name, entry in fixture["worlds"].items()]`.
- `_read_world_pattern6_flags(world_name: str) -> dict` — reads `data/worlds/<world_name>/world.yaml`, returns booleans for whether `faction_tension_overrides`, `information_source_profiles`+`pending_information_responses`, and `pending_self_model_information_events` are present and non-empty (mirrors the fixture's `content` shape). Used only as a cross-check in test 2 if the implementer wants live verification in addition to the static fixture — optional; the primary source of truth for flags is `_load_profile_feature_flags()`, not a reimplementation of world.yaml parsing for flags.

Seven test functions (all in this one file, all marked `@pytest.mark.corpus_flag_guardrail`):

1. **`test_all_worlds_have_a_resolvable_profile_or_default_fallback`**
   For every world in `_live_world_names()`, call the real `_resolve_profile(world_name)` and assert
   it returns either `world_name` (profile file exists) or `"default"` (fallback), and that the
   fixture's `profile_file` for that world matches (`f"{world_name}.yaml"` when resolved to
   `world_name`, else `None`). Fails loudly if a world's fixture `profile_file` disagrees with what
   `_resolve_profile()` actually returns today.

2. **`test_flag_state_matches_expected_per_world`** — parametrized over `_world_params()`.
   For each `(world_name, entry)`: resolve the profile via `_resolve_profile(world_name)`, call
   `_load_profile_feature_flags(profile)`, and assert that for each flag in `_GATED_FLAGS`, the
   returned dict's value (defaulting to `"OFF"` if the key is absent — absence means OFF, per
   `FeatureFlagManager`'s own default) equals `entry["flags"][flag]`.

3. **`test_agency_da_anti_drift_guard`**
   Not parametrized generically — reads `fixture["_meta"]["agency_da_non_routing_worlds"]` directly
   and, for each of those 9 named worlds, asserts `_load_profile_feature_flags(_resolve_profile(w))`
   has `ENABLE_ADVENTURE_ROUTING` absent or `"OFF"`. Docstring cites
   `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s anti-drift note verbatim ("if any calibration world
   enables `ENABLE_ADVENTURE_ROUTING`, AGENCY will activate and grade anchors must be updated").
   Assertion failure message names the specific world and states this breaks the AGENCY-DA guard
   explicitly (not just "flag mismatch"), so a CI failure is immediately diagnostic. Also asserts,
   as a second half of the same test, that `fixture["_meta"]["agency_da_routing_worlds"]`
   (`simq_routing_test`, `hero_guild_routing`) both have it `"ON"` — the guard cuts both ways.

4. **`test_information_flag_content_pairing_both_directions`** — parametrized over `_world_params()`.
   For each world: `content_seeded = entry["content"]["information_content"]`,
   `flag_on = entry["flags"]["ENABLE_BELIEF_ASSIMILATION"] == "ON"`. Assert
   `content_seeded == flag_on` for every world with no exception (this pair has zero documented
   exceptions per the investigation — assert this holds for all 17 rows, no allow-list needed here).
   Failure message states which direction failed ("content seeded but flag OFF" vs. "flag ON but no
   content seeded") — this is AC 3's both-directions requirement made concrete for the one pair with
   no exceptions.

5. **`test_self_model_flag_content_pairing_both_directions_with_documented_exception`** —
   parametrized over `_world_params()`. Same shape as test 4 for
   `self_model_content` ↔ `ENABLE_SELF_MODEL_COGNITION`, except: before asserting, check whether
   `world_name` appears in `fixture["known_exceptions"]["self_model_content_without_flag"]`. If it
   does (currently only `urban_political`), assert the exception's specific shape holds
   (`content_seeded is True and flag_on is False`, i.e. the exception is exactly the asymmetry it
   claims to be — this catches the exception itself going stale) and skip the equality assertion for
   that world only, citing the exception's `citation` field in an informational assertion message or
   comment. For every other world, assert `content_seeded == flag_on` exactly as test 4 does. This
   ensures the exception list cannot silently grow — any new mismatch not present in
   `known_exceptions` fails loudly.

6. **`test_faction_content_has_no_flag_requirement`**
   Not parametrized over the general table — iterates the fixture worlds directly and asserts that
   for every world with `content["faction_tension_overrides"] is True`, none of the three
   `_GATED_FLAGS` being `"OFF"` is treated as a failure (i.e. this test positively asserts FACTION
   worlds may have all three flags OFF simultaneously and that is correct) — concretely: run this
   against `unit_faction_tension`, `dungeon_crawl`, `wilderness_survival` (the FACTION-only-content
   worlds per the fixture) and assert each has `ENABLE_ADVENTURE_ROUTING`, `ENABLE_BELIEF_ASSIMILATION`
   (unless also gated by INFO content, which `dungeon_crawl`/`wilderness_survival`/
   `unit_faction_tension` are not), and `ENABLE_SELF_MODEL_COGNITION` unconstrained by
   `faction_tension_overrides` presence alone. Docstring explains this exists to stop a future
   contributor from "fixing" a FACTION-only world by adding an unneeded flag.

7. **`test_fixture_covers_every_live_world_exactly`**
   Compares `set(fixture["worlds"].keys())` against `_live_world_names()` (live `data/worlds/`
   directory listing, excluding `world_index.json`). Asserts set equality, with a failure message
   listing worlds present on disk but missing from the fixture ("add a fixture entry") and worlds in
   the fixture but no longer on disk ("stale fixture entry — remove or investigate") separately. This
   is the self-enforcing version of AC 2/AC 3's "explicitly enumerates... not just the pre-epic
   baseline" — a future 18th world with no fixture entry fails this test immediately instead of
   silently not being covered by tests 2/4/5.

**Do NOT touch:** `tests/integration/test_scenario_feature_flag_defaults.py` (do not add tests here,
do not import from it, do not merge the two files — different subsystem, different parity entry).
Do not modify `tools/calibrate_simq.py`, `src/domains/optimization/feature_flags.py`, or any
`config/simulation_quality/profiles/*.yaml` / `data/worlds/*/world.yaml` file.
**Verify:** `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v` — all test
functions pass (test 2/4/5 each produce 17 parametrized cases; tests 1/3/6/7 are single functions).

### Step 4 — Run the new test and the regression surface
**Files:** none (verification only)
**Change:** Run, in order:
```
pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v
pytest tests/integration/test_scenario_feature_flag_defaults.py -m "not slow"
pytest tests/unit/config/test_phase10_feature_flags.py tests/unit/worldassembly/test_corpus_diversity.py -m "not slow"
```
Confirm all pass, per `test_plan.md`'s Scoped Pytest Commands. If test 5's exception check reveals
any world beyond `urban_political` with a real self-model asymmetry, or if test 2/4 fail against the
actual corpus state, **stop** — per the ticket's Out of Scope, do not loosen the test to force a
pass; either the fixture was transcribed wrong (fix the fixture to match reality) or a genuine
misconfiguration exists (file a targeted follow-up ticket per the ticket's Out of Scope guidance,
do not fix world/profile content in this ticket).
**Do NOT touch:** any world or profile file to make a failing assertion pass.
**Verify:** all three commands above exit 0.

### Step 5 — Add the new parity ledger entry (companion to the test, per test_plan.md)
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append a new entry, `id: INFRA-262` (next available ID, confirmed — highest existing is
`INFRA-261`), `status: verified`, `priority: P2`, documenting the new per-world calibration-profile
flag guardrail, its `test_path: tests/integration/test_world_profile_feature_flag_guardrail.py`, and
a `divergence_note`/`support_boundary` explicitly stating this is a distinct, non-duplicate companion
to `INFRA-221` (scenario-template half of P2-E) — this ticket closes the calibration-profile half.
Cite `INFRA-259`/`INFRA-260` in the entry text as the source of the one documented exception the new
test allow-lists.
**Do NOT touch:** `INFRA-221`, `INFRA-259`, `INFRA-260`, `INFRA-261`, or any other existing entry —
append only, do not edit existing entries' `status`/`v2_evidence`.
**Verify:** `python3 tools/validate_parity_ledger.py` (or the repo's equivalent parity-ledger
validation entrypoint — confirm exact tool name during implementation, e.g. via
`make` target list) passes with the new entry.

### Step 6 — Update `docs/plans/audit_fix_plan.md` P2-E section and Summary Table row
**Files:** `docs/plans/audit_fix_plan.md`
**Change:** Two edits:

(a) The P2-E section heading and body (lines 287–293, currently no resolution line — compare to the
resolved-item pattern used by every other resolved entry in this file, e.g. P2-D/P2-B above it).
Change the heading from:
```
### P2-E: Feature-gated phases have no per-scenario default test
```
to:
```
### P2-E: Feature-gated phases have no per-scenario default test — **RESOLVED (verified 2026-07-07)**
```
and append a **Resolution** paragraph after the existing **Fix** line:
```
**Resolution:** This finding spans two distinct mechanisms, only one of which had prior coverage.
`TCK-20260627-P2E-FEATURE-FLAG-TEST` (`INFRA-221`, `tests/integration/test_scenario_feature_flag_defaults.py`)
closed the scenario-definition half (`data/content/simulation_scenarios/*.yaml`, flag defaults
derived from the `perspective` field). `TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL`
(`INFRA-262`, `tests/integration/test_world_profile_feature_flag_guardrail.py`) closes the
calibration-profile half (`config/simulation_quality/profiles/<world>.yaml`, the
`_load_profile_feature_flags()` mechanism `tools/calibrate_simq.py` uses to apply per-world flag
overrides) — asserting expected `ENABLE_ADVENTURE_ROUTING`/`ENABLE_BELIEF_ASSIMILATION`/
`ENABLE_SELF_MODEL_COGNITION` state for all 17 corpus worlds, both directions of the Pattern-6
content/flag pairing, and the `ENABLE_ADVENTURE_ROUTING` AGENCY-DA anti-drift guard as a standalone
named test.
```

(b) The Summary Table row (`docs/plans/audit_fix_plan.md:623`). Change:
```
| P2-E | D09 F4 | **P2** | Testing | OPEN (not re-checked 2026-07-03) — S — per-scenario feature flag test |
```
to:
```
| P2-E | D09 F4 | **P2** | Testing | **RESOLVED (verified 2026-07-07)** — scenario-definition half closed by `INFRA-221`/`TCK-20260627-P2E-FEATURE-FLAG-TEST`; calibration-profile half closed by `INFRA-262`/`TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL` |
```

Also update the "Still open, no ticket exists yet" list at line 677, removing `P2-E` from that
enumeration (it currently reads `**Still open, no ticket exists yet (per 2026-07-03 status
refresh):** P2-E, P2-N, P3-A, P3-C — ...`) — change to `P2-N, P3-A, P3-C` and add a parenthetical
note matching the style of the adjacent P2-B/P1-D/P1-H notes: `(P2-E resolved 2026-07-07,
TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL — no longer pending.)`
**Do NOT touch:** any other row in the Summary Table, any other section body, or the "Suggested Fix
Order" narrative beyond the P2-E-specific parenthetical addition described above.
**Verify:** Visual diff review; `grep -n "P2-E" docs/plans/audit_fix_plan.md` shows all three
locations (section heading, summary table row, still-open list) consistently updated to RESOLVED/removed.

### Step 7 — `make evaluate` and knowledge index update
**Files:** none (verification/tooling only)
**Change:** Run `make evaluate` and confirm 0 regressions (expected no-op impact since this ticket
adds a test file and doc edits only, no world/code changes). Then run `make knowledge-index-update`
since `docs/plans/audit_fix_plan.md` changed.
**Do NOT touch:** any file `make evaluate` or `make knowledge-index-update` would normally leave
untouched — do not hand-edit generated index output.
**Verify:** `make evaluate` reports 0 regressions; `make knowledge-index-update` completes without
error and the index reflects the P2-E doc edit.

## Scope Guards

- Do not modify `src/domains/optimization/feature_flags.py`, `FeatureMode`, or any flag-gated
  phase's runtime behavior — this ticket is a static/config-level assertion test only.
- Do not modify `tools/calibrate_simq.py` — import and call its existing `_resolve_profile()` /
  `_load_profile_feature_flags()` functions as-is; do not refactor them as part of this ticket.
- Do not turn `ENABLE_SELF_MODEL_COGNITION` ON in `config/simulation_quality/profiles/urban_political.yaml`
  (or any other profile) to "fix" the documented exception — the exception is correct and cited
  (`INFRA-259`/`INFRA-260`); flipping the flag is an out-of-scope behavior change.
  If, during Step 3/4, the implementer determines `INFRA-259`/`INFRA-260` do NOT actually justify
  this specific asymmetry on close re-reading, stop and escalate for a human decision rather than
  silently accepting this plan's characterization or silently "fixing" the flag.
- Do not add any test to `tests/integration/test_scenario_feature_flag_defaults.py` — new tests live
  only in the new file, `tests/integration/test_world_profile_feature_flag_guardrail.py`.
- Do not re-scope, re-author, or edit any of tickets 1–9's world content
  (`data/worlds/*/world.yaml`, module/composition files, or any prior ticket's Completion Summary).
- Do not edit `tests/simulation_quality/fixtures/grade_anchors.json` or any other existing fixture.
- Do not edit any parity ledger entry other than appending the new `INFRA-262` entry (Step 5) —
  `INFRA-221`, `INFRA-259`, `INFRA-260`, `INFRA-261` and all others stay untouched.
- Do not edit any `docs/plans/audit_fix_plan.md` content beyond the three P2-E-specific locations
  named in Step 6.
- If Step 4 discovers a genuine misconfiguration beyond the one documented `urban_political`
  exception, do not loosen the test to pass — either fix the fixture (if it was mistranscribed
  relative to the real files) or stop and file a targeted follow-up ticket; do not touch the
  offending world/profile file in this ticket.

## Dependency Map

- Step 1 (fixture) must complete before Step 3 (test file imports/reads the fixture).
- Step 2 (pytest marker registration) can run independently, any time before Step 4 (test run needs
  the marker registered to avoid an "unknown marker" warning/strict-marker failure, if
  `--strict-markers` is configured — confirm during implementation).
- Step 3 depends on Step 1 (fixture must exist) but not on Step 2 for the test logic itself, only for
  marker registration cleanliness.
- Step 4 depends on Steps 1–3 all being complete.
- Step 5 (parity ledger) and Step 6 (audit_fix_plan.md) both depend on Step 4 passing — do not
  document a test as resolving anything before it actually passes.
- Step 7 depends on Steps 1–6 all being complete (evaluates the final state; knowledge-index-update
  needs Step 6's doc edit to already exist).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| New test exists loading every world's profile YAML (or default.yaml fallback) and asserting expected feature_flags state | Steps 1, 3 | `test_all_worlds_have_a_resolvable_profile_or_default_fallback`, `test_flag_state_matches_expected_per_world` |
| Test explicitly enumerates and covers all worlds added by tickets 4, 5, 6, 8 | Step 1 (fixture includes all 17), Step 3 test 7 | `test_fixture_covers_every_live_world_exactly` |
| Test asserts both directions of the flag/content-field pairing | Step 3 | `test_information_flag_content_pairing_both_directions`, `test_self_model_flag_content_pairing_both_directions_with_documented_exception` |
| Test asserts the 9 pre-existing non-routing worlds keep ENABLE_ADVENTURE_ROUTING OFF (AGENCY-DA guard) | Step 3 | `test_agency_da_anti_drift_guard` |
| Test passes against the actual corpus state after tickets 1-9 have landed | Step 4 | full `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v` run |
| docs/plans/audit_fix_plan.md P2-E section updated from OPEN to resolved, new test path cited, Summary Table row updated | Step 6 | manual diff review + `grep -n "P2-E"` check |

## Anti-Drift Notes

- **The urban_political exception is settled, not open.** `INFRA-259`/`INFRA-260` (confirmed read in
  full during planning) both explicitly state `pending_self_model_information_events` for
  `urban_political` was verified via a test-scoped override, "never a shipped profile default." This
  is not a bug to fix; it is the one case the guardrail test must allow-list by citation, per Step 3
  test 5's design. `STRAT-245` independently corroborates that `unit_selfmodel_pilot` is the only
  world shipping `ENABLE_SELF_MODEL_COGNITION` ON.
- **Only 2 of 4 Pattern-6 content fields are flag-gated.** `faction_tension_overrides` has no
  `FeatureMode` gate at all (`FactionScorer` runs unconditionally) — Step 3 test 6 exists specifically
  to prevent a future contributor from "fixing" this as if it were a gap. `ENABLE_ADVENTURE_ROUTING`
  has no Pattern-6 content-field counterpart — AGENCY activation is flag + `AdventureDecisionPhase`
  only, no seeded content field required. A naive "all 4 fields must pair with a flag" model is
  wrong and would false-fail on every FACTION-only world.
- **Four worlds correctly have no dedicated profile file** (`crowded_frontier`,
  `resource_dense_basin`, `unit_faction_tension`, `wilderness_survival`) and fall back to
  `default.yaml` (all flags OFF). These must appear as explicit fixture rows asserting all-flags-OFF,
  not be silently skipped because "there's no profile to load" — Step 1's fixture already includes
  all four with `profile_file: null`.
- **This ticket's new test file must never be merged with or import from
  `tests/integration/test_scenario_feature_flag_defaults.py`.** Confirmed by direct read: that file
  tests `data/content/simulation_scenarios/*.yaml` (14 scenario definitions, `perspective`-derived
  flag defaults, parity `INFRA-221`), a completely different mechanism from this ticket's
  `config/simulation_quality/profiles/` calibration-profile subsystem. Zero code or fixture overlap
  confirmed during planning.
- **17 worlds, not the ticket's pre-epic assumption of ~10.** The ticket's own Scope section text
  predates tickets 4/5/6/8 landing; the fixture and test must cover the full live corpus
  (`data/worlds/` minus `world_index.json`), which Step 3 test 7 makes self-enforcing so a future
  18th world can't silently fall out of coverage.
- **`_resolve_profile()` and `_load_profile_feature_flags()` are the real runtime mechanism** — the
  test must call these functions from `tools/calibrate_simq.py` directly rather than reimplementing
  path-fallback or YAML-parsing logic, to avoid the test and the real mechanism silently diverging
  over time.

## Unresolved Questions

None. The investigation's one substantive judgment call (the `urban_political` self-model exception)
already has a settled, cited, parity-verified answer (`INFRA-259`/`INFRA-260`, cross-corroborated by
`STRAT-245`), confirmed independently in this planning session by reading both entries in full. The
only conditional escalation path is the one named in Scope Guards above: if the implementer's own
close re-reading of `INFRA-259`/`INFRA-260` during Step 3/4 turns up a reason those entries do NOT
actually justify this specific asymmetry, that is grounds to stop and escalate — but nothing found
during this planning pass supports that outcome.

## Deviations

None substantive. Two minor notes from implementation:

1. **Step 3 import style**: the plan asked to "confirm which import style resolves cleanly" between
   `sys.path.insert(...)` (matching `calibrate_simq.py` itself) and a direct
   `from tools.calibrate_simq import ...`. Confirmed the direct import works cleanly with no path
   manipulation, because `pyproject.toml`'s `[tool.pytest.ini_options] pythonpath = ["."]` already
   puts the repo root on `sys.path` for every test run — `tests/unit/tools/test_simq_audit_gaps.py`
   (`import tools.simq_audit_gaps as sag`) is the existing precedent for this exact style. Used the
   direct import; no `sys.path` manipulation was needed or added.
2. **Step 3's optional `_read_world_pattern6_flags()` helper was not implemented.** The plan itself
   described it as optional ("Used only as a cross-check in test 2 if the implementer wants live
   verification in addition to the static fixture... not a reimplementation of world.yaml parsing for
   flags"). None of the 7 required test specs depend on it, and the fixture's `content` values were
   independently re-derived and verified against every live `world.yaml` before the fixture was
   written (see the ticket's Implementation Notes) — adding an unused helper would have been a
   premature abstraction.
3. **Step 6's row/line-number references (`:623`, list at `:677`) had drifted to `:634`/`:688`** by
   implementation time — an earlier ticket's edits to the same file shifted line numbers after the
   plan was written. Content match (heading text, table row text, list text) was exact and
   unambiguous; only the line numbers cited in the plan were stale. Edited by content match via
   `Edit`, not by line number, so this required no interpretation call.
4. **Step 7's `make evaluate` found 26 pre-existing `FACTION` pillar regressions**, not the 0
   regressions the plan expected ("should be a no-op impact-wise since this only adds a test").
   Verified via `git stash --include-untracked` + re-run that all 26 are already present on the
   unmodified branch tip (`135cce8c`, a prior, already-completed ticket in this epic,
   `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`) with none of this ticket's changes applied —
   this ticket touches no calibration data, anchors, or world/profile content, so it is not the
   cause. Not fixed here per Scope Guards (out of scope: static config-assertion test only); flagged
   as a candidate follow-up in the implementer's final report rather than silently absorbed or
   fixed unilaterally.

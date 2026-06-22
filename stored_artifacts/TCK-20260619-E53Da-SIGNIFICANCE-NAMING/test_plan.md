---
status: active
ticket_id: TCK-20260619-E53Da-SIGNIFICANCE-NAMING
artifact_type: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E53Da-SIGNIFICANCE-NAMING

## Regression Surface

Existing tests that touch the files this ticket modifies and MUST continue to pass:

| Test | File | What it covers | Risk |
|---|---|---|---|
| `test_significance_scoring_ranks_death_above_harvesting` (TC-1) | `test_chronicle_compiler.py:72` | entity_death=0.5, harvesting=0.1 | Low — no change to these keys |
| `test_hero_death_scores_higher_than_commoner_death` (TC-2) | `test_chronicle_compiler.py:87` | hero_bonus 0.3 on entity_death | Low — hero_bonus logic unchanged |
| `test_is_chronicle_worthy_filters_below_threshold` (TC-3) | `test_chronicle_compiler.py:102` | CHRONICLE_THRESHOLD=0.5 | Low — threshold unchanged |
| `test_known_event_types_score_correctly` (TC-4) | `test_chronicle_compiler.py:122` | Iterates ALL BASE_SIGNIFICANCE keys | **HIGH** — adding 6 new keys auto-expands coverage; test must still pass with new keys |
| `test_score_capped_at_1_0` (TC-5) | `test_chronicle_compiler.py:134` | cap at 1.0 for faction_destroyed+hero | Low — uses existing keys |
| `test_unknown_event_type_scores_default` (TC-6) | `test_chronicle_compiler.py:147` | unknown → 0.1 | Low — new faction keys not "unknown" |
| `test_milestone_naming_deterministic` (TC-13) | `test_chronicle_compiler.py:294` | entity_death, subject_id="1", entity_names={1: "Aldric"} | Low — int-path unchanged |
| `test_known_event_type_templates` (TC-14) | `test_chronicle_compiler.py:311` | **UPPERCASE keys** WAR_DECLARED, TERRITORY_TRANSFERRED, ALLIANCE_FORMED with old template format | **HIGH — MUST BE UPDATED**: this test uses uppercase keys and old single-faction template strings that will be wrong after rename + template upgrade |
| `test_unknown_event_type_falls_back_to_subject` (TC-15) | `test_chronicle_compiler.py:334` | Unknown event_type fallback | Low — fallback path unchanged |
| `test_era_naming_matches_dominant_type` (TC-16) | `test_chronicle_compiler.py:348` | ERA_NAMES keys, "ALLIANCE_FORMED" → "Era 5" | Safe — uppercase arg won't match new lowercase key |
| `test_calamity_includes_tick_not_subject` (TC-17) | `test_chronicle_compiler.py:362` | calamity template tick substitution | Low — calamity unchanged |
| `test_subject_id_not_integer_fallback` (TC-18) | `test_chronicle_compiler.py:377` | Non-numeric subject_id fallback | Low — fallback path still supported |
| All E51B grouper tests (TC-7 through TC-12) | `test_chronicle_compiler.py:162–285` | ChronicleGrouper — unchanged by this ticket | None |
| All E51D renderer tests (TC-R1 through TC-R9) | `test_chronicle_compiler.py:394–576` | ChronicleRenderer — unchanged by this ticket | None |

### Required TC-14 Update

The existing `test_known_event_type_templates` test case list (lines 316–328) must be updated to:
- Remove the 3 uppercase-key cases (`WAR_DECLARED`, `TERRITORY_TRANSFERRED`, `ALLIANCE_FORMED`)
- Add the 3 renamed lowercase cases with new dual-faction template strings
- Add the 3 new faction templates (`peace_treaty`, `betrayal`, `siege_begins`)

The updated cases should be:
```python
cases = [
    ("entity_death", "7", 10, "The Death of Ironhold"),
    ("faction_destroyed", "7", 20, "The Fall of Ironhold"),
    ("quest_completed", "9", 30, "The Quest of Thornwood Guild"),
    # Renamed + upgraded dual-faction templates:
    ("war_declared", "ALPHA:BETA", 40, "The ALPHA War against BETA"),
    ("alliance_formed", "ALPHA:BETA", 50, "The ALPHA–BETA Alliance"),
    ("territory_transferred", "border_region", 60, "The Conquest of border_region"),
    ("peace_treaty", "ALPHA:BETA", 70, "The Peace of ALPHA and BETA"),
    ("betrayal", "ALPHA:BETA", 80, "The Betrayal of ALPHA by BETA"),
    ("siege_begins", "castle_north", 90, "The Siege of castle_north"),
]
```

---

## New Tests Required

New test files to create:
- `tests/unit/chronicle/test_significance.py` — significance-only tests (E53Da faction scoring)
- `tests/unit/chronicle/test_naming.py` — naming-only tests (E53Da faction naming)

### `tests/unit/chronicle/test_significance.py`

#### `test_war_declared_scores_at_or_above_threshold`
- AC: `score(entry)` returns ≥ 0.9 for `event_type="war_declared"`
- Create entry with `event_type="war_declared"`, no hero payload
- Assert `EventSignificanceScorer.score(entry) == pytest.approx(0.95)`
- Assert `EventSignificanceScorer.is_chronicle_worthy(entry) is True`

#### `test_peace_treaty_scores_correctly`
- AC: returns 0.75 for `event_type="peace_treaty"`
- Assert `score == pytest.approx(0.75)`
- Assert `is_chronicle_worthy() is True` (0.75 >= 0.5)

#### `test_territory_transferred_scores_correctly`
- AC: returns 0.85 for `event_type="territory_transferred"`
- Assert `score == pytest.approx(0.85)`
- Assert `is_chronicle_worthy() is True`

#### `test_alliance_formed_scores_correctly`
- Score 0.80 for `event_type="alliance_formed"`
- Assert `score == pytest.approx(0.80)`

#### `test_siege_begins_scores_correctly`
- Score 0.80 for `event_type="siege_begins"`
- Assert `score == pytest.approx(0.80)`

#### `test_betrayal_scores_correctly`
- Score 0.85 for `event_type="betrayal"`
- Assert `score == pytest.approx(0.85)`

#### `test_all_six_faction_events_are_chronicle_worthy`
- Parametrize over all six faction event types
- Assert each `is_chronicle_worthy()` is True (all scores >= 0.5)

#### `test_faction_war_declared_event_in_narrative_ledger`
- Named AC from E53D parent epic
- Create a `NarrativeLedgerEntry` with `event_type="war_declared"`, `significance=0.95`
- Assert `EventSignificanceScorer.score(entry) >= 0.9` (AC verbatim from parent)
- Assert `EventSignificanceScorer.is_chronicle_worthy(entry) is True`

#### `test_faction_events_do_not_receive_hero_bonus`
- Confirm that `war_declared` + `entity_role=HERO` payload does not push score past cap unexpectedly
- `war_declared` base 0.95 + 0.3 hero_bonus → capped at 1.0; assert `score == pytest.approx(1.0)`

### `tests/unit/chronicle/test_naming.py`

#### `test_war_declared_dual_faction_template`
- AC: `name_milestone(entry, entity_names={})` with `event_type="war_declared"`, `subject_id="ALPHA:BETA"` returns `"The ALPHA War against BETA"`
- Use `faction_names=None` (raw ID fallback)

#### `test_alliance_formed_dual_faction_template`
- AC: with `event_type="alliance_formed"`, `subject_id="ALPHA:BETA"` returns `"The ALPHA–BETA Alliance"`
- Verify the em-dash (`–`) is correct Unicode U+2013

#### `test_territory_transferred_region_template`
- AC: with `event_type="territory_transferred"`, `subject_id="border_region"` returns `"The Conquest of border_region"`

#### `test_peace_treaty_dual_faction_template`
- with `event_type="peace_treaty"`, `subject_id="ALPHA:BETA"` returns `"The Peace of ALPHA and BETA"`

#### `test_betrayal_dual_faction_template`
- with `event_type="betrayal"`, `subject_id="ALPHA:BETA"` returns `"The Betrayal of ALPHA by BETA"`

#### `test_siege_begins_region_template`
- with `event_type="siege_begins"`, `subject_id="castle_north"` returns `"The Siege of castle_north"`

#### `test_faction_names_resolved_via_faction_names_dict`
- Pass `faction_names={"ALPHA": "Iron Legion", "BETA": "Shadow Court"}`
- `war_declared` + `subject_id="ALPHA:BETA"` → `"The Iron Legion War against Shadow Court"`

#### `test_region_names_resolved_via_region_names_dict`
- Pass `region_names={"border_region": "The Northern Marches"}`
- `territory_transferred` + `subject_id="border_region"` → `"The Conquest of The Northern Marches"`

#### `test_faction_era_names`
- `name_era(0, "war_declared")` → `"The Age of War"`
- `name_era(1, "alliance_formed")` → `"The Age of Alliances"`
- `name_era(2, "territory_transferred")` → `"The Age of Conquest"`

#### `test_old_entity_path_unchanged_with_new_params`
- Call `name_milestone(entry, entity_names={1: "Aldric"}, faction_names=None, region_names=None)` with `event_type="entity_death"`, `subject_id="1"`
- Assert result is `"The Death of Aldric"` — existing int-path still works with new optional params

#### `test_non_colon_subject_id_not_treated_as_faction`
- `event_type="entity_death"`, `subject_id="single_id"` (no colon)
- Should still resolve via int-cast or raw fallback, NOT split as faction pair

#### `test_format_map_no_keyerror_on_unknown_template_vars`
- Ensure that if a template with `{source_faction}` is rendered for a plain entity event (no colon in subject_id), no `KeyError` is raised — `fmt_vars` defaults give empty string via `defaultdict`

---

## Scoped Pytest Commands

```bash
# Run only the new faction-specific tests
pytest tests/unit/chronicle/test_significance.py -x -v
pytest tests/unit/chronicle/test_naming.py -x -v

# Run all chronicle unit tests (includes regressions)
pytest tests/unit/chronicle/ -x -v

# Targeted single-test run for E53D parent AC
pytest tests/unit/chronicle/test_significance.py::test_faction_war_declared_event_in_narrative_ledger -x -v

# Confirm TC-4 auto-expanded correctly
pytest tests/unit/chronicle/test_chronicle_compiler.py::test_known_event_types_score_correctly -x -v

# Confirm TC-14 updated correctly
pytest tests/unit/chronicle/test_chronicle_compiler.py::test_known_event_type_templates -x -v
```

---

## Anti-Drift Test Guards

1. **TC-4 guard**: After adding 6 new keys to `BASE_SIGNIFICANCE`, `test_known_event_types_score_correctly` iterates all keys. If any score value in the dict differs from what is expected, the test catches it immediately. Run TC-4 first after modifying `significance.py`.

2. **TC-14 update is mandatory**: Do not leave `test_known_event_type_templates` with uppercase key assertions after the rename. The test will fail (key miss, wrong template output). Update the cases list as specified above before committing.

3. **TC-16 uppercase guard**: The `name_era(4, "ALLIANCE_FORMED") == "Era 5"` assertion (line 357) is intentionally preserved because it passes an uppercase string that should NOT match the new lowercase `"alliance_formed"` ERA_NAMES key. This assertion must NOT be removed — it guards against accidentally making ERA_NAMES case-insensitive.

4. **`str.format_map` guard**: `test_format_map_no_keyerror_on_unknown_template_vars` explicitly guards the decision to use `format_map` with `defaultdict(str, ...)` instead of `format(**kwargs)`. If the implementation uses `format(**kwargs)`, this test will raise `KeyError` and catch the drift.

5. **Parity ledger update guard**: After implementation, `SOC-CHRON-001` and `SOC-CHRON-003` in `docs/parity_ledger/social_narrative.yaml` must be updated. The new `SOC-FAC-001` through `SOC-FAC-006` entries must point to passing test paths. Leaving these stale is a parity violation detectable at audit time.

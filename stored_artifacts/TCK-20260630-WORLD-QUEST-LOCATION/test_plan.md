---
ticket_id: TCK-20260630-WORLD-QUEST-LOCATION
phase: test_plan
---

# Test Plan

## Unit Tests (tests/unit/worldbuilding/test_world_compiler.py)

### New Tests to Add

**test_quest_location_tag_matches_region_type**
- Build minimal WorldSpec with region `type: "wilderness"` and quest `required_location_tags: ["wilderness"]`
- Call `WorldCompiler.compile(spec, seed=42)`
- Assert `report["warnings"]` is empty
- Verifies: compiler accepts quest tag that matches region.type

**test_quest_location_tag_matches_region_explicit_tag**
- Build minimal WorldSpec with region `type: "wilderness"`, `tags: ["mine", "underground"]`
- Quest has `required_location_tags: ["mine", "underground"]`
- Assert zero warnings
- Verifies: explicit region tags satisfy quest requirements

**test_quest_location_tag_warns_on_genuine_mismatch**
- Build minimal WorldSpec with region `type: "wilderness"`, no tags
- Quest has `required_location_tags: ["settlement"]`  (nothing matches)
- Assert `len(report["warnings"]) >= 1`
- Assert "settlement" in warning text
- Verifies: warning still fires when truly no match exists (regression guard)

**test_quest_location_tag_type_partial_match**
- Build spec: region type "road" + tags ["wilderness"]; quest needs ["road", "wilderness"]
- Assert zero warnings
- Verifies: mixed type+tags combination satisfies both tags

### Existing Test Coverage

**test_compiler_quest_referential_warnings** (existing, line 148)
- Must still pass after fix — it uses `"unknown_forest"` which genuinely doesn't match any region → warning expected

## Integration Tests (tests/integration/worldassembly/)

**test_real_content_world_compositions.py** (or similar)
- Run full assembly + compile on all four worlds
- Assert zero quest location warnings in each compile report

## Schema Tests

- Load frontier_village_core.yaml through WorldModuleSpec — verify `regions[0].tags == ["plain", "settlement"]` after YAML update
- RegionSpec round-trip: `tags` field serializes/deserializes correctly
- RegionSpec with `tags=[]` (default) still validates

## Compile Verification Script

After implementation, run:
```bash
python3 tools/compile_all_worlds.py
```
or equivalent to recompile all worlds and verify `world_compile_report.json` has zero quest location warnings.

## Pass/Fail Criteria

| Test | Expected |
|------|----------|
| test_quest_location_tag_matches_region_type | PASS (0 warnings) |
| test_quest_location_tag_matches_region_explicit_tag | PASS (0 warnings) |
| test_quest_location_tag_warns_on_genuine_mismatch | PASS (≥1 warning) |
| test_quest_location_tag_type_partial_match | PASS (0 warnings) |
| test_compiler_quest_referential_warnings (existing) | PASS (still warns on unknown) |
| All integration/worldassembly/ tests | PASS |
| dungeon_crawl compile report | 0 quest warnings |
| urban_political compile report | 0 quest warnings |
| wilderness_survival compile report | 0 quest warnings |
| generated_frontier_3_42 compile report | 0 quest warnings |

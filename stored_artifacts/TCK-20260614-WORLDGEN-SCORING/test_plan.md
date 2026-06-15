# Test Plan — TCK-20260614-WORLDGEN-SCORING

## Test File
`tests/unit/worldgeneration/test_module_scorer.py`

## Test Cases

| # | Test Name | What it validates |
|---|-----------|-------------------|
| 1 | `test_danger_level_conflict_scores_higher` | With `danger_level=3.0`, conflict/danger-tagged modules score higher than settlement modules |
| 2 | `test_settlement_style_none_penalises_settlement` | `settlement_style="none"` → settlement module score near 0, reasons mention "penalises settlement type" |
| 3 | `test_required_modules_always_score_one` | Required module gets score=1.0, reasons=["required by intent"] |
| 4 | `test_all_scores_in_range` | All ModuleScore.score values in [0.0, 1.0] |
| 5 | `test_determinism` | Calling twice with same inputs returns identical scores, reasons, dimensions |
| 6 | `test_reasons_non_empty_for_all` | Every module has non-empty reasons list |
| 7 | `test_dimensions_has_at_least_one_key` | Every non-required module has at least one dimension key |

## Stub Strategy
Construct `WorldModuleSpec` directly with minimal required fields:
- `module_id`, `module_type`, `display_name` are required
- `observability_tags` (not `tags`) for tag-based danger scoring
- No loading from YAML files

## Run Command
```bash
python3 -m pytest tests/unit/worldgeneration/test_module_scorer.py -q --tb=short
```

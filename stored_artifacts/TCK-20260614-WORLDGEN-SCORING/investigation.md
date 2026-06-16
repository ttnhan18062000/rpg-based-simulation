# Investigation — TCK-20260614-WORLDGEN-SCORING

## Key Findings

### GenerationIntentSpec fields (src/worldgeneration/schema.py)
- `generation_id: str` (required)
- `seed: int` (required)
- `terrain_style: str` (default "temperate")
- `settlement_style: str` (default "scattered")
- `danger_level: float` (default 1.0)
- `resource_density: float` (default 0.5)
- `population_scale: float` (default 1.0)
- `required_modules: List[str]` (default [])

### WorldModuleSpec fields (src/worldmodules/schema.py)
- `module_id: str` (required)
- `module_type: str` (required; one of: terrain, settlement, ecology, economy, conflict, population, danger_zone)
- `display_name: str` (required)
- `description: Optional[str]`
- `version: str` (default "1.0.0")
- `provides: List[str]`
- `resource_recipes: List[ResourceRecipeSpec]`
- `population_recipes: List[PopulationRecipeSpec]`
- `observability_tags: List[str]` — NOTE: this is the tag field (NOT a generic `tags` field)

### Critical: No `tags` field on WorldModuleSpec
The ticket spec refers to module `tags` for danger scoring. The actual field is `observability_tags`. The scorer uses `observability_tags` for tag-based danger matching.

### Existing generator (src/worldgeneration/generator.py)
- Hardcodes `1.2 * intent.danger_level` and `1.5 * intent.danger_level` for region hazard levels
- No module scoring or selection logic
- `WorldProceduralGenerator.__init__` takes `catalog_repo` and `module_repo`

### Test directory
- `tests/unit/worldgeneration/` already exists with `__init__.py` and `test_generator.py`
- No `test_module_scorer.py` yet — create it

### Parity ledger
- Last entry: `SUBSTRATE-NEW-007` — next is `SUBSTRATE-NEW-008`

## Scope Decisions
- `ModuleScorer` is a pure static method — no I/O, no side effects
- Tag-based danger scoring uses `observability_tags` (the actual field name)
- `module_type` in `{"conflict", "danger_zone"}` also triggers danger scoring
- Normalization: average of dimension scores clamped to [0.0, 1.0]

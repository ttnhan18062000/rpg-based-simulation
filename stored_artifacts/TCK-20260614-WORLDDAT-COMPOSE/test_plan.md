---
artifact_type: test_plan
ticket_id: TCK-20260614-WORLDDAT-COMPOSE
date: 2026-06-15
---

# Test Plan: TCK-20260614-WORLDDAT-COMPOSE

## Target File
`tests/integration/worldassembly/test_real_content_world_compositions.py`

## Tests to Add

### test_wilderness_survival_composition
- Load `data/content/world_compositions/wilderness_survival.yaml`
- Validate as WorldCompositionSpec
- Assemble via WorldAssemblyResolver.assemble() → ResolvedWorldBundle
- Compile via WorldCompiler.compile() → (AuthoritativeState, report)
- Assert: world_id == "wilderness_survival", bundle is not None, state is not None

### test_urban_political_composition
- Load `data/content/world_compositions/urban_political.yaml`
- Validate as WorldCompositionSpec
- Assemble → ResolvedWorldBundle
- Compile → (AuthoritativeState, report)
- Assert: world_id == "urban_political"
- Assert: len(bundle.compile_context.factions) >= 2 (faction relationships present)

### test_dungeon_crawl_composition
- Load `data/content/world_compositions/dungeon_crawl.yaml`
- Validate as WorldCompositionSpec
- Assemble → ResolvedWorldBundle
- Compile → (AuthoritativeState, report)
- Assert: world_id == "dungeon_crawl"
- Assert: "hero_guild_perspective" in spec.default_perspectives
- Assert: len(bundle.world_spec.quest_definitions) >= 2

## Pre-existing failures
17 pre-existing failures in test_strict_world_matrix.py (duplicate resource collision) — unrelated.

## Run command
```bash
python3 -m pytest tests/integration/worldassembly/test_real_content_world_compositions.py -q --tb=short 2>&1 | tail -20
```

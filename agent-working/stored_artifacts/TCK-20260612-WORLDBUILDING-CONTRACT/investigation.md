---
ticket_id: TCK-20260612-WORLDBUILDING-CONTRACT
phase: investigation
---
IDs: WORLD-050/051/052 (compiler+schema+__init__), WORLD-060/061/062 (repository), WORLD-070/071/072 (validator+recipe+cli), CLI-002 (cli). Two compilation paths: direct (WorldSpec→AuthoritativeState) and composition path via WorldAssembly. Compiler uses `random` — not fully deterministic without external seed. Validator: abort on ERROR severity. RegionRecipeSpec: min_x≤max_x, min_y≤max_y validation.

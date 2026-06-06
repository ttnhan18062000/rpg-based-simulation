# design-03: Data-Driven Content Registries

## Objective
Externalize massive configuration dictionaries (`ITEM_REGISTRY`, `CLASS_DEFS`, `SKILL_DEFS`, `TRAIT_DEFS`) from Python source code into structured YAML or JSON files.

## Rationale
As we scale into Epic-10 (Enchantment), Epic-12 (Personalities), and Epic-18 (Entity Progression Depth), defining hundreds of static properties inside Python files will bloat the codebase and hinder rapid iteration. Moving this to data-driven configuration decouples content creation from business logic compilation.

## Status
DONE

## Final Status
**DONE**: Implemented `src/core/registry_loader.py` using Pydantic `TypeAdapter` for robust validation. Successfully externalized item, class, skill, breakthrough, and trait definitions into JSON data files, decoupling content from engine logic.

**Tier:** standard
**Type:** chore
**Priority:** P1

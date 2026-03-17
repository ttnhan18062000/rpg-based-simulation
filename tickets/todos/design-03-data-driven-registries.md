# design-03: Data-Driven Content Registries

## Objective
Externalize massive configuration dictionaries (`ITEM_REGISTRY`, `CLASS_DEFS`, `SKILL_DEFS`, `TRAIT_DEFS`) from Python source code into structured YAML or JSON files.

## Rationale
As we scale into Epic-10 (Enchantment), Epic-12 (Personalities), and Epic-18 (Entity Progression Depth), defining hundreds of static properties inside Python files will bloat the codebase and hinder rapid iteration. Moving this to data-driven configuration decouples content creation from business logic compilation.

## Scope & Affected Systems
- **Target Files**: `src/core/items.py` (850+ lines), `src/core/classes.py` (900+ lines), `src/core/traits.py` (400+ lines).
- **Implementation Steps**:
  1. Define rigid JSON/YAML schemas matching the frozen Pydantic dataclasses (`ItemTemplate`, `ClassDef`, `SkillDef`, `BreakthroughDef`, `TraitDef`).
  2. Build a central `src/core/registry_loader.py` that reads these files, validates them through Pydantic `TypeAdapter`s, and populates the in-memory dicts (`ITEM_REGISTRY`, `CLASS_DEFS`, etc.).
  3. Strip the hardcoded `_reg(...)` calls and massive dictionaries out of the python source files.
  4. Hook `registry_loader.py` into the FastAPI `lifespan` event (`src/api/app.py`) to guarantee registries are loaded before the engine starts or API serves requests.

## Dependencies
- Must be completed before heavily extending definitions in **epic-18** Phase A (which adds Racial Profiles and Leveling Curves to the `ClassDef` logic).

## Acceptance Criteria
- Engine starts and plays identically.
- Replay outputs match the deterministic fingerprint exactly.
- Validation via Pydantic catches missing/bad fields in the YAML/JSON on startup.

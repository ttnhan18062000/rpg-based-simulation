# Walkthrough: RPG V2 Engine Documentation Audit & Hierarchy

We have successfully reorganized the V2 RPG Engine documentation into a developer-first nested hierarchy that mirrors the source code structure.

## Key Changes

### 1. New Documentation Hierarchy
Established a clean, logical structure for all technical specifications:
- `docs/core/`: Foundation models (State, Entities, Attributes, Items).
- `docs/engine/`: Orchestration & Laws (Kernel, Pipeline, Architecture).
- `docs/systems/`: Gameplay domains (Combat, Strategy, World, Economy).
- `docs/guidelines/`: Best practices and conventions.
- `docs/archive/`: Legacy and milestone-specific history.

### 2. Core Architectural Specifications [NEW]
Added three foundational documents to define the engine's "Atomic Laws":
- [Authoritative Pipeline](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/authoritative_pipeline.md): Detailed mapping of the 17-phase mutation refinement loop.
- [State Management](file:///home/vboxuser/Work/rpg-based-simulation/docs/core/state.md): Defines the "Frozen Lifecycle" and component-based composition.
- [Simulation Kernel](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/kernel.md): Details the 6-phase deterministic simulation clock.

### 3. Logic Gap Identification
Identified and tagged latent discrepancies in the current source:
- `src/engine/pipeline_phases/actor_validity.py`: Added TODOs for missing `status_sleeping` checks and `CombatUpdate` rejections.
- `src/systems/strategic_systems/intelligence.py`: Added TODO for magic number `30` in project switching logic.

### 4. Link Integrity & Cleanup
- Automated fixing of 100+ broken or environment-specific links.
- Created `README.md` entry points for every major directory to guide new developers.
- Archived outdated planning documents to reduce "doc noise."

## Verification Results

### Automated Tests
Ran the `tests/docs/` suite to ensure link integrity and contributor guardrails:
```bash
pytest tests/docs/
# Output: 9 passed, 1 skipped in 0.27s
```

### Manual Audit
- Verified that `logic_checklist_exhaustive.md` remains consistent and accessible.
- Confirmed that the new hierarchy correctly maps to `src/` and `tests/` subdirectories.

## Next Steps
- **Developer Review**: Review the `TODO:` tags in `actor_validity.py` and `intelligence.py` for implementation.
- **System Expansion**: Continue expanding `docs/systems/` as new features are added, following the `authoritative_pipeline.md` template.

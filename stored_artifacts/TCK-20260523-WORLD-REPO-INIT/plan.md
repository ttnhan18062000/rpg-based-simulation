# Implementation Plan: World Repository & Versioning

Establish a robust, secure repository layer for managing, loading, listing, and saving WorldSpecs from YAML files.

## Proposed Changes

### Worldbuilding Framework

#### [NEW] [repository.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/repository.py)
Implement `WorldRepository` to manage specifications within a worlds directory:
- Custom domain exception `WorldRepositoryError`.
- `__init__(self, worlds_dir: str | Path)` resolving the worlds root.
- `_resolve_world_path(self, world_id: str) -> Path` returning the path to `{world_id}/world.yaml` with strict path traversal checking (validation of allowed characters in `world_id` and strict parenthood checking).
- `list_worlds(self) -> list[str]` returning list of folders containing a `world.yaml`.
- `load_world(self, world_id: str) -> WorldSpec` loading the spec safely.
- `save_world(self, spec: WorldSpec) -> Path` saving spec into `{world_id}/world.yaml`.
- `rebuild_index(self) -> dict` scanning folder, validating specs, and regenerating `world_index.json`.

#### [MODIFY] [__init__.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/__init__.py)
Export `WorldRepository` and related exceptions.

#### [NEW] [test_world_repository.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/worldbuilding/test_world_repository.py)
Create isolated unit test suite covering listing, secure loading, path traversal blocking, invalid files, saving, and manifest index building.

---

## Verification Plan

### Automated Tests
Run unit tests with pytest:
```bash
pytest tests/unit/worldbuilding/test_world_repository.py
```
Ensure all tests execute cleanly with zero errors.

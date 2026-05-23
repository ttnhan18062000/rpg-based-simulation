# Test Plan: World Repository Verification

We will verify the implementation using isolated, deterministic unit tests in `tests/unit/worldbuilding/test_world_repository.py`.

## Test Scenarios

1. **Listing Worlds**:
   - Create a temp worlds directory with two valid subfolders containing `world.yaml`.
   - Verify `list_worlds()` returns both IDs.

2. **Loading Specs by ID**:
   - Create a valid YAML world.
   - Verify `load_world(world_id)` returns a valid `WorldSpec` model instance.

3. **Missing/Invalid World Errors**:
   - Call `load_world(world_id)` on a non-existent ID; verify custom `InvalidWorldSpecError` or descriptive exception is raised.
   - Put a corrupted YAML file inside a world folder; verify a clear parser error is raised.

4. **Duplicate ID Rejection**:
   - Verify that trying to save a world with a `world_id` that is already registered under a different folder path raises a validation or conflict error.

5. **Path Traversal Protection**:
   - Call `load_world("../../etc/passwd")` or `load_world("../any")`; verify a strict `ValueError` or custom security exception is raised and no file access occurs.
   - Verify `save_world("../../etc/passwd", spec)` is blocked identically.

6. **Index Build & Rebuild**:
   - Rebuild index from a directory with multiple valid worlds.
   - Verify that `world_index.json` is correctly serialized and populated with the appropriate `VALIDATED` status and timestamps.

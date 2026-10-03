---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260523-WORLD-REPO-INIT
artifact_type: investigation
tags: [world, repo, init]
---

# Investigation: World Repository Design & Security

## Root Directory Structure
The repository layer will manage world directories underneath a designated `worlds_dir` root. By default, this will be `data/worlds/`.

Inside this root:
- Each world has its own subdirectory: `data/worlds/{world_id}/world.yaml`.
- An optional manifest index exists at: `data/worlds/world_index.json`.

## Path Traversal Protection
Path traversal is a major risk when loading/saving files dynamically based on input `world_id` strings. We will address this via multi-layered security checks:
1. **Input Sanitization**: Assert that the `world_id` contains only letters, digits, underscores, and hyphens. Characters like `.`, `/`, `\`, or spaces will be strictly rejected.
2. **Directory Ancestry Lock**: Check that the resolved absolute path of the target directory/file is strictly a child of the resolved absolute path of the worlds root directory:
   ```python
   worlds_root_abs = Path(worlds_dir).resolve()
   target_path_abs = Path(target_path).resolve()
   if worlds_root_abs not in target_path_abs.parents:
       raise PermissionError("Path traversal detected")
   ```

## Manifest / Index Semantics
The index file `world_index.json` will list available worlds. Its structure will hold metadata fields:
- `world_id`: Unique identifier
- `name`: Human-readable name
- `path`: Relative path from the root
- `schema_version`: Verifies correct API version
- `tags`: Tag lists for filtering
- `created_at` / `updated_at`: String timestamps
- `status`: One of `DRAFT`, `VALIDATED`, `DEPRECATED`, `BROKEN`

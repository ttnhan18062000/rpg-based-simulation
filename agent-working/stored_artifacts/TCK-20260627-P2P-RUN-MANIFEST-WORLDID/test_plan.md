---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2P-RUN-MANIFEST-WORLDID
artifact_type: test_plan
tags: [run-manifest, observability, world-id]
---

# Test Plan — Add world_id to RunManifest

## Scope

- `tests/unit/observability/test_run_artifact_repository.py` — add `world_id` coverage
- Existing manifest tests must continue to pass without change

## Test Cases

### 1. world_id default ("unknown")
`test_run_manifest_world_id_default` — construct `RunManifest` without `world_id`; assert field
serializes to `"unknown"`.

### 2. world_id explicit value
`test_run_manifest_world_id_explicit` — construct `RunManifest` with `world_id="dungeon_crawl"`;
assert `model_dump()["world_id"] == "dungeon_crawl"`.

### 3. world_id round-trips through repository
`test_manifest_world_id_persists_via_repo` — create a run with `world_id="urban_political"`,
write and read back via `RunArtifactRepository`; assert `read_manifest().world_id == "urban_political"`.

### 4. Existing tests — no regressions
All existing `test_run_artifact_repository.py` tests pass unchanged (they construct `RunManifest`
without `world_id`, which should work fine with the default).

## Run Command

```
pytest tests/unit/observability/test_run_artifact_repository.py -v
```

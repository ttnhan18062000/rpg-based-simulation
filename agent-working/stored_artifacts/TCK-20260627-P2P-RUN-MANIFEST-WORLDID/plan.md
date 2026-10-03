---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2P-RUN-MANIFEST-WORLDID
artifact_type: plan
tags: [run-manifest, observability, world-id]
---

# Plan — Add world_id to RunManifest

## Summary

Three-file change. No architecture change. Pydantic default ensures backward compatibility.

## Unresolved Questions

None.

## Changes

### 1. `src/observability/reporting/artifact_repository.py`
Add `world_id: str = "unknown"` field to `RunManifest` after `failure_reason` (before the world
assembly sidecar block, for logical grouping near identity fields).

### 2. `src/engine/kernel.py`
- Add `world_id: Optional[str] = None` to `Kernel.__init__()` signature (after `module_fingerprints`).
- In the manifest construction block (line 152), add `world_id=world_id or "unknown"` to the
  `RunManifest(...)` call.

### 3. `src/cli/entry.py`
Pass `world_id=world_id` to `Kernel(...)` at line 245. The local variable `world_id` is already set
at line 206.

### 4. `src/lab/orchestrator.py`
At the two `Kernel(...)` call sites (lines 209 and 222), pass `world_id=scenario_spec.world_id`.
`scenario_spec` is in scope at both call sites (loaded at line 67).

## No Changes Needed

- `RunArtifactRepository` — no custom serializer; Pydantic handles it automatically.
- All other Kernel callers — will produce `world_id: "unknown"` via the default.

## Review Status

APPROVED — straightforward additive change with a safe default, no risk of breaking existing callers
or manifests.

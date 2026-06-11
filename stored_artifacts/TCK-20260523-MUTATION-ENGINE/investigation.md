---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-ENGINE
artifact_type: investigation
tags: [mutation, engine]
---

# Investigation Report - Mutation Engine

## Codebase Analysis
- **`WorldSpec`** and **`ScenarioSpec`** use Pydantic v2 with `frozen=True` configuration configurations. Direct attribute assignments like `spec.topology.width = 10` are blocked at runtime.
- **Isolating Mutations**: To modify them safely without in-place mutation, the best approach is to dump the specs to dicts using `spec.model_dump(by_alias=True)`, apply our custom mutating functions recursively or iteratively, and then reconstruct/validate them back using Pydantic `model_validate(dict)`.
- **Pluggable Rules Validation**: After Pydantic reconstructs the mutated model successfully, we must execute `WorldValidator().validate()` and `ScenarioValidator().validate()` to run all semantic and topological integrity checks.

## Path Traversal Map
A path segment `a.b.c` on `WorldSpec` traverses:
1. `a`: Root fields (e.g. `resources`). If the value is a list of dicts:
2. `b`: Look for an element in the list whose ID matches `"b"`. If not found but `"b"` is an intermediate helper (like `"nodes"` in `"resources.nodes.wood_zone.count"`), we skip `"b"` and search using the next segment `"wood_zone"`.
3. `c`: Modifies the leaf target `"count"`.

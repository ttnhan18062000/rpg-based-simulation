---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-WORLDCOMPILER-PLACE-WIRING
artifact_type: plan
tags: [content]
---

# Plan — TCK-20260902-WORLDCOMPILER-PLACE-WIRING

1. Read `WorldCompiler.compile()` end-to-end to find where region content is currently constructed flat.
2. Add Place-shaped content recognition and `PlaceState` construction, linked via
   `TCK-20260902-PLACE-SCHEMA-MIGRATION`'s dual-sided membership fields.
3. Confirm non-Place-shaped content still compiles unchanged (no regression to unmigrated worlds).
4. Write a unit test constructing a minimal Place-shaped content fixture and asserting correct
   `PlaceState`/`RegionState.places` output — do not rely on a full pilot-world run for this.

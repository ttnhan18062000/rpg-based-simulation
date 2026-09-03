---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-WORLDCOMPILER-PLACE-WIRING
artifact_type: test_plan
tags: [content]
---

# Test Plan — TCK-20260902-WORLDCOMPILER-PLACE-WIRING

**Normal flow:** minimal Place-shaped content fixture compiles to correct `PlaceState`/`RegionState`
output.

**Edge cases:** content with zero Places in a Region; content mixing Place-shaped and legacy-flat
regions in the same world (this is exactly what Stage B later stresses at scale).

**Failure modes:** malformed Place content (missing required field) fails compilation with a clear error,
not a silent partial construction.

**Regression-prone paths:** every currently-compiling world must still compile unchanged until its own
migration ticket lands.

**Scope command (fill in exact path once located):**
`pytest tests/unit/worldbuilding/ -k "compiler" -m "not slow"`.

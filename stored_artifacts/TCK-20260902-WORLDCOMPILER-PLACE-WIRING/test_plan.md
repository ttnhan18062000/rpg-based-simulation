---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-WORLDCOMPILER-PLACE-WIRING
artifact_type: test_plan
tags: [content]
---

# Test Plan — TCK-20260902-WORLDCOMPILER-PLACE-WIRING

**Normal flow:** a Place-shaped region compiles to a real `PlaceState`, correctly linked to its parent
region on both sides of the dual-sided membership decision.

**Edge cases:** multiple Places in one region; a world mixing Place-shaped and legacy-flat regions; a
region with zero Places (existing content's default).

**Failure modes:** an invalid `PlaceKind` value is rejected at Pydantic schema validation time, not
silently accepted or discovered later.

**Regression-prone paths:** every existing (non-Place-shaped) world must compile with byte-identical
`places=[]` output — the single most important acceptance criterion, since a false positive here would
silently corrupt every one of the 21 existing worlds' compiled state.

**Composition-path specific:** place ids must be namespaced with the same module prefix as their parent
region id, avoiding collision when a module is composed multiple times.

**Scope command (used):**
`pytest tests/unit/worldbuilding/test_place_wiring.py tests/unit/worldassembly/test_resolver.py -v -m "not slow"`
— 6 + 2 new tests, all passed.
Full regression: `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/unit/worldmodules/ tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/ -m "not slow"`
— 893 passed, 2 skipped (pre-existing, unrelated), 0 failed.

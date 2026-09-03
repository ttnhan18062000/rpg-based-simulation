---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-SCHEMA-MIGRATION
artifact_type: test_plan
tags: [content]
---

# Test Plan — TCK-20260902-PLACE-SCHEMA-MIGRATION

**Normal flow:** construct a `PlaceState`, attach to a `RegionState`, confirm both directions of the
membership reference resolve consistently.

**Edge cases:** a Region with zero Places (empty wilderness, per the plan doc); a Place with no
`owner_faction_id` (sovereignty defaults to the parent Region).

**Failure modes:** a `place_id` back-reference pointing to a Place not present in its Region's `places`
list must be caught (invariant violation), not silently tolerated.

**Regression-prone paths:** canonical-hash round-trip for every new field; existing `RegionState`
construction/serialization tests must still pass unchanged.

**Scope command (fill in exact path once located):**
`pytest tests/unit/worldbuilding/ tests/unit/core/ -k "place or region" -m "not slow"`.

---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-SCHEMA-MIGRATION
artifact_type: plan
tags: [content]
---

# Plan — TCK-20260902-PLACE-SCHEMA-MIGRATION

1. Add `PlaceKind` enum and `PlaceState` dataclass to `src/worldbuilding/schema.py` per the Target Shape.
2. Extend `RegionState` with `places: List[str]`.
3. Add the cached `place_id` back-reference field to the appropriate entity/building component, mirroring
   `NavigationComponent.region_id`'s placement.
4. Wire `to_canonical_dict()`/`from_canonical_dict()` for every new field immediately — do not defer, per
   this session's own Social/Knowledge canonical-hash gap findings.
5. Write construction + canonical round-trip + back-reference-consistency unit tests.
6. Confirm with the concurrent M3 session before touching `src/core/state.py`.

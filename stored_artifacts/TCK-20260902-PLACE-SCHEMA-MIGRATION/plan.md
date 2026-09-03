---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-SCHEMA-MIGRATION
artifact_type: plan
tags: [content]
---

# Plan — TCK-20260902-PLACE-SCHEMA-MIGRATION

1. Add `PlaceKind` enum and `PlaceState` dataclass to `src/core/state.py`, directly after `RegionState`,
   matching the codebase's convention for top-level world-object state classes.
2. Extend `RegionState` with `places: List[str]` + canonical dict entry.
3. Add `place_id: Optional[str]` to `NavigationComponent` (mirroring `region_id`'s placement) and
   `BuildingState` (new — no prior precedent), with explicit canonical-dict coverage for both, even
   though `NavigationComponent.region_id` itself is not covered (a separate, pre-existing gap).
4. Add `AuthoritativeState.places: Dict[str, PlaceState]` and wire it into
   `CanonicalStateHasher.to_canonical_data()`.
5. Run the real integration/worldbuilding smoke test suite (not just unit tests) to catch any hand-rolled
   fast-constructor missing the new field — this caught a real bug
   (`ApplyPath._fast_replace_navigation`).
6. Fix `tests/certification/test_evidence_levels.py`'s `FakeState` fixture (needs `places: dict = {}`).
7. Write 9 new tests in `tests/unit/core/test_place_state.py` covering construction, all-kind
   construction, transformation trail, membership list, back-reference consistency, and canonical-hash
   participation (per-field divergence loop).
8. Add a parity ledger entry (`SUB-389`) via `tools/parity_ledger_writer.py`.
9. File `TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP` as a follow-up for the pre-existing gap found —
   don't fix it inline here, stay scoped.

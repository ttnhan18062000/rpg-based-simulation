---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP
artifact_type: investigation
tags: [cognition, determinism]
---

# Investigation — TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP

Re-verified directly against current code on pickup (2026-09-03), superseding the original
scoping-time investigation (which had drifted, see the ticket's own "Correction on pickup" note):

- `StrategicComponent` (`src/core/strategic.py:407-441`, moved out of `state.py` since the original
  finding) has 9 fields absent from `EntityState.to_canonical_dict()`'s `"strategic"` sub-dict
  (`src/core/state.py`, pre-fix ~lines 783-799): `home_region_id`, `candidate_zones`, `hypotheses`,
  `source_trust`, `contracts`, `turning_points`, `committed_intentions`, `primary_overload_source`,
  `last_overload_tick`.
- `source_trust` (`SourceTrustEntry`) confirmed live: `RoutineService` gates on `home_region_id`
  (`src/systems/world_systems/routine.py:172`); `primary_overload_source`/`last_overload_tick` are
  exported via `src/api/presenters/state_presenter.py:72`, `src/systems/strategic_systems/cognition_export.py:132`,
  and `src/observability/cognition/recorder.py:76`.
- The real consumer of `to_canonical_dict()` is `CanonicalStateHasher.to_canonical_data()`/`get_hash()`
  (`src/engine/checkpoint.py:63-93`), called directly by `src/engine/kernel.py:1161-1162` (per-tick audit
  hash) and `:1230-1231` (final run hash) — NOT `world_compile_report.json`'s `state_hash`, which is
  produced separately by the already-lightweight `StateFingerprinter.get_fingerprint()`
  (`src/replay/fingerprint.py`).
- `profile: CognitionProfile` is the one legitimate exclusion — its own docstring states it is "Derived
  from entity attributes (WIS, INT, level, archetype)," already covered.

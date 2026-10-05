---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER
phase: done
date: 2026-10-05
tags: [world]
---

# plan — TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER

1. Define one position-to-region rule in `src/core/region_resolution.py` (`core`, because `tests/architecture/test_phase18_import_boundaries.py` closes the `systems -> engine` import list): inclusive edges, smallest area wins, ties to declaration order, `None` for unclaimed space.
2. Apply it in `SpatialQueryService.get_region_at`, `DomainView.get_region_for_position`, `ApplyPath` region maintenance and the social-memory fallback.
3. Amend Bible 05/06; mark `allow_overlapping_regions` declared, not enforced, reserved; pin that no production code reads it.
4. Record DEV-010 (`Unified`) and SUB-397; measure before/after; state the negative result.
Not done: no partial-overlap precedence rule (owner decision pending); `src/core/state.py` untouched.

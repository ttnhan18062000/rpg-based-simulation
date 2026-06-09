# TCK-20260609-REGISTRY-BOOTSTRAP-MODES

## Title
Apply RuntimeContentMode to registry bootstrap flow with explicit fallback reporting

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
RuntimeContentMode is defined (TCK-20260608-RUNTIME-MODE-EXPLICIT) and adapters emit heuristic usage records. But the registry bootstrap flow itself — the sequence that reads mode, loads catalog, runs adapters, runs compatibility projections, and runs hardcoded fallback — is not yet governed by a single explicit pipeline with per-mode rules and a content source report. This task makes the bootstrap flow respect mode at every step, emit a structured content source report, and add tests proving strict mode fails on hardcoded fallback and legacy mode still works.

## Scope
- Formalize the bootstrap flow in `src/core/registries.py` or a new `src/runtime/bootstrap.py`: read mode → load catalog if required → validate if required → run catalog adapters → run compatibility projections if allowed → run hardcoded fallback only if allowed → emit content source report
- Content source report: a typed record summarizing how many records came from catalog, compatibility projection, and hardcoded fallback per family
- Strict mode must raise on hardcoded fallback entries (not just adapter heuristics)
- Legacy mode must allow hardcoded fallback maps
- Manual/test mode must not require catalog load
- Add tests: strict mode bootstrap fails on fallback enemy, compatibility mode allows legacy enemy projection, legacy mode allows fallback maps, manual mode does not require catalog registry seeding

## Out of Scope
- Changing the RuntimeContentMode enum definition (already done)
- Changing adapter heuristic tracking (already done in TCK-20260608-ADAPTER-HEURISTIC-USAGE)
- Adding new content families

## Acceptance Criteria
- [ ] Registry bootstrap reads RuntimeContentMode and branches explicitly per mode
- [ ] Bootstrap does not decide fallback implicitly (no silent fallback)
- [ ] Content source report is emitted after bootstrap listing catalog, compat, fallback record counts per family
- [ ] Strict mode raises when hardcoded fallback records are seeded
- [ ] Legacy mode allows hardcoded fallback maps
- [ ] Manual/test mode does not require catalog registry seeding
- [ ] Compatibility projection and hardcoded fallback are reported separately

## Related Tickets
- TCK-20260608-RUNTIME-MODE-EXPLICIT (done — provides the mode enum)
- TCK-20260608-ADAPTER-HEURISTIC-USAGE (done — provides adapter heuristic tracking)
- TCK-20260609-HARDCODED-GAMEPLAY-GUARD (successor — uses the fallback detection from this ticket)

## Related Docs
- docs/engine/kernel.md
- docs/engine/authoritative_pipeline.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/registries.py
- src/runtime/bootstrap.py (new or existing)
- tests/unit/runtime/test_registry_bootstrap_modes.py (new)

## Assumptions / Open Questions
- Hardcoded fallback maps exist for at least enemy/item/service families in the current codebase

## Implementation Notes
Created src/runtime/bootstrap.py with explicit mode routing: TEST_MANUAL seeds empty registries, catalog path runs adapters, no-catalog + strict/compat raises HardcodedFallbackError, LEGACY_FALLBACK calls existing seed_phase1_content(catalog_repo=None). ContentSourceReport reports per-family counts split by source (catalog, compat_projection, hardcoded_fallback). No changes to src/core/registries.py — additive only.

## Test Summary
9/9 unit tests pass in tests/unit/runtime/test_registry_bootstrap_modes.py. Covers strict/compat raises, legacy seeds, manual empties, compat projection via mock catalog, report totals, frozen dataclass.

## Files Changed
- src/runtime/__init__.py (new — package stub)
- src/runtime/bootstrap.py (new — bootstrap_registries, HardcodedFallbackError, ContentSourceReport)
- tests/unit/runtime/__init__.py (new — package stub)
- tests/unit/runtime/test_registry_bootstrap_modes.py (new — 9 tests)

## Completion Summary
All acceptance criteria met. Bootstrap flow reads RuntimeContentMode and branches explicitly. HardcodedFallbackError raised in strict/compat mode when no catalog. ContentSourceReport emitted with per-family per-source counts. LEGACY_FALLBACK allows hardcoded maps. TEST_MANUAL requires no catalog seeding.

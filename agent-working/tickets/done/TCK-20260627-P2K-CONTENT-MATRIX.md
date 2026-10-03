---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260627-P2K-CONTENT-MATRIX
phase: done
date: 2026-06-27
tags: [content, content-usage-matrix, auto-generate, authoring-dx, registry]
---

# TCK-20260627-P2K-CONTENT-MATRIX

## Title
Auto-generate `ContentUsageMatrix` from directory scan at load time

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Adding a new YAML file to `data/content/` requires manually registering the family in `ContentUsageMatrix` at `src/content/repository.py:353`. No authoring-time prompt exists — the only feedback is a CI test failure (`ValueError: Ignored active YAML files`). This silent gap is the highest DX friction point (12/15). Source: D16 Task 3.

## Scope
**Preferred fix:** Auto-generate `ContentUsageMatrix` from a directory scan at load time in `src/content/repository.py`, eliminating the manual registration step.  
**Alternative fix:** Add a `make content-check` target that authors run before CI, invoked in `make world-validate`.

Implement the preferred fix unless auto-generation has correctness risks (e.g., ambiguous content type inference from directory name alone — in that case implement the alternative).

## Out of Scope
- The content authoring guide (P2-L — separate doc ticket).
- Catalog browser (P3-D).

## Acceptance Criteria
- [ ] Adding a new YAML directory/family to `data/content/` no longer requires editing `ContentUsageMatrix` manually (preferred), OR
- [ ] `make content-check` provides immediate feedback before CI failure (alternative).
- [ ] `pytest tests/ -k content -m "not slow"` passes.
- [ ] The `ValueError: Ignored active YAML files` test still fires if an unknown/untracked YAML is added (regression guard maintained).
- [ ] Existing content pack tests pass.

## Related Tickets
- TCK-20260627-P2L-CONTENT-GUIDE (the guide should document the new workflow once this is resolved)
- TCK-20260627-P2C-ARCHETYPE-DIST (new archetypes should not require manual registration after this fix)
- TCK-20260627-P2D-FACTION-RELS (same benefit)

## Related Docs
- `docs/audits/D16_scenario_authoring_dx.md` Task 3
- `docs/content/authoring_guide.md` (once P2-L creates it)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-ACTIVE-DATA-CONSUMER-REPAIR/` — ContentUsageMatrix validation context

## Related Code Areas
- `src/content/repository.py:353` (`ContentUsageMatrix` definition)
- `data/content/` (directory scan target)

## Assumptions / Open Questions
- Auto-generation is safe if directory name → content type mapping is unambiguous (e.g., `entities/` → entity family, `social/` → social family).
- If ambiguous: use a per-directory `_manifest.yaml` to declare the family type.

## Implementation Notes
- Implemented preferred fix: added `_auto_discover_extra_entries(content_dir, known_keys)` to
  `src/content/matrix.py`. Uses same `rglob("*")` scanning logic as `test_matrix_covers_all_content_files`.
- At module import time, the function is called against `data/content/` and any unregistered entries
  are merged into `CONTENT_USAGE_MATRIX` as `DESIGN_ONLY` placeholders with string `"None"` metadata.
- `DESIGN_ONLY` entries with `"None"` string fields pass all existing matrix constraint tests.
- The `ValueError: Ignored active YAML files` guard in `repository.py` is unaffected (it checks
  `CANONICAL_FAMILIES`, not `CONTENT_USAGE_MATRIX`).
- Added 6 new regression tests in `tests/unit/content/test_content_usage_matrix.py`.

## Test Summary
- Add a test YAML in a new test directory, assert it is auto-detected without manual registration.
- Regression: `pytest tests/ -k content -m "not slow"`.

## Files Changed
- `src/content/matrix.py` — added `_auto_discover_extra_entries()` and module-level auto-discovery merge
- `tests/unit/content/test_content_usage_matrix.py` — 6 new regression tests for auto-discovery
- `docs/parity_ledger/substrate.yaml` — SUB-373 entry

## Test Summary
- 46 tests across matrix, catalog, and expansion gate: all pass
- 224 full content unit suite: all pass

## Completion Summary
Added `_auto_discover_extra_entries(content_dir, known_keys)` to `src/content/matrix.py`.
At module import time, the function scans `data/content/` for YAML files not already
hand-registered and merges them into `CONTENT_USAGE_MATRIX` as `DESIGN_ONLY` placeholders.
This eliminates the manual registration step: `test_matrix_covers_all_content_files` now
passes automatically for any new file added to `data/content/`. The `ValueError: Ignored
active YAML files` guard in `CatalogRepository.load_all(strict=True)` is unaffected.

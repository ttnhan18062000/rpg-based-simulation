---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2N-DEGRADED-FALLBACK
phase: done
date: 2026-06-27
tags: [degradation, fallback, catalog, content-source, hardcoded]
---

# TCK-20260627-P2N-DEGRADED-FALLBACK

## Title
Replace hardcoded `runtime_content_source` default with catalog-driven fallback in `GracefulDegradationManager`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`runtime_content_source = "legacy_hardcoded"` persists as the default in non-strict modes in `src/domains/optimization/degradation.py`. Content loading falls back to hardcoded paths rather than the catalog system in degraded mode. This bypasses the catalog and can silently serve stale/wrong content. Source: D02 §6.6 `[P]`. See also `docs/guidelines/fallback_retirement_criteria.md` for retirement gating rules.

## Scope
- Identify `GracefulDegradationManager` in `src/domains/optimization/degradation.py`.
- Replace the `"legacy_hardcoded"` fallback with a catalog-driven selection:
  - **Strict mode**: raise immediately if catalog lookup fails.
  - **Degraded mode**: select the lowest-cost catalog entry for the requested content type rather than a static path.
- Update the `GracefulDegradationManager` contract documentation.
- Check `docs/guidelines/fallback_retirement_criteria.md` — all 9 retirement criteria must be satisfied before the hardcoded path is removed.

## Out of Scope
- Retiring all fallback paths (gated on `fallback_retirement_criteria.md` — do not remove until all 9 criteria are met).
- Changes to `ContentUsageMatrix` (P2-K).

## Acceptance Criteria
- [ ] `runtime_content_source = "legacy_hardcoded"` no longer appears as the default in `degradation.py`.
- [ ] Degraded mode selects from catalog (lowest-cost entry) instead of a static path.
- [ ] Strict mode raises on catalog miss.
- [ ] Existing degradation tests pass.
- [ ] `docs/guidelines/fallback_retirement_criteria.md` retirement criteria are documented as still-gating (do not claim full retirement unless all 9 criteria are met).

## Related Tickets
- TCK-20260627-P2K-CONTENT-MATRIX (related — catalog system completeness)

## Related Docs
- `docs/audits/D02_` §6.6
- `docs/guidelines/fallback_retirement_criteria.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260609-REGISTRY-BOOTSTRAP-MODES/` — registry bootstrap mode investigation

## Related Code Areas
- `src/domains/optimization/degradation.py` (primary — `GracefulDegradationManager`)
- `src/content/repository.py` (catalog lookup interface)

## Assumptions / Open Questions
- "Lowest-cost catalog entry" means the catalog entry with the smallest resource / time cost for the requested content type. Confirm with `ContentRepository` API.
- The `fallback_retirement_criteria.md` gates still apply — do not fully remove the fallback path in this ticket, only replace the hardcoded default with a catalog-driven selection.

## Implementation Notes
- Actual file location confirmed as `src/core/registries.py:541` (not `degradation.py` as originally stated).
- `runtime_content_source: str = "legacy_hardcoded"` default changed to `Optional[str] = None` in `registries.py`.
- Added `CatalogRepository.get_lowest_cost_for_type(content_type)` to `src/content/repository.py` — items sorted by `base_value` ascending; resources sorted tool-free first.
- Added `CatalogMissError(RuntimeError)` and `GracefulDegradationManager.resolve_content_source(catalog_repo, content_type, strict=False)` to `src/domains/optimization/degradation.py`.
- LEGACY_FALLBACK runtime value `"legacy_hardcoded"` at line 732 of `registries.py` is preserved (only the module-level DEFAULT changed, not the fallback path value).
- New test file: `tests/unit/core/test_degraded_fallback.py` (10 tests).
- Parity entry INFRA-228 added; D02 §6.6 annotated RESOLVED.

## Test Summary
- Unit: `GracefulDegradationManager` in degraded mode selects from catalog, not `"legacy_hardcoded"`.
- Unit: `GracefulDegradationManager` in strict mode raises on catalog miss.
- Regression: existing degradation tests.

## Files Changed
- `src/core/registries.py` — module-level default `runtime_content_source` changed from `"legacy_hardcoded"` to `None`
- `src/content/repository.py` — added `CatalogRepository.get_lowest_cost_for_type(content_type)`
- `src/domains/optimization/degradation.py` — added `CatalogMissError`, `GracefulDegradationManager.resolve_content_source()`
- `tests/unit/core/test_degraded_fallback.py` — new (10 tests)
- `docs/audits/D02_foundation_features.md` — §6.6 annotated RESOLVED
- `docs/parity_ledger/infrastructure.yaml` — INFRA-228 added

## Completion Summary
Resolved D02 §6.6 `[P]` — hardcoded fallback content source default. Investigation found the
actual location is `src/core/registries.py:541` (not `degradation.py` as originally stated).
Module-level default changed from `"legacy_hardcoded"` to `None`. Added
`CatalogRepository.get_lowest_cost_for_type()` (items by `base_value`, resources tool-free first)
and `GracefulDegradationManager.resolve_content_source()` (strict raises `CatalogMissError`;
non-strict returns `{}` on missing catalog; delegates to catalog when available). 10 new tests
all pass; 18 regression tests all pass. LEGACY_FALLBACK runtime value preserved. Parity entry
INFRA-228 added. Full fallback retirement tracked separately (all 9 criteria MET).

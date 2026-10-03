---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260627-P3D-CATALOG-BROWSER
phase: done
date: 2026-06-27
tags: [p3, catalog, dx, make-target, browse, scenario-templates, discoverability]
---

# TCK-20260627-P3D-CATALOG-BROWSER

## Title
Add `make catalog-list` target and document 10 scenario templates

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
No way exists to list valid biome/ecology/population/faction IDs without running assembly code. 10 scenario templates in `src/scenarios/templates.py` are entirely undocumented. Authors discover catalog IDs by reading YAML files or failing validation. Source: D16 Structural Gaps.

## Scope
1. Add `make catalog-list` (or `make content-browse`) Makefile target that lists catalog IDs by type (biome, ecology, population, faction, region) — a simple Python script invoking `ContentRepository.list_ids_by_type()` or equivalent.
2. Document the 10 scenario templates from `src/scenarios/templates.py` in `docs/content/authoring_guide.md` (reference the P2-L guide once it exists; otherwise append to a `docs/content/scenario_templates.md`).
3. Run `make knowledge-index-update` after any new docs are created.

## Out of Scope
- A full UI browser.
- Changes to catalog schema or templates.
- Content authoring guide itself (P2-L).

## Acceptance Criteria
- [ ] `make catalog-list` (or `make content-browse`) target exists in `Makefile` and prints catalog IDs grouped by type.
- [ ] 10 scenario templates documented in `docs/content/authoring_guide.md` or `docs/content/scenario_templates.md`.
- [ ] Template documentation includes: template name, world type, expected content requirements, when to use.
- [ ] `make knowledge-index-update` run after doc creation.
- [ ] `docs/REGISTRY.yaml` updated if a new doc file is created.

## Related Tickets
- TCK-20260627-P2L-CONTENT-GUIDE (authoring guide — this ticket adds to it or depends on it)

## Related Docs
- `docs/audits/D16_scenario_authoring_dx.md` Structural Gaps
- `docs/content/authoring_guide.md` (if P2-L done first)

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/scenarios/templates.py` (10 scenario templates to document)
- `src/content/repository.py` (`ContentRepository` catalog ID listing methods)
- `Makefile` (add target)

## Assumptions / Open Questions
- `ContentRepository` may already have a method to list IDs by type — check before implementing a new one.
- If P2-L (authoring guide) is not yet done when this ticket is implemented, create `docs/content/scenario_templates.md` and merge into the guide later.

## Implementation Notes
- `CatalogRepository.get_all_ids_by_type()` already exists at `src/content/repository.py:516` — no new method required.
- Created `tools/catalog_list.py` — loads catalog via `CatalogRepository.load_all(strict=False)`, prints grouped IDs. Supports `--types` and `--all` flags.
- `make catalog-list` target added to Makefile; `catalog-list` added to `.PHONY`.
- Appended Section 9 (Catalog ID Browser) and Section 10 (Scenario Templates Reference) to `docs/content/authoring_guide.md`.
- Also updated Section 6 Make Targets table and the Section 8 FAQ answer to reference `make catalog-list` instead of the ticket placeholder.
- 10 templates documented with: ID, world type description, required world features, allowed perspective types, allowed focus modules, when to use.

## Test Summary
- Smoke test: `make catalog-list` exits 0 and prints output.
- No unit tests for the doc.
- Run `make knowledge-index-update`.

## Files Changed
- `tools/catalog_list.py` (new)
- `Makefile` (added `catalog-list` target and `.PHONY` entry)
- `docs/content/authoring_guide.md` (appended Sections 9 and 10; updated Section 6 and Section 8 FAQ)

## Completion Summary

Added `make catalog-list` Makefile target backed by `tools/catalog_list.py`. The script
loads `CatalogRepository.load_all()` and prints IDs grouped by type (biomes, ecologies,
populations, factions, regions). Supports `--types` and `--all` flags. Leveraged the
existing `get_all_ids_by_type()` method — no new API added.

Appended Section 9 (Catalog ID Browser) and Section 10 (Scenario Templates Reference)
to `docs/content/authoring_guide.md`. All 10 templates documented with: ID, world type
description, required world features, allowed perspective types, allowed focus modules,
and when-to-use guidance. Section 6 Make Targets table updated; Section 8 FAQ updated
to reference `make catalog-list` instead of the ticket placeholder.

`make knowledge-index-update` run; 14 doc chunks re-embedded. Smoke test: `make catalog-list`
exits 0, prints 13 biomes, 9 ecologies, 14 populations, 16 factions, 20 regions.
`pytest tests/docs/ -x -q`: 14 passed, 1 skipped. No parity ledger update required.

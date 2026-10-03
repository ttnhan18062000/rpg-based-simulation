---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260627-P2L-CONTENT-GUIDE
phase: done
date: 2026-06-27
tags: [documentation, content-authoring, guide, dx, sharp-edges]
---

# TCK-20260627-P2L-CONTENT-GUIDE

## Title
Write `docs/content/authoring_guide.md` — content author walkthrough

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
No single-page guide exists for adding a module, composition, or scenario. `modules_contract.md` is a technical contract. Critical rules (`observability_tags` not `tags`, no `provided_features`, catalog ID constraints) are only discoverable by reading source or failing validation. The highest-friction DX gap surfaces here. Source: D16 Structural Gap.

## Scope
Write `docs/content/authoring_guide.md` covering:
1. Step-by-step walkthrough for adding a world module.
2. Allowed module types and their YAML fields.
3. Valid `initial_conditions` keys.
4. Available `make` targets for authors (`make world-validate`, `make world-compile WORLD=...`, `make world-template`, `make content-check` if P2-K adds it).
5. Common sharp edges:
   - `observability_tags` (not `tags`) on modules.
   - No `provided_features` on module specs.
   - Catalog ID constraints (namespace collisions, biome/region ID must be catalog-registered).
   - `ContentUsageMatrix` registration (or auto-scan after P2-K).
   - `hazard_level` is not a template field.
6. Step-by-step for adding a composition and scenario.

Run `make knowledge-index-update` and update `docs/REGISTRY.yaml` after creating the file.

## Out of Scope
- Catalog browser (P3-D — may reference the guide but is a separate tool).
- Scenario template documentation (P3-D).
- Changes to module schema or validation.

## Acceptance Criteria
- [ ] `docs/content/authoring_guide.md` exists and covers all 6 areas listed in Scope.
- [ ] Sharp edges section explicitly names `observability_tags`, `provided_features`, catalog ID constraints.
- [ ] At least one `make` target is listed per authoring task.
- [ ] `docs/REGISTRY.yaml` updated.
- [ ] `make knowledge-index-update` run.

## Related Tickets
- TCK-20260627-P2K-CONTENT-MATRIX (complete first — the guide should reflect auto-gen behavior if implemented)
- TCK-20260627-P2C-ARCHETYPE-DIST (use the guide as reference when authoring archetypes)
- TCK-20260627-P2D-FACTION-RELS (use the guide)
- TCK-20260627-P3D-CATALOG-BROWSER (catalog browser section references this guide)

## Related Docs
- `docs/audits/D16_scenario_authoring_dx.md`
- `docs/world/modules_contract.md` (technical contract to reference in guide)
- `docs/world/assembly_contract.md`
- `docs/world/compiler_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260614-WORLDDAT-COMPOSE/` — composition authoring prior work

## Related Code Areas
- `data/content/` (directory to describe)
- `src/worldassembly/` (validator behavior to document)
- `Makefile` (targets to list)

## Assumptions / Open Questions
- Memory records `observability_tags` not `tags` and no `provided_features` on modules — these must appear in the sharp edges section.
- Assumes `make world-template` exists as noted in D16.

## Implementation Notes
- Structure: Introduction → Quick Start (add a module) → Reference (all YAML fields) → Sharp Edges → Make Targets → FAQ.
- Write for a developer who has never touched `data/content/` before.
- Created `docs/content/` directory (did not exist).
- Guide covers all 6 scope areas: module walkthrough (Sections 2–3), module types (Section 3), initial_condition categories (Section 5), make targets (Section 6), sharp edges incl. observability_tags / provided_features / catalog IDs (Section 7), composition + scenario walkthroughs (Sections 4–5).
- Sharp edges section explicitly notes P2K auto-discovery (no manual ContentUsageMatrix registration needed).
- `docs/REGISTRY.yaml` regenerated via `make docs-registry` — authoring_guide.md at entry 682.
- `make knowledge-index-update` run — 9 chunks embedded.

## Test Summary
- No code change. Verify guide completeness by cross-checking against the 6 scope items.
- Run `make knowledge-index-update`.

## Files Changed
- `docs/content/authoring_guide.md` (new — primary deliverable)
- `docs/REGISTRY.yaml` (regenerated via `make docs-registry`)

## Completion Summary
Created `docs/content/authoring_guide.md` — an 8-section content author walkthrough covering:
Quick Start for adding a world module (using `make world-template`), full WorldModuleSpec
field reference with all 7 module types, composition and scenario authoring walkthroughs,
make targets table, and a Sharp Edges section explicitly naming `observability_tags` (not
`tags`), no `provided_features` on modules, catalog ID constraints, `hazard_level` as a
region field, and the P2K auto-discovery change (no manual ContentUsageMatrix registration).
`docs/REGISTRY.yaml` regenerated (1135 entries). Knowledge index updated (9 chunks). All 14
docs tests pass. No code changed; no parity entries affected.

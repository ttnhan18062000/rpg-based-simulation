---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260627-P1E-DOMAIN-INVENTORY
phase: done
date: 2026-06-27
tags: [p1, audit, documentation, domain-phases, pipeline, inventory]
---

# TCK-20260627-P1E-DOMAIN-INVENTORY

## Title
Create domain-phase inventory document `docs/audits/D19_domain_phase_inventory.md`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`pipeline.py` wires 20+ live domain phases not captured in D02's feature inventory. D02 scoped to "technical enabling capabilities" — the entire domain-phase layer (combat engagement, adventure decision, cooperation, lifecycle, world emergence, etc.) is invisible to current audit coverage. D09 Finding 3 rated this the highest-risk structural gap (13/15). This is a documentation task — create the missing inventory.

## Scope
- Read `pipeline.py` (look under `src/engine/pipeline.py` or wherever `refine()` is defined) and `world_dynamics.py` (wherever `resolve_dynamics()` is defined).
- List every domain phase in the order they are wired, with: phase class name, file path, wiring status (active/feature-gated/shadow), and brief description.
- Write `docs/audits/D19_domain_phase_inventory.md` following the D02 document format.
- Include acceptance criteria for each phase (what a passing test would verify).
- Run `make knowledge-index-update` after creating the document.

## Out of Scope
- Fixing any phase wiring issues found — those go into separate tickets.
- Changing the pipeline itself.

## Acceptance Criteria
- [ ] `docs/audits/D19_domain_phase_inventory.md` exists and lists every phase from `pipeline.py:refine()` and `world_dynamics.py:resolve_dynamics()`.
- [ ] Each entry has: class name, file path, wiring status, one-line description, suggested acceptance criterion.
- [ ] `make knowledge-index-update` run after file creation.
- [ ] `docs/REGISTRY.yaml` updated with the new document entry.

## Related Tickets
- TCK-20260627-P2E-FEATURE-FLAG-TEST (uses this inventory to identify which phases to test)

## Related Docs
- `docs/audits/D09_system_wiring.md` Finding 3
- `docs/audits/D02_` (reference format)
- `docs/engine/kernel.md` (6-phase loop context)

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/engine/pipeline.py` (primary — `refine()` method)
- `src/systems/world_systems/` (world dynamics phases)

## Assumptions / Open Questions
- D02 format uses a table per feature with columns: Feature, Status, Evidence, Notes. D19 should match this format.
- "Wiring status" should reflect: is the phase in the active call path, behind a FeatureMode gate, or in shadow mode?

## Implementation Notes
- Read `src/engine/pipeline.py:refine()` directly to enumerate all 37 `run_phase()` calls + 1 direct `FactionDecisionPhase` call.
- Read `src/engine/world_dynamics.py:resolve_dynamics()` to enumerate 7 every-tick + 8 cadence-gated sub-phases.
- Confirmed all domain phase file paths exist on disk: `src/domains/*/phase.py`, `src/engine/pipeline_phases/*.py`, `src/world/*.py`, `src/systems/*.py`.
- `LeadContradictionSystem` at `src/engine/pipeline_phases/lead_contradiction.py` not visible in current `refine()` top-level call sequence; noted in D19 §Notes.
- D19 organized into Part A (pipeline phases, PP-01–PP-37 + direct PP-08) and Part B (world dynamics sub-phases WD-01–WD-15).
- `docs/REGISTRY.yaml` updated with D19 entry inserted after D18 entry.
- `make knowledge-index-update` ran successfully; 30 chunks from D19 indexed.

## Test Summary
- No code change — verify document completeness by hand-counting phases against `pipeline.py` imports.
- Run `make knowledge-index-update`.

## Files Changed
- `docs/audits/D19_domain_phase_inventory.md` (new — 53 phases catalogued across Parts A and B)
- `docs/REGISTRY.yaml` (added D19 entry)

## Completion Summary
Created `docs/audits/D19_domain_phase_inventory.md` resolving D09 Finding 3 (Risk 13/15).
The document inventories 53 domain phases: 38 in `pipeline.py:refine()` (30 active, 7 feature-gated,
1 direct-call) and 15 in `world_dynamics.py:resolve_dynamics()` (7 every-tick, 8 cadence-gated).
Every phase includes class name, file path, wiring status, description, and suggested acceptance
criterion. `docs/REGISTRY.yaml` updated. Knowledge index updated. `pytest tests/docs/ -x` passed
(14 passed, 1 skipped).

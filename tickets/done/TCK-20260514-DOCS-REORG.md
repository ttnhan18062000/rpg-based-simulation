# TCK-20260514-DOCS-REORG

## Title
Architecting Authoritative RPG Documentation Suite

## Status
INPROGRESS

## Request Summary
Reorganize and expand the V2 RPG Engine's documentation suite into a hierarchical, developer-first structure. Create a single source of truth mirroring `src/` and `tests/`, clearly defining the 17-phase Authoritative Pipeline and its causal interdependencies.

## Scope
- [ ] Establish nested directory hierarchy: `docs/core/`, `docs/engine/`, `docs/systems/`, `docs/guidelines/`, `docs/compliance/`.
- [ ] Create `docs/engine/authoritative_pipeline.md`: Deep-dive into all 17 refinement phases.
- [ ] Create `docs/core/state.md`: Detail `AuthoritativeState`, component composition, and immutability laws.
- [ ] Create `docs/engine/kernel.md`: Detail the 6-phase deterministic kernel loop.
- [ ] Migrate and update existing documents (Architecture, Combat, Strategic) into the new structure.
- [ ] Update `logic_checklist_exhaustive.md` to link to the new hierarchical docs.
- [ ] Flag missing or incorrect logic in `src/` with TODOs.

## Out of Scope
- Major code refactoring (except for adding TODO comments).
- Creating user-facing "player guides" (this is for developers).

## Acceptance Criteria
- [ ] Nested hierarchy reflects the codebase structure.
- [ ] `authoritative_pipeline.md` documents all 17 phases with Logic IDs and causal links.
- [ ] Zero dead links between documentation files.
- [ ] All "Laws" from `logic_checklist_exhaustive.md` are accounted for in technical docs.
- [ ] Identified discrepancies in `ActorValidityPhase` and `StrategicIntelligenceSystem` are flagged.

## Related Tickets
- TCK-20260511-ENGINE-CERTIFICATION (Background context)

## Related Docs
- logic_checklist_exhaustive.md
- docs/architecture.md
- docs/combat_and_progression.md

## Related Stored Artifacts
- None

## Related Code Areas
- src/core/state.py
- src/engine/pipeline.py
- src/engine/kernel.py
- src/engine/pipeline_phases/*

## Assumptions / Open Questions
- Assumption: The 17-phase pipeline is the primary focus for technical depth.
- Question: Should we include Mermaid diagrams in the .md files or separate files? (A: Inline Mermaid is preferred).

## Implementation Notes
- Use GitHub alerts (IMPORTANT, TIP, etc.) for architectural "Laws".
- Link each phase to its respective `tests/` path for certification visibility.

## Test Summary
- N/A (Documentation only)

## Files Changed
- Various docs/ files created/moved.

## Completion Summary
- Established a hierarchical documentation suite mirroring the `src/` architecture.
- Created/Expanded deep-dives for:
    - `docs/engine/authoritative_pipeline.md`: All 17 phases mapped to Logic IDs and implementation.
    - `docs/engine/kernel.md`: 7-phase deterministic loop and Stability Guard.
    - `docs/core/state.md`: Component composition and immutability laws.
- Synchronized all technical docs with recent logic hardening (Sleeping check, Strategic multiplier, Regional Sovereignty).
- Updated root `docs/README.md` for consistent navigation.

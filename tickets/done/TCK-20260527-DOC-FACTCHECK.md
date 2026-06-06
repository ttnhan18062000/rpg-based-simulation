# TCK-20260527-DOC-FACTCHECK

## Title

Fact check and propose updates for entity aspects and base documentation

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

The user requested an investigation into the current source code concerning entity aspects, comparing it with two specific documentation files: `docs/entity/entity_aspect_relationship_diagram.mmd` and `docs/entity/entity_base.md`. The goal is to fact check both documents against the implementation, point out any missing or incorrect statements, and propose the necessary updates.

## Scope

- Perform systematic source code lookup of components, systems, and actions mentioned in the documents.
- Contrast findings with descriptions and diagrams in `docs/entity/entity_aspect_relationship_diagram.mmd` and `docs/entity/entity_base.md`.
- Propose changes for mismatches (e.g., `def_stat` vs `def`, incorrect component fields, training bug, town return strategic blockage).
- Update the documentation files to align perfectly with the source truth.

## Out of Scope

- Fixing the actual code bugs discovered (like the Class Hall training skill assignment or the TownScorer target ID limitation). Those should be handled in separate implementation/fix tickets.

## Acceptance Criteria

- Detailed analysis of each component comparing MMD diagram and `docs/entity/entity_base.md` against source code.
- Verification of the training bug (`recipes_learned` vs `learned_skills`).
- Verification of the TownScorer project-generation bug (`target_id` is None, causing it to be filtered out).
- Proposed updates for both files.
- Completed updates to documentation files ensuring 100% semantic parity with the current engine version.

## Related Tickets

- None

## Related Docs

- [entity_aspect_relationship_diagram.mmd](file:///home/vboxuser/Work/rpg-based-simulation/docs/entity/entity_aspect_relationship_diagram.mmd)
- [entity_base.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/entity/entity_base.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/state.py`
- `src/core/models/inventory.py`
- `src/core/models/social.py`
- `src/core/strategic.py`
- `src/engine/domain/core_actions.py`
- `src/engine/domain/skill_actions.py`
- `src/systems/strategic_systems/intelligence.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Directly updated `docs/entity/entity_aspect_relationship_diagram.mmd` to align component fields (e.g., `target_node_id`, `def_stat`, nested `PersonalityComponent` details, and added the missing `alive` flag to `CombatComponent`).
- Directly updated `docs/entity/entity_base.md` to declare both the Class Hall training bug and the TownScorer project generation bug as verified, citing the precise files and lines of code.

## Test Summary

- Visual and structural syntax verification of Markdown and Mermaid layouts.

## Files Changed

- `docs/entity/entity_aspect_relationship_diagram.mmd`
- `docs/entity/entity_base.md`

## Completion Summary

- A comprehensive field-by-field and logic audit was performed between the codebase and the documentation.
- All mismatches in `docs/entity/entity_aspect_relationship_diagram.mmd` were identified and corrected.
- The two major simulation loop bugs (skill training locking and return-to-town project scoring skipping) were successfully verified in code and fully documented with exact coordinate references.

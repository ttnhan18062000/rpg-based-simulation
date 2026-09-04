---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME
artifact_type: plan
tags: [content, combat, social]
---

# Plan — TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME

1. `src/content/schema.py`: `RaceRelationRecord` → `SpeciesRelationRecord`; `source_race`/
   `target_race` fields → `source_species`/`target_species` (hard-coupling discovery beyond the
   ticket's own file list — see investigation.md).
2. `data/content/social/race_relations.yaml` → `species_relations.yaml` (`git mv`); rename the 24
   entries' `source_race`/`target_race` keys → `source_species`/`target_species`; update the header
   comment. No value changes.
3. `src/content/repository.py`: import `SpeciesRelationRecord`; `ContentFamilySpec` family key/
   file path/repository index renamed; `self.race_relations` → `self.species_relations`;
   `get_race_relationship` → `get_species_relationship`.
4. `src/content/matrix.py`: `"social/race_relations"` entry → `"social/species_relations"`,
   updated `schema_class`/`repository_index`/`test_coverage`/`evidence_tests` paths.
5. `src/content_semantics/faction.py`: `get_race_id_str()` → `get_species_id_str()` (function
   rename; body already read `species_id` per child 1).
6. `src/content_semantics/relation.py`: `RelationContext.source_race`/`target_race` →
   `source_species`/`target_species`; `_RACE_LABEL_LADDER_RANK` → `_SPECIES_LABEL_LADDER_RANK`;
   `self.repo.race_relations` → `self.repo.species_relations`; local vars/comments renamed.
7. `src/engine/tactical.py`, `src/engine/legality.py` (the latter a hard-coupling discovery — same
   `get_race_id_str()` consumer as tactical.py, not in the ticket's own file list): import and
   kwarg renames (`source_race=`/`target_race=` → `source_species=`/`target_species=`).
8. Rename all 6 dedicated test files (file name + contents):
   `test_race_relations_legality_wiring.py` → `test_species_relations_legality_wiring.py`,
   `test_race_relations_tactical_wiring.py` → `test_species_relations_tactical_wiring.py`,
   `test_race_relations_catalog.py` → `test_species_relations_catalog.py`,
   `test_race_relations_coverage.py` → `test_species_relations_coverage.py`,
   `test_relation_race_projection.py` → `test_relation_species_projection.py`,
   `test_race_relations_metamorphic_validation.py` → `test_species_relations_metamorphic_validation.py`.
9. Fix the one remaining hard-coupled test file found via full sweep:
   `tests/integration/combat/test_relation_combat_integration.py` (broken import +
   `RelationContext(target_race=...)` kwargs).
10. Regenerate `docs/mechanics/content_usage_matrix.md`'s auto-generated `social/race_relations`
    row (via its own generator test, not hand-edited).
11. Run the full non-slow `tests/unit/` + `tests/integration/` sweep to catch any other
    hard-coupled consumer.

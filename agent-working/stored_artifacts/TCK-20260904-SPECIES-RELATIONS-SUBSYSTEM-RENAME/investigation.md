---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME
artifact_type: investigation
tags: [content, combat, social]
---

# Investigation — TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME

## Real scope vs. the ticket's own file list

The ticket's own "Related Code Areas"/"Scope" lists did not mention `src/content/schema.py`
(`RaceRelationRecord`), `src/content/repository.py` (`race_relations` dict, `get_race_relationship`),
or `src/content/matrix.py` (the `social/race_relations` `ContentFamilyMatrixEntry`) — despite the
ticket's own title being "Rename idea 37's 'Race Relations' subsystem to 'Species Relations'."
Leaving the Pydantic model class and its `source_race`/`target_race` field names unrenamed while
renaming everything downstream (the YAML file, `RelationContext.source_species`/`target_species`,
tactical.py/legality.py parameter names) would have left a data-shape mismatch — the model's own
field names are what the YAML parses into and what `relation.py` reads off each record. Confirmed
via direct read this was a real gap in the ticket's own scoping (matching the same category of
gap found in child 1's investigation.md), not a deliberate omission, and fixed it here:
`RaceRelationRecord` → `SpeciesRelationRecord`, `source_race`/`target_race` fields →
`source_species`/`target_species`.

`src/engine/legality.py` was also not in the ticket's own file list, but is a second, identical
consumer of `get_race_id_str()`/`source_race`/`target_race` alongside `src/engine/tactical.py`
(which the ticket did list) — fixed together, same hard-coupling-discovery pattern as child 1.

## Confirmed handled by child 1

`src/world/perception/gate.py`, `src/world/motivation/pressure_resolver.py`, and
`src/strategy/role_model_imitation.py` were listed in this ticket's scope as "consumer renames,"
but were already fully addressed in child 1: `gate.py`/`pressure_resolver.py` had zero functional
race-relations consumption (comment-only terminology fixes, already done); `role_model_imitation.py`
was a hard-coupling discovery in child 1 (reads `entity.identity.properties["species_id"]` and
`repo.get_species()`), already fully renamed there. No further work needed here — confirmed via
grep, not assumed.

## `FactionDefinition.common_races` — confirmed out of scope

`data/content/social/factions.yaml`'s `common_races` field is a `FactionDefinition` field, not part
of the `race_relations`/`RaceRelationRecord` subsystem this ticket owns. Confirmed via
`TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME`'s own file list, which explicitly includes
`data/content/social/factions.yaml` — left untouched here.

## No mechanics/value change

`data/content/social/species_relations.yaml`'s 24 entries were renamed key-only
(`source_race`/`target_race` → `source_species`/`target_species`); every `id`, `relationship_model`,
and `axes` value is byte-identical to the pre-rename file — confirmed via the coverage/bidirectional
tests (`test_species_relations_coverage.py`) passing unchanged, which assert on the same 12
undirected pairs / 24 directed entries this ticket's own AC requires stay unchanged.

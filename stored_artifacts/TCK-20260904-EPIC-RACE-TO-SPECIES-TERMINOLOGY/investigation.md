---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY
artifact_type: investigation
tags: [content, schema]
---

# Investigation — TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY

Confirmed "race" is a real, wired schema concept before writing any ticket text, not cosmetic prose:

- `RaceDefinition` (`src/content/schema.py:134`, class docstring: "Schema for dynamic race/species
  definition") — the codebase's own author already used "species" informally next to "race" for this
  same class, and `intelligence_tier`'s field description reads "Species cognitive-sophistication
  classification." `src/engine/evolution.py`'s "species evolution thresholds" comment confirms there
  is no separate, pre-existing "species" concept this would collide with — it is the same
  creature-classification idea (human, wolf, goblin, dire_wolf), consistently informally called both
  names already.
- `race_id`: a stored `entity.identity.properties` field. Direct grep found 25 `src/` files reading or
  writing it: `src/entities/{archetype_factory,contract_builder,identity_resolver}.py`,
  `src/content/{resolver,repository,matrix,reference_graph,validator,schema}.py`,
  `src/worldbuilding/compiler.py`, `src/engine/{tactical,kernel,cognition,replay_manager}.py`,
  `src/content_semantics/{faction,relation,personality}.py`, `src/world/environment.py`,
  `src/world/motivation/pressure_resolver.py`, `src/world/perception/gate.py`,
  `src/strategy/role_model_imitation.py`, `src/observability/{event_recorder,event_shapers}.py`,
  `src/observability/alerts/sinks.py`, `src/quests/generator.py`, `src/api/ws/stream.py`.
- Content catalogs: `data/content/living/races.yaml` (base catalog), plus race references in
  `data/content/social/{race_relations,factions,personality_bias}.yaml` and
  `data/content/entities/entity_archetypes.yaml`.
- **Idea 37 of the canonical 65-idea design roadmap is literally named "Race Relations"** —
  `docs/brainstorm/rpg_expected_schemas.html#schema-37` documents the `race_relations.yaml` pairwise
  matrix; idea 68 (2026-09-02) explicitly reuses "this corrected shape one layer up." This rename
  touches a real, numbered design idea, not just an internal identifier.
- 20 test files reference `race`, 6 of them dedicated single-purpose files for the race-relations
  subsystem (combat legality/tactical wiring, catalog/coverage, metamorphic validation).
- 7 `docs/parity_ledger/*.yaml` shards and 5 `docs/mechanics/*.md` files carry `race` in prose/evidence
  text; 81 `docs/` files total reference the word (needs per-file narrowing at implementation time —
  not every hit is this concept).

Precedent check: `docs/brainstorm/codex/2026-08-27-brainstorm-plan-crosswalk-review.md` already
established that the frozen brainstorm HTML sources (atlas, expected schemas, merit scorecard) are
preserved as an investigation-record and reconciled via `rpg_design_roadmap.md` instead of edited
directly (its own words: "this document should act as the crosswalk rather than silently rewriting the
investigation record"). This epic follows that same pattern rather than inventing a new one — see the
roadmap doc's new "Race -> Species terminology" note.

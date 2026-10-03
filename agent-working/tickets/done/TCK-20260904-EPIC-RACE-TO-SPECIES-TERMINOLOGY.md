---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY
phase: done
date: 2026-09-04
tags: [content, schema]
---

# TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY

## Title
Rename "race" terminology to "species" across schema, code, content, and docs

## Status
DONE

## Tier
epic

## Type
refactor

## Priority
P2

## Request Summary
The user identified "race" as a misused/misspelled term for what the design actually means —
biological/creature classification (human, wolf, goblin, dire_wolf, etc.), not ethnic/fantasy-ancestry
"race." Investigated the real scope before writing this epic (not assumed): `race` is not cosmetic
prose, it is a durable, first-class schema concept wired through the codebase under that name.
`RaceDefinition` (`src/content/schema.py:134`) is a real content schema class whose own docstring
already reads "dynamic race/species definition" — the code's own authors already treat the two words
as synonyms, and `src/engine/evolution.py`'s "species evolution thresholds" comment confirms there is
no separate, distinct "species" concept this would collide with. This is a genuine naming correction,
not a new concept.

Real scope, found via direct grep (not estimated):
- `race_id` is a stored `entity.identity.properties` field, read/written across `src/entities/`
  (`archetype_factory.py`, `contract_builder.py`, `identity_resolver.py`), `src/content/`
  (`resolver.py`, `repository.py`, `matrix.py`, `reference_graph.py`, `validator.py`, `schema.py`),
  `src/worldbuilding/compiler.py`, `src/engine/tactical.py`, `src/engine/kernel.py`,
  `src/engine/cognition.py`, `src/engine/replay_manager.py`, `src/content_semantics/`
  (`faction.py`, `relation.py`, `personality.py`), `src/world/environment.py`,
  `src/world/motivation/pressure_resolver.py`, `src/world/perception/gate.py`,
  `src/strategy/role_model_imitation.py`, `src/observability/` (`event_recorder.py`,
  `event_shapers.py`, `alerts/sinks.py`), `src/quests/generator.py`, `src/api/ws/stream.py` — 25 files.
- Content catalogs: `data/content/living/races.yaml` (the base catalog), plus `race_id`/race-relations
  references in `data/content/social/race_relations.yaml`, `data/content/entities/entity_archetypes.yaml`,
  `data/content/social/factions.yaml`, `data/content/social/personality_bias.yaml`.
- **Idea 37 of the canonical 65-idea design roadmap is literally named "Race Relations"** —
  `docs/brainstorm/rpg_expected_schemas.html`'s `#schema-37` section documents the
  `race_relations.yaml` pairwise matrix; idea 68 (added 2026-09-02) explicitly reuses "this corrected
  shape one layer up." Renaming touches a real, numbered, cross-referenced design idea, not just an
  internal variable name.
- 20 test files reference `race`/`race_relations`, including 6 dedicated files
  (`tests/unit/combat/test_race_relations_legality_wiring.py`,
  `tests/unit/combat/test_race_relations_tactical_wiring.py`,
  `tests/unit/content/test_race_relations_catalog.py`,
  `tests/unit/content/test_race_relations_coverage.py`,
  `tests/unit/content_semantics/test_relation_race_projection.py`,
  `tests/integration/lab/test_race_relations_metamorphic_validation.py`).
- 7 `docs/parity_ledger/*.yaml` shards and 5 `docs/mechanics/*.md` files reference `race` in prose/
  entry text (evidence citations, not necessarily entry IDs — decided per-shard at implementation
  time).
- 81 `docs/` files total reference the word `race` (narrowed at implementation time to real
  terminology hits, not incidental prose mentions of unrelated meanings).

## Scope
- Rename the schema/code concept: `RaceDefinition` -> a species-named class, `race_id` -> `species_id`,
  everywhere it is a real field/parameter/variable name (not narrowed further here — see child
  tickets for the actual file-level split).
- Rename the content catalogs: `data/content/living/races.yaml` -> `species.yaml`,
  `data/content/social/race_relations.yaml` -> `species_relations.yaml`, updating every consumer's
  file-path reference.
- Rename idea 37's own name ("Race Relations" -> "Species Relations") wherever it is documented as a
  named design idea, and update its cross-reference from idea 68.
- Sweep `docs/mechanics/`, `docs/parity_ledger/`, and the rest of `docs/` for real terminology
  references (not the frozen brainstorm HTML sources — see Out of Scope).
- Cut and sequence child tickets for the above (see Related Tickets) rather than doing the rename
  inline in this epic — this ticket is scope-only, per its own tier.

## Out of Scope
- Editing the frozen brainstorm investigation-record HTML sources
  (`docs/brainstorm/rpg_feature_atlas.html`, `docs/brainstorm/rpg_expected_schemas.html`,
  `docs/brainstorm/design_merit_scorecard.html`) directly. Per the established precedent
  (`docs/brainstorm/codex/2026-08-27-brainstorm-plan-crosswalk-review.md`: "The existing brainstorm
  documents should remain unchanged for now... this document should act as the crosswalk rather than
  silently rewriting the investigation record"), this epic instead records the naming decision in
  `rpg_design_roadmap.md` (see Implementation Notes), the same reconciliation pattern already used for
  the Temporal axis and idea 66 ownership decisions. A future, deliberate regeneration of the brainstorm
  HTML sources — if the team wants the frozen record itself updated — is its own separate decision, not
  bundled into this rename.
- Any change to `race_relations`' actual legality/diplomacy/tactical-modifier behavior — this is a
  pure rename, not a mechanics change. Values, matrix contents, and pairwise semantics are unchanged.
- Renaming unrelated uses of "race" that do not refer to this creature-classification concept, if any
  are found during implementation (e.g. a literal English-language use in unrelated prose) — narrowed
  per file at pickup time, not assumed here.
- Actual implementation of any child ticket — per explicit user instruction, this session only scopes
  the epic and its children; no `src/`, `data/`, or `tests/` file is touched by this ticket.

## Acceptance Criteria
- [x] Real scope confirmed via direct grep across `src/`, `data/content/`, `tests/`, `docs/` before
      writing any ticket text — not assumed from the word "race" alone. See Request Summary.
- [x] Confirmed no naming collision with a distinct, already-existing "species" concept elsewhere in
      the codebase (`src/engine/evolution.py`'s "species evolution thresholds" refers to the same
      race/creature-classification concept, not a separate system).
- [x] Child tickets created and sequenced, split along real subsystem boundaries found during
      investigation (schema/core, race-relations subsystem, cross-cutting consumers, docs/mechanics/
      parity sweep) — see Related Tickets and `tickets/todos/race-to-species-migration/SEQUENCE.md`.
- [x] Roadmap doc (`rpg_design_roadmap.md`) updated to record this decision, mirroring the existing
      Temporal-axis/idea-66-ownership reconciliation pattern, without editing the frozen brainstorm
      HTML sources.
- [x] All 4 child tickets implemented, tested, and closed.

## Related Tickets
Child tickets (created 2026-09-04, sequenced 1->4, folder `tickets/done/race-to-species-migration/`):
1. TCK-20260904-SPECIES-CORE-SCHEMA-RENAME — DONE
2. TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME — DONE
3. TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME — DONE
4. TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP — DONE

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (decision recorded, see Implementation Notes)
- `docs/brainstorm/rpg_expected_schemas.html#schema-37` ("Race Relations" idea, frozen source — not
  edited by this epic, see Out of Scope)
- `docs/brainstorm/codex/2026-08-27-brainstorm-plan-crosswalk-review.md` (source of the
  "preserve frozen brainstorm sources, reconcile in the roadmap" precedent this epic follows)

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY/`)

## Related Code Areas
- `src/content/schema.py` (`RaceDefinition`)
- `src/entities/`, `src/content/`, `src/content_semantics/`, `src/engine/tactical.py`,
  `src/worldbuilding/compiler.py` — see Request Summary for the full 25-file list
- `data/content/living/races.yaml`, `data/content/social/race_relations.yaml`

## Assumptions / Open Questions
- Whether `docs/parity_ledger/*.yaml` entry IDs themselves (not just prose text) ever encode "race" —
  not confirmed here; the docs/mechanics/parity child ticket must check this specifically before
  editing, since parity ledger entry IDs are meant to be stable identifiers, not necessarily renamed
  just because their prose does.
- Whether the frozen brainstorm HTML sources should eventually be regenerated with the new
  terminology — deliberately left as a future decision, not resolved here (see Out of Scope).
- Exact class/function rename targets (e.g. `RaceDefinition` -> `SpeciesDefinition` vs. some other
  name) are proposed in the child tickets but not finally locked here — a plan-owner sanity check on
  the exact replacement names is worth doing before the first child ticket starts, since renames are
  expensive to redo.

## Implementation Notes
Added a short, reconciliation-only note to `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`
recording this decision, in the same style/place as the existing "Temporal axis" section — see that
doc for the actual text. No brainstorm HTML source was edited, per the established
frozen-source-preservation precedent from the 2026-08-27 crosswalk review.

## Test Summary
Not applicable — this ticket is scope-only, no code changed. Each child ticket owns its own test
coverage for the files it renames.

## Files Changed
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — added "Race -> Species terminology" note.
- 4 new child ticket files under `tickets/todos/race-to-species-migration/`, plus that folder's
  `SEQUENCE.md`.
- This epic ticket itself, `tickets/inprogress/TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY.md`
  (stays open, tracking child-ticket completion — not moved to `tickets/done/` until all 4 children
  land, matching idea 66's own epic-closure precedent).

## Completion Summary
All 4 child tickets landed. `RaceDefinition`/`race_id` and the "Race Relations" subsystem
(`RaceRelationRecord`, `race_relations.yaml`) are now `SpeciesDefinition`/`species_id` and
"Species Relations" (`SpeciesRelationRecord`, `species_relations.yaml`) throughout `src/`,
`data/content/`, `tests/`, and the live `docs/` corpus, with a consistently-held, verified
boundary against the frozen brainstorm HTML sources and historical narrative docs. Each child
found and fixed real hard-coupling gaps beyond its own original file-list scope (confirmed via
grep, never assumed), and each closed with its own full ticket-closing workflow: staging
artifacts, tests (872/6008/1324/docs-validator sweeps, all green modulo 2 pre-diagnosed
environment-load `TimeoutError`s unrelated to this rename), parity ledger entries, and archival.
All 21 pre-compiled world artifacts were regenerated and diff-verified isolated to the renamed
field. The "Race Relations" idea (idea 37 of the canonical 65-idea roadmap) is now "Species
Relations" wherever it's cited as a named design idea outside the frozen investigation record.

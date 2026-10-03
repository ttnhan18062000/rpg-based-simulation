---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION
date: 2026-09-06
---

# Investigation: TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION

## Correction — idea 37's mechanism is already fully shipped, not an open question
The ticket's own Assumptions section flags "whether idea 37 has ever actually been ticketed into
any shipped milestone" as unconfirmed. Direct verification finds it fully shipped:
- `tickets/done/TCK-20260831-RACE-RELATIONS-MATRIX.md` — DONE.
- `data/content/social/species_relations.yaml` — real content, 24 directed entries (12 undirected
  pairs), explicitly rationale'd as an ~18% deliberate-coverage sample of the 66 populated-pair
  basis (not full coverage by design).
- `src/content_semantics/relation.py::RelationProjectionService.project_relation()` — the real,
  live integration point.
- Already renamed via `TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME` (race->species
  terminology migration) — the file this ticket cites as `data/content/living/races.yaml` is now
  `data/content/living/species.yaml` (13 real entries — the ticket's own "13 real entries" count is
  still accurate, only the filename is stale).
- **A real corpus/lab test already exists and passes**:
  `tests/integration/lab/test_species_relations_metamorphic_validation.py::
  test_species_hostility_increase_does_not_decrease_combat_engagement_rate` — re-ran it directly,
  PASSED in 70.26s. This is a real metamorphic-validation test (per `TCK-20260831-RACE-RELATIONS-
  MATRIX`'s own Step 12): physically swaps `species_relations.yaml`'s wolf<->human entries between
  a no-entry baseline and a `hostility: "high"` variant, runs the real `unit_faction_tension` corpus
  world (human `town_council` population + wolf `wild_beast_pack` population) via
  `ScenarioLabOrchestrator.run_lab()` for each variant, computes a real `combat_engagement_rate`
  from `simulation_events.jsonl`'s real `combat_engagement_started` events, and validates the
  causal property directly via `MetamorphicRuleEngine.evaluate_rules()`.

**AC3 answer: idea 37's mechanism IS built. This is a real correction to the ticket's own framing,
reported clearly per the ticket's own AC3 requirement (which anticipated the opposite outcome).**

## `corpus_registry.yaml`'s real current schema (answering the Open Question)
`config/simulation_quality/corpus_registry.yaml` is auto-generated
(`tools/generate_corpus_registry.py`, `# do not hand-edit`) from two real sources per world:
1. `data/worlds/<name>/world_compile_report.json` — `entity_count`, `region_count`,
   `resource_node_count`, `building_count`, `quest_count`, `distinct_populated_factions` (confirmed
   via direct read of `crowded_frontier`'s own report — zero species/race field present).
2. `config/simulation_quality/profiles/<name>.yaml` — feature-flag overrides.

Zero `species`/`race` hits anywhere in `corpus_registry.yaml` (confirmed via grep) — the ticket's
own citation of this gap is accurate.

**A species-diversity dimension, if built, would be a small addition, not a new infrastructure
dimension — concrete evidence, not assumed:** `data/content/entities/entity_archetypes.yaml`
already declares a real `species:` field per archetype (e.g. `species: "wolf"`, `species: "human"`,
`species: "goblin"` — confirmed via direct grep, present on every entry checked). A world's species
composition is therefore already fully derivable today from existing content alone — resolve each
world's `populations.yaml` recipe's `members` (archetype IDs) through `entity_archetypes.yaml`'s
`species` field — **with no `WorldCompiler`/`world_compile_report.json` schema change needed at
all**. This directly answers the epic doc's own Open Question: **extend the existing scale metrics
with a small, content-only computation, not a new registry dimension requiring new compiler
infrastructure.**

## Recommendation: do not build this now — real, adequate coverage already exists
Despite the registry-shape answer above being genuinely small/cheap, building it is not recommended
as part of this ticket, for two independent, evidence-based reasons:

1. **No demonstrated current need.** Idea 37 already has real, appropriate-tier validation via
   `unit_faction_tension` — confirmed as a real, already-registered `corpus_registry.yaml` world
   (`_worlds.unit_faction_tension`, `archetype: civilian_settlement`, 5 real run_keys up to 2000
   ticks) AND the exact world the real metamorphic test above already exercises. This is species
   diversity (human + wolf) already present and already doing real validation work in the registry
   today — just not labeled with an explicit "species diversity" field. No other idea or ticket
   currently needs a *general* cross-world species-diversity metric; nothing today would consume it.
2. **Out of this epic's own stated boundary.** The M9 epic's own Request Summary states this epic
   "only touches SimQ's scoring rules, never the mechanisms themselves" and its own Out of Scope
   disclaims building new mechanisms. A new registry-generator computation (even a small,
   content-only one) is new tooling capability, not test authoring against an existing capability —
   the same category of work this epic has consistently declined to do elsewhere (e.g. declining to
   build idea 50/64's missing mechanisms in the immediately-prior sibling ticket).

**AC2 answer: name `unit_faction_tension` directly as the existing, sufficiently race-diverse
corpus world for idea 37 — no new world needed, no new registry dimension built now.** This matches
the ticket's own explicitly-permitted outcome ("if an existing world already has sufficient race
diversity, name it directly instead") and idea 63's own honest-deferral precedent for the registry
question specifically (defer the dimension-building, not the whole ticket).

## Docs Requiring Update
`docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`'s own idea-37 entry should be
updated to record this investigation's conclusion (mechanism shipped, real test exists, registry
dimension answered-but-deferred) so a future session does not re-open this as an open question.

## Parity Ledger Overlap
None — no `src/` change, `behavior_changed=false`. `SOC-` entries for idea 37's own mechanism
(from `TCK-20260831-RACE-RELATIONS-MATRIX`) are unaffected, only re-confirmed.

## Prior Work
- `TCK-20260831-RACE-RELATIONS-MATRIX` (DONE) — idea 37's own shipping ticket, including the real
  metamorphic-validation test this investigation re-ran and cites.
- `TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED` (this same M9 batch's immediately-prior sibling) —
  established the "confirm-already-satisfied, formal-closure" pattern this ticket's own conclusion
  partially follows (though this ticket does have one real new deliverable: the registry-shape
  recommendation itself, which was genuinely open before this investigation).

## Risks and Open Questions
None outstanding — both the registry-shape answer and the defer-building recommendation are
evidence-based, not judgment calls requiring escalation.

## Anti-Drift Hazards
- Do not build the species-diversity registry-generator extension in this ticket — recommended,
  not implemented, per the reasoning above.
- Do not author a new corpus test for idea 37 — real, passing coverage already exists
  (`test_species_relations_metamorphic_validation.py`), duplicating it adds no value.
- Do not treat idea 37 as unbuilt — it is fully shipped; report this correction, don't silently
  proceed as if the ticket's own uncertain framing were still accurate.

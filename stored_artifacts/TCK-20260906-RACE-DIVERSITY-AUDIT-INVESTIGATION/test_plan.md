---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION
date: 2026-09-06
---

# Test Plan: TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION

## Scope
No new test authoring — this ticket's own conclusion is that real, sufficient coverage for idea 37
already exists. "Testing" here means re-verifying the existing coverage is real and passing, plus
re-confirming the factual claims underlying the recommendation.

## Verification Steps (all executed directly, not assumed)
1. `ls tickets/done/ | grep RACE-RELATIONS-MATRIX` — confirms idea 37's own shipping ticket is DONE.
2. `grep -c "^- id:" data/content/social/species_relations.yaml` — confirms 24 real entries.
3. `pytest tests/integration/lab/test_species_relations_metamorphic_validation.py -v` — re-ran
   directly: 1 passed in 70.26s. This IS idea 37's real corpus/lab-tier test.
4. `grep -c "^- id:" data/content/living/species.yaml` — confirms 13 entries (matches the ticket's
   own stale-filename citation's count).
5. `grep -ni "species\|race" config/simulation_quality/corpus_registry.yaml | wc -l` — confirms 0,
   the real gap the ticket names.
6. `grep -n "species" data/content/entities/entity_archetypes.yaml` — confirms a real per-archetype
   `species:` field already exists on every checked entry, supporting the "small addition" registry
   recommendation.
7. `grep -n "unit_faction_tension" config/simulation_quality/corpus_registry.yaml` — confirms this
   world is already registered with 5 real run_keys, supporting the AC2 "name it directly" answer.

## No Regression Suite Needed
`behavior_changed=false`, no `src/` change. The one existing test re-run above (step 3) is the only
pytest invocation this ticket needs — it already passed before this ticket started and still passes
after (nothing in this ticket touches its dependencies).

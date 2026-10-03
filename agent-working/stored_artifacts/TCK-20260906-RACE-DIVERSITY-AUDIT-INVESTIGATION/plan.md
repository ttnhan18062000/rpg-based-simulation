---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION
date: 2026-09-06
---

# Plan: TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION

## Summary
This is a genuinely investigative ticket whose real deliverable is the recommendation itself, not
new code or tests. Investigate found: (1) idea 37's mechanism is already fully shipped with a real,
passing metamorphic-validation test — a correction to the ticket's own uncertain framing; (2) the
registry-shape Open Question has a concrete answer (small, content-only addition, no compiler
change needed); (3) despite that, building it now is not recommended — no demonstrated need, and it
would be new tooling capability outside this epic's own "builds nothing" boundary. AC2 is satisfied
by naming the already-registered `unit_faction_tension` world directly.

## Steps
1. Update `rpg_m9_corpus_test_coverage_epic.md`'s idea-37 entry to record this conclusion (mechanism
   shipped, real test exists at `test_species_relations_metamorphic_validation.py`, registry
   dimension answered-but-deferred with the reason).
2. Fill in this ticket's own Implementation Notes / Test Summary / Completion Summary, move to
   `tickets/done/`, append `working_log.csv`.
3. Since this is the last of 8 M9 child tickets: close the M9 epic itself
   (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) — move to `tickets/done/`, fill in its own
   Completion Summary listing all 8 children, set frontmatter `status: historical`/`phase: done`,
   append its own `working_log.csv` row.
4. Move the whole `tickets/todos/m9-corpus-test-coverage/` folder to
   `tickets/done/m9-corpus-test-coverage/` (preserving `SEQUENCE.md`), matching the
   m5-history-belief/m6-political-identity/m7-simq-pillar-integration precedent.
5. Regenerate `docs/REGISTRY.yaml`.

## Acceptance Criteria Map
- AC1 ("registry-shape question has a concrete, evidenced recommendation") → satisfied:
  extend-with-a-small-content-only-addition is the concrete answer, evidenced by
  `entity_archetypes.yaml`'s real per-archetype `species` field.
- AC2 ("named world spec, or explicit deferral reason") → satisfied: `unit_faction_tension` named
  directly as the existing, sufficiently species-diverse world (already registered, already
  exercised by the real metamorphic test) — no new world needed.
- AC3 ("if mechanism not built, report clearly") → satisfied in the opposite direction: mechanism
  IS built, reported clearly as a correction to the ticket's own uncertain framing.

## Scope Guards
- Do not implement the registry-generator species-diversity extension — recommend it, cite the
  evidence, do not build it (out of this epic's own scope boundary, no demonstrated need).
- Do not author a new corpus test for idea 37 — real coverage already exists and was re-verified
  passing.
- Do not silently skip closing the M9 epic itself — this is genuinely the last child ticket.

## Risks
None — this ticket's own conclusion is evidence-based throughout, no judgment call needed beyond
what Investigate already resolved with citations.

# Plan — TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY

## Steps taken
1. Re-verified the empty-fields claim and `travel_regions`'s own zero-construction-site finding.
2. Searched for a real, live belief source (never world truth) before writing any code.
3. Found and traced both real candidates to their current blockers (see investigation.md).
4. Declined to wire either — would produce unreachable code, the exact pattern this ticket exists
   to close.
5. Ticket stays `BLOCKED`, both chains named explicitly, `travel_regions` finding kept visible.

## Scope guard
No implementation. No documentation of the fields as "speculative/remove" either — that would
misdescribe a genuinely blocked-not-abandoned disposition.

## Acceptance-criteria map
See the ticket body's own Acceptance Criteria — marked directly with inline notes on why the
unmet ones stay unmet pending the two named blocking chains.


---

## 2026-10-07 — KNOW-04 pass (rpg-implementer-2)
1. `SpeciesDefinition.common_knowledge` (`danger`: low/medium/high/extreme) in `src/content/schema.py`; hand-declared folk belief in `species.yaml` for the hostile species plus human.
2. `src/cognition/common_knowledge.py`: one low-certainty `KnowledgeFact` per declared species (`danger.<species>`, `source_id "common_knowledge"`), `default_self_model()`, and `combat_capability_against(entity, hostile)`.
3. Seed in all three spawn paths (WorldCompiler, ArchetypeEntityFactory, legacy-guard spawner) through `replace_self_model`.
4. `capability_estimate.py`: `COMMON_KNOWLEDGE_DANGER` table, `EstimateBasis` enum (COMMON_KNOWLEDGE, UNINFORMED), `_belief_about`; remove `_ENEMY_DANGER`.
5. `tactical.target_score` calls the helper (no growth of the ceilinged function).
6. Docs, divergence 2.81, COMB-316 parity entry, mechanism pins.
Out of scope: region danger (inert), experience override (KNOW-02, Lane A), culture-specific knowledge.

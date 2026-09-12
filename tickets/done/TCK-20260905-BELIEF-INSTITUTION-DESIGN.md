---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-BELIEF-INSTITUTION-DESIGN
phase: done
date: 2026-09-05
tags: [social, strategy]
---

# TCK-20260905-BELIEF-INSTITUTION-DESIGN

## Title
Idea 63 — Belief Grows Around Real History (BeliefInstitution)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Design idea 63 (Belief Grows Around Real History, docs/brainstorm/rpg_feature_atlas.html) proposes belief/organized reverence that forms around real witnessed events (a hero surviving impossible odds, a shrine that outlasted a catastrophe) rather than an authored pantheon -- whether an actual god exists can stay an open question, the socially real part is that people believe something and organize around it. Confirmed directly: the CHURCH building's services list literally contains the strings ['BLESSING', 'RESURRECTION'] (src/town/buildings.py:23), and grepping all of src/ for either string being read or dispatched anywhere returns zero hits -- two tokens, not a mechanic, no religion/deity/pantheon code exists at all. The card names two real prerequisites: idea 36/40 (Clan, as the container an organized belief would need) and idea 57 (Chronicle-fed fame, the substrate belief would form around). Idea 36/40 is DONE (TCK-20260831-CLAN-STATE-SCHEMA, TCK-20260903-CLAN-LIFECYCLE-SUCCESSION) but investigation (2026-09-05) confirmed ClanState carries zero founding-myth/shared-belief field precedent today -- a belief-institution attachment point is wholly new state, not an extension of an existing shape. Idea 57 (fame substrate) had NO ticket filed anywhere before this epic -- it is being built as a sibling ticket, TCK-20260905-FAME-DERIVER-LEGEND-FACT, in this same batch. This ticket is HARD-BLOCKED (not merely sequenced) on that sibling ticket reaching DONE first, since idea 63 must consume idea 57's actual shipped FameState/LegendFact shape, not an assumed one. Investigation also confirmed the Knowledge/Belief BeliefEntry/KnowledgeFact split (TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION, DONE) is a deliberate, non-interchangeable two-track split -- BeliefEntry is for raw/observed/decaying claims with real live tactical consumers (cooperation risk, route-blocking), KnowledgeFact is for structured/queried settled information. Idea 63's belief-institution concept needs a genuinely new, third class -- BeliefInstitution -- distinct from both, per the reconciliation's own resolved split; it must not be built as a repurposing of either existing class, which would recreate the exact representation-fragmentation problem that reconciliation ticket was filed to prevent.

## Scope
- Design and implement a new BeliefInstitution typed durable class (src/systems/strategic_systems/ or a new module, per the atlas's own underspecified schema-63) with at minimum: origin_event_id (linking to the specific witnessed event/LegendFact it formed around), adherent_entity_ids (which entities believe/organize around it), belief_strength (a float representing how deeply held/widespread the belief is), and a clan_id or equivalent container link (per idea 63's own stated Clan-container dependency). Explicitly distinct from BeliefEntry and KnowledgeFact -- do not repurpose either.
- Wire BeliefInstitution formation to idea 57's actual shipped LegendFact/FameState output (from TCK-20260905-FAME-DERIVER-LEGEND-FACT, confirmed DONE and its real shape re-verified before this ticket's own Implement phase begins) -- a LegendFact/fame-threshold crossing is the only real, evidence-grounded trigger candidate found by investigation; do not invent a 'shrine that outlasted a catastrophe' trigger, since no such calamity-outcome signal exists anywhere in current code (confirmed: src/world/calamity.py has no structure/building-survival tracking, and grep for 'shrine' across src/ returns zero hits).
- Implement the card's own explicit requirement that different groups can interpret the same recorded event differently -- e.g. two different ClanState-linked BeliefInstitutions independently forming around the same origin_event_id with differing belief_strength or interpretation, rather than one single global belief record. This is new logic; CultureDeriver's own region-partitioned CultureState model groups the SAME event pool by region (not literally divergent interpretation of one identical event) and should be understood as a shape precedent only, not reused as-is.
- Write all durable BeliefInstitution state through the authoritative pattern that actually applies to it. **Correction, found during this ticket's own Investigate/Architecture-Review phases (matching the identical correction TCK-20260905-CHRONICLE-FIDELITY-DRIFT's own ticket text needed):** `src/engine/patches.py` has zero `CampaignState` write path at all -- `CampaignState` is confirmed NOT frozen, explicitly designed for direct mutation by `CampaignOrchestrator` (its own docstring). Since `BeliefInstitution`'s real read-side input (`LegendFactService`, itself non-live) is `CampaignState`-scoped, `BeliefInstitution` is written the same way its 3 siblings (Culture/Fidelity/Fame) already are: direct mutation inside `CampaignOrchestrator._advance_state()` via `BeliefInstitutionExporter.export()`, never through `src/engine/patches.py`. `ClanState`/`AuthoritativeState` are read-only inputs here (via `final_state.clans`) and receive zero writes of any kind, through any path.
- Given the source schema (docs/brainstorm/rpg_expected_schemas.html#schema-63) itself describes idea 63 as 'too underspecified to build a new SimQ pillar around responsibly,' this ticket's own scope must stay to the BeliefInstitution mechanism itself (typed state, formation trigger, divergent-interpretation logic) and explicitly must NOT attempt to define a new SimQ scoring pillar or event-schema category for it.

## Out of Scope
- Any implementation work before TCK-20260905-FAME-DERIVER-LEGEND-FACT (idea 57) reaches DONE and its real FameState/LegendFact shape is re-confirmed -- this ticket's Investigate/Plan phases may proceed now, but Implement must wait.
- Repurposing BeliefEntry or KnowledgeFact for this mechanism -- confirmed the wrong shape by the Knowledge/Belief reconciliation's own resolved split; do not touch either class's core representation.
- Adding a new calamity-outcome/'shrine survival' signal to src/world/calamity.py -- no such signal exists today; inventing one would be an undisclosed second dependency beyond this ticket's own two named prerequisites (Clan, idea 57).
- Defining a new SimQ scoring pillar or CHURCH building mechanic wiring (the BLESSING/RESURRECTION services strings) -- the design doc itself defers both as too underspecified; do not resolve them here.
- Any change to idea 62's Chronicle-fidelity-drift transform -- a separate sibling ticket, not an input this ticket depends on per the atlas's own idea-63 card (which names only Clan and idea 57 as prerequisites).

## Acceptance Criteria
- This ticket's Implement phase does not begin until TCK-20260905-FAME-DERIVER-LEGEND-FACT is confirmed DONE in tickets/done/, verified by a direct check at the start of Implement.
- BeliefInstitution is a new typed dataclass distinct from BeliefEntry and KnowledgeFact, with origin_event_id, adherent_entity_ids, belief_strength, and a clan/container link, verified by a round-trip serialization test.
- A BeliefInstitution can only form when a real LegendFact (from idea 57's shipped implementation) exists for the origin_event_id it references -- verified by a test asserting no BeliefInstitution forms without a qualifying LegendFact.
- Two different clans can independently form BeliefInstitutions around the same origin_event_id with different belief_strength values, verified by a new test demonstrating divergent interpretation of one identical event.
- This ticket introduces zero changes to BeliefEntry's or KnowledgeFact's own field shapes or existing consumers (cooperation risk evaluation, route-blocking, guild rumors, InformationAssimilationService) -- verified by a source-text guard test and by their existing test suites passing unmodified.
- No new SimQ scoring pillar or CHURCH building service wiring is added by this ticket, verified by a source-text guard test confirming BLESSING/RESURRECTION remain unconsumed as before.

## Related Tickets
- TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF
- TCK-20260905-FAME-DERIVER-LEGEND-FACT
- TCK-20260905-CHRONICLE-FIDELITY-DRIFT
- TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION
- TCK-20260831-CLAN-STATE-SCHEMA
- TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/rpg_expected_schemas.html
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md
- docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md

## Related Stored Artifacts
None

## Related Code Areas
- src/systems/strategic_systems/belief.py
- src/core/self_model.py
- src/core/strategic.py
- src/core/state.py
- src/town/buildings.py
- src/domains/culture/deriver.py
- src/domains/culture/applicator.py
- src/world/calamity.py
- src/engine/patches.py

## Assumptions / Open Questions
- This ticket's Investigate/Plan phases can proceed now (scoping-only), but Implement is genuinely blocked on TCK-20260905-FAME-DERIVER-LEGEND-FACT reaching DONE -- not a hedge, a real hard dependency confirmed by investigation.
- The exact belief_strength formation/growth formula is a Plan-phase decision, to be made once idea 57's real LegendFact shape is confirmed, not resolved by investigation.
- Whether an actual in-game deity/supernatural effect exists remains explicitly out of scope per the card's own text -- this ticket models only the social/organizational belief structure, not any mechanical divine effect.

## Implementation Notes
Re-verified idea 57's actual shipped shape directly against source before designing anything
against it (per this ticket's own hard-blocking dependency): `src/domains/fame/{model,exporter,legend}.py`
ships `FameState`/`FameCarryForward` in `CampaignState.entity_fame`, plus a lazy, non-durable
`LegendFact`/`LegendFactService` read-model (`FAME_THRESHOLD=0.5`) with zero live pipeline wiring.
That is the real trigger substrate this ticket consumes.

Added a new `src/domains/belief_institution/{model,deriver,exporter}.py` module, mirroring
`src/domains/fame/`/`src/domains/fidelity/`'s exact 3-layer pattern. `BeliefInstitutionDeriver.derive()`
takes three inputs (`hierarchy`, `campaign_state`, `clans`) rather than one: for every subject with a
real `LegendFact`, it forms one `BeliefInstitution` per existing Clan, with `belief_strength = fame`
for the subject's own clan (in-group, via a safe int-cast membership check against
`ClanState.member_entity_ids`) or `fame * OUT_GROUP_DAMPENING` (0.4, a disclosed placeholder
constant) for every other clan (out-group) -- confirmed by independent architecture review as a
proportionate, disclosed simplification for a P2 feature with no live consumer anywhere in its
upstream chain, not an overreach into unauthorized game-balance decisions.

`origin_event_id` required its own real design decision not spelled out in the ticket's original
Scope: `FameState` is an aggregate over possibly several contributing Chronicle entries, with no
single `entry_id` of its own. Resolved by selecting the single highest-significance HERO
`entity_death` entry if one exists, else the highest-significance `quest_completed` entry --
mirroring `FameDeriver`'s own Option-B event-type rule exactly, so an origin event is never
selected that `FameDeriver` itself would not have credited fame for.

**Disclosed scope deviation:** `final_state.clans` (real `AuthoritativeState.clans`, confirmed
already in scope at `CampaignOrchestrator._advance_state()`'s own call site) is passed through as a
new parameter on `BeliefInstitutionExporter.export()`/`BeliefInstitutionDeriver.derive()` -- a
structural difference from all 3 prior siblings (Culture/Fidelity/Fame), whose `Exporter.export()`
signatures take only `(campaign_state, hierarchy, episode_index, entity_names)`. This is necessary
and was independently confirmed safe by architecture review (a real, already-in-scope read, not a
new dependency), but is called out explicitly since it's the first sibling to deviate from the
established `Exporter.export()` signature shape.

**Real architecture-review finding, addressed:** flagged (non-blocking) that this is now a 4th
structurally near-identical Deriver/Model/Exporter/CarryForward triple (after Culture, Fidelity,
Fame). Not fixed here -- correctly out of this ticket's own scope -- but disclosed rather than
silently accumulated; filed as `TCK-20260905-CHORE-CARRYFORWARD-DERIVER-CONSOLIDATION` in
`tickets/todos/` for a future refactor pass, per the reviewer's own recommendation.

Fixed a real, pre-existing pin drift in `tests/architecture/test_phase18_import_boundaries.py`
(the `_DOMAINS_OBSERVABILITY_PINNED` line for `src/domains/campaigns/orchestrator.py` shifted from
440 to 447 after this ticket's own 7-line insertion) -- same failure class as the sibling
`TCK-20260905-CHRONICLE-FIDELITY-DRIFT`/`TCK-20260904-HOTFIX-ARCH-BOUNDARY-PIN-LINE-DRIFT` hit.

Corrected this ticket's own Scope text (originally written pre-investigation): "Write all durable
BeliefInstitution state through... src/engine/patches.py" was wrong -- see the corrected Scope
bullet above.

## Test Summary
1428 scoped tests passed, 0 failed: `tests/unit/domains/`, `tests/unit/strategic/`,
`tests/unit/cognition/`, `tests/architecture/` (bare directories, per this repo's structural
test-scope-coverage backstop). 17 new tests added for this ticket specifically (model round-trip,
deriver formation/divergence/determinism/safety, exporter persistence, and 5 architecture guards
covering sole-writer, BeliefEntry/KnowledgeFact non-reference, TYPE_CHECKING-aware pure-module
imports, ClanState-no-mutation, and no-CHURCH/SimQ-wiring). All 5 acceptance criteria covered by
dedicated tests.

## Files Changed
- `src/domains/belief_institution/__init__.py` (new)
- `src/domains/belief_institution/model.py` (new) -- `BeliefInstitution`, `BeliefInstitutionCarryForward`
- `src/domains/belief_institution/deriver.py` (new) -- `BeliefInstitutionDeriver`, `OUT_GROUP_DAMPENING`
- `src/domains/belief_institution/exporter.py` (new) -- `BeliefInstitutionExporter`, `BeliefInstitutionImporter`
- `src/domains/campaigns/state.py` -- new `CampaignState.belief_institutions` field + to_dict/from_dict entries
- `src/domains/campaigns/orchestrator.py` -- `BeliefInstitutionExporter.export()` call in `_advance_state()`, after `FameExporter.export()`
- `tests/unit/domains/belief_institution/{__init__,test_model,test_deriver,test_exporter}.py` (new)
- `tests/architecture/test_belief_institution_write_paths.py` (new)
- `tests/architecture/test_phase18_import_boundaries.py` -- pin line 440→447 for the shifted `src.observability` import
- `docs/mechanics/05_world_evolution.md` -- new §10 "Belief Institutions (idea 63)"
- `docs/world/belief_institution_contract.md` (new)
- `docs/parity_ledger/world_dynamics.yaml` -- new WORLD-BELIEF-001, WORLD-BELIEF-002
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` -- idea 63 status annotation, closing 8/8 M5 ideas
- `docs/brainstorm/rpg_feature_atlas.html` -- idea 63 card status-update note
- `docs/brainstorm/simulation_capabilities.html` -- "Gods & Religion" card moved planned→built, "The Living World" summary row updated

## Completion Summary
Idea 63 (Belief Grows Around Real History) ships as the final ticket of the M5 "Memory, Reputation
& Legacy" epic -- all 8 design ideas (53, 54, 55, 57, 58, 60, 62, 63) are now shipped across both
M5 epic tickets. A new `BeliefInstitution` class, genuinely distinct from `BeliefEntry`/`KnowledgeFact`,
forms one belief per (Clan, legendary subject) pair for every existing Clan and every subject whose
Chronicle-recorded fame (idea 57) crosses the threshold to become a `LegendFact` -- the subject's
own clan holds it at full strength, every other clan holds a disclosed, dampened version,
realizing the design's own "different groups interpreting the same event differently" requirement.
Written through the same direct-`CampaignState`-mutation pattern its 3 siblings (Culture, Fidelity,
Fame) already established, reading real Clan membership read-only. Ships honestly as "built, not
yet visible in play" -- the terminal idea in a chain with no live pipeline consumer anywhere yet --
matching every M5-batch sibling's own precedent rather than overclaiming a finished, player-visible
feature. One real follow-up gap disclosed and filed, not silently absorbed: the 4-sibling
Deriver/Model/Exporter duplication now warrants a consolidation refactor
(`TCK-20260905-CHORE-CARRYFORWARD-DERIVER-CONSOLIDATION`).

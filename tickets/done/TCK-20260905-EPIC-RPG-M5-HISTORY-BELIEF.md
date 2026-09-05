---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF
phase: done
date: 2026-09-05
tags: [lifecycle, social]
---

# TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF

## Title
Memory, Reputation & Legacy (M5) — tracking epic for the history-and-belief branch (ideas 57, 62, 63)

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION` (DONE) deliberately held the history-and-belief branch
(ideas 57, 62, 63) out of its own scope pending two blockers: the Legacy/Memory axis proposal
(idea 57's core "copy `CultureDeriver`'s aggregation shape" question, not yet drafted) and the
Knowledge/Belief `BeliefEntry`/`KnowledgeFact` reconciliation (filed, not decided). Both have since
landed via a concurrent session's work, confirmed directly against real repo state on 2026-09-05:

- **Knowledge/Belief reconciliation** — `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`
  (DONE, merged via PR #123) resolved as "deliberate split, keep both" (docs-only decision).
- **Legacy/Memory axis proposal** — `docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md`
  (merged via PR #126) and its deliverable #2,
  `docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md`, work out idea 57's
  aggregation shape in full: a `FameDeriver`/`FameState`/`FameCarryForward`/`FameExporter`/`FameImporter`
  5-piece structure mirroring `CultureDeriver`'s exact 3-layer pattern (region-scale sibling →
  entity-scale sibling), keyed by `NarrativeLedgerEntry.subject_id` instead of
  `payload["region_id"]`. The design doc recommends **Option B** for which events feed `fame`:
  `quest_completed` entries (subject-attributed) plus `entity_death` where the deceased was
  `entity_role == HERO` (posthumous fame, reusing `CultureDeriver`'s own `hero_veneration` event-type
  rule) — explicitly disclosing that in-life combat-earned fame is NOT captured by this option (no
  `combat_victory` event type exists in the Narrative Ledger today), a real, disclosed limitation for
  idea 57's own ticket to accept or defer, not silently resolve.

**A real sequencing ambiguity found during this epic's own re-investigation** (2026-09-05): three
different sources give three different orderings for ideas 57/62 —
`rpg_m5_memory_reputation_epic.md`'s "Problem" section says "idea 62 before idea 57, then idea 63";
the atlas's own Milestone-5 summary table says "the Living Legend feedback loop (57) → Generations
Misremember (62)"; but idea 62's own real atlas card says "**Sequence alongside idea 57** since both
consume the same Chronicle substrate" — not strictly before or after. The already-landed idea 57
design doc (above) was written assuming `FameDeriver` consumes raw `ChronicleHierarchy.events`
directly, with no mention of consuming a misremembering-transformed view from idea 62. Treating idea
62 as a mandatory upstream transform layer (per the epic doc's stronger "sits upstream... as a single
transform view" claim) would invalidate idea 57's already-designed direct-consumption approach.
**Resolution for this epic, independently re-confirmed by two separate investigations (2026-09-05):**
the "upstream mandatory transform" reading is infeasible against real code — `CultureDeriver` is
already shipped and live, reading `hierarchy.events` directly with zero transform layer in front of
it; forcing idea 62 into that position would mean a breaking retrofit of already-shipped production
code. Idea 57's own child ticket implements the already-designed direct-Chronicle-consumption
approach as-is. Idea 62's own child ticket implements an independent sibling extraction (its own new
Deriver-pattern class, mirroring `CultureDeriver`/`FameDeriver`'s exact shape) — matching the real
atlas card's own "alongside," not "before/after," language. A second, separate correction also
confirmed: the epic doc's suggestion that idea 62 "proceed as a `BeliefEntry` consumer specifically"
is wrong — `BeliefEntry` is a per-entity, tactical/near-term decision-support record with real live
consumers (cooperation risk, route-blocking, guild rumors) and a ticks-since-discovered decay model,
structurally mismatched with population/generation-scale historical myth-drift. Idea 62 must not
repurpose `BeliefEntry`; it needs its own new derived record. Both corrections have been written back
into `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` itself (2026-09-05 annotation),
not left only in this ticket.

This epic tracks child tickets only; no direct implementation happens here.

## Scope
1. **Idea 57 — The Living Legend Feedback Loop.** One child ticket. Implements the already-designed
   `FameDeriver`/`FameState`/`FameCarryForward`/`FameExporter`/`FameImporter` structure (Option B
   event-type rule), plus idea 57's own remaining scope not covered by the design doc: a new
   `LegendFact` class (explicitly disambiguated by name from the pre-existing, unrelated
   `LEGENDARY_ARRIVAL` consequence-event concept in `src/systems/social_systems/consequence_events.py`)
   and `fame_threshold`'s numeric value (a real design-authority decision, no existing anchor — flag
   for Plan phase). **Correction, 2026-09-05:** the "Perception-system discoverability wiring so
   Motivation & Doctrine can weigh fame" half of this item, as originally framed, targets two systems
   confirmed dormant in the live pipeline today (`PerceptionUpdatePhase` and `MotivationBiasService`,
   both zero call sites — a separate, already-disclosed, out-of-scope gap per
   `TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION`), and idea 34's real candidate-role set has no
   ADVENTURER/HERO slot to bias toward. This ticket must build `LegendFact` as real typed state,
   unit-tested directly against `PerceptionFilterService`, and disclose it honestly as "built, not yet
   visible in play" (matching idea 60's own precedent) rather than wiring the dormant pipeline stages
   into production or extending idea 34's candidate set — both are separate, larger, out-of-scope
   follow-ups.
2. **Idea 62 — Generations Misremember.** One child ticket, independent of idea 57's own landing per
   the "alongside" resolution above. Builds a new Deriver-pattern sibling (its own class, e.g. a
   `HistoricalDriftDeriver`/`FidelityState`/`FidelityCarryForward` structure mirroring
   `CultureDeriver`'s exact 3-layer pattern, reusing Chronicle's existing `Era` concept
   — `ERA_EPISODE_MIN=3` episodes/era — as the natural "generation" proxy) producing a *separate*
   derived record of how a specific recorded event's fidelity/certainty degrades with Era-distance —
   a battle survivors remember personally becomes a simplified story for their children, and a
   national myth after enough generations, whether or not it's accurate to what Chronicle actually
   recorded. Must NOT repurpose `BeliefEntry` (see Request Summary correction above) and must NOT
   mutate `NarrativeLedgerEntry`/`ChronicleHierarchy` in place. Disclosed as shipping with no live
   consumer yet (idea 63 is the eventual consumer, not built until after idea 57) — matching the
   sibling M5 batch's own disclosed `NamedIntentionBundle` precedent, not hidden as a complete
   end-to-end feature.
3. **Idea 63 — Belief Grows Around Real History.** One child ticket, HARD-BLOCKED (not merely
   sequenced) on idea 57 reaching DONE first — per two independent confirmations, idea 63 must consume
   idea 57's actual shipped `FameState`/`LegendFact` shape, not an assumed one; no ticket for idea 57
   existed anywhere before this epic, so idea 63 cannot even be planned in detail yet, only scoped.
   Also depends on idea 36 (Clan, already DONE — the organizational container), though `ClanState`
   carries zero founding-myth/shared-belief precedent today, confirmed by direct read — a
   `BeliefInstitution` attachment is wholly new state, not an extension of an existing field.
   `BeliefInstitution` (a new class — `origin_event_id`, `adherent_entity_ids`, `belief_strength`,
   a clan/container link — distinct from both `BeliefEntry` and `KnowledgeFact` per the resolved
   Knowledge/Belief reconciliation split) is the structural shape to build, per its own atlas card's
   underspecified schema. The card's own illustrative "shrine that outlasted a catastrophe" trigger
   has zero grounding in current code (confirmed: no such calamity-outcome signal exists anywhere) —
   do not invent one as an undisclosed second dependency; the only real, evidence-grounded trigger
   candidate is idea 57's own `fame`/`LegendFact` threshold-crossing. This ticket's Implement phase
   must not start until idea 57's own child ticket is DONE.

## Out of Scope
- Idea 67 (Living Relationship Decay) — a candidate the epic doc itself flags as "not yet one of the
  8 ideas this epic's Scope commits to."
- Any new `combat_victory`/`monster_slain` Narrative Ledger event type — idea 57's design doc
  explicitly scopes this out as "new event-scoring, not aggregation"; disclosed as a known limitation
  of Option B, not silently worked around.
- Building any new Culture Drift derivation/bias-application machinery — `CultureDeriver`/
  `CulturalBiasApplicator` is already real, live, and tested; idea 57/62 need only their own
  sibling/parallel consumption of Chronicle's grouped output.
- Anything from Milestones 1, 2, 3, 4, or 6.
- Re-litigating the Knowledge/Belief `BeliefEntry`/`KnowledgeFact` split decision — already made
  (deliberate, keep both) by `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`.

## Acceptance Criteria
- [x] All 3 child tickets (idea 57, idea 62, idea 63) are DONE, idea 63 landing after both idea 36
      (already true) and idea 57. Verified: all 3 in `tickets/done/m5-history-belief/` (folder moved
      as a whole once the last, idea 63, landed) — `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`,
      `TCK-20260905-FAME-DERIVER-LEGEND-FACT`, `TCK-20260905-BELIEF-INSTITUTION-DESIGN`. Per
      `tickets/working_log.csv`, idea 57 (`FAME-DERIVER-LEGEND-FACT`) landed 2026-09-05T05:55:00Z,
      before idea 63 (`BELIEF-INSTITUTION-DESIGN`, 2026-09-05T09:10:00Z).
- [x] Idea 57's child ticket documents, with fresh evidence, whether the "alongside" resolution for
      idea 62 held up in practice (i.e., idea 57 did not end up needing idea 62's output as an input).
      Verified: idea 57's own investigation independently found the epic's own "alongside" framing
      did NOT fully hold as stated (its own more specific scope language actually described a
      sequential dependency) but confirmed the practical resolution — building idea 62 as an
      independent sibling — was correct because a literal upstream-transform reading would have
      broken the already-shipped `CultureDeriver`. Idea 57 shipped consuming raw Chronicle output
      directly, with zero dependency on idea 62's output, confirming the practical outcome intended.
- [x] Idea 57's `FameDeriver` mirrors `CultureDeriver`'s exact 3-layer pattern (Deriver/Model/
      Exporter-Importer), introduces zero new Chronicle event-scoring logic beyond the disclosed
      Option B event-type rule, and is called from the same `CampaignOrchestrator._advance_state()`
      episode-boundary call site. Verified by `TCK-20260905-FAME-DERIVER-LEGEND-FACT`'s own
      Architecture-Verify pass and 1282 passing tests.
- [x] Idea 62's transform does not mutate `NarrativeLedgerEntry`/`ChronicleHierarchy` in place — it
      produces its own separate derived view, preserving Chronicle's own record as ground truth.
      Verified: `src/domains/fidelity/` writes only into a new `CampaignState.historical_drift`
      field, confirmed by `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`'s own architecture guard test.
- [x] Idea 63's belief/reverence mechanism reads both `ClanState` (as container) and idea 57's fame
      substrate as inputs; it is not a thin wrapper on either alone. Verified:
      `BeliefInstitutionDeriver.derive()` reads real `ClanState` membership (`final_state.clans`,
      read-only) and real `LegendFact`/`FameState` (idea 57) together to form per-clan divergent
      `BeliefInstitution` records — neither input alone would produce the in-group/out-group
      distinction this mechanism's own acceptance signal requires.

## Related Tickets
### Predecessor epic (done)
- `TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION` — death-and-lineage and reputation branches, DONE.
  This epic covers the remainder of the same parent roadmap doc's 8-idea scope.

### Upstream dependencies (gates now cleared)
- `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` (DONE, PR #123)
- `docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md` (PR #126)
- `docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md` (PR #126)
- `TCK-20260831-CLAN-STATE-SCHEMA` (idea 36, DONE — idea 63's container prerequisite)

### Child tickets (implementation sequence, all DONE)
- TCK-20260905-CHRONICLE-FIDELITY-DRIFT — idea 62 (Generations Misremember), no intra-batch deps (DONE)
- TCK-20260905-FAME-DERIVER-LEGEND-FACT — idea 57 (The Living Legend Feedback Loop), no intra-batch deps (DONE)
- TCK-20260905-BELIEF-INSTITUTION-DESIGN — idea 63 (Belief Grows Around Real History), hard-blocked
  on TCK-20260905-FAME-DERIVER-LEGEND-FACT landing first (DONE)

### Real, disclosed follow-up work (not silently treated as complete)
- `TCK-20260905-CHORE-CARRYFORWARD-DERIVER-CONSOLIDATION` — filed during idea 63's own Architecture
  Review, which flagged (non-blocking) that Culture, Fidelity, Fame, and Belief-Institution are now
  4 structurally near-identical Deriver/Model/Exporter-Importer triples worth a consolidation pass.

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md
- docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md
- docs/brainstorm/rpg_feature_atlas.html (ideas 57, 62, 63)
- docs/brainstorm/rpg_expected_schemas.html (schema-57)
- docs/domains/culture (CultureDeriver precedent, read via source not a doc)

## Related Stored Artifacts
None — epic tier tracks child tickets only; each child ticket carries its own staging artifacts.

## Related Code Areas
- src/domains/culture/deriver.py, model.py, exporter.py (the precedent pattern being mirrored)
- src/domains/campaigns/state.py (NarrativeLedgerEntry, ChronicleHierarchy)
- src/domains/campaigns/orchestrator.py (episode-boundary call site)
- src/domains/chronicle/significance.py, naming.py, grouper.py
- src/core/state.py (ClanState — idea 63's container)
- town/buildings.py (CHURCH services — confirmed dead, idea 63's own finding)

## Assumptions / Open Questions
- The "idea 57/62 alongside, not strictly sequenced" resolution is this epic's own judgment call,
  based on idea 62's real atlas card language and idea 57's already-merged design doc's own
  implementation assumption — each child ticket's Investigate phase must independently re-confirm
  this holds against real code before implementation, not inherit it uncritically (the same
  discipline applied to every premise correction in the predecessor epic).
- `fame_threshold`'s numeric value and whether `FameState` needs more than one axis (fame vs.
  notoriety/infamy) are both explicitly left open by the design doc — real Plan-phase decisions for
  idea 57's child ticket, not resolved here.
- Idea 63's exact belief/reverence mechanism shape (what triggers it, how it's read) is not yet
  designed anywhere — its own child ticket's Investigate phase must derive it from the real atlas
  card text plus whatever idea 57 actually ships, not invent it from scratch independently.

## Implementation Notes
(Epic tier — no direct implementation. See each child ticket.)

## Test Summary
(Epic tier — see each child ticket's own Test phase. Aggregate: idea 62 landed with 969 scoped
tests passing, idea 57 with 1282, idea 63 with 1428 — each ticket's own final scoped run, not
cumulative across tickets since the same broad `tests/unit/domains/` etc. directories were re-run
each time.)

## Files Changed
(Epic tier — see each child ticket's own Files Changed section. Epic-level summary of touched
subsystems: `src/domains/fidelity/`, `src/domains/fame/`, `src/domains/belief_institution/` (all
new), `src/domains/campaigns/{state,orchestrator}.py`, plus corresponding tests,
`docs/mechanics/05_world_evolution.md` (§8/§9/§10), 3 new `docs/world/*_contract.md` files,
`docs/parity_ledger/world_dynamics.yaml`, the parent epic doc, `docs/brainstorm/rpg_feature_atlas.html`,
and `docs/brainstorm/simulation_capabilities.html`.)

## Completion Summary
All 3 child tickets landed successfully, closing out the history-and-belief branch and, with it,
the entire M5 "Memory, Reputation & Legacy" epic — all 8 source design ideas (53, 54, 55, 57, 58,
60, 62, 63) are now shipped across this epic and its predecessor
(`TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION`). The epic's own two premise corrections (idea 62 is
an independent sibling, not a mandatory upstream transform; idea 62 must not repurpose
`BeliefEntry`) both held up under real implementation, independently re-confirmed by each child
ticket's own investigation rather than inherited on faith. All three tickets (idea 62's Chronicle
fidelity drift, idea 57's Living Legend Fame, idea 63's Belief Institutions) follow the same
Deriver/Model/Exporter-Importer pattern originated by `CultureDeriver`, and all three honestly
disclose shipping as "built, not yet visible in play" — real, tested, typed state and derivation
logic with no live pipeline consumer wired in yet, rather than overclaiming a finished,
player-visible feature. One real follow-up gap was found and filed rather than silently absorbed:
the now-4-sibling structural duplication across Culture/Fidelity/Fame/Belief-Institution
(`TCK-20260905-CHORE-CARRYFORWARD-DERIVER-CONSOLIDATION`).

---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-CHRONICLE-FIDELITY-DRIFT
phase: open
date: 2026-09-05
tags: [social, strategy]
---

# TCK-20260905-CHRONICLE-FIDELITY-DRIFT

## Title
Idea 62 — Generations Misremember (Chronicle fidelity drift)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 62 (Generations Misremember, docs/brainstorm/rpg_feature_atlas.html) proposes that Chronicle's recorded history loses fidelity as it passes down generationally — a battle survivors remember personally, their children know as a simplified story, a hundred years on becoming "we were betrayed" whether or not that's accurate. Confirmed via direct grep: zero code anywhere in src/ implements any fidelity/distortion/misremember-style degradation of Chronicle's output today.

Investigation (2026-09-05) resolved two real premise errors in the M5 epic doc's original framing of this idea:

1. Idea 62 is NOT a mandatory upstream transform that CultureDeriver (src/domains/culture/deriver.py, already shipped and live) or idea 57's FameDeriver must route through — CultureDeriver already reads hierarchy.events directly with zero transform layer in front of it, and forcing idea 62 into that position would mean a breaking retrofit of already-shipped production code. The real atlas card for idea 62 itself says "sequence alongside idea 57 since both consume the same Chronicle substrate," i.e. an independent sibling, not a pipeline stage.
2. Idea 62 should NOT be built by repurposing BeliefEntry (src/systems/strategic_systems/belief.py) — that class is a per-entity, tactical/near-term decision-support record (real live consumers: cooperation risk evaluation via src/domains/cooperation/evaluators.py, route-blocking via src/systems/strategic_systems/detour.py, guild rumor propagation via src/systems/social_systems/guilds.py) with a ticks-since-discovered decay model, structurally mismatched with population/generation-scale historical myth-drift.

This ticket instead builds a new Deriver-pattern sibling mirroring CultureDeriver's exact 3-layer pattern (Deriver/Model/Exporter-Importer), reusing Chronicle's existing Era concept (ERA_EPISODE_MIN=3 episodes/era, src/domains/chronicle/grouper.py) as the natural generation-distance proxy instead of inventing a new time unit or trying to walk the reproduction epic's per-entity lineage graph (which requires live entity-population access a stateless ChronicleHierarchy-only Deriver doesn't have).

## Scope
- Add a new Deriver-pattern sibling to src/domains/culture/deriver.py's exact 3-layer shape — a new module (e.g. src/domains/chronicle/drift.py or a new package, following the same reasoning idea 57's design doc used for choosing a new module over reusing culture/), with: a pure, stateless classmethod (e.g. FidelityDeriver.derive(hierarchy, current_era) -> Dict[event_key, FidelityState]) that computes a per-recorded-event fidelity/certainty value that decreases with Era-distance from the current Era; a frozen FidelityState dataclass (at minimum a fidelity: float in [0.0, 1.0]) plus a FidelityCarryForward wrapper (event/subject key + FidelityState + derived_episode), mirroring CultureCarryForward's exact shape; a FidelityExporter.export(campaign_state, hierarchy, episode_index, ...) static method called from the same CampaignOrchestrator._advance_state() episode-boundary call site as CultureDriftExporter.export() and idea 57's FameExporter.export(); a FidelityImporter with a thin, None-safe lookup.
- The new derived record must NOT mutate NarrativeLedgerEntry or ChronicleHierarchy in place — Chronicle's own record stays ground truth; the drift view is a separate, additional derived structure written into a new CampaignState field (e.g. campaign_state.historical_drift: Dict[str, FidelityCarryForward]), mirroring region_cultures'/entity_fame's own field shape.
- The transform must stay pure/stateless and deterministic given the same sorted input, matching Chronicle's own documented contract (docs/simulation/domains/chronicle_contract.md) and CultureDeriver's own no-engine-import constraint — calling it twice with the same ChronicleHierarchy input must produce byte-identical output.
- Any durable write must go through a typed Update object applied via the existing authoritative apply path (src/engine/patches.py), matching CultureDriftExporter's own established write pattern — never a direct state mutation.
- Disclose explicitly, in this ticket's own Implementation Notes, that this ships with no live consumer yet: idea 62's real eventual consumer is idea 63 (Belief Grows Around Real History), not yet built, and possibly future feud/national-myth mechanics — matching the sibling M5 batch's own disclosed NamedIntentionBundle-write-no-read gap pattern (TCK-20260904-LINEAGE-DEATH-DISPATCH), not hidden as a complete end-to-end feature.

## Out of Scope
- Repurposing BeliefEntry or KnowledgeFact for this mechanism — confirmed the wrong shape; do not touch either class.
- Making this a mandatory preprocessing layer that CultureDeriver or idea 57's FameDeriver must route through — confirmed infeasible against already-shipped code; both continue reading hierarchy.events directly, unchanged by this ticket.
- Idea 57's FameDeriver/FameState/LegendFact structure and idea 63's belief-institution mechanism — sibling/downstream tickets of the same epic.
- Any change to Chronicle's own grouping/significance-scoring logic (src/domains/chronicle/grouper.py, significance.py) — this ticket reads Chronicle's output, it does not change how Chronicle itself scores or groups events.
- Reworking the per-entity lineage/generation fields already in src/core/state.py (LifecycleComponent.generation, CorpseState.generation) — confirmed unrelated concepts (hero-rebirth counter, corpse-decay counter), do not repurpose them by name-matching.

## Acceptance Criteria
- Given a ChronicleHierarchy with events spanning 2 or more Eras, FidelityDeriver.derive() produces a fidelity value for an event that is strictly lower the further that event's Era is from the current Era, verified by a new test.
- FidelityDeriver.derive() called twice with the same ChronicleHierarchy input produces byte-identical output (determinism guard test), matching Chronicle's own documented stateless/deterministic contract.
- FidelityExporter.export() is called from the same CampaignOrchestrator._advance_state() episode-boundary call site as CultureDriftExporter.export(), verified by a test asserting both run within the same advance-state call.
- The new campaign_state.historical_drift field (or equivalently-named field) is written only through a typed Update applied via the authoritative apply path — verified by a source-text guard test confirming no direct state.historical_drift mutation exists outside that path.
- This ticket introduces zero changes to BeliefEntry, KnowledgeFact, or CultureDeriver's own read/write behavior — verified by a source-text guard test and by CultureDeriver's own existing test suite passing unmodified.

## Related Tickets
- TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF
- TCK-20260905-FAME-DERIVER-LEGEND-FACT
- TCK-20260905-BELIEF-INSTITUTION-DESIGN
- TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION
- TCK-20260904-LINEAGE-DEATH-DISPATCH

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/rpg_expected_schemas.html
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md
- docs/simulation/domains/chronicle_contract.md

## Related Stored Artifacts
None

## Related Code Areas
- src/domains/culture/deriver.py
- src/domains/culture/model.py
- src/domains/culture/exporter.py
- src/domains/campaigns/state.py
- src/domains/campaigns/orchestrator.py
- src/domains/chronicle/grouper.py
- src/domains/chronicle/significance.py
- src/systems/strategic_systems/belief.py
- src/engine/patches.py

## Assumptions / Open Questions
- Exact fidelity-decay formula (linear vs. stepped vs. exponential by Era-distance) is a Plan-phase decision, not resolved by investigation.
- Whether the derived key should be per-event, per-subject, or per-region is a Plan-phase decision — the design intent (a specific recorded event's story degrading) suggests per-event, but this should be confirmed against real NarrativeLedgerEntry structure during Plan.
- This ticket has no dependency on idea 57's own ticket landing first (independent sibling, per this epic's own re-confirmed resolution) — safe to implement in either order relative to it.
- `layer: strategy` was chosen because this mechanism derives from and feeds strategic/cognitive belief formation over historical record, matching the existing `strategy` layer registration; it is not a `social` mechanic in the interpersonal-relationship sense despite the `social` tag reflecting its narrative/reputation-adjacent subject matter.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

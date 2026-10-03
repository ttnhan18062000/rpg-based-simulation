---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-BELIEF-INSTITUTION-DESIGN
artifact_type: investigation
tags: [social, strategy]
---

# Investigation — TCK-20260905-BELIEF-INSTITUTION-DESIGN

## Current Behavior (file:line refs)

- `src/domains/fame/model.py` — `FameState.fame: float` (default 0.0, clamped [0.0,1.0]), `FameCarryForward(subject_id, fame, derived_episode)`. Ships with no live consumer.
- `src/domains/fame/exporter.py` — `FameExporter.export()` derives/writes `campaign_state.entity_fame`. `FameImporter.get_fame(campaign_state, entity_id) -> Optional[FameState]`, `None`-safe.
- `src/domains/fame/legend.py:38` — `FAME_THRESHOLD = 0.5` (anchors `CHRONICLE_THRESHOLD`). `LegendFactService.for_entity(campaign_state, subject_id, entity_name=None) -> Optional[LegendFact]` — the real, confirmed trigger substrate for this ticket. `LegendFact(subject_id, fame, entity_name)`, frozen, no live pipeline caller (unit-tested only against `PerceptionFilterService.filter()`).
- `src/domains/fidelity/model.py` — sibling precedent: `FidelityState`/`FidelityCarryForward`, keyed by `entry_id` (not `subject_id`), same no-live-consumer disclosure pattern, explicitly names idea 63 (this ticket) as "the intended eventual reader" (`model.py:17`).
- `src/domains/campaigns/orchestrator.py:210-249` (`_advance_state`) — the call site all three siblings hook into. Confirmed by direct read: `final_state: "AuthoritativeState"` (the completed episode's tick-loop state, includes `final_state.clans: Dict[str, ClanState]`, `src/core/state.py:1367`) and `self._state` (the `CampaignState`, where `region_cultures`/`historical_drift`/`entity_fame` all live) are BOTH in scope at this single call site. This means a 4th exporter call here can read real `ClanState` membership (`final_state.clans`) alongside Chronicle-derived fame (`self._state`/`FameImporter`) with zero new plumbing.
- `src/core/state.py:757-773` — `ClanState`: `clan_id, name, member_entity_ids: Tuple[int,...], home_region_ids, asset_ids, tension_level, clan_reputation, leader_entity_id, founded_tick, dissolved_tick`. No founding-myth/shared-belief field — confirmed, matches prior investigation.
- `src/domains/campaigns/state.py:226-241` — `NarrativeLedgerEntry`: `episode, tick, event_type, subject_id: str, payload, significance, entry_id` (`entry_id` format: `"{episode}:{tick}:{event_type}:{subject_id}"`, a stable dedup key). `subject_id` is a string that may represent an entity OR faction/node id — not guaranteed int-castable.
- `src/systems/strategic_systems/belief.py:23-31` — `BeliefEntry(id, subject, claim, certainty, source, source_entity_id, created_tick, last_refreshed_tick, contradictions)`, per-entity, on `StrategicComponent.beliefs`, decayed by `BeliefCycleSystem.decay_stale_beliefs` (tick-based, ticks-since-refresh). Confirmed real live consumers exist elsewhere (cooperation risk, route-blocking, guild rumors) — none touched by this ticket.
- `src/core/self_model.py:49-61` — `KnowledgeFact(subject, fact_type, details, certainty, source_id, recorded_tick)`, per-entity, queried/structured. Neither `BeliefEntry` nor `KnowledgeFact` has an `adherent_entity_ids`/`belief_strength`/clan-linkage shape — confirmed, both structurally wrong for this ticket's population-scale institution concept.
- `src/town/buildings.py:23` — `CHURCH: services=["BLESSING","RESURRECTION"]`, confirmed zero consumers anywhere in `src/` (re-verified via grep).
- `src/world/calamity.py` — confirmed no structure/building-survival or "shrine" signal exists (re-verified).

## Mechanics/Engine Constraints

- Durable State Rule (CLAUDE.md): any state surviving beyond one tick/episode needs a typed model, stable location, defined lifecycle, tests.
- `CampaignState` is confirmed NOT frozen — mutated directly by `CampaignOrchestrator` (its own docstring), the same pattern `CultureDriftExporter`/`FidelityExporter`/`FameExporter` all use. Since this ticket's real read-side input (`LegendFactService`, non-live) is itself `CampaignState`-scoped, `BeliefInstitution` is scoped to `CampaignState` too, mirroring `entity_fame`/`historical_drift`'s own field shape — NOT `AuthoritativeState`/`ClanState` (which would require a `src/engine/patches.py`-routed typed `ClanUpdate`, a heavier and, for a non-live trigger, unjustified path). `ClanState` is read-only input here (via `final_state.clans`, already in scope at the call site) — never written.
- Chronicle pipeline stages are stateless/deterministic given the same sorted input (`docs/simulation/domains/chronicle_contract.md`) — this ticket's derivation must preserve that.

## Docs Requiring Update

- `docs/mechanics/05_world_evolution.md`: new subsection for BeliefInstitution, following §8's (Chronicle fidelity) precedent shape.
- `docs/parity_ledger/world_dynamics.yaml`: new entry, following `WORLD-FIDELITY-001/002`'s precedent.
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`: status annotation for idea 63, closing out the 8-idea M5 epic.
- `docs/brainstorm/rpg_feature_atlas.html`: status-update note on idea 63's card, matching the established M5-batch convention (idea 60's own precedent).

## Parity Ledger Overlap (IDs + status)

None pre-existing for this exact mechanism. `docs/parity_ledger/world_dynamics.yaml`'s `next_available_id()` for the `WORLD-FIDELITY` family is `WORLD-FIDELITY-003` (two entries already exist from the sibling ticket); this ticket's own entry uses a new, distinct id (checked via `next_available_id()` at Parity phase, not guessed here).

## Prior Work

- `TCK-20260905-CHRONICLE-FIDELITY-DRIFT` (idea 62, DONE) — sibling precedent, `src/domains/fidelity/`.
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (idea 57, DONE) — this ticket's hard blocking dependency, now satisfied; `src/domains/fame/`.
- `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` (DONE) — `BeliefEntry`/`KnowledgeFact` deliberate split; `BeliefInstitution` must be a third, genuinely distinct class.
- `TCK-20260831-CLAN-STATE-SCHEMA`, `TCK-20260903-CLAN-LIFECYCLE-SUCCESSION` (DONE) — `ClanState`'s real shape.

## Risks and Open Questions

- `origin_event_id`: `FameState` is an AGGREGATE over possibly multiple contributing `NarrativeLedgerEntry` records (no single `entry_id`). Resolution: derive `origin_event_id` as the single highest-significance contributing entry for that subject (preferring a posthumous HERO `entity_death` entry — "died gloriously" is the more legend-shaped moment — falling back to the highest-significance `quest_completed` entry). This is a real design simplification, disclosed in Plan.
- `subject_id` (str) vs. `ClanState.member_entity_ids` (Tuple[int,...]): membership check requires a safe int cast; a non-numeric `subject_id` (e.g. a faction id) safely means "no clan member match" rather than raising.
- Divergent-interpretation formula: no real per-member "awareness" signal exists (Perception is dormant, per the sibling ticket's own disclosure). Grounded simplification: `belief_strength = fame` for the subject's own clan (in-group — the legend is one of their own), `belief_strength = fame * OUT_GROUP_DAMPENING` for every other existing clan (out-group — they've heard of the legend but don't own it), where `OUT_GROUP_DAMPENING` is a Plan-phase-decided constant < 1.0. This is a genuine, disclosed simplification of "different groups interpreting the same event differently," not a full social-simulation model.
- Ships with a real but disclosed limitation: BeliefInstitution formation is entirely dependent on LegendFact, which is itself "built, not yet visible in play" (no live Perception/Motivation wiring) — this ticket does not change that; the whole idea-57→63 chain remains dormant end-to-end for actual live gameplay, only unit-testable, which must be disclosed honestly, not hidden.

## Anti-Drift Hazards

- Do not repurpose `BeliefEntry`/`KnowledgeFact` — confirmed wrong shapes, both have real live consumers this ticket must not touch.
- Do not write to `ClanState`/`AuthoritativeState` — `final_state.clans` is read-only input.
- Do not invent a new calamity/shrine-survival signal — confirmed not to exist; use `LegendFactService` as the sole real trigger.
- Do not add a new SimQ scoring pillar or CHURCH building wiring — explicitly out of scope per the source schema's own "too underspecified" caveat.

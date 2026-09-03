---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-SETTLEMENT-CULTURE-READ
phase: open
date: 2026-09-04
tags: [content, documentation]
---

# TCK-20260904-SETTLEMENT-CULTURE-READ

## Title
Settlements read region_cultures as a Culture Drift consumer (idea 61)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 61 (Settlements Develop Personalities). Corrected scope per the 2026-09-02 culture-drift-hardening finding: `CultureDeriver`/`CulturalBiasApplicator` is NOT dormant — it's live, tested, and has a real write-side call site (`CampaignOrchestrator._advance_state` -> `CultureDriftExporter.export`, `src/domains/campaigns/orchestrator.py`) populating `CampaignState.region_cultures`. The real blocker is reachability: `CampaignOrchestrator._build_initial_state()` never carries Region/Place data into its per-episode `AuthoritativeState` at all (no `regions=` argument, no `WorldCompiler` call), so Campaign mode cannot deliver `region_cultures` back into in-episode settlement behavior today, independent of idea 66. This ticket scopes idea 61 as a read-side consumer and resolves the Campaign-mode-reachability question explicitly rather than assuming it's trivially unblocked.

## Scope
- Resolve, as an explicit AC (not left open), whether any of the 21 real corpus worlds runs multi-episode Campaign mode today (the same open question named in `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`'s Scope item 2) — record the answer in `investigation.md`.
- Scope idea 61 to non-Campaign-mode consumption of settlement-personality-relevant culture signal only: name the specific field(s)/method(s) this ticket reads (`region_cultures` / `CultureCarryForward` or the underlying `CultureState` it derives from) and implement a read-side consumer that biases settlement/Place behavior using `CulturalBiasApplicator.compute_culture_delta` or an equivalent narrow adapter, without depending on `CampaignOrchestrator`'s episode-boundary machinery.
- File a separate new ticket (not part of this one's implementation) for the Campaign-mode Region/Place-carry gap in `CampaignOrchestrator._build_initial_state()` — name it explicitly in this ticket's Out of Scope and Related Tickets rather than silently dropping it.
- Correct the stale badge text on `docs/brainstorm/rpg_feature_atlas.html`'s idea 61 card (currently implies `CulturalBiasApplicator` itself is unwired/dormant) to reflect: `CultureDeriver`/exporter write-side is live; `CulturalBiasApplicator` read-side has zero production call sites; the real gap is Campaign-mode Region/Place reachability, not activation.
- `PlaceState` currently has no name/descriptive-identity field (only `place_id` slug) — if this ticket's settlement-personality read-side needs a display identity to attach flavor/bias output to, that gap must be named explicitly (schema addition or explicit workaround), not silently assumed to already exist.

## Out of Scope
- Extending `CampaignOrchestrator._build_initial_state()` to carry compiled regions/places into per-episode `AuthoritativeState` — recommended as a separate, larger ticket given `CulturalBiasApplicator` has zero production call sites today and `CampaignOrchestrator`'s episode-state gap is independent of idea 66.
- Wiring `CultureDeriver`/`CulturalBiasApplicator` for the first time — confirmed already live/complete by the 2026-09-02 hardening-plan investigation; not this ticket's job.
- Broader doc-language corrections to `rpg_m5_memory_reputation_epic.md` / `rpg_m6_political_identity_epic.md` / the parent roadmap (also flagged by the culture-drift-hardening plan) — only the M4 epic doc and the atlas idea-61 card are in this ticket's scope.

## Acceptance Criteria
- `investigation.md` records a definite answer to whether any real corpus world runs multi-episode Campaign mode today.
- A read-side consumer exists that reads `region_cultures` (or the `CultureState` it derives from) and produces a settlement/Place-level personality signal, scoped explicitly to non-Campaign-mode consumption.
- A new ticket is filed for the `CampaignOrchestrator` Region/Place-carry gap and referenced by ID in this ticket's Related Tickets / Out of Scope — the gap is not silently dropped.
- `docs/brainstorm/rpg_feature_atlas.html`'s idea 61 card badge/text is corrected to distinguish `CultureDeriver` (live) from `CulturalBiasApplicator` (zero production call sites) and to name the real Campaign-mode-reachability gap.
- New tests cover the read-side consumer's behavior given populated vs. empty/absent `region_cultures` data.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
- (new, to be filed by this ticket) Campaign-mode Region/Place-carry gap in CampaignOrchestrator._build_initial_state()

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md
- docs/world/culture_drift_contract.md
- docs/mechanics/05_world_evolution.md (Cultural Drift)
- docs/parity_ledger/world_dynamics.yaml (WORLD-CULT-001/002/003)
- docs/brainstorm/rpg_feature_atlas.html (idea 61)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/domains/culture/deriver.py
- src/domains/culture/applicator.py
- src/domains/culture/exporter.py
- src/domains/campaigns/orchestrator.py (_build_initial_state, _advance_state)
- src/domains/campaigns/state.py (CampaignState.region_cultures)
- src/core/state.py (PlaceState — no name/identity field)

## Assumptions / Open Questions
- Whether any of the 21 real corpus worlds actually runs multi-episode Campaign mode is unresolved today and must be answered by this ticket, per the hardening plan's own Scope item 2.
- `CulturalBiasApplicator` (`src/domains/culture/applicator.py`) has zero production call sites today — only test coverage; this ticket is expected to wire it to at least one real production consumer as part of the read-side implementation, not add another unused/inert piece.
- `PlaceState` has no name/descriptive-identity field; if settlement personality needs one, that's a real schema gap this ticket must name rather than assume solved.
- This ticket deliberately narrows scope away from fixing `CampaignOrchestrator`'s episode-state Region/Place gap, per the epic doc's own recommended narrower framing — the Campaign-mode fix is real but out of scope here and must be tracked by a new ticket, not dropped.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)

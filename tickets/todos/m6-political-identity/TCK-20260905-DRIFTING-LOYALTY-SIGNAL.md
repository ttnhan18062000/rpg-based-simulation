---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260905-DRIFTING-LOYALTY-SIGNAL
phase: open
date: 2026-09-05
tags: [world, faction]
---

# TCK-20260905-DRIFTING-LOYALTY-SIGNAL

## Title
Drifting Loyalty (M6 idea 56) — a real read-side region_cultures consumer, not culture-drift activation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Idea 56 (M6 epic child 2 of 3, `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`) derives gradual
loyalty pressure that may request or influence idea 39's affiliation-mutation primitive. Its own
epic doc's original framing ("needs Culture Drift's substrate activated first") was corrected
2026-09-02 (hardening backlog item 3,
`docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`): `CultureDeriver`/
`CulturalBiasApplicator` is real, live, and tested today, not dormant. This ticket's real remaining
scope is narrower than originally framed — a read-side consumer of `region_cultures`, not new
derivation/bias-application machinery.

**Confirmed real, not assumed, before this ticket's own Investigate phase re-confirms at
implementation time:**
- `region_cultures: Dict[str, CultureCarryForward]` (`src/domains/campaigns/state.py`) is real,
  populated, durable state — but only when a Campaign actually runs multi-episode.
- **Real, narrow reachability gap, confirmed 2026-09-05**: exactly one real corpus profile
  (`config/simulation_quality/profiles/campaign_life_arc.yaml`) enables multi-episode Campaign mode,
  hardcoded to one world (`frontier_living_world`), and it is not wired into the standard CI/
  calibration sweep (confirmed via `.github/workflows/` grep — zero hits). This ticket's own consumer
  logic will be real and correct, but testing it against the routine corpus-grading flow is currently
  not possible without also addressing that reachability gap (M9's own `CampaignScorecardEvaluator`
  field gap) — scope a targeted integration test against the one real profile instead of assuming
  corpus-wide coverage.
- Sequencing: per the 2026-08-29 plan-owner decision, idea 39 establishes the mutation primitive
  first; this ticket's derived signal is meant to request/influence that primitive, so this ticket
  depends on `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` landing first (not "before or alongside,"
  correcting the epic doc's own prior internal contradiction, resolved in the parent epic ticket).

## Scope
- Implement a read-side consumer of `region_cultures` that derives a gradual loyalty-pressure signal
  per entity (or per relevant population unit — to be confirmed during Investigate) based on how far
  an entity's current affiliation has drifted from their home region's carried-forward culture.
- Wire this signal as an input to idea 39's affiliation-mutation trigger condition (from
  `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`), not as an independent mutation path of its own.
- Add a targeted integration test against the one real Campaign-mode-enabling profile
  (`campaign_life_arc.yaml`), rather than assuming standard-CI coverage exists.
- Document the read-only consumption pattern (mirroring idea 61's own precedent,
  `TCK-20260904-SETTLEMENT-CULTURE-READ`) so this doesn't reinvent that wiring.

## Out of Scope
- Building any new Culture Drift derivation/bias-application machinery — confirmed already complete;
  this ticket only consumes existing `region_cultures` output.
- Closing M9's `CampaignScorecardEvaluator` field gap or wiring Campaign mode into standard CI — that
  is M9's own scope; this ticket only needs to test correctly against the one real profile that
  exists today.
- Idea 39's own mutation-primitive implementation — `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`,
  sequenced before this ticket.
- Idea 59/65 — `TCK-20260905-HOME-EXILE-REFUGEE-THREADS`.

## Acceptance Criteria
- [ ] A real, tested function derives a per-entity (or per-population-unit) loyalty-drift signal from
      `region_cultures`, read-only, with no mutation of `CampaignState` or any other durable structure
      outside its own sanctioned output.
- [ ] The derived signal is wired as a real input to idea 39's mutation-trigger condition (confirmed
      via a test exercising both tickets' code together, once idea 39 has landed).
- [ ] A targeted integration test runs against `campaign_life_arc.yaml`'s real multi-episode Campaign
      path and confirms the signal derives correctly from real, populated `region_cultures` data.
- [ ] Determinism confirmed: no unsorted iteration over `region_cultures` or any derived collection
      feeds a durable structure's key/iteration order — this is exactly the failure class PR #128's
      own architecture review caught (`belief_institution/deriver.py`'s unsorted `set`); guard against
      repeating it here.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (parent epic)
- `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` (idea 39, must land first)
- `TCK-20260904-SETTLEMENT-CULTURE-READ` (idea 61, the precedent read-side consumer pattern)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`
- `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md` (Campaign-mode-reachability
  finding this ticket's own test scope is built around)
- `docs/world/culture_drift_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/culture/{model,deriver,exporter,applicator}.py`
- `src/domains/campaigns/state.py` (`region_cultures`)
- `src/domains/campaigns/orchestrator.py`
- `tools/calibrate_simq.py` (`_run_campaign_engine`)
- `config/simulation_quality/profiles/campaign_life_arc.yaml`

## Assumptions / Open Questions
- Whether the loyalty-drift signal is computed per-entity or per-population-unit is not decided here
  — real design work for this ticket's own Investigate/Plan phases.
- Whether this ticket can meaningfully land before idea 39 (as a pure derivation with no live
  consumer yet, matching idea 57/62's own "built, not yet visible in play" precedent from M5) instead
  of strictly after it, is worth revisiting during Investigate if idea 39 turns out to be
  significantly delayed — not decided here, the epic's default order is 39 first.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

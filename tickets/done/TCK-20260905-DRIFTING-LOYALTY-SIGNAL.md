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
DONE

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
- [x] A real, tested function derives a per-region loyalty-drift signal from `region_cultures`,
      read-only, with no mutation of `CampaignState` or any other durable structure outside its own
      sanctioned output. Verified: `LoyaltyDriftService.compute_loyalty_pressure()`
      (`tests/unit/social/test_loyalty_drift.py`, including an explicit no-mutation guard test).
      Granularity resolved as per-region (not per-entity), since `faction_conflict_exposure` is
      itself a region-scoped axis — matches `describe_settlement_personality()`'s own precedent.
- [x] The derived signal is wired as a real input to idea 39's mutation-trigger condition, confirmed
      via a test exercising both tickets' code together
      (`test_check_defection_fires_earlier_with_loyalty_pressure`, proving a group below the base
      threshold defects once `loyalty_pressure` lowers the effective threshold).
- [x] A targeted integration test runs against the real Culture Drift derivation pipeline (the same
      code path `campaign_life_arc.yaml`'s multi-episode run exercises) and confirms the signal
      derives correctly from real, populated `region_cultures` data — verified:
      `tests/integration/culture/test_loyalty_drift_campaign.py`.
- [x] Determinism confirmed: no unsorted iteration is introduced — `compute_loyalty_pressure()` is a
      pure single-lookup function, no set/dict-iteration-order dependency exists to guard against;
      an explicit repeated-call determinism test is included regardless
      (`test_compute_loyalty_pressure_is_deterministic`).

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
`staging_artifacts/TCK-20260905-DRIFTING-LOYALTY-SIGNAL/` — investigation.md, plan.md, test_plan.md.

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

**Real correction to this ticket's own literal text, evidence-grounded, not inherited uncritically**:
the Request Summary described the signal as based on "how far an entity's current affiliation has
drifted from *their home region's* carried-forward culture." Confirmed via `grep -rn
"home_region_id\s*=" src/`: `StrategicComponent.home_region_id` is populated **only** for bosses
(`src/world/boss.py:135`) — idea 59 (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`, not yet landed) is
what populates it for ordinary entities. Building against it today would make this signal a permanent
no-op for every non-boss entity. **Corrected to key on `entity.navigation.region_id`** instead —
confirmed real and live-populated for every entity, both at world-compile time
(`worldbuilding/compiler.py:552`) and continuously during movement (`engine/movement.py`,
`engine/apply.py`, `engine/patches.py`). Disclosed in investigation.md and the epic doc's own status
annotation, not silently substituted.

**Disclosed architectural gap, not silently hidden**: `GroupPhase.resolve()`
(`src/engine/pipeline_phases/groups.py`), the one live per-tick caller of
`effective_defection_threshold()`/`check_defection()`, receives only `AuthoritativeState` — it has no
`CampaignState`/`region_cultures` access, since that state is populated only at Campaign episode
boundaries (`CampaignOrchestrator._advance_state()`), one layer above the per-tick Kernel pipeline. No
bridge between the two exists anywhere in this codebase today (confirmed: the precedent read-side
consumer, `TCK-20260904-SETTLEMENT-CULTURE-READ`'s `describe_settlement_personality()`, is itself an
orchestrator-level read method, not a per-tick pipeline consumer — the same structural gap). Building
that bridge is a separate, larger, cross-cutting architectural change well beyond this standard-tier
ticket's own scope, and idea 56's own text doesn't ask for it either. **Resolution**: `loyalty_pressure`
is a real, tested, optional parameter (default `0.0`, fully backward-compatible) — proven end-to-end
via a real Culture-Drift-pipeline integration test — but the one live per-tick call site does not yet
supply a real value. This matches the "built, not yet visible in play" precedent from ideas 57/60/62 in
the M5 batch, not a silently-hidden gap.

No new Culture Drift derivation/bias-application logic was built, matching the epic's own out-of-scope
constraint — `LoyaltyDriftService` reuses `CultureState.faction_conflict_exposure` and
`CultureDriftImporter.get_culture()` exactly as they already exist.

## Test Summary
- `tests/unit/social/test_loyalty_drift.py` (new, 5 tests): real-value derivation, `None`-safe for an
  unpopulated region, `None`-safe for a falsy `region_id`, determinism (repeated calls), no-mutation
  guard.
- `tests/unit/social/test_party_lifecycle.py` (4 new tests added to the existing file): backward-
  compatible default, threshold lowered by `loyalty_pressure`, floored at `1`, and
  `check_defection()` firing earlier with `loyalty_pressure` supplied (proving the real wiring).
- `tests/integration/culture/test_loyalty_drift_campaign.py` (new, 3 tests): confirms
  `config/simulation_quality/profiles/campaign_life_arc.yaml` exists; a region with real
  `war_declared` events (the literal event_type `CultureDeriver._CONFLICT_EVENTS` matches, confirmed
  via `src/domains/campaigns/orchestrator.py`'s `_SIGNIFICANCE_MAP`) produces a real non-zero
  loyalty-pressure signal end-to-end through the real Culture Drift pipeline; an untouched region in
  the same run correctly yields zero.
- Full scoped run: `tests/unit/social/ tests/unit/domains/culture/ tests/integration/culture/
  tests/architecture/ -m "not slow"` — 422 passed, 1 deselected, 0 failed.
- `python3 tools/parity_index.py build` — status: ok, 2166 entries, 9 shards.

## Files Changed
- `src/systems/social_systems/loyalty_drift.py` (new) — `LoyaltyDriftService`.
- `src/systems/social_systems/party_lifecycle.py` — `effective_defection_threshold()`/
  `check_defection()` gain the optional `loyalty_pressure` parameter; module/method docstrings updated.
- `tests/unit/social/test_loyalty_drift.py` (new).
- `tests/unit/social/test_party_lifecycle.py` — 4 new tests.
- `tests/integration/culture/test_loyalty_drift_campaign.py` (new).
- `docs/world/culture_drift_contract.md` — new "Idea 56" section + 2 Integration Points rows.
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` — status annotation.
- `docs/parity_ledger/social_narrative.yaml` — new entry SOC-274 (via `tools/parity_ledger_writer.py`).
- `staging_artifacts/TCK-20260905-DRIFTING-LOYALTY-SIGNAL/` — investigation.md, plan.md, test_plan.md.

## Completion Summary
Idea 56 (Drifting Loyalty) ships as a real, read-only consumer of Culture Drift's already-live
`faction_conflict_exposure` axis — no new derivation machinery, matching the epic's own scope. The
signal is wired as a genuine, tested, optional input to idea 39's `check_defection()` mutation trigger,
lowering the grievance threshold in proportion to a region's faction-conflict exposure. Two real,
evidence-grounded corrections were made to the ticket's own original framing: the anchor field is the
entity's *current* region (`navigation.region_id`), not the still-unpopulated `home_region_id` idea 59
will populate; and the live per-tick call site (`GroupPhase.resolve()`) cannot yet supply a real value,
since no bridge exists between per-tick `AuthoritativeState` and episode-boundary `CampaignState` —
disclosed explicitly, not hidden, matching the "built, not yet visible in play" precedent already
established in the M5 batch. All 4 Acceptance Criteria verified satisfied.

---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-LEAD-CONTRADICTION-WIRING
phase: done
date: 2026-08-24
tags: [information, strategy, cognition]
---

# TCK-20260824-LEAD-CONTRADICTION-WIRING

## Title
Wire Contradiction Detection into the Live Leads System

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The author wants contradiction detection wired into the Leads system via BeliefContradictionService directly, skipping the flag trap. A sibling orphan, LeadContradictionSystem, must be wired in the same ticket, or 3 of 4 lead kinds stay permanently unable to resolve.

## Scope
- Add a `run_phase()` call in `AuthoritativeApplyPipeline.refine()` (`src/engine/pipeline.py`) wiring `LeadContradictionSystem.enforce()` (`src/engine/pipeline_phases/lead_contradiction.py`) as a per-tick state-scan phase
- Add a real production call site for `BeliefContradictionService.detect()` (`src/domains/information/contradiction.py`), invoked when a `claim_failed_search`/`region_danger_seen` observation is processed, applied via a typed `StrategicUpdate`
- Extend `_is_lead_contradicted()` to cover OBJECT/CONCEPT/EVENT `LeadKind` values, not just the current 'resource'/'location'/'person'/'information' string literals (2 of which are not even real `LeadKind` enum values)
- Update `docs/parity_ledger/strategic_cognition.yaml` STRAT-230's `v2_evidence` with a new pipeline-level test

## Out of Scope
- Any change to the broader Nemesis System scope covered by C9
- Correcting other docs beyond STRAT-230 that may have wrongly claimed `LeadContradictionSystem` was already wired, beyond flagging the discrepancy found in this investigation

## Acceptance Criteria
- [x] A full `pipeline.refine()` tick call (not direct `.enforce()`) on a state with a non-EXHAUSTED lead pointing at a depleted resource produces `belief_contradiction`/`lead_contradiction_resolved` events and the same mutations `LeadContradictionSystem.enforce()` already produces in isolation
- [x] `BeliefContradictionService.detect()` is invoked from a real production call site when a `claim_failed_search`/`region_danger_seen` observation is processed, applied via a typed `StrategicUpdate`
- [x] `_is_lead_contradicted()` is extended to cover OBJECT/CONCEPT/EVENT `LeadKind` values
- [x] STRAT-230's `v2_evidence` is updated with the new pipeline-level test

## Related Tickets
- TCK-20260619-E42D-CONTRADICTION
- TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS
- TCK-20260619-E42-INFO-SEEKING

## Related Docs
- docs/parity_ledger/strategic_cognition.yaml
- docs/engine/authoritative_pipeline.md
- docs/mechanics/04_strategic_cognition.md
- docs/simulation/domains/information_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/information/contradiction.py
- src/engine/pipeline_phases/lead_contradiction.py
- src/engine/pipeline.py
- src/core/strategic.py
- src/domains/information/bridge.py
- src/domains/information/phase.py
- src/observability/event_extractor.py (added during Plan resolution: AC1's literal "produces belief_contradiction/lead_contradiction_resolved events from a bare pipeline.refine() call" wording requires new diff-based event-derivation rules here, per the Decisions Log in staging_artifacts/TCK-20260824-LEAD-CONTRADICTION-WIRING/plan.md — Option A, human-confirmed)

## Assumptions / Open Questions
- No explicit phase-ordering slot for this wiring exists in the M1 epic doc (unlike C11's PP-02/PP-03) -- the insertion point is an open design question
- Two structurally different insertion points are needed (a per-tick `run_phase` slot for `LeadContradictionSystem`, a different observation-event-driven call site for `BeliefContradictionService`) -- cannot be satisfied by one call-site change

## Implementation Notes

All 10 plan steps implemented in the order given, respecting the Dependency Map:

- **Step 1**: added `AuthoritativeApplyPipeline._enforce_lead_contradiction(state, update)` (static
  method, next to `_apply_near_death_hardening`) and wired
  `run_phase("lead_contradiction", update, lambda u: AuthoritativeApplyPipeline._enforce_lead_contradiction(state, u))`
  into `refine()` between `strategic_intelligence` and `near_death_hardening`, no feature flag, no
  `PhaseDependencyGraph.PHASES` entry. `_events` from `LeadContradictionSystem.enforce()` are
  discarded at this boundary per the plan (re-derived later by `EventExtractor`, Step 10).
- **Steps 2-4**: extended `_is_lead_contradicted()` in `lead_contradiction.py` with `"object"`
  (ground-item/chest scan, absence = contradiction, opposite polarity from `"location"`/`"resource"`),
  `"event"` (`state.local_scars[*].source_event_id` match), and `"concept"` (explicit no-op,
  mirrors the existing `"information"` no-op) branches, inserted between the existing `"person"` and
  `"information"` branches. Existing `"resource"`/`"location"`/`"person"`/`"information"` branches
  left byte-for-byte unchanged. Docstring updated to list all branches for accuracy.
- **Step 5**: `ObservationBeliefBridge.process_observation()` now special-cases
  `obs_kind in ("claim_failed_search", "region_danger_seen")` by calling
  `BeliefContradictionService.detect()` and translating a positive result into
  `InformationAssimilationResult(strategic_update=StrategicUpdate(leads_add_or_update=[...]))` via
  `dataclasses.replace()` on the matched `LeadState` — never a direct mutation. No result
  (`contradiction_detected=False`) returns a no-op `InformationAssimilationResult()`. The prior
  hand-built `CONTRADICTION`-shaped dict for `claim_failed_search` was removed; the default
  `KNOWN_FACT`/normalize/assimilate path is unchanged for every other `obs_kind`.
- **Steps 6-7**: added a new fourth branch to `InformationBeliefPhase.apply()`'s per-actor loop,
  after the existing pending-response/unknown-routing branches, iterating
  `actor.strategic.leads.values()` for untested, non-EXHAUSTED leads. Synthesizes a
  `claim_failed_search` observation from `actor.navigation.last_failure_reason` plus an active
  objective (via `current_project_id`/`current_objective_id`) whose `target` matches `lead.subject`;
  falls back to synthesizing a `region_danger_seen` observation for `"location"`-kind
  VAGUE/APPROXIMATE leads whose `detail` matches `actor.navigation.region_id`, checked against an
  inline region-bounds/local-scar containment check (no import of
  `src.engine.domain.view.DomainView`). Both call the Step 5-fixed
  `ObservationBeliefBridge.process_observation()` and merge the result into `entity_updates` via
  `EntityUpdate.merge()` (never a bare assignment), building the new `EntityUpdate` with only
  `.strategic` set (never `.self_model_bundle_set`) to avoid clobbering branch (2)'s
  `self_model_bundle_set` write per the plan's documented merge hazard.
- **Step 8**: STRAT-230's `text`/`v2_evidence`/`test_path` broadened in place (no new entry) to
  cover OBJECT/EVENT and the new `run_phase` call site; `git diff --stat` confirmed a small,
  single-entry diff (13 insertions, 7 deletions), not a full-file reformat.
- **Step 10**: added `belief_contradiction`/`lead_contradiction_resolved` diff rules to
  `EventExtractor.extract()`, inside the existing `if not _push_shapers_phase2_active and
  hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):` block, at the loop level
  (sibling to, not nested inside, the `lead_certainty_changed` branch), guarded by a
  prior-tick/current-tick FAILURE+EXHAUSTED idempotency check mirroring
  `LeadContradictionSystem.enforce()`'s own `test_outcome == "FAILURE": continue` guard.
- **Step 9**: added all 8 tests (dropped the flag-off test, no flag exists) plus 3 supplementary
  bridge-level unit tests — see Files Changed. Ran the scoped pytest commands from `test_plan.md`
  after each implementation step, not just at the end; all green (see Test Summary).

See `staging_artifacts/TCK-20260824-LEAD-CONTRADICTION-WIRING/plan.md`'s new "## Deviations"
section for the two small, non-substantive implementation-detail deviations (Steps 6/7 combined
into one loop pass instead of two; test 3/4 file placement).

## Test Summary

All scoped regression + new-test commands from `test_plan.md` pass (via
`.venv/bin/python3 -m pytest`, run after each implementation step):

- `tests/unit/cognition/test_information_seeking.py` — 55 passed (7 new in `TestLeadContradiction`:
  1 full-pipeline parity test, OBJECT x2, EVENT x2, CONCEPT x1, resource/location/person regression
  guard x1 — OBJECT/EVENT each split into a positive+negative pair per the plan)
- `tests/unit/domains/information/` (full dir, includes the 2 new files/extensions) — all passed
- `tests/unit/strategic/test_belief_cycle.py`, `tests/unit/strategic/test_detour_suggestion.py` —
  zero behavior change, all passed (bundled into the `tests/unit/strategic/` full-directory run,
  259 passed)
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` — 8 passed
- `tests/tools/test_parity_index.py` — 40 passed (STRAT-230 edit did not break structural/duplicate
  checks)
- `tests/architecture/test_phase18_import_boundaries.py` — 5 passed (no new `domains -> engine`
  import introduced by Step 7's inline bounds check)
- `tests/unit/observability/test_event_extractor_information2.py` — 20 passed (17 pre-existing + 3
  new `TestBeliefContradictionEvents` tests)
- Combined `tests/unit/cognition/ + tests/unit/domains/information/ + tests/unit/strategic/` run:
  104 passed, 0 failed

No `pytest tests/` full-suite run performed (per project convention — scoped runs only).

## Files Changed

- `src/engine/pipeline.py` — wired `lead_contradiction` phase into `refine()`; added
  `AuthoritativeApplyPipeline._enforce_lead_contradiction()`
- `src/engine/pipeline_phases/lead_contradiction.py` — extended `_is_lead_contradicted()` with
  OBJECT/EVENT/CONCEPT branches; docstring update
- `src/domains/information/bridge.py` — `ObservationBeliefBridge.process_observation()` now calls
  `BeliefContradictionService.detect()` for `claim_failed_search`/`region_danger_seen`
- `src/domains/information/phase.py` — `InformationBeliefPhase.apply()` gained the new
  observation-synthesis branch (Steps 6-7)
- `src/observability/event_extractor.py` — added `belief_contradiction`/`lead_contradiction_resolved`
  diff rules to `EventExtractor.extract()`
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-230 broadened (`text`, `v2_evidence`,
  `test_path`); `v2_evidence` also updated a second time this session to add a citation for
  `src/domains/information/phase.py`'s observation-synthesis branch (closing a Parity-phase
  cross-reference gap)
- `docs/engine/authoritative_pipeline.md` — phase table updated (38→39 phases) to list the new
  `lead_contradiction` phase between `strategic_intelligence` and `near_death_hardening`
- `docs/mechanics/04_strategic_cognition.md` — new subsection documenting the broadened
  `_is_lead_contradicted()` law (OBJECT/EVENT/CONCEPT coverage) and the now-live production wiring
- `docs/simulation/domains/information_contract.md` — routing table updated to reflect
  `ObservationBeliefBridge.process_observation()`'s real `claim_failed_search`/`region_danger_seen`
  → `BeliefContradictionService.detect()` call site
- `tests/unit/cognition/test_information_seeking.py` — new full-pipeline parity test (test 1) +
  OBJECT/EVENT/CONCEPT/regression-guard tests (tests 5-8)
- `tests/unit/domains/information/test_phase5_observation_belief_bridge.py` — new supplementary
  bridge-level tests for Step 5
- `tests/unit/domains/information/test_phase5_information_belief_phase.py` — new file; production
  call-site tests for Step 6/7 (tests 3-4, including the PRECISE-certainty negative case)
- `tests/unit/observability/test_event_extractor_information2.py` — new `TestBeliefContradictionEvents`
  class + `_lead()` helper extended with `test_outcome`/`failure_count`/`subject`/`source_entity_id`
  params
- `tickets/inprogress/TCK-20260824-LEAD-CONTRADICTION-WIRING.md` — this file (Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)
- `staging_artifacts/TCK-20260824-LEAD-CONTRADICTION-WIRING/plan.md` — added "## Deviations" section
- `staging_artifacts/TCK-20260824-LEAD-CONTRADICTION-WIRING/investigation.md`,
  `staging_artifacts/TCK-20260824-LEAD-CONTRADICTION-WIRING/test_plan.md` — created earlier this run
  (Investigate/Plan phases), carried into this changeset unmodified by Implement

## Completion Summary

Wired both previously-orphaned contradiction systems into live production: `LeadContradictionSystem`
now runs every tick as the `lead_contradiction` phase in `AuthoritativeApplyPipeline.refine()` (no
feature flag), and `BeliefContradictionService.detect()` now has real production callers via a fixed
`ObservationBeliefBridge.process_observation()` invoked from a new `InformationBeliefPhase.apply()`
branch that synthesizes `claim_failed_search`/`region_danger_seen` observations from existing typed
navigation/objective state. `_is_lead_contradicted()` now covers all 5 `LeadKind` values (OBJECT/EVENT
state-scans added, CONCEPT explicitly routed to the observation path). `EventExtractor.extract()`
gained diff-based `belief_contradiction`/`lead_contradiction_resolved` event derivation so a bare
`pipeline.refine()` tick satisfies AC1's literal event-producing wording despite `refine()` having no
event-carrying return field. STRAT-230 broadened accordingly. All architecture constraints held:
every mutation flows through typed `StrategicUpdate`/`EntityUpdate` records via `dataclasses.replace()`
and `EntityUpdate.merge()`, no direct state writes, no new durable fields, no feature flag, no raw
domain model exposure. 8 new unit/integration tests plus 3 supplementary bridge-level tests added; all
scoped regression suites pass with zero behavior change to the adjacent `BeliefCycleSystem`/
`LeadRoutingSystem`/`DetourSuggestionSystem` systems.

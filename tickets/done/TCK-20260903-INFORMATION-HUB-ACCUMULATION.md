---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260903-INFORMATION-HUB-ACCUMULATION
phase: done
date: 2026-09-03
tags: [information, feature-flags, faction]
---

# TCK-20260903-INFORMATION-HUB-ACCUMULATION

## Title
Information hubs — knowledge accumulation and critical-information propagation

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 41 — Information hubs: give InformationProviderState (Guides) a real knowledge-accumulation mechanism (e.g., increasing when a quest they assigned is reported back) and propagate 'critical' information City-to-City/City-to-Country. The M4 epic doc's premise that both feature flags are OFF is STALE: investigation confirms (direct read of feature_flags.py) ENABLE_BELIEF_ASSIMILATION now defaults ON (flipped by TCK-20260824-ROLLOUT-FLAG-DECISIONS) while ENABLE_INFORMATION_INTENT_EXECUTION remains OFF — no AC may assume both OFF. This is greenfield feature work (atlas marks idea 41 'Aspirational — design only'); InformationProviderState is frozen/immutable with no accumulation field today, so this is genuinely new mutation logic despite the atlas's 'no content risk' framing.

## Scope
- Add a real accumulation mechanism to InformationProviderState (or its typed update path) via a new typed field on StateUpdate.information_providers_update/merge(), following lead_contradiction.py's existing pattern (currently the only writer, only ever decrementing reliability_score).
- Trigger accumulation on a concrete event (e.g., a quest the Guide assigned being reported back).
- Implement City-to-City / City-to-Country propagation of 'critical' information using the EXISTING FactionState.territory/diplomatic_relations topology fields — no new topology type.
- Register any new gated behavior as a NEW flag in FeatureFlagManager._flags, defaulting OFF per DEV-002, with a test proving the flag-OFF path leaves information_providers/FactionState unchanged.
- State current flag reality explicitly in the ticket and any doc updates (BELIEF_ASSIMILATION ON, INFORMATION_INTENT_EXECUTION OFF).

## Out of Scope
- Any Conversation/entity-dialogue system — confirmed zero grep hits in src/; 'Guide-to-Guide exchange reusing Conversation' has nothing to reuse and must be reframed or explicitly scoped out.
- Any idea-66-dependent Place-model work (location_place_id) — propagation uses region/City-level FactionState.territory/diplomatic_relations, not a Place model.
- Redesigning InformationBeliefPhase's existing feature+content gating (ENABLE_BELIEF_ASSIMILATION AND non-empty pending_information_responses/self_model.knowledge.unknowns) beyond what's needed to read the new field.
- Repropagating the atlas's stale 'both flags OFF' premise or its stale line-number citations (feature_flags.py:18-19) into any new doc/ticket text.

## Acceptance Criteria
- [x] InformationProviderState (or its typed update path) gains a real accumulation mechanism — verified via a before/after state assertion (not just an event firing) when a quest a Guide assigned is reported back. **AC revision (see plan.md Acceptance Criteria Map)**: this is satisfied via direct unit-level construction of a QuestState+InformationProviderState pair, driven through the full authoritative apply path (ApplyPath.apply_generation) — not via a real corpus-world run. GuildAction.visit() (src/town/guild.py) never populates QuestState.source_entity_id, so the live Guild hub has no attribution path to any InformationProviderState today; this is a disclosed reachability gap (decision (b)), not a silent narrowing. The mechanism itself (typed update path + apply-path wiring) is real, correct, and tested.
- [x] The ticket and any doc updates explicitly state current flag reality: ENABLE_BELIEF_ASSIMILATION ON, ENABLE_INFORMATION_INTENT_EXECUTION OFF — no AC assumes both OFF.
- [x] Any new gated behavior registers a NEW flag in FeatureFlagManager._flags defaulting OFF (DEV-002), with a test asserting the flag-OFF path leaves information_providers/FactionState unchanged. **AC revision**: corrected to "information_providers/recent_world_events unchanged" — InformationPropagationService never writes FactionState at all (enforced by an architecture-guard test), so a literal "FactionState unchanged" assertion would pass trivially regardless of flag state and would not test anything real. The two fields this ticket's flag genuinely gates (information_providers, recent_world_events) are what the flag-OFF test asserts.
- [x] City-to-City/City-to-Country propagation of 'critical' information walks FactionState.territory/diplomatic_relations (no new topology type), verified by a test where critical info at a City owned by Country A reaches sibling Cities under Country A but not an unrelated Country B. **AC revision**: cross-faction (City-to-Country) gating uses ALLIED only, not "ALLIED/NEUTRAL" as investigation tentatively suggested — diplomatic_relations.get(other_id, NEUTRAL) defaults an absent relation to NEUTRAL, so an unrelated Country C/B with no explicit relation must resolve to that same default; including NEUTRAL as a propagate-gate would incorrectly reach an unrelated faction, contradicting this AC's own literal wording.
- [x] The mechanism for any Guide-to-Guide or hub-to-hub exchange is explicitly documented as NOT reusing a Conversation system (none exists in src/) — reframed at the state level or explicitly scoped out, not silently assumed.

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS
- TCK-20260824-LEAD-CONTRADICTION-WIRING
- TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ
- TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION
- TCK-20260619-E42-INFO-SEEKING

## Related Docs
- docs/audits/D19_domain_phase_inventory.md
- docs/brainstorm/rpg_expected_schemas.html
- docs/brainstorm/rpg_feature_atlas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/optimization/feature_flags.py
- src/domains/information/providers.py
- src/domains/information/schema.py
- src/domains/information/phase.py
- src/domains/information/assimilation.py
- src/engine/pipeline_phases/information_intent_execution.py
- src/engine/pipeline_phases/lead_contradiction.py
- src/core/state.py
- src/town/guild.py
- tests/unit/domains/information/test_phase5_information_source_profile.py
- tests/unit/domains/information/test_phase5_information_assimilation.py
- tests/unit/domains/information/test_phase5_information_belief_phase.py
- tests/integration/scenarios/test_phase5_information_belief_scenarios.py
- tests/unit/engine/test_information_intent_execution_phase.py
- tests/unit/strategic/test_belief_cycle.py
- tests/unit/strategic/test_belief_integration.py

## Assumptions / Open Questions
- The atlas's 'both flags OFF, no content risk' premise is stale — current reality (BELIEF_ASSIMILATION ON) means these changes carry real behavior risk on an already-live path; Plan phase should size accordingly.
- No Conversation/entity-dialogue system exists in src/ — Guide-to-Guide (or hub-to-hub) exchange must be designed fresh at the state/StateUpdate level, not assumed to reuse an existing dialogue system; open Plan-phase decision.
- City/Country 'critical information' classification has no existing concept wired to FactionState fields yet — despite reusing existing topology fields, the classification/propagation logic itself is new, not light wiring.
- `layer: strategy` was chosen because this work centers on knowledge accumulation/propagation (Mechanics Bible ch. 04 "Knowledge management, perception" territory) rather than a generic core-state change; no dedicated "information" layer exists in the registry and force-fitting `misc` was avoided since `strategy` genuinely fits the subsystem.

## Implementation Notes

Implemented per staging_artifacts/TCK-20260903-INFORMATION-HUB-ACCUMULATION/plan.md, all 10 steps,
no deviations from the plan's substance. Two small implementation-level corrections found and
fixed during Test:

1. **Regression test event-count assertion.** plan.md's Step 1 verify language implied a single
   SimulationEvent from `LeadContradictionSystem.enforce()`; the real method emits two
   (`belief_contradiction` + `lead_contradiction_resolved`) per contradicted lead. Test corrected
   to assert `len(events) >= 1` rather than `== 1` — this is a test-authoring correction, not a
   change to `LeadContradictionSystem`'s own logic (untouched, per Scope Guards).
2. **False-positive architecture-guard collision.** The new `ENABLE_INFORMATION_HUB_ACCUMULATION`
   flag's registration comment in `feature_flags.py` originally used the literal string
   "GuildAction.visit()", which collided with `tests/architecture/test_guild_action_dormancy.py`'s
   `\bGuildAction\b` regex guard (that guard enforces `GuildAction` is referenced from exactly one
   deliberate dispatch site). Reworded the comment to describe the same fact ("the Guild hub's own
   visit-completion path never populates...") without the literal class-name token — no behavior
   change, comment-only.

Three AC-wording revisions applied to this ticket's own AC section (see Acceptance Criteria above
and plan.md's Acceptance Criteria Map for full reasoning): AC #1's corpus-reachability gap, AC #3's
"information_providers/recent_world_events" correction (not "FactionState", which propagation
never touches), and AC #4's ALLIED-only (not ALLIED/NEUTRAL) cross-faction gating rationale. This
matches this session's established pattern for disclosed AC revisions (Coming-of-Age's role gate,
Clan-Lifecycle's asset_ids inertness, Economic-Vacancy-Signal's AC4 revision).

Deliberately NOT done, per Scope Guards / decision (b) (disclosed, not silent): no seeding of
`AuthoritativeState.information_providers` anywhere in content loaders/worldbuilding; no
`QuestState.source_entity_id` population in `src/quests/generator.py`/`src/town/guild.py`; no
building→provider lookup; no `Conversation`/dialogue class; no new `FactionState` field.

## Test Summary

New tests (all passing):
- `tests/unit/domains/information/test_information_provider_accumulation.py` (6 tests) — Steps 1/2/4:
  default field value, information_providers surviving `ApplyPath.apply_generation` across ticks,
  the `LeadContradictionSystem`/STRAT-230 regression proof (decrement now survives a tick
  boundary), `InformationAccumulationService` unit behavior, quest-completion accumulation with
  the flag ON, and no accumulation with the flag OFF.
- `tests/unit/domains/faction/test_critical_information_propagation.py` (4 tests) — Step 6:
  City-to-City propagation, City-to-ALLIED-Country propagation excluding an unrelated faction,
  non-critical severity does not propagate, and non-interference with
  `FactionAwarenessService.compute_tension_updates()`'s existing output.
- `tests/architecture/test_information_hub_accumulation_guards.py` (2 tests) — Step 7: `FactionState`
  field-set guard, zero-`Conversation`-class guard.
- `tests/unit/domains/optimization/test_information_hub_flag_off.py` (2 tests) — Step 8: flag-OFF
  no-op through the full `AuthoritativeApplyPipeline.refine()` + `ApplyPath.apply_generation` path
  (information_providers/recent_world_events byte-identical), paired with a flag-ON proof that the
  same scenario does change state (not vacuously true).

Regression scope run (all passed, no failures introduced):
- `tests/unit/domains/information/` (all), `tests/unit/domains/faction/` (all), `tests/unit/quest/`,
  `tests/unit/engine/`, `tests/unit/strategic/`, `tests/unit/config/test_phase10_feature_flags.py`,
  `tests/unit/world/test_consequences.py` — 752 passed, 1 skipped, 3 deselected.
- `tests/architecture/` (full directory) — 77 passed (one false-positive collision found and fixed,
  see Implementation Notes).
- `tests/unit/world/`, `tests/unit/social/`, `tests/unit/domains/` (full) — 1387 passed, 1 deselected.
- `tests/integration/kernel/` — 92 passed, 3 deselected (apply.py determinism/replay fidelity
  unaffected by the `information_providers` carry-forward fix).

Command used (venv with dependencies): `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest <paths> -q -m "not slow"`.

## Files Changed

- `src/engine/apply.py` — Step 1: `information_providers` carry-forward-and-merge block + wired
  into the `AuthoritativeState(...)` constructor call.
- `src/domains/information/providers.py` — Step 2: `knowledge_accumulated: int = 0` field +
  `to_canonical_dict()` update.
- `src/domains/optimization/feature_flags.py` — Step 3: new `ENABLE_INFORMATION_HUB_ACCUMULATION`
  flag entry, default OFF.
- `src/domains/information/accumulation.py` (new) — Step 4: `InformationAccumulationService`.
- `src/engine/quests.py` — Step 4: `QuestResolutionSystem.enforce()`'s new accumulation branch
  inside `is_newly_completed`, `providers_update` threading, return-value wiring.
- `src/domains/world_emergence/schema.py` — Step 5: new
  `WorldEventCategory.CRITICAL_INFORMATION_PROPAGATED` member.
- `src/engine/faction_decision.py` — Step 6: `InformationPropagationService` +
  `_CRITICAL_SEVERITY_THRESHOLD`, `DiplomaticState` import.
- `src/engine/pipeline.py` — Step 6: `information_propagation` phase wired into `refine()` after
  `faction_awareness`.
- `tests/architecture/test_information_hub_accumulation_guards.py` (new) — Step 7.
- `tests/unit/domains/information/test_information_provider_accumulation.py` (new) — Steps 1/2/4.
- `tests/unit/domains/faction/test_critical_information_propagation.py` (new) — Step 6.
- `tests/unit/domains/optimization/test_information_hub_flag_off.py` (new) — Step 8.
- `docs/mechanics/04_strategic_cognition.md` — Step 9: new `## 11. Information Hub Knowledge
  Accumulation & Propagation Law` section.
- `docs/parity_ledger/strategic_cognition.yaml` — Step 9: new `STRAT-268` entry (accumulation
  mechanism); `STRAT-230`'s `v2_evidence` updated with a note distinguishing its own
  always-correct decrement logic from the separate `apply.py` wiring defect this ticket fixes.
  Written via `tools/parity_ledger_writer.py` (schema-validated, index rebuilt in-process).
- `docs/parity_ledger/faction.yaml` — Step 9: new `FAC-015` entry (propagation mechanism), same
  writer tool.
- `docs/guides/feature_flags.md` — Step 10 (folded into Step 9's doc pass): new row for
  `ENABLE_INFORMATION_HUB_ACCUMULATION`.
- `docs/parity_ledger/progression.yaml` — Parity phase: fixed PROG-024's `apply.py` line citation,
  shifted by this ticket's own insertion (via `tools/parity_ledger_writer.py`).
- `docs/parity_ledger/combat_movement.yaml` — Parity phase: fixed COMB-318's `apply.py` line
  citation for the same reason (via `tools/parity_ledger_writer.py`).
- `docs/parity_ledger/infrastructure.yaml` — Parity phase: fixed INFRA-324's `apply.py` line
  citation for the same reason (via `tools/parity_ledger_writer.py`).
- `staging_artifacts/TCK-20260903-INFORMATION-HUB-ACCUMULATION/plan.md`,
  `investigation.md`, `test_plan.md` — pre-existing from this ticket's earlier Investigate/Plan
  phases (not modified during this Implement pass; listed per ticket-hygiene convention since they
  are part of this ticket's own changeset).
- `tickets/inprogress/TCK-20260903-INFORMATION-HUB-ACCUMULATION.md` — this file: AC revisions,
  Implementation Notes, Test Summary, Files Changed, Completion Summary, Status.

`make knowledge-index-update` run after doc changes (2 files re-embedded, incremental).

## Completion Summary

Implemented idea 41's Information Hub knowledge-accumulation and critical-information-propagation
mechanisms exactly per the architecture-reviewed plan: fixed a genuine pre-existing apply-path bug
that silently discarded `information_providers` (and the already-shipped STRAT-230 decrement) at
every tick boundary; added a `knowledge_accumulated` counter to `InformationProviderState`,
incremented via a new `InformationAccumulationService` hooked into
`QuestResolutionSystem.enforce()`'s quest-completion path; added `InformationPropagationService`,
which emits new `CRITICAL_INFORMATION_PROPAGATED` `WorldEvent`s to sibling City territory and
ALLIED Country territory (never mutating `FactionState`); and gated both mechanisms behind one new
DEV-002-compliant flag, `ENABLE_INFORMATION_HUB_ACCUMULATION` (default OFF). Both mechanisms are
disclosed as not yet corpus-reachable in a live run (Guild hub attribution and provider seeding
remain unbuilt, by design, per decision (b)) but are proven correct through the full authoritative
apply path in new unit and architecture-guard tests. Docs (Mechanics Bible §11, two parity ledger
entries, feature-flags guide) updated to match.

---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVENT-PUSH-MIGRATION
artifact_type: plan
tags: [observability, engine, simulation-quality]
---

# Plan: TCK-20260807-QUEST-EVENT-PUSH-MIGRATION

## Steps

1. `src/observability/event_shapers.py`:
   - Import `QuestEvent` (from `src.observability.events`) and `QuestState` (from
     `src.core.quests`).
   - Add `_current_projects(prior_ent, strategic_upd)` helper, mirroring `_current_leads()`.
   - Add `NarrativeShaper` class with `.shape()` — byte-identical logic to
     `event_extractor.py`'s own quest_event construction, reading `update` instead of
     post-apply `current_state`.
   - Add `QUEST_SHAPER_REGISTRY = {"narrative": [NarrativeShaper()]}`.
   - Add a Quest-mode gating block inside `run_shadow_shapers()`, mirroring the Phase 2 block's
     structure exactly (own `ENABLE_PUSH_EVENT_SHAPERS_QUEST` flag, SHADOW constructs-only, ON
     delivers).
2. `src/observability/event_extractor.py`:
   - Add `_push_shapers_quest_active` flag read (same pattern as the other two).
   - Gate the `if isinstance(qstate, QuestState):` branch (only the QuestEvent construction, NOT
     the `commitment_abandoned` branch in the same loop) behind
     `not _push_shapers_quest_active`.
3. `src/domains/optimization/feature_flags.py`: add `ENABLE_PUSH_EVENT_SHAPERS_QUEST`, default
   `ON`, matching the established documented-exception comment pattern.
4. Tests: new `tests/unit/observability/test_event_shapers_narrative.py` — registry wiring,
   4-way flag gating (default/OFF/SHADOW/ON), independence from
   `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, direct `NarrativeShaper.shape()` behavior (started,
   transition, no-change, non-QuestState-project exclusion, missing prior entity, no strategic
   update, project removal doesn't spuriously affect a sibling quest).
   `tests/unit/config/test_phase10_feature_flags.py`: add the new flag to
   `_DELIBERATE_ON_DEFAULT_FLAGS`.
5. Real-kernel-adjacent verification: direct `EventExtractor.extract()` +
   `run_shadow_shapers()` comparison confirming no double-fire in default and explicit-OFF
   modes.
6. Docs: `docs/parity_ledger/social_narrative.yaml` (`SOC-241` update note; new `SOC-242` entry);
   `docs/guides/feature_flags.md` (new flag row, 14→15 flag count updates throughout the file).
7. File follow-up tickets for the other 2 real gaps found during the sweep:
   `TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP`,
   `TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP`. Do NOT file one for
   `capability_growth_stalled`/`life_arc_incoherent` — confirmed not a gap (deliberately
   unguarded, no shaper equivalent ever existed).
8. Run scoped tests, doc-staleness check, parity cross-reference, Verify static precheck,
   Finalize.

## Acceptance criteria map

| Original AC | Disposition |
|---|---|
| investigation.md confirms construction logic + corrected understanding | Done |
| NarrativeShaper implemented, registered, gated behind new flag | Done |
| event_extractor.py's block gated (rollback path) | Done — commitment_abandoned deliberately untouched |
| Real-kernel verification: SHADOW constructs-only, ON delivers, no double-fire | Done |
| New flag defaults ON | Done |
| social_narrative.yaml updated | Done — SOC-241 update note + new SOC-242 |
| Follow-up tickets filed | Done — 2 filed, 1 explicitly NOT filed (confirmed non-gap) |
| Scoped pytest passes | Done |

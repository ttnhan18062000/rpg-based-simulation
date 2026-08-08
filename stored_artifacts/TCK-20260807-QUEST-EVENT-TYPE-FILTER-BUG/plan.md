---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG
artifact_type: plan
tags: [observability, simulation-quality, progression]
---

# plan.md — TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG

## Ordered Steps

1. `src/observability/event_extractor.py`: import `QuestState` (`src.core.quests`); restructure
   the quest-lifecycle block — gate `QuestEvent` construction to `isinstance(qstate, QuestState)`,
   read `.quest_status` (not `.status`), pass `payload={"status": ...}` explicitly (closes the
   payload-carryover gap found during Implement); keep `commitment_abandoned` structurally
   independent, still reading generic `.status`/`ProjectStatus`.
2. Fix the 3 pre-existing tests whose fixtures/assertions encoded the bug being fixed
   (`test_event_extractor_narrative.py`'s `TestQuestEventConfirmation`,
   `test_event_extractor_agency2.py`'s `TestCommitmentAbandoned`/`TestAntiDriftGuards`).
3. Real-kernel verification: confirm `quest_event` count drops to 0 in a real run (expected,
   given the sibling `GuildAction` wiring ticket is still open — no real quests exist yet).

## Files to Change

- `src/observability/event_extractor.py`
- `tests/unit/observability/test_event_extractor_narrative.py`
- `tests/unit/observability/test_event_extractor_agency2.py`

## Scope Guards

- Do NOT fix `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s own scope (wiring quests into live
  gameplay) — this ticket only fixes the observability layer's own mislabeling.
- Do NOT change `QuestEvent`/`ObservabilityEventEnvelope`'s class-level definitions — the
  payload-carryover fix is scoped narrowly to `event_extractor.py`'s own construction sites,
  confirmed via `normalizer.py`'s own existing usage that a class-level change carries wider risk
  than necessary here.
- Do NOT touch `quality_hub.py`'s `_translate_quest_event()` vocabulary (e.g. adding
  `"rewarded"`/`"reward_pending"` recognition) — out of scope, flagged as a future follow-up in
  investigation.md instead.

## Dependency Map

Step 1 must land before step 2 (tests assert the new behavior). Step 3 depends on step 1.

## Acceptance Criteria Map

- AC "event_extractor.py's quest-event block only constructs QuestEvent for real QuestState" →
  step 1
- AC "QuestEvent's status field reflects .quest_status transitions, not .status" → step 1
- AC "unit test: mixed projects dict produces exactly 1 QuestEvent" →
  `test_non_quest_project_does_not_emit_quest_event` (step 2)
- AC "unit test: quest_status transitions independent of .status" → `TestQuestEventConfirmation`'s
  rewritten fixtures (step 2)
- AC "docs/parity_ledger/progression.yaml updated (or the relevant entry for this event)" →
  `quest_event` is scored by `NarrativeScorer`, not `ProgressionScorer`/`FactionScorer` — new
  `SOC-241` entry added to `docs/parity_ledger/social_narrative.yaml` instead (the correct file
  for this event's actual consumer)
- AC "scoped pytest run passes" → step 2's real run (921/921 `tests/unit/observability/`,
  460/460 `tests/simulation_quality/` excluding grade_regression)

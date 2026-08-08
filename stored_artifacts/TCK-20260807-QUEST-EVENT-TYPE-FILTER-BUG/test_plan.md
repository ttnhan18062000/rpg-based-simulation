---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG
artifact_type: test_plan
tags: [observability, simulation-quality, progression]
---

# test_plan.md — TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG

## Regression Surface

- `tests/unit/observability/` (full directory — `event_extractor.py` is heavily shared code)
- `tests/simulation_quality/` (excluding `test_grade_regression.py`, pre-existing unrelated
  staleness) — `quality_hub.py`'s translation layer consumes `quest_event`'s payload

## New/Updated Tests

- `tests/unit/observability/test_event_extractor_narrative.py::TestQuestEventConfirmation` —
  rewrote fixtures to use `MagicMock(spec=QuestState)` with real `QuestStatus` enum values
  (previously bare `MagicMock().status = "<string>"`, which never actually exercised a real
  `QuestState`); added assertions on `evt.status`/`evt.payload["status"]` (new coverage — the
  payload-carryover fix); replaced the "failed" test (asserted a state `QuestStatus` cannot
  produce) with a real `REWARD_PENDING → REWARDED` transition; added a new test confirming a
  non-`QuestState` project does NOT emit `quest_event` at all.
- `tests/unit/observability/test_event_extractor_agency2.py` — corrected 2 tests
  (`TestCommitmentAbandoned`, `TestAntiDriftGuards`) that previously asserted a generic
  (non-quest) `ABANDONED` project transition should ALSO emit a `QuestEvent` — encoding the exact
  mislabeling bug this ticket fixes. Now asserts `commitment_abandoned` still fires (generic,
  project-kind-agnostic) while `QuestEvent` does not (correctly gated).

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/observability/ -q
.venv/bin/python3 -m pytest tests/simulation_quality/ -q --ignore=tests/simulation_quality/test_grade_regression.py
```

## Real-kernel verification

`dungeon_crawl_seed42_500t`: `quest_event` count dropped from 700 (pre-fix, 100% mislabeled AI
strategic-goal activity) to 0 (post-fix — correctly excludes non-quest projects; 0 is expected,
not a regression, since `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` — still open — means no real
`QuestState` quests exist in live gameplay yet).

## Anti-Drift Test Guards

Once `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` lands, this fix's own real-kernel verification
should be re-run — `quest_event` should then show real, non-zero activity with accurate
`started`/`completed`/`rewarded` status values, not just correctly-suppressed non-quest noise.

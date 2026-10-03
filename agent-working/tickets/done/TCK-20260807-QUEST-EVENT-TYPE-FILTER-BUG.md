---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG
phase: done
date: 2026-08-07
tags: [observability, simulation-quality, progression]
---

# TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG

## Title
`event_extractor.py`'s "quest_event" has no quest-type filter — it mislabels every AI strategic
goal as a quest

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE`'s investigation found `event_extractor.py`'s
"Quest progress lifecycle events" block (lines 768-782) iterates
`entity.strategic.projects.items()` with **no `isinstance(qstate, QuestState)` check** —
constructing a `QuestEvent` for every strategic project of every kind, quest or not.

Confirmed via raw `simulation_events.jsonl` from 3 real 2000-tick corpus runs (`dungeon_crawl`,
`sandbox_world`, `hero_guild_routing`, seed 42): 182-700 "quest_event" messages per run, with
`quest_id` values like `proj_town_return_267`, `proj_combat_engage_9`, `proj_harvesting_12`,
`proj_fatigue_400`, `proj_resolve_blocker_37`, `proj_combat_retreat_388` — every single one a
`GoalKind`-typed AI strategic goal (`TOWN_RETURN`/`COMBAT_ENGAGE`/`HARVESTING`/`RECOVERY`/etc.),
none an actual quest. The "quest_event" stream is currently pure AI-goal-churn noise mislabeled as
quest telemetry — this is why an earlier, narrower sample (2 of 650+ messages) looked like real
quest activity.

Separately, even where the code does compare `prior_qstate.status != qstate.status` (line 778), it
reads `.status` (the generic `ProjectState`-inherited `ProjectStatus` field) — not `.quest_status`
(the `QuestStatus` field `QuestService.add_progress()`/`mark_rewarded()` actually mutate,
`src/core/models/quests.py:35-48`). Even once real quests exist
(`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`), this event stream would still never observe their
completion correctly — `QuestService`'s own methods never touch `.status`, only `.quest_status`.

## Scope
1. Add an `isinstance(qstate, QuestState)` filter to `event_extractor.py`'s quest-event block
   (skip non-`QuestState` projects entirely — they are legitimately observable elsewhere, if at
   all, under the `GoalKind` strategic-project vocabulary, not as quest events).
2. Change the status comparison to read `.quest_status` (the field that actually drives reward
   delivery) instead of `.status`, so `QuestEvent`'s status values reflect real
   `ACTIVE`/`COMPLETED`/`REWARD_PENDING`/`REWARDED` transitions.
3. Confirm the `commitment_abandoned` classification logic (lines 786-799, keyed on the generic
   `ProjectStatus.ABANDONED`) is unaffected or update it consistently — it is NOT quest-specific
   today (fires for abandonment of any strategic project) and should very likely stay reading
   `.status`, not `.quest_status` — verify this distinction explicitly rather than assuming.

## Out of Scope
- `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` — this fix makes the event stream *correct* once
  real quests exist, but does not itself make any real quests exist; the two tickets are
  independent and this one's tests should use a hand-constructed `QuestState` fixture, not depend
  on the other ticket landing first.
- `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP` — unrelated.
- The `commitment_abandoned` classification's own correctness for non-quest projects — out of
  scope unless step 3 above finds it actually needs to change.

## Acceptance Criteria
- [x] `event_extractor.py`'s quest-event block only constructs `QuestEvent` for real `QuestState`
      instances
- [x] `QuestEvent`'s status field reflects `.quest_status` transitions, not `.status`
- [x] Unit test: a mixed `entity.strategic.projects` dict (1 `QuestState` + 1 non-quest
      `ProjectState`) produces exactly 1 `QuestEvent`, not 2
- [x] Unit test: a `QuestState` whose `.quest_status` transitions but whose `.status` does not
      still produces a `QuestEvent` with the correct new status
- [x] `docs/parity_ledger/progression.yaml` updated (or the relevant entry for this event) with the
      corrected behavior — `quest_event` is scored by `NarrativeScorer`, not `ProgressionScorer`;
      new `SOC-241` entry in `docs/parity_ledger/social_narrative.yaml` instead (the correct file)
- [x] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE (source of this finding — Finding 2, DONE)
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING (sibling, independent)

## Related Docs
- `docs/simulation/quest_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE/investigation.md` (Finding 2,
  full trace)

## Related Code Areas
- `src/observability/event_extractor.py` (lines 768-799)

## Assumptions / Open Questions
- Whether `commitment_abandoned`'s own `.status`-based check needs to change alongside the
  `QuestEvent` fix is not yet decided — this ticket's own Implement phase must verify it explicitly
  (see Scope item 3), not assume either way.

## Implementation Notes
Found and fixed a second, deeper bug during Implement, inline (not filed as a separate
follow-up, since it directly undermines this ticket's own fix): `QuestEvent.status` is a
top-level Pydantic field, never copied into `.payload` by `QuestEvent.__init__` —
`ObservabilityEventEnvelope.from_simulation_event()` only carries `.payload` through, so
`quality_hub.py`'s `_translate_quest_event()` was structurally blind to the real status
regardless of which field was read. Fixed by passing `payload={"status": ...}` explicitly at
both `event_extractor.py` construction sites, not at the class level — confirmed
`normalizer.py:244` already correctly prefers the direct attribute for a different consumer, so a
class-level change carried unnecessary wider risk.

Also found: `QuestStatus` has no `FAILED` value at all — `NarrativeScorer`'s `quest_failed`
branch can never fire from a real quest's own lifecycle. Disclosed in the new parity entry, not
fixed (would need new quest-system design work).

Kept `commitment_abandoned` structurally independent of the new `isinstance(qstate, QuestState)`
gate — confirmed it's generic (any project kind, not quest-specific), reads the generic `.status`
field, translated separately via `quality_hub.py`'s `_TRANSLATE_CONDITIONAL` into
`project_abandoned` (AGENCY-scored).

Corrected 3 pre-existing tests whose fixtures/assertions encoded the exact bug being fixed here
(bare `MagicMock().status = "<string>"` instead of real `QuestState`-typed fixtures; asserting a
generic ABANDONED project transition should ALSO emit a `QuestEvent`; asserting a "failed"
`QuestStatus` that doesn't exist) — added 2 new tests directly, replaced 1.

## Test Summary
`tests/unit/observability/` full directory: 921 passed, 6 skipped (was 915 passed + 5 failed
before the test corrections). `tests/simulation_quality/` (excluding
`test_grade_regression.py`): 460 passed, 3 skipped. Real-kernel verification
(`dungeon_crawl_seed42_500t`): `quest_event` count dropped from 700 (pre-fix, 100% mislabeled) to
0 (post-fix — correctly excludes non-quest projects; 0 is expected, not a regression, since
`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` is still open).

## Files Changed
- `src/observability/event_extractor.py`
- `tests/unit/observability/test_event_extractor_narrative.py`
- `tests/unit/observability/test_event_extractor_agency2.py`
- `docs/parity_ledger/social_narrative.yaml` — new `SOC-241` entry

## Completion Summary
Fixed `event_extractor.py`'s quest-event mislabeling: added an `isinstance(qstate, QuestState)`
filter, switched the status comparison from generic `.status` to the real `.quest_status` field,
and closed a second, deeper payload-carryover bug found during implementation that would have
made the first two fixes functionally inert for SimQ scoring. `commitment_abandoned` confirmed
generic and left independent. Corrected 3 pre-existing tests that encoded the bug being fixed,
added 2 new ones matching this ticket's own ACs precisely. Real-kernel verification confirms the
fix: `quest_event` count dropped from 700 (100% noise) to 0 (correct, given no real quests exist
yet). New `SOC-241` parity entry in the correct file (`social_narrative.yaml`, `NarrativeScorer`'s
own file, not `progression.yaml`).

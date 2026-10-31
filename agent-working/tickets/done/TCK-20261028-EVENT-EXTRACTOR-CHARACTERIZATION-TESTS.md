---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS
phase: done
date: 2026-10-28
tags: [observability, testing]
---

# TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS

## Title
Characterization tests that pin the event stream of EventExtractor.extract before src/observability/event_extractor.py is split

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
This is the M7 refactor lane, batch 2, ticket 1 of 2, for `src/observability/event_extractor.py` (see SEQUENCE.md). rpg-planner cleared the file on 2026-10-28 on these conditions: characterization tests come first, event output stays byte-identical, and the pure-run digest is unchanged.

The roadmap's section 9 says characterization tests come first. `EventExtractor.extract` is a single 1,581-line static method. It is one per-entity loop of about 1,100 lines followed by world, faction, resource and world-event blocks. Four feature flags gate rollback branches: `ENABLE_PUSH_EVENT_SHAPERS`, `_PHASE2`, `_QUEST` and `_AGENCY`, each defaulting to `"ON"`. With a flag OFF, `extract()` emits the events that the push shapers emit when it is ON.

This ticket pins what `extract()` emits today, so that ticket 2 can prove it changed nothing. The tests pass on origin/main after #779 with `src/` untouched, and they stay as permanent regression tests.

## Scope
1. **Golden event-stream fixture.** Choose one or two short, seeded scenarios through the real kernel. Prefer existing `tests/` scenario helpers, and pick ones that hit many domains.
   - Capture every event `EventExtractor.extract` returns on each tick, recorded at the `extract()` call, not after the recorder or queue.
   - Record each event as one canonical JSON line, in emission order: tick, `event_type`, `event_category`, `entity_id`, `severity`, `source_system`, `message`, and the payload or details with sorted keys.
   - **Exclude `timestamp`.** It is `time.time()`, which is wall clock.
   - Store it under `tests/fixtures/` as `.jsonl`. Emission order is behavior, so the order of lines matters.
2. **The flag matrix.** Record the stream under the default flags (all ON) and under each rollback flag set OFF alone: 5 configurations. Set the flags the way `prior_state.feature_flags` carries them.
3. **Modes.** `OFF` returns `[]`, which a cheap assert covers. Record `LIGHT`, `NORMAL` and any other mode in `ObservabilityConfig` that `extract()` branches on. If a mode never changes the output, say so with evidence (a grep of mode checks inside `extract()`) rather than pinning a duplicate fixture.
4. **Per-run class state.**
   - A test asserts that `reset_run_state()` clears each of the 8 class-level collections and `DivergenceEpisodes`.
   - A second test shows that the emit-once events (plateau, stale lead, social memory, contract milestones, capability stalled) are emitted once and only once across ticks.
5. **Branch coverage report.** Run the characterization tests under `coverage` for `src/observability/event_extractor.py` only.
   - Record the line and branch percentages, and the list of `events.append` sites that no fixture reaches, in test_plan.md.
   - For each unreached emitting block, either add a targeted unit test with a hand-built `prior_state`/`current_state`/`update` triple pinning its event, or record why that is not cheap.
   - A block absent from the scenarios is not unreachable; do not call it dead. Target: every `events.append` site is reached by at least one test, or is listed with a reason.
6. **A regeneration path** for the fixtures (an `--update` switch or a helper), documented in the test module's docstring. No ticket in this batch uses it.

## Out of Scope
- Any edit under `src/`.
- Changing, fixing or removing anything the fixtures reveal, including the flag-gated rollback branches. Record findings in investigation.md and tell codebase-planner, who routes them to rpg-planner.
- SimQ scorer output, which is downstream of the recorder. The event fixture is the contract here.

## Acceptance Criteria
1. The new tests pass on origin/main after #779 with `src/` untouched: `git diff origin/main -- src/` is empty at this ticket's commit.
2. **Deterministic.** Two runs in fresh processes produce byte-identical fixtures, and the test runs under `-p no:randomly` and with the plugin, if the repo uses it.
3. **Probes.** Run these 5 probes, record each probe and the failing test in test_plan.md, then revert them. Breaking any of them makes a test fail:
   1. rename one payload key;
   2. swap the order of two emitting blocks inside the per-entity loop;
   3. flip one rollback flag's default from `"ON"`;
   4. drop one `events.append`;
   5. change `_SOCIAL_MEMORY_THRESHOLD`.
4. test_plan.md holds the coverage report and the unreached-site list from Scope 5.
5. `pytest tests/unit/observability` passes, along with the existing tests that import `EventExtractor` (48 files on origin/main; list the command used) and `tests/architecture`.
6. Test runtime stays proportionate. If the new tests take over 60 s, mark them `slow` and say so, and keep one fast default-flags test unmarked.

## Related Tickets
- Next: `TCK-20261028-EVENT-EXTRACTOR-SPLIT-BY-DOMAIN`
- Pattern: `TCK-20261024-API-SERVER-CHARACTERIZATION-TESTS` (M7 batch 1)
- Background on the flags: `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`, `TCK-20260806-PUSH-CUTOVER-PHASE2`, `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`, `TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP`
- Must merge first: #779 (rpg-observability-hotfix-batch)

## Related Docs
- `docs/plans/codebase_health/python_code_craft_roadmap.md`: the M7 row, the decision 7 amendment, and section 9 "Refactor risk"
- `docs/guides/observability.md`
- `docs/observability/decision_trace_contract.md`, which reads event fields

## Related Stored Artifacts
- none

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/observability/event_recorder.py`, `src/engine/kernel.py` (callers)
- `src/observability/event_shapers.py`, which emits the same events when a flag is ON
- `src/domains/optimization/feature_flags.py`

## Assumptions / Open Questions
- With flags OFF, the shapers and `extract()` should not both emit; that is how the flags were designed. If they double-emit, record it and don't fix it.
- `tests/fixtures/` is not gitignored for `.jsonl`. Check with `git check-ignore` before committing.
- **Hold-and-fix ordering.** Event order for set-listing events used to follow the process hash seed. The goldens were held until rpg hotfix (A) (#790, de5a223ca) merged, then recorded on top of it. This ticket does not wait for (B), the state-side `list(set())` fix (STATE-SET-ORDER).
- **(B) is a finding, not a re-pin.** If (B) later changes any event these goldens pin, that is a finding for rpg-planner-ubuntu. The goldens are never silently re-pinned.
- **Two-seed check.** The recorders run at `PYTHONHASHSEED=0`, and a test records the corpus and both kernel scenarios again at a second seed and asserts they are byte-identical.

## Implementation Notes
Test-only. A pytest plugin wraps `EventExtractor.extract`, evaluates each call under 8 configs and writes count plus SHA-256 prefix over canonical lines. Details: staging artifacts `plan.md`, `investigation.md`, `test_plan.md`. Findings (not fixed): under default flags `extract()` emits almost nothing; the rollback flags are where output lives.

## Test Summary
`tests/unit/observability/test_event_extractor_characterization.py`: 12 passed (about 70 s; each test under 15 s). Coverage of `event_extractor.py` 98 % branch; both unreached emitting sites have direct tests. 5 probes each fail the tests. Two-seed check passes. `git diff origin/main -- src` empty.

## Files Changed
`tests/unit/observability/test_event_extractor_characterization.py`, `tests/unit/observability/extractor_characterization/{__init__,recorder_plugin,kernel_scenario,corpus}.py`, `tests/fixtures/event_extractor_characterization/{unit_corpus,kernel_runs}.jsonl`.

## Completion Summary
Event output of `EventExtractor.extract` is pinned per config for 371 unit-corpus calls and two 200-tick seeded kernel runs, on top of hotfix (A).

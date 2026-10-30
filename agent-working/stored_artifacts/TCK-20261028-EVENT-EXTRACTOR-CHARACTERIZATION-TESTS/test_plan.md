---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS
artifact_type: test_plan
tags: [observability, testing]
---

# Test plan
Passing on origin/main de5a223ca (after rpg hotfix (A), #790) with `src/` untouched (`git diff origin/main -- src/` empty). Goldens recorded on top of (A): 371 corpus rows, 400 kernel rows. Two-seed check: corpus and both kernel scenarios recorded at `PYTHONHASHSEED=0` and `12345` are identical (`test_recording_is_identical_under_a_second_hash_seed`). New module: 10 tests, about 82 s in total, each test well under the 60 s budget except the two-seed test (about 50 s of subprocess work); not marked slow.

AC5 wide run (before (A), on 33da13604): `tests/unit/observability`, the 19 other files that import EventExtractor, `tests/architecture`: 1425 passed, 83 skipped, plus failures in `tests/unit/worldassembly/test_corpus_diversity.py` (score-anchor drift / resource time limit under load) and one `tests/architecture` thread-leak error that follow from machine load, not from this ticket (`src/` untouched). Reported to codebase-planner.

Coverage of `src/observability/event_extractor.py` (branch) from the recorded calls (unit corpus plus both kernel scenarios): 98 % (580 stmts, 10 missed; 370 branches, 13 partial). Missed lines: 124, 383, 764, 866-867, 1061, 1219-1220, 1411-1412.
Unreached `events.append` sites and what covers them:
- 764 `paid_info_changed_goal`: `test_paid_info_changed_goal_fires_when_an_information_purchase_switches_the_project`.
- 1220 `progression_plateau_detected` (skill_silence): `test_progression_plateau_skill_silence_fires_at_level_five_with_no_skills`.
Other missed lines emit nothing: 124 is the OFF early return (`test_off_mode_emits_nothing`), 383 a durability-rise `continue` path, 866-867 the `int()` failure fallback for a lead's discovered tick, 1061 a `continue` for elapsed <= 0, 1411-1412 the `except` for a non-numeric trauma. None is cheap to reach with a state a real run produces; a block absent from the scenarios is not claimed dead.

Probes (src edited, module run, src reverted each time; every probe fails the characterization tests):
1. rename payload key `ticks_since_xp`: unit corpus + both kernel scenarios fail.
2. swap `paid_information_transaction` and `paid_info_transaction` appends: unit corpus fails.
3. flip `ENABLE_PUSH_EVENT_SHAPERS_QUEST` default to OFF: unit corpus + lifecycle kernel scenario fail.
4. drop the `trade_executed` append: unit corpus fails.
5. `_SOCIAL_MEMORY_THRESHOLD` 0.3 -> 0.31: unit corpus fails.

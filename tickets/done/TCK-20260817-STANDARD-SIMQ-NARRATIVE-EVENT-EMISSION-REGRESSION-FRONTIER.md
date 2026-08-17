---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER
phase: open
date: 2026-08-17
tags: [simulation-quality, calibration, corpus, investigation, root-cause]
---

# TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER

## Title
5 frontier-corpus `NARRATIVE`-pillar `-m slow` tests fail against a stale `grade_anchors.json`
anchor — root cause is NOT a missing-`.merge()` emission-path regression, it is a since-fixed
mislabeling bug's fake "quest" telemetry the anchors were never recalibrated away from

## Status
BLOCKED

## Tier
standard

## Type
bug (investigation — no live defect confirmed; see Completion Summary)

## Priority
P1

## Request Summary
`tests/unit/worldassembly/test_corpus_diversity.py`'s `-m slow` suite never ran to completion on
real CI before `TCK-20260817-HOTFIX-MAKEFILE-PYTHON-DISCOVERY-BROKEN-ON-CI` (closed). Now that it
runs, 5 of its 32 tests fail on the `NARRATIVE` pillar specifically (all other pillars pass in the
same runs):
- `test_generated_frontier_3_42_seed123_200t_combat_narrative_grade_stability`
- `test_frontier_extended_seed42_200t_narrative_grade_stability`
- `test_frontier_extended_seed123_200t_combat_progression_narrative_grade_stability`
- `test_frontier_living_world_seed123_200t_combat_narrative_grade_stability`
- `test_frontier_marches_seed42_200t_narrative_grade_stability`

A prior 5-agent investigation batch triaged all 10 originally-failing tests and assigned these 5
to this ticket under the hypothesis that they share one confirmed real regression: a missing
`.merge()`/aggregation call in the `world_events_add` population chain, of the exact class already
found and fixed once by `TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS`. This
ticket's own independent investigation (git-worktree bisection, live instrumentation, 2 real
`pytest -m slow` reproductions) **refutes that hypothesis**: every `world_events_add` population
site named in the parent investigation is confirmed correct (merges/extends prior state properly).
The real cause is that the `NARRATIVE` anchors for these 5 tests were calibrated against telemetry
from *before* `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` (closed 2026-08-07) fixed a real
mislabeling bug that had been counting ordinary AI strategic goals (`proj_combat_engage_N`,
`proj_combat_retreat_N`, etc.) as fake "quest" events. Post-fix, these 5 worlds' shipped
calibration profiles genuinely produce zero real narrative activity (no world enables
`ENABLE_GUILD_QUEST_GENERATION`, the only live real-quest-generation path, and none of their
seeds reach `WAR`/sovereignty-shift within 200 ticks). Full evidence chain in
`staging_artifacts/.../investigation.md`.

## Scope
1. Context Scan, reproduce >=2 of the 5 failing tests, bisect/trace the real root cause — all done.
2. Fix the real bug in `src/` **if one is found** — none was found; see Completion Summary.
3. Check whether the same signature plausibly affects other worlds — spot-checked, noted, not
   independently fixed (out of scope per the assigning task).
4. Do NOT touch `grade_anchors.json` or any anchor value for these 5 tests, and do NOT
   force-adjust anchors if a fix doesn't restore real narrative activity — honored: **no file
   under `tests/simulation_quality/fixtures/` or `test_corpus_diversity.py` was modified.**

## Out of Scope
- Recalibrating the 5 stale `NARRATIVE` anchors (a product/architecture decision: recalibrate to
  the new, correct zero-activity baseline, or activate real quest content for these worlds first —
  either requires human/orchestrator sign-off, not a unilateral bug-fix-ticket action).
- Wiring `spec.quest_definitions` → `AuthoritativeState.quest_registry` (the pre-existing,
  older, unrelated dead-code gap found in `src/worldbuilding/compiler.py:426-482` — `compiled_quests`
  is computed but never attached to state at any point in this repo's history, confirmed via full
  `git log -p` on the file).
- Enabling `ENABLE_GUILD_QUEST_GENERATION` for any of these 5 worlds' calibration profiles.
- Fixing `tools/calibrate_simq.py`'s `_KNOWN_FLAGS` allowlist gap (does not include
  `ENABLE_GUILD_QUEST_GENERATION`/`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`/`_QUEST`/`_AGENCY` for env-var
  override) — noted during investigation, minor, unrelated to the 5 tests' failure.
- The other 5 of the original 10 failing tests (quest/self-model related, covered by a sibling
  ticket) and the 4 already-recalibrated stale-anchor tests (covered by a separate sibling ticket).

## Acceptance Criteria
- [x] Context Scan run before investigation (search_docs, graphify query)
- [x] >=2 of the 5 tests reproduced locally via real `pytest -m slow`
- [x] Root cause bisected/traced with evidence (git worktree bisection to pre-migration commit,
      live call-count instrumentation, raw JSONL inspection)
- [x] The "missing merge()" hypothesis was checked and refuted, not assumed
- [ ] Tests pass against their existing, unmodified anchors — **not achieved**, correctly: the
      anchors are stale, the code is correct; forcing a pass would require either fabricating a
      source change with no real effect or editing the anchors, both explicitly disallowed
- [x] Anchors/test file left untouched
- [x] Cross-world check performed (2 additional worlds spot-checked, matching signature)
- [x] Full standard-tier ticket/staging-artifact discipline followed

## Related Tickets
- TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS (DONE — the template
  hypothesis this ticket checked and refuted for this specific case)
- TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG (DONE, 2026-08-07 — the real, already-shipped fix whose
  correct zeroing of fake quest telemetry is what actually broke these 5 anchors)
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (DONE — compounding, also-intentional architecture
  consolidation confirmed via `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py`)
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING (DONE — introduced the only live real-quest-generation
  path, `ENABLE_GUILD_QUEST_GENERATION`, default OFF, not enabled for any of these 5 worlds)
- TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP (the source of the original 31-39
  NARRATIVE-event-count sweep that calibrated these anchors — now known to be measuring the
  mislabeling bug's fake output)
- TCK-20260817-HOTFIX-MAKEFILE-PYTHON-DISCOVERY-BROKEN-ON-CI (DONE — the reason this suite runs
  for real now, surfacing this stale-anchor state)
- TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE (the reason the 5 tests were verified one
  at a time, not concurrently)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` (NARRATIVE pillar's event-type contract)

## Related Stored Artifacts
None yet (staging artifacts for this ticket are being migrated at Finalize).

## Related Code Areas
- `src/observability/event_shapers.py` (`NarrativeShaper`, `WorldDynamicsShaper` — confirmed correct)
- `src/observability/event_extractor.py` (quest-event rollback path — confirmed correct, already fixed)
- `src/simulation_quality/quality_hub.py` (`_translate_quest_event` — confirmed correct)
- `src/engine/pipeline.py` (diplomatic/military/world-emergence phase registrations — confirmed correct)
- `src/engine/world_dynamics.py`, `src/engine/economy.py` (`world_events_add` population — confirmed correct)
- `src/domains/optimization/feature_flags.py` (`ENABLE_GUILD_QUEST_GENERATION` default-OFF confirmed intentional)
- `src/worldbuilding/compiler.py` (unrelated, pre-existing `compiled_quests` dead-code gap, noted not fixed)
- `tests/simulation_quality/fixtures/grade_anchors.json` (the stale anchors — read, not modified)
- `tests/unit/worldassembly/test_corpus_diversity.py` (the 5 failing tests — read, not modified)

## Assumptions / Open Questions
- Whether `frontier_extended_seed123_200t_combat_progression_narrative_grade_stability` and
  `frontier_living_world_seed123_200t_combat_narrative_grade_stability` (the 2 of the 5 not
  independently re-run this session) share the identical cause is inferred from the shared
  profile/world family, not independently re-verified — flagged in `investigation.md`, not
  assumed silently.
- Whether the intended resolution is anchor recalibration or real-content activation is an open
  product decision, explicitly left to a human/orchestrator, not decided here.

## Implementation Notes
No `src/` file was changed. See `staging_artifacts/TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-
EMISSION-REGRESSION-FRONTIER/investigation.md` for the full evidence chain (git worktree
bisection, live instrumentation, raw JSONL dumps).

## Test Summary
- `pytest tests/unit/worldassembly/test_corpus_diversity.py::test_generated_frontier_3_42_seed123_200t_combat_narrative_grade_stability -m slow` — FAILED (expected/correct: `NARRATIVE grade=C` vs anchor `A`, all 3 trials).
- `pytest tests/unit/worldassembly/test_corpus_diversity.py::test_frontier_marches_seed42_200t_narrative_grade_stability -m slow` — FAILED (expected/correct: same signature).
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow" -q` — 58 passed, 32 deselected (no regression).
- `pytest tests/unit/observability/test_event_shapers_narrative.py tests/unit/observability/test_event_extractor_narrative.py tests/unit/observability/test_event_extractor_agency2.py tests/unit/observability/test_event_shapers.py -q` — 100 passed, 1 skipped (no regression).

## Files Changed
None under `src/`, `tests/`, or `config/`. This ticket, its staging artifacts, `agent-monitoring/`,
`tickets/working_log.csv`, and `docs/REGISTRY.yaml` are the only repo changes.

## Completion Summary
Investigated 5 `NARRATIVE`-pillar `-m slow` test failures the parent investigation flagged as one
confirmed real regression (a missing-`.merge()` emission-path bug). Independent bisection (git
worktree to the pre-suspected-migration commit, live call-count instrumentation on every
`world_events_add` population site, raw JSONL inspection, and 2 real `pytest -m slow`
reproductions) refutes that hypothesis: the emission pipeline is intact and correct end-to-end
(confirmed by forcing `ENABLE_GUILD_QUEST_GENERATION=ON` and observing a real quest event fire
correctly). The true explanation is that `grade_anchors.json`'s `NARRATIVE` anchors for these 5
tests were calibrated against telemetry from before `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`
correctly fixed a mislabeling bug that had inflated the "quest" event stream with fake AI-goal
noise — post-fix, these 5 worlds' shipped configuration genuinely produces zero real narrative
activity. Per the assigning task's own explicit instruction and CLAUDE.md's Hard Rule against
gaming a gate, no anchor was touched and no fabricated source fix was made. This is reported as a
BLOCKED, evidence-complete investigation: the next action (recalibrate vs. activate real content)
requires a decision beyond this ticket's authorized scope.

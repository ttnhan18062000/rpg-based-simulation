---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-SIMQ-STALE-ANCHOR-RECALIBRATION-BATCH
tags: [simulation-quality, calibration, testing, bug]
---

# Investigation — TCK-20260817-STANDARD-SIMQ-STALE-ANCHOR-RECALIBRATION-BATCH

## Failing tests
`tests/unit/worldassembly/test_corpus_diversity.py`'s `-m slow` suite (32 tests) never ran to
completion on real CI before today — blocked first by upstream CI job failures, then by a real
`Makefile` bug (`$(PYTHON)` discovery silently resolving to empty on CI, fixed this session as
`TCK-20260817-HOTFIX-MAKEFILE-PYTHON-DISCOVERY-BROKEN-ON-CI`). Now that it runs for real, 10 of
32 tests fail. This ticket covers 4 of the 10, dispatched as a parallel investigation batch
across 5 sub-agents; the other 6 are covered by 3 sibling tickets (see the parent ticket's
Related Tickets).

## Test 1 — `test_urban_political_seed42_200t_social_grade_stability`
Real failure:
```
AssertionError: urban_political_seed42_200t -- 1 pillar(s) drifted beyond evidence-derived score tolerance:
  SOCIAL: mean_score=15.8967 across 3 trials outside tolerance of anchor_score=7.525 (abs_floor=1.5275) -- per-trial values: [15.61, 16.47, 15.61]
```
A second independent 3-trial run gave `mean_score=15.2683`, per-trial `[18.355, 13.565, 13.885]`
— same story, all 6 samples land in 13.5–18.4, never near 7.525.

`git blame` confirms both the test's `7.525` literal and
`tests/simulation_quality/fixtures/grade_anchors.json`'s `urban_political_seed42_200t.SOCIAL`
entry (`{"grade": "S", "score": 16.815}`) were added in the exact same commit (`29d78798`,
"Simulation quality (#20)", 2026-08-14) — the correct value was already committed to the fixture
alongside the stale literal in `test_corpus_diversity.py`; this is an internal sync gap authored
in one commit, not later drift. A sibling guard in the same file,
`test_urban_political_seed42_1000t_social_grade_stability`, already uses the correct
higher-magnitude anchor (`15.45`) for the same world/seed at a different tick count, further
confirming `16.815` is the real regime.

## Test 2 — `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability`
Real failure:
```
AssertionError: urban_political_selfmodel_probe_seed42_200t -- 1 pillar(s) drifted beyond evidence-derived score tolerance:
  SOCIAL: mean_score=14.5517 across 3 trials outside tolerance of anchor_score=7.525 (abs_floor=0.546) -- per-trial values: [14.2, 12.065, 17.39]
```
(WORLD pillar, the test's other anchor, passed both before and after — the drift is
SOCIAL-specific.) Same root cause and same commit (`29d78798`) as Test 1: the fixture already has
the correct `17.895` for this run_key, never synced to the test's own literal.

## Test 3 — `test_frontier_living_world_seed42_200t_social_grade_stability`
Real failure:
```
AssertionError: frontier_living_world_seed42_200t -- 1 pillar(s) drifted beyond evidence-derived score tolerance:
  SOCIAL: mean_score=36.0833 across 3 trials outside tolerance of anchor_score=4.9625 (abs_floor=1.0757) -- per-trial values: [33.725, 36.685, 37.84]
```
Grade band passed (measured grade S == anchor grade S); only the score magnitude failed, ~7x.
Same root cause and same commit (`29d78798`): `grade_anchors.json`'s
`frontier_living_world_seed42_200t.SOCIAL` is already `{"grade": "S", "score": 33.7}`, matching
the fresh measurement far better than the test's own stale `4.9625`.

## Test 4 — `test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability`
Real failure:
```
AssertionError: unit_selfmodel_pilot_seed42_1000t -- 1 pillar(s) drifted beyond evidence-derived score tolerance:
  NARRATIVE: mean_score=-0.0003 across 3 trials outside tolerance of anchor_score=0.3715 (abs_floor=0.0908) -- per-trial values: [-0.001, 0.0, 0.0]
```
COGNITION/ECONOMY passed both band and tolerance checks; only NARRATIVE fails, and fails hard
(anchor 0.3715 vs. ~0). Deterministic across all 3 fresh trials — `quest_started`,
`chronicle_entry_created`, `world_emergence_event`, `narrative_milestone`,
`scenario_objective_progressed` are all 0 in every trial's `simulation_events.jsonl`; the only
NARRATIVE event across all 3 trials is a single `hero_death_unrecorded` (entity 15, tick 1000).

Root cause traced via `git diff 29d78798^ 29d78798` and the two closed tickets it landed:
- `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`: `event_extractor.py`'s quest-event block had no
  `isinstance(qstate, QuestState)` filter, mislabeling every AI strategic-goal transition
  (`TOWN_RETURN`/`COMBAT_ENGAGE`/`HARVESTING`/etc.) as a quest event. Its own verification:
  quest_event count dropped from 700 (100% mislabeled noise) to 0 post-fix, documented as
  "0 is expected, not a regression."
- `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`: wired a real quest path
  (`GuildAction.visit()` → `GuildVisitPhase`) but gated it behind `ENABLE_GUILD_QUEST_GENERATION`,
  default OFF. `unit_selfmodel_pilot`'s world profile only enables
  `ENABLE_SELF_MODEL_COGNITION`, not guild quests, so 0 real quests is correct for this world.

The `0.3715` anchor (from `staging_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/
repro_sweep.md`, dated 2026-07-15) was computed **before** the 2026-08-07 fix — its ~69-88
NARRATIVE events were the mislabeled AI-goal-churn noise the fix removed. The fix is legitimate
and correct; this test's anchor was simply never recalibrated afterward.

Also co-discovered in this same test's log output: `LAW-SPAWN-OCCUPANCY`/`LAW-OCCUPANCY-COLLISION`
firing deterministically for entities 6 & 14 on tile (27,38). Confirmed **not** causally linked to
the NARRATIVE drift — entity 6=WORKER, entity 14=HERO, and the uninvolved sibling hero (entity 15,
not in the collision) shows the *same* dormant-quest behavior as entity 14 throughout all 1000
ticks (`decision_trace.jsonl`: both consistently pick `gather_resource` over `form_party`). This
is a separate, already-known, deferred bug (`TCK-20260716-PLACELEGAL-HARDLAW`, AC #2, unticketed
follow-up) — split into its own ticket,
`TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE`.

## grade_anchors.json discrepancy (flagged, not resolved)
`grade_anchors.json`'s own NARRATIVE entry for `unit_selfmodel_pilot_seed42_1000t` is
`{"grade": "B", "score": 0.42126}` — disagreeing with this investigation's live-measured
near-zero value. `test_grade_regression.py` (the test that actually exercises this fixture
entry) compares against a *committed calibration snapshot*
(`data/calibration/unit_selfmodel_pilot_seed42_1000t/quality_report.json`), not a fresh engine
run — and that snapshot does not exist in this working tree (not git-tracked). Its provenance
(when it was generated, under what feature-flag configuration) could not be verified without
running `make calibrate`, a heavy operation out of scope for this ticket. Left as an explicit
open question — not edited here, since editing a shared fixture without verified evidence would
violate this repo's rule against editing artifacts to make a gate pass on unverified grounds.

## Verification performed
- All 4 tests reproduced failing with the stale anchors (see per-test sections above).
- Each new anchor value traced to either a same-commit sibling fixture (`grade_anchors.json`) or
  a specific closed ticket's own documented root-cause/verification — never guessed.
- Fresh `abs_floor` values derived from the real trial samples gathered during this
  investigation, using the file's own established `1.3x max single-sample deviation, floored at
  0.05` methodology.
- All 4 tests re-run individually post-fix: 3/4 passed on first isolated attempt; Test 2
  transiently failed once when run concurrently with 3 other heavy engine tests in the same batch
  (self-inflicted contention matching this repo's documented `TCK-20260715-SIMQ-CORPUS-DIVERSITY-
  SESSION-LOAD-FLAKE` pattern), then passed cleanly on 2 subsequent fully-isolated re-runs.

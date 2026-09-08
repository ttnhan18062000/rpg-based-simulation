---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT
artifact_type: investigation
tags: [simulation-quality, calibration, corpus]
---

# Investigation — TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT

## Finding 1: no committed, regression-tracked baseline exists for Campaign mode at all

`config/simulation_quality/profiles/` has exactly one Campaign-mode profile
(`campaign_episodes:` set): `campaign_life_arc.yaml` (`campaign_episodes: 3`,
`ENABLE_LIFE_ARC_CAMPAIGNS: ON`).

Checked every regression-tracked fixture file this repo's SimQ/calibration machinery reads:
- `tests/simulation_quality/fixtures/grade_anchors.json` — zero occurrences of "campaign" anywhere
  in the file (confirmed via grep).
- `tests/simulation_quality/fixtures/expected_world_flag_state.json` — zero occurrences.
- `tests/simulation_quality/test_grade_regression.py`'s own `FAST_ANCHOR_KEYS` list (the
  regression-swept run_key set, ~85 entries) — zero `campaign_*` entries anywhere in the list.

`tests/scratch/campaign_reports/campaign_scorecard.json` (the only other Campaign-adjacent JSON
found) is gitignored (`git check-ignore` confirms) — transient scratch output, not a checked-in
baseline.

**Conclusion**: there is no pre-PR-#148-captured numeric Campaign-mode SimQ/calibration baseline
anywhere in this repo's regression-tracked fixtures. Nothing was ever recorded under the dormant
(no-op) behavior in the sense the ticket's own Request Summary describes for `grade_anchors.json`-
style values, because Campaign mode was never added to that regression sweep in the first place —
its own calibration test (`test_calibrate_simq_campaign_profile_runs_multiple_episodes`) is marked
`@pytest.mark.slow`, consistent with being excluded from the fast baseline set by design, not by
accident.

## Finding 2: all existing Campaign-mode tests pass cleanly on current `main`

`pytest tests/integration/campaigns/ tests/unit/domains/campaigns/ -m "not slow and not
extra_slow"` → **154 passed, 2 deselected, 0 failed**. No hidden numeric-assertion regression
found in any existing Campaign-mode test.

## Finding 3: the reactivated subsystems did not fire within `campaign_life_arc`'s *observed* episodes — narrower claim than first drafted, corrected after peer review

Ran `tools/calibrate_simq.py --name campaign_life_arc --seed 42 --ticks 200` for real (not
reasoning from code alone). The JSONL event stream showed no siege/territory/calamity-related
event types (156 `scenario_objective_progressed`, 18 `world_emergence_event` — all
`POPULATION_MIGRATION`-category at tick 1 — 3 `scenario_stalled`, 3 `GovernorModeChanged`).

Confirmed this is not a logging-visibility gap (`MilitaryConflictPhase`'s siege-completion path
does emit a real `WorldEvent` via `world_events_add`, `src/engine/military_conflict.py:283-293` —
so an event WOULD appear if a siege ever completed) by instrumenting a direct
`CampaignOrchestrator.run_episode()` call (bypassing the JSONL replay layer entirely) and
inspecting the resulting `AuthoritativeState` directly at the end of each of 3 episodes:

- Every episode completed at **tick 52, not the configured `tick_limit=200`.**
- `state.regions` had 8 entries in every episode (confirming `state.places`/`.regions` ARE
  populated — the PR #148 fix is genuinely working, and (after this session's own
  `TCK-20260908-HOTFIX-STATE-PLACES-APPLY-CARRYFORWARD-GAP`) survives the whole episode, not just
  tick 1).
- **Every non-hometown region's `owner_faction_id` was `None` and every `siege_state` was `None`,
  in all 3 episodes, at episode end.** `calamity_intensity` was `0.0` on every region in every
  episode.

`MilitaryConflictPhase`'s siege logic only engages once a region-finding call fires for a real
`(attacker_id, defender_id)` pair with `DiplomaticState.WAR` between them
(`src/engine/military_conflict.py:201`, `fa.diplomatic_relations.get(defender) ==
DiplomaticState.WAR`) — a formal diplomatic state, not mere faction-alignment hostility (i.e. not
the same thing as `is_hostile_compat()` used elsewhere in this session's own combat_risk work). No
such formal war declaration occurred in any of the 3 real 52-tick episodes observed.
`CalamityService.process_world_dynamics()`'s own spawn-target filter (`calamity_intensity >
0.3`) never had anything to select either, since `calamity_intensity` never left 0.0.

**Correction (post-peer-review): the 52-vs-200 gap is load-bearing and was initially glossed over.**
The first draft of this finding concluded these subsystems "structurally can't fire in practice" —
overstated. Siege completion takes ~20-34 ticks *after* a war pair persists; a 52-tick episode
leaves little room for a war to be declared and then hold long enough, while a full 200-tick
episode plainly would. **The honest, evidenced claim is narrower: these subsystems did not fire
within the 52-tick episodes actually observed. Whether they fire at the full configured 200-tick
episode length is unknown and untested** — the observed truncation prevented answering that
question, not the reactivated subsystems themselves.

Traced the truncation itself (cheaply — one grep, no reruns needed, not a deep investigation):
`ScenarioRuntimeService`'s own stall detector (`src/engine/scenario_runtime.py`,
`STALL_THRESHOLD=50`) sets `self._paused = True` once 50 consecutive ticks produce zero simulation
events, and the run loop is gated on `not self._paused` — matching the observed ~52-tick
truncation almost exactly (50 + a couple of ticks for the counter to cross the threshold and the
loop to notice). The JSONL trace's own `3 scenario_stalled` events (one per episode) corroborate
this directly. This is filed as its own ticket below rather than chased further here — it has real
consequences beyond this investigation (every future measurement of `campaign_life_arc` is
affected by it) and deserves its own scope.

**This is a genuinely separate fact from PR #148's own fix, not a sign the fix is incomplete.**
PR #148 removed the *structural* blocker (empty `state.regions`/`.places` made these subsystems
impossible regardless of any other precondition). It did not, and was never scoped to, change the
war-declaration/calamity-threshold preconditions, or the unrelated stall-detector truncation, that
together determine whether these now-structurally-possible subsystems are observed to fire within
any specific profile's real run. The originally-scoped third subsystem (regional tax/suppression
via `TownResolutionSystem`) was already directly verified live by `CAMPAIGN-REGION-PLACE-CARRY`
itself, not re-litigated here.

## Conclusion

No Campaign-mode baseline, fixture, or SimQ expectation drifted, because none was ever recorded in
this repo's regression-tracked fixtures for Campaign mode to begin with (Finding 1) — this alone
fully answers this ticket's own scope. Finding 2 (all 154 existing Campaign-mode tests pass)
supports it. Finding 3's real-run observation (war/siege/calamity did not fire within the 52-tick
episodes actually run) is recorded honestly with its own real limitation stated plainly — whether
they fire at the intended 200-tick episode length remains genuinely unknown, and the reason
episodes truncate at 52 ticks is filed as its own ticket rather than left as an aside. This is a
valid, evidenced null result per the ticket's own Acceptance Criteria escape clause. No baseline
refresh and no code change are warranted by this investigation; one new follow-up ticket is filed
for the truncation itself.

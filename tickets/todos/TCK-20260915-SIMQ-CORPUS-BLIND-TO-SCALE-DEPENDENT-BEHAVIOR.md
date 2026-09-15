---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR
phase: open
date: 2026-09-15
tags: [simulation-quality, combat, observability]
---

# TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR

## Title
The SimQ calibration corpus runs at ~10 entities and cannot detect a change that only manifests at
population scale — confirmed on a real 58% combat-volume reduction that produced zero pillar
movement; determine what class of change the corpus can actually see, and whether a scale tier
should exist

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
While verifying `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s gate — a real,
measured 57.3% reduction in real attacks (58.1% cross-faction) on a 1000-entity metropolis
scenario — the standing instruction was to also run the SimQ corpus and report what the pillars
show, "rather than have it surface as a mystery next week." Ran
`tools/calibrate_simq.py --name frontier_living_world --seed 42 --ticks 100`, with and without the
gate:

| Condition | COMBAT pillar events | COMBAT pillar norm |
|---|---|---|
| Gate absent | 17 | +0.3871 |
| Gate active | 17 | +0.3871 |

**Identical.** Passing `--entities 500` to override the default did not change this either (still
14 events, no material shift) — these calibration profiles do not scale their real population with
that flag the way `build_metropolis_state` does; `calibrate_simq.py`'s default world-building path
runs at a fixed, small population (~10 entities) regardless.

**This means the corpus is structurally blind to any change whose effect only shows up at
population scale** — which describes most of this arc's own findings (the tension-cascade fix, the
faction-sentiment mechanism, this combat gate). SimQ is the gate this project would naturally cite
as evidence a change is safe; if it cannot see scale-dependent regressions or improvements at all,
that's a gap in the safety net itself, not a one-off null result.

## Scope
- Determine exactly what class of change the current corpus profiles *can* detect (event-presence/
  absence, small-population interaction patterns) versus what they structurally cannot (anything
  whose effect requires enough population for statistical signal to emerge — this gate's own
  reduction, faction pairwise-tension accumulation, etc.).
- Investigate why `--entities` does not scale `frontier_living_world`'s (or other profiles')
  real population — is this profile-specific, or true of every `calibrate_simq.py` profile? Check
  `tools/calibrate_simq.py`'s own world-building path (`build_world`/equivalent) to see whether
  `--entities` is honored at all for non-default profiles, or only for a specific code path.
  (Not yet root-caused in this ticket's own filing — first `frontier_living_world` +
  `--entities 500` attempt showed no material change, but the mechanism was not traced.)
- Propose (not decided here) whether a scale tier should exist — e.g. a metropolis-scale SimQ
  profile that runs at population sizes comparable to `build_metropolis_state` (1000 entities),
  even if it must run less frequently than the standard corpus given cost.
- Cross-check whether other prior SimQ investigations already ran into this same wall without
  naming it as a corpus-scale limitation — `stored_artifacts/TCK-20260808-SIMQ-LARGE-SCALE-WORLD-
  VALIDATION/` looks directly relevant by name and should be read before concluding this is a new
  finding rather than a rediscovery.

## Out of Scope
- Re-running or second-guessing `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s
  own metropolis-scale measurement — that measurement is real and already reported; this ticket is
  about the corpus's own blind spot, not about re-verifying the gate.
- Building the scale tier itself, if that's the chosen fix — scope that as its own
  implementation ticket once the investigation above lands on a concrete recommendation.

## Acceptance Criteria
- A clear, evidence-backed statement of what the current SimQ corpus can and cannot detect, scale-
  wise — not assumed from this one data point.
- Root cause for why `--entities 500` didn't change `frontier_living_world`'s measured population.
- A concrete recommendation (scale tier, different corpus design, or an explicit documented
  limitation) — reported back before any implementation, since this is a design decision about
  what the SimQ safety net is supposed to cover.

## Related Tickets
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` (the measurement that
  surfaced this gap)
- `TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION` (check for prior overlap before treating this
  as new)

## Related Docs
- `docs/guides/agent_monitoring.md`
- `config/simulation_quality/profiles/frontier_living_world.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION/` (check first)

## Related Code Areas
- `tools/calibrate_simq.py` (world-building path, `--entities` handling)
- `src/simulation_quality/pillar_accumulator.py`, `src/simulation_quality/scorers/`

## Assumptions / Open Questions
- Not yet known whether `--entities` is genuinely non-functional for this profile, or whether a
  different override mechanism is needed (a population-scale field inside the profile YAML
  itself, rather than a CLI override). Check before assuming either.

## Implementation Notes
_(none — filed as a finding, not yet investigated)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_

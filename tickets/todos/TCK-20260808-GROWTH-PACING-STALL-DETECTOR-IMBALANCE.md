---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE
phase: open
date: 2026-08-08
tags: [progression, combat, simulation-quality]
---

# TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE

## Title
Real combat/kill frequency (3-5 XP-granting kills population-wide per 2000 ticks) is ~13-21x
lower than `capability_growth_stalled`'s own 300-tick re-firing cadence — a real pacing/balance
mismatch, not a code bug, found by `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX` (DONE) root-caused why population-level
`growth_trajectory` stays negative even after a real, verified kill-reward wiring fix: real
combat/kill frequency across the corpus is genuinely low (3-5 `xp_granted` events population-wide
per 2000 ticks, confirmed via 2 independent live probes), while `capability_growth_stalled`
re-fires roughly every 300 ticks for any entity that hasn't grown — a real ~13-21x imbalance. That
ticket evaluated and rejected a narrow fix (raising the per-kill XP multiplier) because the real
numbers showed it couldn't flip the sign — the fix has to be one of two larger levers, neither of
which that ticket's own narrow scope could responsibly take on:

1. **Raise real combat/kill frequency corpus-wide** — a real change to combat-engagement rates,
   AI targeting behavior, or hostile-population density, with broad ripple effects across COMBAT/
   PROGRESSION/AGENCY pillar grades.
2. **Lengthen `capability_growth_stalled`'s own 300-tick cadence** to match genuinely slower-paced
   worlds — a smaller, more surgical change, but still a real, documented detector-threshold
   change (`config/simulation_quality/scoring_weights.yaml` or wherever this constant lives) with
   its own real risk: `grade_anchors.json` recalibration for any scenario whose PROGRESSION grade
   shifts.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm the real, current location and value of `capability_growth_stalled`'s own 300-tick
     window constant, and survey how many real corpus scenarios' PROGRESSION grades are actually
     sensitive to it (some worlds may already be stall-dormant for unrelated reasons — don't
     assume every scenario is affected equally).
   - Measure real combat/kill frequency across a broader sample than the 2 worlds
     `GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX` directly probed — confirm the ~13-21x imbalance
     holds corpus-wide, not just in those 2.
   - Decide which lever (raise kill frequency vs. lengthen stall cadence) is the real, lower-risk
     fix — likely the stall-cadence lengthening, given it's a single config value vs. a
     combat-behavior change with much broader ripple effects, but confirm with real data, not
     assumed.
2. **Plan**: design the specific change and its real recalibration blast radius.
3. **Implement**: the change, re-verified via the real long-run observation tier
   (`make simq-long-run-lifecycle-observation`) showing `growth_trajectory` genuinely move on
   multiple worlds, and `grade_anchors.json` recalibrated for any affected scenario.

## Out of Scope
- Re-opening the orphaned-kill-reward fix itself (`TCK-20260808-PROGRESSION-GROWTH-ECONOMY-
  UNREACHABLE-IN-PRACTICE`) — independently verified correct, not the remaining cause.
- The COMBAT pillar's own credit-gap question (`TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-
  CREDIT-GAP`) — a related but distinct, separately-tracked investigation.

## Acceptance Criteria
- [ ] investigation.md confirms the real imbalance scale across a broader world sample
- [ ] investigation.md reaches a real, evidenced decision on which lever to pull
- [ ] A real fix lands, re-verified via the real long-run observation tier showing measurable
      `growth_trajectory` movement on at least 2 worlds
- [ ] `grade_anchors.json` recalibrated for any scenario whose grade shifts, or confirmed no shift
      with real evidence
- [ ] `docs/simulation_quality/quality_scoring_contract.md` / `docs/parity_ledger/progression.yaml`
      updated if any threshold changes
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX (DONE — the real investigation and
  rejected-fix-candidate analysis this ticket is grounded in)
- TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE (DONE — the real wiring fix that
  is not the remaining cause)
- TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC (parent context — not a formal child, filed as a
  standalone follow-up given its own larger/riskier real scope)

## Related Docs
- `docs/simulation_quality/entity_lifecycle_score.md` (the real finding this ticket addresses)
- `docs/simulation_quality/quality_scoring_contract.md` §7.6 (`capability_growth_stalled`)
- `docs/simulation_quality/long_run_observations/*.json` (real data this ticket's own Investigate
  should extend)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX/`

## Related Code Areas
- `config/simulation_quality/scoring_weights.yaml` / `detection_params.yaml` (stall-window config)
- `src/simulation_quality/scorers/progression.py`
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- Which lever (kill-frequency vs. stall-cadence) is the real, lower-risk fix — not assumed;
  Investigate must weigh real recalibration blast radius for each before deciding.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)

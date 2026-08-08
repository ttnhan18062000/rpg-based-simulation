---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [progression, simulation-quality]
---

# Plan — TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX

## No code fix — real, evidenced conclusion, not a gap in effort

Per investigation.md: the remaining negative `growth_trajectory` is a genuine pacing/balance
characteristic (real combat/kill frequency too low relative to the stall-detector's own cadence),
not a residual wiring bug. The one concrete fix candidate evaluated (raising the per-kill XP
multiplier) was found, with real numbers, insufficient to flip the population sign (~13-21x
imbalance vs. at most ~2x improvement from that lever alone) — implementing it anyway would be a
disclosed Mechanics Bible divergence that doesn't resolve the finding, exactly the kind of
gate-dodge/cosmetic-fix CLAUDE.md's own Gate Integrity rule (and this session's own established
discipline) says not to do.

## Real deliverables

1. **Docs**: record the real finding (6 growth-tag fire rates, the imbalance, the evaluated-and-
   rejected fix candidate) in `docs/simulation_quality/entity_lifecycle_score.md`, so a future
   reader of a negative `growth_trajectory` mean has real, calibrated context instead of assuming
   it's an unexamined bug.
2. **New follow-up ticket**: file the real remedy this investigation identified — raising real
   combat/kill frequency corpus-wide, or lengthening `capability_growth_stalled`'s own 300-tick
   cadence to match genuinely slower-paced worlds — as its own, appropriately-scoped standard-tier
   ticket (real risk: `grade_anchors.json` recalibration across dozens of scenarios), not folded
   into this one. Matches this session's own established pattern (e.g.
   `TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING`) of turning a real, disclosed,
   out-of-scope finding into a new ticket rather than silently dropping it.
3. **Ticket's own Acceptance Criteria**: the "(if warranted)" fix clause is satisfied by the real
   conclusion that no fix is warranted *in this ticket* — the criteria's own kill-rate/quest-rate
   reporting requirements are satisfied by investigation.md's real measurements.

## Acceptance-criteria map

| Criterion | Satisfied by |
|---|---|
| Real double-application question resolved | Already resolved by the sibling fix ticket (re-confirmed here, not re-litigated) |
| Real kill rate measured | investigation.md — 2 independent real 2000-tick probes |
| Real quest-completion rate confirmed current | investigation.md — direct real probe, `quest_started`/`quest_completed` both 0 at 2000 ticks |
| Real fix lands *if warranted* | Not warranted, per real evidence — documented, not silently dropped |
| Docs/parity updated if formulas change | No formula changed — nothing to update there |
| Scoped pytest passes | N/A — no code change; existing suite unaffected |

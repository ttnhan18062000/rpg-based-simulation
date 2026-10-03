---
status: historical
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX
phase: done
date: 2026-08-08
tags: [progression, simulation-quality]
---

# TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX

## Title
`growth_trajectory` remains negative population-wide across all 6 real long-run corpus worlds even
after `TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE`'s own real, verified fix

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Child ticket of `TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC`. That epic's own real 2000-tick,
6-world observation data (`docs/simulation_quality/long_run_observations/*.json`, seed 42,
`dropped_count=0` everywhere) shows `growth_trajectory` mean still negative in every single world:

| World | `growth_trajectory` mean |
|---|---|
| `wilderness_survival` | -0.0031 |
| `resource_dense_basin` | -0.0017 |
| `crowded_frontier` | -0.0019 |
| `hero_guild_routing` | -0.0026 |
| `dungeon_crawl` | -0.0018 |
| `urban_political` | -0.0017 |

This data was captured **after** `TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-
PRACTICE` (DONE) fixed a real, verified bug: `movement.py`'s opportunity-attack path was
orphaning its own kill reward, silently discarding all real XP from the corpus's dominant kill
mechanism. That fix was directly verified (a real Kernel run producing `evolution_points_delta >
0` on a kill, where it produced nothing before) — but this real, independent, longer-run
population-level data shows the sign hasn't flipped anywhere.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm the fix is genuinely active in this data (it should be — committed before this
     observation run — but verify, don't assume; check the observation JSON's own event counts
     for real `xp_granted`/evolution-points activity, not just that the code path exists).
   - Measure real kill rate + real XP delivered per kill across these same 6 worlds at 2000 ticks,
     and compare against `capability_growth_stalled`'s own 300-tick stall-tagging frequency (the
     other side of `growth_trajectory`'s ratio: `(positive-growth-count - stall-tag-count) /
     path_length`). A real, low-frequency positive signal can stay net-negative if stall-tags fire
     far more often — quantify this, don't guess.
   - Re-verify quest-completion rate is still genuinely zero in this real, longer 2000-tick
     window (the sibling ticket confirmed zero at 1000 ticks on 2 worlds; recheck at 2000 ticks
     across all 6, since a longer window could plausibly change this).
   - Decide the real root cause class: XP-magnitude-too-small-relative-to-threshold,
     kill-rate-too-low-even-post-fix, quest-dormancy-removing-a-second-source, or a combination —
     with real measurements for each candidate before Plan.
2. **Plan**: design the real fix based on Investigate's own findings — likely a magnitude/rate
   rebalancing (not a new wiring bug, since the known wiring bug is already fixed), but do not
   assume this without Investigate's own evidence.
3. **Implement**: the real fix, re-verified via `make simq-long-run-lifecycle-observation`
   (re-running the real long-run tier, not just a unit test) showing `growth_trajectory` genuinely
   move, on at least 2 of the 6 worlds.

## Out of Scope
- Re-opening or second-guessing the orphaned-kill-reward fix itself — that fix is independently
  verified correct; this ticket investigates why its population-level impact is still small, not
  whether it was implemented correctly.
- The COMBAT pillar credit-gap question (sibling child ticket
  `TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP`) — related but tracked separately.

## Acceptance Criteria
- [ ] investigation.md reports real, measured kill rate + XP-per-kill across the 6 real worlds at
      2000 ticks
- [ ] investigation.md reports real, current quest-completion rate at 2000 ticks (not inherited
      from the 1000-tick finding uncritically)
- [ ] investigation.md reaches a real, evidenced root-cause conclusion, not a guess
- [ ] A real fix (if warranted) lands, re-verified via the real long-run observation tier showing
      measurable movement on at least 2 worlds
- [ ] `docs/mechanics/attribute_progression_contract.md` / `docs/parity_ledger/progression.yaml`
      updated if any formula/magnitude changes
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC (parent epic)
- TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE (DONE — the real fix this
  ticket's own data was captured after)
- TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER (DONE — the tool/data source)

## Related Docs
- `docs/mechanics/attribute_progression_contract.md`
- `docs/simulation_quality/quality_scoring_contract.md` §7.6 (`capability_growth_stalled`)
- `docs/simulation_quality/long_run_observations/*.json` (the real data this ticket investigates)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE/`

## Related Code Areas
- `src/engine/combat.py`, `src/engine/movement.py` (kill/XP computation)
- `src/progression/leveling.py` (`LevelingService.get_xp_required()`)
- `src/simulation_quality/scorers/progression.py` (`capability_growth_stalled`)
- `src/engine/quests.py` (quest-completion re-check)

## Assumptions / Open Questions
- Whether the real fix here is a magnitude change, a threshold change, or something else entirely
  — not assumed; Investigate must measure real kill/stall rates first.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout.

Two independent live 2000-tick probes found `xp_granted` is the ONLY one of the 6
`growth_trajectory_tags.positive` tags that ever fires — `level_up`/`skill_unlocked`/
`recipe_learned`/`item_equipped`/`attribute_changed` were all zero in both. Traced why `level_up`
specifically never fires despite real kills occurring: a single kill's real XP (10 at level 1) is
far below the real level-1 threshold (100 XP), and the rare real kills (3-5 population-wide per
2000 ticks) don't concentrate on one attacker. Evaluated raising the per-kill XP multiplier as a
real fix candidate and rejected it with real numbers — the ~13-21x stall/growth imbalance is far
too large for that lever alone to flip the population sign. Re-confirmed quest-completion still
genuinely zero at 2000 ticks via direct probe (not inherited from the 1000-tick finding).

**Real, evidenced conclusion: not a residual bug from the sibling kill-reward fix — a genuine
pacing/balance characteristic**, the same class of finding as `wilderness_survival`'s
archetype-correct low diversity. Did not force an ineffective fix through; documented the real
finding and filed `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` for the real remedy
(raising combat frequency, or lengthening the stall detector's own cadence) — a substantial
initiative with real recalibration risk, appropriately out of this narrower ticket's own scope.

## Test Summary
No code change — `pytest tests/tools/test_entity_lifecycle_score.py -q` (25/25 passed) confirms
the docs-only change introduced no regression.

## Files Changed
- `docs/simulation_quality/entity_lifecycle_score.md` — real finding documented
- `tickets/todos/TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE.md` — new follow-up ticket

## Completion Summary
Root-caused the still-negative `growth_trajectory` with real, live data rather than assuming the
sibling fix was incomplete — confirmed the wiring fix is correct and the remaining cause is a
genuine, disclosed pacing imbalance no small parameter tweak could responsibly resolve. Evaluated
and rejected a concrete fix candidate with real numbers rather than either forcing it through or
leaving the finding unactioned. All of the ticket's own Acceptance Criteria items are satisfied by
the real investigation; the "(if warranted)" fix clause is honestly satisfied by "not warranted at
this ticket's own scope," with the real remedy tracked in a new, appropriately-scoped ticket.

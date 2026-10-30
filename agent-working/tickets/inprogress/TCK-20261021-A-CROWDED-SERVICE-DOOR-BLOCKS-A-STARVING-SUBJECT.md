---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT

## Title
A crowded service door blocks a starving subject 2 tiles away indefinitely (occupancy_violation, falls back to REST)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Lane A traced urban_political s44 on step 2 (f9b21b55b, TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY, 2026-10-21; probe tick_log.py, outputs in /mnt/data/scratch-rpg-implementer/paired_en/v3btr/). Merchant 28 dies of STARVATION at t3140, which is a V3.
- proj_hunger_1372 is ACTIVE and current, with the top score (160 at hunger 100), for the whole window t2990-3140. Its objective is hunger_20003, the inn at (39,23). The merchant has 0 gold, so this is a free inn meal.
- The merchant stands at (41-42, 23-24), 2 tiles from the target.
- On 150 of 150 ticks it takes ENTITY_ACT REST (SUCCESS). nav.last_failure_reason is occupancy_violation on every sampled tick.
- Workers 4 and 6, hero 23 and merchants 29, 30 and 12 stand 1-2 tiles away the whole time, so the inn door is crowded. The move toward the inn is refused, and the merchant falls back to REST.
- No threat, stock or money issue.

The designer's ruling (2026-10-21): OUT of family under the user's v1 cutoff (2026-10-21), because the cause is movement and occupancy, not a decision-side cause. It is an owned known red at v1, disclosed as N14, and its rpg_gate_known.yaml entry cites the cutoff.

- SECOND CASE CONFIRMED (rpg-implementer worker 1 execution trace, 2026-10-29; c32db1a41 crowded s46, t3760-4247, new arm only, pure; /mnt/data/scratch-rpg-implementer/c1610/w1c/):
  - The hunger project is current in 448 of 488 ticks, at hunger 100. Its objective is reach_location at inn 20003, and the nav target is (27,20) for 374 ticks.
  - The worker hovers 1-2 tiles from the target (222 ticks at (28-29, 21-22)) and never arrives. In the adjacent ticks it falls back to REST 126 times.
  - nav.last_failure_reason is position_swap in 328 ticks and LEGAL in 160.
  - Neighbours within 2 tiles: merchant 12 (202 ticks), worker 7 (199), hero 32 (90).
  - No leash. No interaction update and no transfer at all. It dies at t4248.
  - Differences from case 1:
    - (a) the failure reason is position_swap, not occupancy_violation, so the cause analysis covers both;
    - (b) it holds 85 GOLD throughout, so this is not a free-meal case: BUY was open and it still never ate. Say whether gold changes the service path.
  - Caveat: inn_in_reach reads 20003 even 11 tiles away, so it means "an inn exists", not proximity. Who occupies (27,20) is not logged.
  - Earlier text below, kept for history:
- (was) CANDIDATE SECOND CASE, not yet confirmed (rpg-designer, 2026-10-29, from the :1610 crowded s46 trace on c32db1a41; /mnt/data/scratch-rpg-implementer/c1610/trace/):
  - crowded_frontier s46, worker 1. Its hunger project is CURRENT for the whole window t3740-4272 at hunger 100 (current in 473 of 533 ticks; fatigue in 60).
  - Ways in reach: INN_MEAL (the free meal on that tree), FORAGE, BUY and WORK_SHIFT.
  - Threat present in 5 of 25 decisions, acting in 1. It never eats and starves at about t4240-4271 (last decision t4239). CORRECTED 2026-10-29: the first report read a nonexistent `alive` attribute and gave t4772.
  - In base it died of COMBAT at about t2000, so a life about 2250 ticks longer exposed this.
  - No :1610 path is involved: the project selection is right.
  - If its execution trace matches this ticket's door shape (an inn in reach, the project current, never served, a refused move or an occupancy fallback), it stays here as a second case. If not, it splits into its own ticket: "a subject whose hunger project is current with a meal in reach starves without eating".
  - First evidence, per tick, new arm only, since base cannot be forced to keep it alive (say so in the report): the action dispatched and its result (move refused or blocked, EAT refused and the reason), position against the inn door, leash, gold, and whether the free meal was offered.
  - Sequenced after lane B's D73 job. Not a :1610 blocker.


## Designer Ruling 2026-10-30 (N14, verbatim summary; full text at main-checkout .claude/handover/drafts/rpg-designer-n14-ruling-UNSENT.md)
- CAUSE (lane B, main de5a223ca, urban s46): FATIGUE squatters hold all 4 door tiles, chattering in 1-tick RESTs at the wake line 58.8 (is_rested_enough), while the fatigue project completes only at REST_MIN_SLEEP_DEBT 20 and its goal keeps winning at about 59. Gold is irrelevant. The free-door share was mostly target-type artifact (100 of 155 stalls aim at an entity or position).
- RULING: F1 GENERALIZED (Unified divergence). A chosen REST or SLEEP lasts until the fatigue project completes (debt <= 20), unless a wake ends it: a hunger wake (2.115 / A'), a present threat to life, or any existing sleep end. The wake line stays only as the scheduler's wake trigger and the goal's "tired" read. No new constant. It applies to rough rest and to a bed.
- CHECK: paired run on main, 3 worlds × s42-46. Report:
  - asleep share per person-day, base vs new (a move beyond noise is a STOP to the designer, then an owner question);
  - stall runs within 2-6 tiles (878 expected to fall to a small number);
  - door-tile occupancy;
  - collapses;
  - deaths by cause (a rise is a STOP).
- TESTS:
  (a) the p22 hover: a REST at 59 runs to 20, the project completes, the subject leaves the tile;
  (b) a hunger wake ends it;
  (c) a threat ends it;
  (d) a sleep from 90 ends at 20, not 58.8.
- BIBLE 04 §1 sleep paragraph, add: "A rest, once begun, lasts until the sleep need is met (sleep debt at REST_MIN_SLEEP_DEBT) unless a wake ends it; the wake line only wakes a sleeper's brain and marks a subject as tired." The diff goes to the designer. Unified divergence (u24 id 2.153 / STRAT-293) plus a parity entry.
- F2 (a door yield to pressing hunger) is need ordering, so an owner row; ask only if the re-measure shows starving subjects still waiting behind real sleepers. F3 (a served rest occupies the building, 2.78) is a parked design ticket for rpg-designer, after the A'/D73 chain.
- To the STALEMATE/WANDER nav ticket: the 100 entity/position-target stalls (counts split by target type), and the sub-finding that the movement rungs consider only the subject's own neighbours, so never a door tile 2+ steps away (p4).
- SEQUENCE: N14 (F1) -> A' re-measure (p7/11/27/30 arrive) -> STALEMATE/WANDER nav family -> #781.

## Designer Ruling 2026-10-30 (N14 follow-up: Q1 collapse, Q2 threat end)
- Q1 COLLAPSE: confirmed, a collapse (decision 41, owner's) keeps its end at the wake line 58.8. F1 covers chosen rests only. After a collapse ends, a still-live fatigue project picks a chosen sleep, which F1 runs to 20. Extra test: a collapse from 98 ends at 58.8, and a sleep chosen after it runs to 20.
- Q2 THREAT END: option 1, its OWN id 2.154 / STRAT-294, class Enforced. SURV-06 says rest happens "wherever it is not in danger" and Bible 04 l.40 says "when no present threat holds", so a held sleep that no threat can end already breaks the text. It is a separate mechanism, true even without F1.
  - Condition (existing predicates only): wake a holder of SLEEP or REST, collapse included, when decision 32's condition holds (an unengaged hostile adjacent) OR acting_threat_to(subject). A hit or an aimed attack wakes it, including at range. It runs on decision 32's cadence. No new constant.
  - The wake is a re-decision only (l.30 / l.38). At debt >= 98 the subject collapses again; otherwise it answers the threat (flee or fight). The fatigue project stays live.
  - Tests:
    (a) a hostile steps adjacent to a chosen sleeper, which wakes and flees or fights;
    (b) a ranged acting attacker wakes it;
    (c) a collapse at 98 under threat wakes and re-collapses;
    (d) with no threat there is no wake and F1 runs to 20;
    (e) after the threat ends, the fatigue project is still live and sleep resumes by ordinary decision.
  - Paired run adds: sleeps ended by threat, and deaths of subjects asleep at the death tick, base vs new. A rise in asleep-at-death is a STOP to the designer.
- BIBLE 04 §1 sentence (replaces the F1 sentence; send the designer one diff covering both ids): "A rest, once begun, lasts until the sleep need is met (sleep debt at REST_MIN_SLEEP_DEBT) unless a wake ends it; the wake line only wakes a sleeper's brain and marks a subject as tired. A present threat wakes a sleeper, a collapsed one included (decision 32's adjacent hostile, or a perceived hostile acting on it); the wake is a re-decision, so a collapse past its line is chosen again and otherwise the threat is answered."
- 2026-10-30 designer ack: acting_threat_to stays unchanged (it also gates row 88). The saliency-cap gap (a shooter behind 5+ closer non-acting hostiles) is guarded by a measured STOP: a non-zero count of hits on a sleeper from an unperceived hostile goes to the designer. Bible wording changed to "a perceived hostile acting on it". An item or spell range above 10 also goes to the designer before the code lands.
- 2026-10-30 rpg-planner (counter definition): count a hit on a sleeper whose SLEEP/REST hold is still intact at the first wake-check tick after the hit (next tick with (tick + id) % ADJACENCY_WAKE_COOLDOWN == 0). Per case record: tick, entity id, attacker id, whether the attacker was in perceived_hostiles at the hit tick, hostiles within 10 tiles. Any non-zero total is a STOP to the designer, whatever the cause.
- 2026-10-30 designer ruling (lane B finding: the rest ends at 19.9, but the project completion check needs a brain tick, so the hover moved to 20): OPTION 1, FOLDED into 2.153.
  - On the tick a chosen SLEEP/REST ends because debt fell BELOW REST_MIN_SLEEP_DEBT, the scheduler wakes that subject's brain on that same tick, or on the next tick in pipeline order, whichever runs before debt accrues. Then intelligence.py:1436 completes the project. The trigger is only "a rest ended at the floor". No new constant. It extends the existing need-wake (2.115 family).
  - Test (a) becomes deterministic: the exact tick, the project COMPLETED, and no rest_in_place dispatch afterwards, across brain-cadence offsets 0-9. Add (a') for an inn-bed SLEEP.
  - The paired run adds rest_in_place dispatches within 10 ticks of a floor-end. Expected 0; anything else is a STOP to the designer. Options 2, 3 and 4 are rejected.
  - Wording: "below" in both the code and the Bible. New 2.153 sentence: "A rest, once begun, lasts until the sleep need is met (sleep debt below REST_MIN_SLEEP_DEBT), and the sleeper's brain is woken as it ends so the need is closed; otherwise only a wake ends it. The wake line only wakes a sleeper's brain and marks a subject as tired." The 2.154 sentence is unchanged ("a perceived hostile acting on it").
- 2026-10-30 designer ruling (s44 collapse loop), CONDITIONAL on lane B confirming that the threat wake ends the short collapse holds:
  - 2.154 narrowed: a COLLAPSE is woken only by a perceived hostile ACTING on it. Adjacency alone does not wake a collapse; it still wakes a chosen sleep. 2.154 stays Enforced (SURV-06 / l.40 is about chosen rests).
  - Bible: "A present threat wakes a chosen sleeper (decision 32's adjacent hostile, or a perceived hostile acting on it); a collapsed one is woken only by a perceived hostile acting on it" (the rest of the sentence unchanged).
  - Tests: (c) is replaced by (c1) a collapse with an adjacent non-acting hostile is NOT woken; (c2) a collapse that is hit is woken and re-collapses if past the line; (c3) the s44 shape, an adjacent hostile across 50 ticks of collapse, gives one uninterrupted collapse.
  - Re-run s44 with the narrowed wake (expected collapses about 0 to low) before the full table is re-read.
  - NOT ruled yet: s44 deaths 16-17 with either wake off (base 6). All-seeds deaths, the asleep-share split and the door occupancy are judged together. Record subject 17 (a hostile kind, 10 kills at the inn door) in the trace.
- 2026-10-30 designer RE-RULING (supersedes the conditional "acting only" narrowing above, which is WITHDRAWN): lane B's dump showed the short collapse holds were ended by the threat wake while the subject was being hit, and every wake landed at 97.4-97.9, so it re-collapsed within 2 ticks.
  - 2.154: a COLLAPSE is not woken by ANY threat, adjacent or acting. It stands until its own end or the existing hunger wake. The threat wake applies to chosen SLEEP/REST only. Still Enforced.
  - 2.115 (the hunger wake of a collapse, owner ruling 2026-10-11, Bible 04 l.38) is UNCHANGED. The s44 hunger re-collapse loop at the jammed door is F3 evidence; if it remains after F3 or N14's final re-run, it becomes an owner row via the lead: "should hunger end a collapse that cannot reach food?"
  - Bible threat sentence: "A present threat wakes a chosen sleeper (decision 32's adjacent hostile, or a perceived hostile acting on it); a collapse is not woken by a threat (decision 41), only by hunger as above; the wake is a re-decision, so otherwise the threat is answered (divergences 2.153 and 2.154)."
  - Tests: (c1) a collapse with an adjacent hostile is not woken; (c2) a collapse being hit is not woken and runs to its end (or the hunger wake); (c3) the s44 shape, 50 ticks of adjacent hits, gives one uninterrupted collapse; (c4) a chosen sleep with an adjacent hostile is woken.
  - s44 single-seed re-run: report collapses and, separately, the hunger-wake re-collapses. The deaths ruling waits for the all-seeds table.

## Scope
- Cause first:
  - Is "reach" for a service a single tile or an area? Does an adjacent tile count (divergence 2.78, the walk ending on reach)?
  - Why does a refused move fall back to REST instead of a re-path, a wait-for-gap or another tile?
  - Do the six entities at the door ever clear, and are they queued for the same service?
- The designer rules the shape. Implement, add real-kernel tests (a starving subject at a crowded service door is served within a bound), and measure paired against v1 (seeds 42-46, D76).

## Out of Scope
- Capacity admission (step 2).
- Inn pricing or the free meal (D73, after v1).

## Acceptance Criteria
- The cause is named with evidence.
- No starvation V3 from a service-door occupancy block in the 3 gate worlds × seeds 42-46.
- D76 shows no unexplained drift against v1, and N14 is closed with numbers.

## Related Tickets
- TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK (trigger A of the same stall family; 12 runs on main, mostly crowded; this ticket owns trigger B, the door stall)
- TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED (its A' re-measure needs this stall fixed first)
- TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY (which surfaced this)
- TCK-20261019-RECORD-BASELINE-V1 (known red, cutoff citation)

## Related Docs
- docs/guidelines/intentional_divergences.md 2.78 (the walk ends on reach) and 2.106 (held move)
- docs/plans/systemic_world/v1_disclosure.md (N14)

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/paired_en/v3btr/ (probe tick_log.py)

## Related Code Areas
- movement and occupancy (MovementCandidateSelector, occupancy checks), service reach

## Assumptions / Open Questions
- Is this specific to inns, or to every service with a single entry tile?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

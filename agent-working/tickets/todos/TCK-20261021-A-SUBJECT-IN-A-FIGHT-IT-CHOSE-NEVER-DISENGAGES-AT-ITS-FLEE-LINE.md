---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE

## Title
A subject in a fight it chose never disengages at its flee line (crowded s44 merchant 12, hp 9 to 1 over about 200 ticks)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A traced the crowded_frontier STOP cases for the corpse fix (TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT, 23fbe0ecf, 2026-10-21). On seed 44, new arm:
- Merchant 12 pursues raider 35 from t1851 at (25,24). The two attack each other every tick.
- The merchant loses about 9 hp per 21 ticks from t1856 and stays in ATTACK down to hp 1. It dies by COMBAT at t2066.
- The raider stays at about 25 hp throughout.
- The merchant's sleep_debt is 92.5 (context).

Bible 04 §1 puts flight (Tier 1) above any chosen goal, and the flee line exists for merchants: frontier merchant 37 panicked at hp 16 or below. So in a fight it chose, the merchant's flee line never fired.

The designer's ruling (2026-10-21): a defect independent of the corpse fix, since the same meeting would play out the same way in base. It does not block the STOP or v1, no V check catches it, and D78 keeps behaviour changes after v1. Disclosed in v1_disclosure.md as row C6.

## Scope
- Lane A's one-line cause, one of:
  - (a) the flee or retreat check isn't evaluated while pursuing or committed to ATTACK;
  - (b) it is evaluated, but the engagement's score beats retreat;
  - (c) appraisal rates the opponent as beatable.
  Cause letter: (a), from Lane A's read-only probes (2026-10-21; /mnt/data/scratch-rpg-implementer/probes_hs/m12_cause.py and m12_cause2.py, output in paired_cn/).
  - Merchant 12 holds an ATTACK order on raider 35 from t1855. `TacticalDecisionSystem.evaluate_entity_intent` ran once in t2030-2066 (at t2048), so the panic gate, which is the first gate in the tactical pass, was never reached. (b) and (c) do not apply.
  - The panic line: merchant 12 has bravery 0.914. Its appraisal says is_fleeing is True at hp 9 of 80 (panic 0.583, destination (35,24)), so the line is about hp 10-12. It was crossed around t2036-2040, but no tactical pass ran then.
  - What ends it: the single tactical pass at t2048 returned SLEEP. Sleep debt was 92-97, and the collapse gate (decision 41, must_collapse) runs before the panic gate. The merchant falls asleep beside the raider at hp 1 and dies at t2066.
  - Who started the pursuit: merchant 12 (a SHOPKEEPER role, hp 80/80, aggression_mod 1.5 above 80% hp). At t1851 it was in PURSUE on raider 35 with no project and no objective. The engagement is the default tactical branch for any perceived tactical hostile, and there is no exemption for non-combat roles. Raider 35 had just ended a PANIC_RETREAT at hp 24-25.
  - Related pattern: a held move that is never re-decided (divergence 2.106, where a pressing need wakes the brain of an entity holding a move). Here it is a held ATTACK, and the panic line does not wake the tactical pass.
- Framing (designer, 2026-10-21): this is the 2.106 held-order pattern applied to ATTACK. The likely fix shape is the same as 2.106: the panic line wakes a held ATTACK at strategic cadence. It is its own measured step after v1. The designer's suggested shape (2026-10-21): wake the WHOLE tactical gate stack (legality, collapse, panic) under a held ATTACK, not only panic. Then a collapse that is due lands at the right tick, and TCK-20261021-SHOULD-A-PRESENT-ATTACKER-PUSH-THE-COLLAPSE-LINE is judged on correct timing, so land this ticket before that one.
- Context only, not in scope: engagement is the default tactical branch for any perceived hostile, with no exemption for non-combat roles, so a shopkeeper at full hp pursues a raider. Whether a shopkeeper should start fights at all is a design question for the M-series role and temperament work.
- Split out: collapse being ordered before panic (D41), which lets a merchant sleep beside its attacker, is its own after-v1 item (TCK-20261021-SHOULD-A-PRESENT-ATTACKER-PUSH-THE-COLLAPSE-LINE; the t2048 SLEEP was the involuntary D41 collapse at sleep_debt 100 against line 98. Also in scope here: the debt was measured at 92.5 at t1851 and 100.0 from t2036 (nothing sampled between), with no tactical pass to apply the collapse until t2048, which is the same held-ATTACK bypass for at least t2036-2047).
- The designer rules the shape, together with TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE and the D32 pursuing-hostile wake.
- Implement, add real-kernel tests (a subject in a chosen fight crosses its flee line and disengages), and measure paired against v1 (seeds 42-46, D76).

## Out of Scope
- The corpse fix and step 2 (before v1).
- Changing the flee line itself without a ruling.

## Acceptance Criteria
- The cause is named with evidence.
- A subject that chose a fight disengages at its flee line in a real-kernel test, and the s44 replay no longer shows ATTACK below the flee line.
- D76 shows no unexplained drift against v1, and C6 in v1_disclosure is closed with numbers.

## Related Tickets
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
- TCK-20261020-A-PURSUING-HOSTILE-WAKES-ITS-TARGET (D32)
- TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT (which surfaced this)
- TCK-20261019-RECORD-BASELINE-V1

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1 (flight, Tier 1)
- docs/mechanics/02_combat_laws.md
- docs/plans/systemic_world/v1_disclosure.md (C6)

## Related Stored Artifacts
- Lane A traces: /mnt/data/scratch-rpg-implementer/paired_cn/traces/ (s44)

## Related Code Areas
- src/engine/tactical.py (panic and flee gate, emotion.is_fleeing)
- the combat engagement and pursuit scorers

## Assumptions / Open Questions
- Pointer (designer, 2026-10-21): a second case of a non-combat role picking fights, in the context bullet. Crowded s42 on step 2 (f9b21b55b): merchant 12 attacks goblin leader 30 on 24 ticks and flees it 103 times from t946 to t4998, while the leader never attacks it (v1 row C4, N9; Lane A dump paired_en2/f4/, probe pair_probe.py).
- Does sleep debt 92.5 change the flee line or the appraisal?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

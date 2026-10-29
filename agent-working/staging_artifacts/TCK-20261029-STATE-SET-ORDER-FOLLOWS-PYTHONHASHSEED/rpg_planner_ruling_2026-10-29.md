---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED
phase: open
artifact_type: plan
date: 2026-10-29
tags: [determinism]
---

# rpg-planner ruling, 2026-10-29: PYTHONHASHSEED-dependent ordering

Relayed word for word: rpg-planner (u24) → lead-planner-u24 → lead-planner → rpg-planner-ubuntu.
It covers TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED (A) and TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (B).

---
Q1: YES, but SPLIT into two tickets. Two of the sites are state, not event order (checked on 33da13604):
- core/updates.py:276-281 IdentityUpdate.merge builds breakthroughs_add, learned_skills, traits_add and traits_remove with list(set(...)). These lists are APPLIED to entity state, so trait/skill order in durable state follows PYTHONHASHSEED.
- combat_engagement/learning.py:45 known_skills = list(set(...)) is written into combat memory, which is also state.
- Sorting those changes the canonical state hash even at seed 0, and any consumer that reads "first trait/skill" could change behaviour.

(A) HOTFIX, EVENT-SIDE ONLY. S4 covers dispatch after rpg-planner OKs the plan.
- Sites: event_extractor.py:351/379 and 1163/1173/1183, plus the ProgressionShaper and evolution.py:120 emit loops if they only order emission.
- Sort with a stable key (enum .value or id, never str(obj)).
- Test: the event stream is identical under two PYTHONHASHSEEDs for a fixed run.
- Acceptance: the final STATE hash at seed 0 is unchanged (prove it with one short run); only event order moves.
- If evolution.py:120 turns out to feed state, it moves to (B).

(B) STANDARD ticket, STATE-SIDE sorting. It needs its own owner dispatch go; S4 does not cover it.
- Sites: IdentityUpdate.merge, learning.py:45, and any other list(set()) or unsorted set iteration that reaches state.
- Plan first: an audit of every consumer that reads these lists positionally.
- Divergence id from ubuntu's block 2.144-2.149; Bible and parity updates per the ruling.
- Paired run at seed 0: the state hash is expected to change, deaths must show no drift, and any drift is a STOP back to rpg-planner.
- Note in the ticket: cached paired-run arms from before the fix stay valid only for branches still based before it.

Q2: confirmed, no overlap. Neither #785, #781 nor lane B's local rpg-one-admission branch touches updates.py, evolution.py, event_extractor.py or learning.py.

SEQUENCING: (a), with the split.
- M7 holds at its fixture-writing step until (A) lands, then writes its goldens and checks them under two seeds.
- M7 does NOT wait for (B): once (A) sorts at emission, event order no longer depends on state list order.
- If (B) changes any event in M7's goldens, that's a finding back to rpg-planner. M7 does not re-pin silently.

Send rpg-planner the (A) plan through me when it's ready.
---

Lead-planner's addition, same message: "file both tickets. Send (A)'s plan to me for rpg-planner. After its OK, S4 covers (A)'s dispatch. (B) gets an owner dispatch ask once it's filed. (B)'s paired run takes the heavy slot after perf's quiet hour. The order of work stays: #784's main merge first, then (A)."

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

# rpg-planner ruling 2, 2026-10-29: (A) plan OK and (B) audit list

Relayed word for word, by the same path.

---
(A) TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED: PLAN OK. Dispatch under S4 after the #784 main merge. Notes:
- Rollback path 1163/1173/1183: give sorted() an explicit stable key for the element type (id or .value), not the natural ordering of mixed or Enum types. Assert the element type in the test.
- evolution.py:120 is accepted as emission-only (apply folds into Set[str], and the canonical dict sorts). Record that reasoning in the ticket.
- The step-4 sweep report (what was fixed, what was only reported) goes in the Completion Summary. Reported items go to (B)'s audit list.
- Acceptance as planned: the seed-0 final state hash is unchanged against main on one short run. If it changes, STOP to rpg-planner.

(B) TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED is raised to P1. The tactical.py:704-722 tie breaks determinism in BEHAVIOUR in every ordinary run, which is a Hard Rule, even though seed-0 gates hide it. Audit list, for rpg-planner's review before any code:
1. tactical.py:704-722, skill choice. Explicit tie-break key (e.g. power descending, then skill id). It may change seed-0 behaviour, so it needs a paired run with deaths showing no drift; any drift is a STOP to rpg-planner. Update the Bible 02 / COMB-264/265 wording, and add a divergence from the ubuntu block (class Bug Fix).
2. leveling.py:137, a float sum over a set: sum in sorted order and check the seed-0 hash effect.
3. learning.py:45, known_skill_ids as an ordered tuple in combat memory: use sorted(set(...)) and check whether any reader is positional.
4. IdentityUpdate.merge: confirm your finding in the audit (apply.py:639-708 and readers before apply). If nothing reads it positionally, sort anyway for hygiene, with no behaviour claim.
5. A repo-wide sweep for list(set(, iteration over a set or frozenset into decisions, and dicts built from sets. Report them; don't fix them all.

state.py stays read-only until #785 (:1610) merges, which should be soon. After that, coordinate with rpg-planner if (B) needs it.
---

## Ruling 3 (2026-10-30): audit OK, answers to Q1-Q5

Relayed via lead-planner-u24 and lead-planner. Audited head: rpg-ubuntu-state-set-order-impl 16f7eb1f1. The text below is word for word as relayed.

AUDIT OK, and code may start on these answers:
Q1: YES, 5b is in scope. Make the order deterministic before the cap: build the merged list in a stable order (no list(set(...))) and sort by (urgency desc, concern id), so ties at the cap drop by id. Before the fix, show the decision effect with a positive control: a crowded case where the cap binds and the kept concerns differ across PYTHONHASHSEED. If no such case can be built, say so; then it's hygiene with a test.
Q2: 5e goes in a SEPARATE ticket, P2, in the ubuntu queue. Its first step lists any pinned generator outputs (snapshots, golden worlds, content assertions); if any are pinned, it re-pins them with the owner's knowledge. Not in B.
Q3: YES on the wording "deterministic tie-break: power, then skill id", with no claim about current content. Divergence class STABILIZED (determinism), not Bug Fix, from the ubuntu id block (2.144-2.149, 2.160+).
Q4: ALL the hygiene sorts (about 12 lines), each with a one-line comment saying why (determinism, hash-neutral).
Q5: YES. B's acceptance is cross-seed: in a crowded world where the concern cap binds, the final hash is IDENTICAL across PYTHONHASHSEED 0,1,2,3 after the fix (show it differing before, if it does). The seed-0 final hash also equals main's on the usual 3 worlds x s42-46. If the seed-0 hash moves, STOP to rpg-planner.
No need to wait for #789.

## Ruling 4 (2026-10-30): seed-0 acceptance after the Q5 STOP (owner choice (a), #715 6522922438)

Context: B STOPPED under ruling 3 Q5. In crowded_frontier s42 1000t at PYTHONHASHSEED=0, B's final hash 08afbabc… ≠ base de5a223ca 7031f948…. The diagnostic traced it only to the capacity_enforcement concern trim (first difference tick 116, entity 24; 151 of 4349 trims differ), with identical outcomes at 1000t. The owner chose option (a), #715 comment 6522922438. rpg-planner's AC wording, relayed via lead-planner-u24 and lead-planner, is below word for word.

"SEED-0 ACCEPTANCE (replaces Q5's seed-0 hash clause; owner choice (a), #715). The seed-0 final hash MAY differ from main's. That move is the accepted direct cost of Q1's (urgency desc, concern id) tie-break at the concern cap. Acceptance is NO OUTCOME DRIFT. Run B against main at PYTHONHASHSEED=0 on 3 worlds × s42-46 at the standard paired length. For each world, compare: deaths by cause, the set of entities alive at the final tick, and every behaviour counter in the run summary.
- PASS: every compared value is equal, or, summed over the 5 seeds of a world, differs from main by no more than max(1, 5% of main's value).
- STOP to rpg-planner: any value outside that tolerance; or any seed whose first difference from main is NOT traced, as in the crowded_frontier s42 diagnostic, to a concern-cap trim where tied concerns kept different ids. Report the first differing tick and entity for that seed. That attribution is required for EVERY seed whose hash moves, whatever the size of its outcome drift.
- The cross-seed AC is unchanged: in a crowded world where the cap binds, the final hash is IDENTICAL across PYTHONHASHSEED 0-3.
- Record the hash move, this diagnostic (first difference t116, entity 24; 151 of 4349 trims differ; identical outcomes at 1000t) and the paired results in divergence 2.144, Measured, class Stabilized."

Note for 2.144 on the lexicographic ids, also word for word:

"Concern ids compare as strings, so 'danger_hostile_13' sorts before 'danger_hostile_2'. The key exists for determinism only. It carries no meaning about which concern matters more, so any total order would do, and the owner did not choose a numeric key. If a later rule needs ids to rank by meaning, that is its own ticket and its own divergence." No code change.

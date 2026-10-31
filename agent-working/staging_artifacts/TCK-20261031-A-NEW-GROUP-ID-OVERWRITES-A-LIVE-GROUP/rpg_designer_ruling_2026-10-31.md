---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP
artifact_type: ruling
date: 2026-10-31
tags: []
---

# Fix-shape ruling, group ids

From rpg-designer, agreed by rpg-planner (u24), relayed by lead-planner-u24 and lead-planner, 2026-10-31. Scope and acceptance under rpg-planner's dispatch; original acceptance items stand where this does not replace them. Word for word:

"OPTION A with four additions. Why A: B and C are correct only while 'nothing removes records', a hidden assumption the durable-state rule forbids.
1. The counter: state.next_group_id starts at 10000 and only rises. Only the apply path advances it, as part of the typed group-add update; decision code only reads it. It goes in the canonical dict and round-trips, with an architecture test.
2. Skip taken ids: the allocator steps past any id already in the group store, whether a live group or a squad hash. It's deterministic, one lookup per allocation. This drops the disclosure that a formation id could equal a squad hash.
3. No silent overwrite at apply_plan.py:124. Overwriting is allowed only for a deliberate in-place update of the same group. An add over a different live group becomes a TYPED REJECTION: counted and surfaced, never a replace. That also covers a squad hash landing on a formation id; if one ever shows, its own ticket fixes the squad side. Squad id generation stays as it is.
4. Older saved states: on load, if next_group_id is absent, seed it with max(10000, highest non-squad id + 1). Squads are recognised by FACTION_SQUAD for this one-time seed only. That closes the 'no saved state needs migrating' assumption without a migration.

Counts (reported, not gated):
- On base (at or after 6fdfdf555; the same 15-run set if your slot allows): the number of overwrites today and the ghost members they leave (entities whose group_id points at a group that doesn't list them).
- After the fix, both are 0, and an end-of-run check passes: every living entity's group_id resolves to a group that lists it.
- The hash moves, attributed: the first diff is the first allocation the old formula would have collided on or inflated.
Then COGNITION (entity 6 / group 10009) is re-measured on this fix together with the retention fix, before the s42 re-anchor."

lead-planner's notes, same message: TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT is dispatched on u24 lane C (owner go #715 6543058711). The re-measure needs both fixes on one tree; tell lead-planner when this fix is near so the leads can order the merges. Check u24's open branches before touching shared files; that fix may touch state too. The 15-run base count needs a plan, wall estimate and stop time for lead-planner's go. The expiry re-date stays in this PR, on main before 11-15.

---

## rpg-planner's follow-up ruling (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Binding, word for word:

"1. The set: YES, the retention trace's set (crowded_frontier, frontier_living_world, urban_political × s42-46, 2000t, at or after 6fdfdf555). Counts are reported, not gated, and 2000t matches the s42 re-anchor horizon. Keep the slot go as given.

2. Omitting next_group_id while it is 10000: ACCEPTED, with one condition. Omission is safe only if load reproduces the value. When the field is absent, the load seed is max(10000, highest non-squad id + 1), which gives 10000 only when no non-squad group sits at an id of 10000 or above.
- The architecture round-trip test must cover three cases: no groups; squad-only groups; and formed groups with the counter above 10000. Each must satisfy load(dump(s)).next_group_id == s.next_group_id.
- Show that every producer of a non-squad group advances the counter: the merge paths in updates.py and pipeline_phases/groups.py, plus any world-gen or content-seeded groups.
- If any path creates a non-squad group without advancing the counter, always serialise the field instead. That moves the hash at t0, which is fine as long as it's stated.

3. Rejecting an add over ANY existing id, dissolved records included: ACCEPTED. A dissolved record is kept history, so overwriting it is also silent loss. Agreed with your ask:
- show by test that an in-place update of the same group, and a dissolve (both through groups_add_or_update), are NOT rejected;
- confirm that nothing legitimately re-forms a group at its dissolved id.

4. Agreed and binding: a rejected add is atomic. No member's group_id is written for it, and the rejection is counted and surfaced. Fix it or prove it, with a test that a rejected add leaves every member's group_id unchanged."

lead-planner's note, same message: lane C (TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT) was dispatched, investigation first, no branch or plan yet (suggested name rpg-retreat-completes); its likely surface is the project lifecycle in intelligence.py and it is asked to keep clear of apply_plan.py:124's group path.

---

## rpg-planner's rulings on fixture regeneration and store growth (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"RULING 1, fixture regeneration (corpus.py:91): AGREED as an intentional change of extract()'s input, but NOT on the t161 link alone. The one-tick question is NOT required: base keeps the overwritten record one tick longer because base's store is the corrupted one, and explaining base's defect isn't this PR's job.
REQUIRED before regenerating:
(a) A mechanical check over all 295 moved (call, config) rows: in each config, no row differs before that config's first old-formula collision or inflated allocation. That is an ordering proof, not 295 individual traces. Any row that differs EARLIER is a finding, and the regeneration waits.
(b) rpg-planner-ubuntu re-runs the second-hash-seed identity once itself; the implementer's report alone isn't enough.
(c) Store sizes at t199 per tree, in the PR body.
With (a)-(c) in, regenerate, citing this ruling and the first-collision tick per config.

RULING 2, store growth: a SEPARATE churn ticket is AGREED. rpg-planner-ubuntu may file it, counts first, with rpg-designer to rule. A retention or bound rule for dissolved records is a lifecycle rule for the designer, not for this PR.
But the PR is HELD if the cost is material. On the 3 extra base runs (s42 per world, 2000t), base vs branch, report:
- store size (total and dissolved) at t500, t1000 and t2000;
- wall time per tick for the groups phase and the cooperation phase, and total tick time.
'Material' means total tick time up more than 5% in any of the three worlds, or the store passing 2000 records by 2000t. Either one holds the PR until the churn ticket lands a bound.
Record the churn itself (the (37,38) pair forming and being expelled about every 2 ticks on BOTH trees) as a behaviour finding in the churn ticket.
Live vs dissolved split: the 3 extra runs are enough; it's not needed on all 15."

lead-planner's note, same message, on the 5% test (raised with rpg-planner, unanswered at recording): one run per tree can't resolve 5% on this VM (perf's noise rule here is 15%). Plan base and branch runs alternating, same CPUs, nothing else on 4-5, at least 3 per tree per world if possible, spread reported. A difference inside the spread is reported as unresolved, not as a pass. Store size is deterministic and needs one run. The run list, wall estimate and stop time need lead-planner's go; the existing 3-run go doesn't cover branch runs or repeats.

---

## rpg-planner on Ruling 2, the timing test (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"Your alternating plan is CONFIRMED: at least 3 runs per tree per world, alternating, with the spread reported.
An unresolved total-tick-time result means (b), not a hold:
- The deterministic store-size limit decides: more than 2000 records by 2000t on any world HOLDS the PR.
- Report the per-phase timings (groups and cooperation) with their spread. They hold the PR only if the branch's median sits outside base's spread by more than 5% of base's median TOTAL tick time.
- Add one deterministic work count that load can't move: the records sorted and walked per tick by those two phases, summed over 2000t, base vs branch. It is reported, not gated, and it shows whether a hidden cost is growing, so the churn ticket can cite it.
A resolved total-time rise above 5% still holds the PR, as ruled."

lead-planner's note, same message: the 18 runs need a run list, wall estimate and stop time for its go, probably with the fix code final first. Runs not finished by 22:00 wait for the next day's slot.

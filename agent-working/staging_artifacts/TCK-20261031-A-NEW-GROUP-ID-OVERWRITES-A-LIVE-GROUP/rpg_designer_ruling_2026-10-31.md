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

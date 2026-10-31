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

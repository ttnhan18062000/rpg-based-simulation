---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP
phase: open
date: 2026-10-31
tags: [social, simulation-quality]
---

# TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP

## Title
A new group's id comes from a count, so it can collide with a live group's id and overwrite that record. Allocate group ids so they never repeat.

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`src/systems/world_systems/groups.py:308` (origin/main c5139b410):

```
new_g_id = 10000 + len(state.groups) + len(groups_add_or_update)
```

rpg-planner-ubuntu found this while verifying the SimQ trace chain. Measured on urban_political_selfmodel_probe, seed 42, 200t, PYTHONHASHSEED=0, audit_mode, at a25619971, the parent of #769. The formula is the same at d914bace7, where the same run re-issues a dissolved record's id (10004 at t104):
- t106: (12,19) takes id 10006 while (18,30), also 10006, is undissolved. (18,30) is gone from the update rows at t107.
- t113: (5,25) takes 10006 and overwrites (12,19) the same way.
- t123: (3,28) takes 10006 in the tick that dissolves (5,25).

Not yet checked: what the overwritten members' `identity.group_id` points to afterwards. The rows are `group_upd` rows, so they show what update_groups emits, not the applied store; the investigation confirms the store.

rpg-planner ruled this a separate ticket, settled before the SimQ re-anchor. The ruling is word for word as Ruling 3 in the staging file `rpg_planner_ruling_2026-10-30.md` of TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT. Its defect statement: the count includes in-place updates of existing groups (the dissolution markers at l.110 and l.170, the update at l.227), and it can collide with a live id. That is a durable-state integrity defect: a live group silently disappears. It sits on the path that produces the anchors' group objectives, so re-anchoring first would mean a second 162-run re-anchor after the fix.

## Scope
1. Investigation (ruling's list), in investigation.md before any code:
   (a) what shrinks or overwrites `state.groups` so that a count collides with a live id (removal path vs dict overwrite on apply);
   (b) what the overwritten members' `identity.group_id` points to afterwards;
   (c) whether any other site mints group ids the same way. Start from `src/engine/military_conflict.py:356` and the faction squad group id (divergence 2.141), which are other producers of group records.
2. Fix. Shape, for rpg-designer-ubuntu to confirm before implementing: ids allocated so they can never repeat, e.g. the max over all retained ids (dissolved records are kept per TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED), plus ids pending this tick, plus 1. Any counter must be typed state, not a local.
3. Tests and the hard-law style check below.
4. `Bug Fix` divergence from the ubuntu id block, and a parity entry in `docs/parity_ledger/social_narrative.yaml`. Update the Bible if it states the id rule.
5. Measure the seed-0 outcome change on the usual worlds and disclose it.

## Out of Scope
- The SimQ re-anchor and the known-red entry for test 2, which stay with TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT. This ticket changes no anchor.
- Why the parent's arbiter creates no retreat project at t62, and entity 3's later behaviour (observed leads, not traced, per the ruling).
- `registries/mechanisms.yaml` content, unless the fix changes a cited mechanism's `implemented_by`; rpg-planner supplies that note text then.

## Acceptance Criteria
1. investigation.md answers (a), (b) and (c), each with the code path and a measured or tested case.
2. A test with dissolve-then-form in the same tick and across ticks: no live group is overwritten, and every member's `group_id` resolves to a live or dissolved record. Positive control: the test fails on the old formula.
3. A hard-law style check that a GroupRecord id is never re-issued. Positive control: it fires on the old formula.
4. The seed-0 outcome change is measured and disclosed, with hashes and the moved outcomes per world.
5. Any allocation counter is typed durable state with a stable location, lifecycle and inspection visibility.
6. Divergence, parity entry and any Bible change land in the same PR; scoped tests, generate_registry --check and paths-guard pass.

## Related Tickets
- TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT (found here; its re-anchor waits for this fix to merge)
- TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED (retained dissolved records)
- TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1 (divergence 2.121, the same kind of defect for entity ids)
- TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID (divergence 2.141, another group id site)

## Related Docs
- docs/guidelines/intentional_divergences.md
- docs/parity_ledger/social_narrative.yaml

## Related Stored Artifacts
- Staging evidence/trace/ of TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT, on rpg-ubuntu-simq-anchor-bisect-impl (a50e06e0e): chain.md, key rows, planner_verify/

## Related Code Areas
- src/systems/world_systems/groups.py (l.110, l.170, l.227, l.308)
- src/engine/pipeline_phases/groups.py, src/engine/military_conflict.py, src/domains/cooperation/phase.py (other group update producers)

## Assumptions / Open Questions
- Owner DISPATCH GO #715 6540533093 and #715 6540575319, standard P1. The SimQ re-anchor waits for both this fix and TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT. Dispatch only: pushes and merge are separate asks. Branch off current origin/main (6fdfdf555 at the go). The retention trace keeps the slot first. Heavy runs for this ticket need lead-planner's go; the fresh 162-run sweep is separate, after the merge.
- If the owner prefers to re-anchor now and accept a second move later, that is the owner's call.
- Divergence id: next free in the ubuntu block at close (2.144 is B; 2.145 is likely the generator's).
- Check u24's open branches before editing, per the cross-host rule.
- Owner decision #715 6540197059: the 12 whole-key slow_known_reds entries under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE move their expiry from 2026-11-15 to 2026-11-29, no other change. rpg-planner-ubuntu owns the edit, citing that id, in the first of its PRs to reach main; it must be on main before 2026-11-15. This ticket's PR carries the edit as its only change outside scope (lead-planner, with the dispatch go), unless it would land after 2026-11-15. Tell lead-planner by 2026-11-10 if nothing is on course to land by then.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary

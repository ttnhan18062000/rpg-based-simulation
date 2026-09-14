# Test Plan — TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED

**Blocked, same reason as plan.md.** If Option 1 is chosen, minimum real coverage per this
ticket's own likely needs: a dissolved group's `GroupRecord` remains queryable in `state.groups`
with `dissolution_tick` set (not absent); `find_group_for_contract()` returns the dissolved record
rather than `None` after dissolution; each of the audited consumer sites still behaves correctly
when a dissolved-but-present record appears in `state.groups` (regression, not new behavior, for
each). Filled in once a direction is picked.

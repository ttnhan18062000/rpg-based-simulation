# Investigation — TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING

## Ticket's own original claim, checked before writing any code

Filed claiming `GroupRecord` had "no reverse reference to the contract that produced it." This is
**false in current code**. Confirmed via exhaustive grep for `contract_id` across
`src/systems/world_systems/groups.py` and `src/core/state.py`:

- `GroupRecord.contract_id: Optional[str] = None` (`src/core/state.py:669`) already exists.
- `groups.py:319` (`GroupSystem.update_groups()`'s formation block) is the **only write site** —
  set once, at group-formation time, to the real `active_contract_id` derived from scanning the
  forming leader's own active `RECRUITMENT`/social contracts. Never updated afterward.
- `groups.py:136-144` (the per-tick group-invalidation check) is the **only read site** before this
  ticket: `leader.strategic.contracts.get(group.contract_id)` — used to decide whether a group's
  founding contract is still `ACTIVE` and unexpired; if not, the group is marked invalid.

So group→contract (forward direction) is real, live, and already load-bearing.

## The actual gap

`ContractState` has no `group_id` field, and nothing scans `state.groups` keyed by contract. Given
a `contract_id`, there was no way to ask "which group (if any) did this contract's recruitment
produce" — only the reverse question was answerable.

## Design options considered

- **Option A (chosen)**: a reverse-lookup function, `GroupSystem.find_group_for_contract(state,
  contract_id) -> Optional[GroupRecord]`, a plain O(n_groups) scan over `state.groups.values()`
  matching `contract_id`. No new stored state.
- **Option B (rejected)**: mirror `contract_id` onto `ContractState` as a new `group_id` field,
  written at group formation alongside `GroupRecord.contract_id`. Rejected because it creates a
  second, independently-writable copy of the same fact — the dual-mechanism shape this arc has
  spent multiple prior tickets deleting (two mechanisms that can silently drift apart). Routed to
  peer; peer confirmed Option A for exactly this reason.

**Precedent for Option A's shape**: `ClanLifecycleService.find_clan_id_for_entity()`
(`src/systems/social_systems/clan_lifecycle.py:41-51`) is the established real precedent for a
plain O(n) reverse-lookup scan over a small collection in this codebase — justified there by real
clan counts being small in this repo's own fixtures, sorted iteration for determinism. The same
justification applies to group counts.

## Real, disclosed limitation found during investigation

Dissolved groups are removed from `state.groups` entirely: `groups.py`'s cohesion-check block
(`if len(new_member_ids) < 2: groups_remove.append(g_id)`, ~line 157) drops the group outright,
and the purpose-driven formation block does the same via `groups_remove`. Confirmed via grep: no
code path anywhere retains a dissolved group in queryable form. `GroupRecord.dissolution_tick` is a
declared field with no write site — dead at the data-model level.

This means `find_group_for_contract()` can only answer "is this contract's recruitment currently a
live group" — once the group dissolves, the record and any linkage from it disappear. Filed as a
separate ticket rather than assumed into this one's scope: `TCK-20260913-GROUP-DISSOLUTION-OUTCOME-
NOT-CAPTURED`, scoped as the open question (what to capture, where), not a chosen mechanism.

## Conclusion

Implement Option A only. `find_group_for_contract()` makes the linkage queryable while a group is
alive — real and sufficient for live checks — but does not make recruitment outcomes durable past
dissolution. That limitation is stated explicitly in the PR description per peer's instruction.

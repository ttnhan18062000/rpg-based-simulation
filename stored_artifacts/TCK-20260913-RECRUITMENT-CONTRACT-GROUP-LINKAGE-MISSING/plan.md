# Plan — TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING

## Steps

1. Correct the ticket body itself (Title, Request Summary, Scope, Out of Scope, Acceptance
   Criteria) to reflect what investigation actually found, rather than leaving the original false
   "no reverse reference exists at all" framing in place. Done first, before any code.
2. Implement `GroupSystem.find_group_for_contract(state, contract_id) -> Optional[GroupRecord]` in
   `src/systems/world_systems/groups.py`, placed immediately after `update_groups()`. Plain scan
   over `sorted(state.groups.items())` for determinism, matching on `group.contract_id ==
   contract_id`. Docstring cites `ClanLifecycleService.find_clan_id_for_entity()` as the matched
   precedent and states the dissolution limitation directly (points at the sibling ticket).
3. Add two tests to `tests/unit/social/test_domain_7_social.py` (already imports `GroupSystem`/
   `GroupRecord`, established pattern for constructing `AuthoritativeState` with `groups={...}`
   directly):
   - Finds the correct group when one exists for the contract, ignoring an unrelated group.
   - Returns `None` when no group exists for the given contract id.
4. Run regression: `tests/unit/social/test_domain_7_social.py`,
   `tests/unit/domains/cooperation/`, `tests/integration/domains/cooperation/`,
   `tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py` (also imports
   `GroupSystem`).
5. File `TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED` (todo tier, standard) scoped as the
   open question, cross-referenced in both directions.
6. `graphify update .` (src/ changed).
7. Close the ticket: staging artifacts → stored_artifacts, ticket → tickets/done, working_log
   entry, docs/REGISTRY.yaml regen, hand-orchestrated monitoring record, commit.

## Scope guard

No new field on `ContractState`. No change to `update_groups()`'s existing formation/invalidation
logic — this is purely an additive read-only lookup function alongside it.

## Acceptance-criteria map

| AC | Step |
|---|---|
| `find_group_for_contract()` implemented, cites precedent in comment | Step 2 |
| Real test evidence (finds correct group / returns None) | Step 3, verified Step 4 |
| No regression in cooperation/world test suites | Step 4 |
| Dissolution-outcome ticket filed, cross-referenced both directions | Step 5 |

# TCK-20260610-FALLBACK-RECORDS-REMOVAL

## Title
Graduated removal of fallback records by family after catalog equivalents verified

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Phase 44.3. Remove or quarantine hardcoded fallback records in graduated order, one family at a time, after verifying catalog equivalents exist and all parity/strict tests pass. Removal order: items → recipes → services → regions → enemy projections → legacy enemy registry fallback → legacy role/faction-only content. Each family requires a full verification cycle before removal.

## Scope
Per-family workflow for each of the 7 families:
1. Verify catalog equivalent exists
2. Verify adapter equivalent if needed
3. Run registry parity tests
4. Run strict matrix
5. Remove or quarantine fallback records
6. Update migration map
7. Confirm existing tests pass in intended modes

Families in order:
- `items` — fallback item definitions
- `recipes` — fallback recipe definitions
- `services` — fallback service definitions
- `regions` — fallback region definitions
- `enemy_projections` — hardcoded enemy projection records
- `legacy_enemy_registry_fallback` — registry-level fallback for unknown enemies
- `legacy_role_faction_only` — content that depends solely on enum role/faction

## Out of Scope
- Removing compatibility projection adapters (these may remain permanently)
- Deleting test infrastructure for legacy modes
- Processing all families in one commit (each family is a discrete change)

## Acceptance Criteria
- [ ] Each family has complete catalog replacement before removal
- [ ] Each family has passing registry parity tests after removal
- [ ] Each family has passing strict matrix after removal
- [ ] Fallback records removed or quarantined (not silently ignored)
- [ ] Migration map updated after each family
- [ ] No hidden fallback usage remains after each family removal
- [ ] Existing tests still pass in their intended modes after each removal

## Related Tickets
- TCK-20260610-FALLBACK-RETIREMENT-CRITERIA (prerequisite — criteria gates must pass)
- TCK-20260610-FALLBACK-RESTRICT-MODES (prerequisite — restriction must be in place first)

## Related Docs
- `docs/guidelines/fallback_retirement_criteria.md`
- `docs/guidelines/v2_intentional_divergences.md`

## Related Code Areas
- `src/content/registry.py` — fallback record storage
- `src/content/repository.py` — catalog loading
- `data/content/` — catalog replacement records

## Assumptions / Open Questions
- This ticket may naturally split into 7 sub-tickets (one per family) during implementation. If so, create hotfix-tier child tickets and reference them here.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->

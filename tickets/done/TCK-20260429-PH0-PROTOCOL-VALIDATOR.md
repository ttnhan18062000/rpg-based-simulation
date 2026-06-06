# TCK-20260429-PH0-PROTOCOL-VALIDATOR

## Title
Implement Phase 0 Protocol Validator

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement an authoritative validation tool that checks the exhaustive semantic ledger (`logic_checklist_exhaustive_v2.md`) against the actual code implementation to prevent "logic drift."

## Scope
- Create `scripts/protocol_validator.py`
- Regex-based parsing of the checklist (`[x]` items and their `VERIFIED v2` tags)
- Recursive source scanning of `src/` and `tests/` for verification markers
- Comparison of checklist items vs source markers
- Summary report generation (total items, checked items, missing markers, extra markers)
- CI-friendly exit codes

## Out of Scope
- Automated fixing of missing markers
- Integration with external tracking tools (Jira, etc.)

## Acceptance Criteria
- [ ] `protocol_validator.py` exists in `scripts/`
- [ ] Parses `logic_checklist_exhaustive_v2.md` correctly
- [ ] Correctness: If an item is `[x]` but has no `VERIFIED v2` marker in the source, it reports a failure
- [ ] Correctness: If an item has a marker but is `[ ]` in the checklist, it reports a warning
- [ ] Summary report displays coverage percentage
- [ ] Exit code 1 if any checked item is missing its trace

## Related Tickets
- None

## Related Docs
- logic_checklist_exhaustive_v2.md
- resource_v2_e3_phases_enhanced.md

## Related Code Areas
- All source files (for markers)

## Assumptions / Open Questions
- Marker format: `VERIFIED v2: <item_name>` or similar.
- I will use the item name found in the checklist comment (e.g., `test_stamina_drain_on_attack`).

## Implementation Notes
- I'll use `re` for parsing and `os.walk` for scanning.
- Verification markers should look like `<!-- VERIFIED v2: ... -->` in markdown or `# VERIFIED v2: ...` in python.

## Test Summary
- None yet.

## Files Changed
- None yet.

## Completion Summary
- None yet.
